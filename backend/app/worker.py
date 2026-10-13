"""Scheduler persistente, un líder por PostgreSQL; no requiere Redis ni Celery."""

import logging
import argparse
import os
import signal
import threading
import time
from datetime import timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select, text, delete, update, or_, case, func
from .config import settings
from .db import engine, session_scope
from .models import League, Fixture, FixtureStatistics, FixtureDetails, SyncJob, WorkerState, ApiUsage, utcnow
from .ingest import (
    upsert,
    save_fixtures,
    save_teams,
    save_standings,
    save_scorers,
    save_statistics,
    LIVE,
    FINISHED,
)
from .provider import FootballClient, Deferred, ProviderError, aware
from .match_details import store_details

log = logging.getLogger("latente.worker")
stop = threading.Event()
background_turn = 0


def ensure_job(s, key, kind, params, at=None):
    if not s.get(SyncJob, key):
        s.add(SyncJob(key=key, kind=kind, params=params, next_run=at or utcnow()))


def save_catalog(s, rows):
    overrides = dict(
        part.split(":", 1)
        for part in os.getenv("SEASON_OVERRIDES", "").split(",")
        if part.strip()
    )
    active_keys = {"catalog", "live"}
    if settings.all_leagues:
        active_keys.add("settle")
        ensure_job(s, "settle", "settle", {}, utcnow() + timedelta(minutes=2))
        # Ventana móvil global: dos días previos y siete próximos. Una llamada
        # por fecha sustituye miles de consultas de fixtures por liga.
        for offset in ((0, -1, 1) if settings.profile == "free" else (0, -1, 1, -2, 2, 3, 4, 5, 6, 7)):
            key = f"day:{offset}"
            active_keys.add(key)
            ensure_job(s, key, "day", {"offset": offset})
    priority = {league_id: i for i, league_id in enumerate(settings.league_ids)}
    rows = sorted(rows, key=lambda r: (
        0 if r.get("country", {}).get("name") == "Argentina" else 1,
        priority.get(r["league"]["id"], 1000), r["league"]["id"],
    ))
    matched = 0
    for row in rows:
        league = row["league"]
        if not settings.accepts_league(league["id"]):
            continue
        seasons = row.get("seasons") or []
        if not seasons:
            continue
        ordered = sorted(
            seasons, key=lambda x: (bool(x.get("current")), x["year"]), reverse=True
        )
        season = next(
            (x for x in seasons if str(x["year"]) == overrides.get(str(league["id"]))),
            ordered[0],
        )
        if (
            str(league["id"]) in overrides
            and str(season["year"]) != overrides[str(league["id"])]
        ):
            raise ValueError("SEASON_OVERRIDES contiene una temporada no disponible")
        upsert(
            s,
            League,
            dict(
                source="api",
                id=league["id"],
                name=league["name"],
                kind=league["type"],
                country=row["country"]["name"],
                season=season["year"],
                seasons=[x["year"] for x in seasons],
                coverage=season.get("coverage") or {},
                updated_at=utcnow(),
            ),
        )
        params = {"league": league["id"], "season": season["year"]}
        matched += 1
        # Los planes pagos importan competiciones importantes y todas las
        # categorías argentinas presentes en el catálogo, nunca miles de
        # ligas sin prioridad.
        is_argentina = (row.get("country") or {}).get("name") == "Argentina"
        is_priority = league["id"] in settings.league_ids or is_argentina
        if settings.profile == "free" and settings.all_leagues:
            continue
        if settings.all_leagues and not is_priority:
            continue
        if settings.all_leagues and not season.get("current") and not is_argentina and str(league["id"]) not in overrides:
            # Conservamos el último año conocido cuando no hay activo.
            pass
        # Datos completos por temporada (tabla, clubes, goleadores y fixtures).
        years = [season["year"]]
        if settings.profile == "live":
            # Archivo acotado: 2025 y 2024, priorizando grandes ligas y AFA.
            history = [y["year"] for y in seasons if y["year"] < season["year"] and y["year"] >= 2024]
            years.extend(sorted(history, reverse=True)[:2])
        for year in dict.fromkeys(years):
            season_info = next((x for x in seasons if x["year"] == year), None)
            coverage = (season_info or {}).get("coverage") or {}
            params = {"league": league["id"], "season": year}
            for kind in ("fixtures", "teams", "standings", "scorers"):
                if kind == "standings" and coverage.get("standings") is False:
                    continue
                if kind == "scorers" and coverage.get("top_scorers") is False:
                    continue
                key = f"{kind}:{league['id']}:{year}"
                active_keys.add(key)
                ensure_job(s, key, kind, params, utcnow() + timedelta(seconds=matched))

    if not matched:
        raise ValueError("El catálogo no contiene las ligas configuradas")
    s.execute(delete(SyncJob).where(SyncJob.key.not_in(active_keys), SyncJob.kind.not_in(("statistics", "details"))))


def sync_fixture_rows(s, rows):
    save_fixtures(s, rows, settings.allowed_leagues)
    # Máximo dos fichas enriquecidas nuevas por día en Free (hasta 4 requests),
    # para reservar cuota a los resultados. En planes amplios refrescar vivo.
    now = utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    already_done = s.scalar(select(func.count()).select_from(FixtureDetails).where(
        FixtureDetails.source == "api", FixtureDetails.updated_at >= start_of_day
    )) or 0
    queued = s.scalar(select(func.count()).select_from(SyncJob).where(
        SyncJob.kind == "details"
    )) or 0
    capacity = max(0, (2 if settings.profile == "free" else 12) - already_done - queued)
    selected = sorted(
        (r for r in rows if r["fixture"]["status"]["short"] in LIVE | FINISHED),
        key=lambda r: (
            0 if r["league"]["id"] in settings.league_ids else 1,
            0 if r["fixture"]["status"]["short"] in LIVE else 1,
            r["fixture"]["id"],
        ),
    )
    for raw in selected:
        if capacity <= 0:
            break
        fixture_id = raw["fixture"]["id"]
        fixture = s.get(Fixture, ("api", fixture_id))
        if not fixture or not settings.accepts_league(fixture.league_id):
            continue
        old = s.get(FixtureDetails, ("api", fixture_id))
        if old and (settings.profile == "free" or fixture.status in FINISHED):
            continue
        key = f"details:{fixture_id}"
        if s.get(SyncJob, key):
            continue
        ensure_job(s, key, "details", {"fixture": fixture_id})
        capacity -= 1
    if settings.profile == "free":
        return
    for raw in rows:
        if not settings.accepts_league(raw["league"]["id"]):
            continue
        fixture = s.get(Fixture, ("api", raw["fixture"]["id"]))
        if not fixture or fixture.status not in LIVE | FINISHED:
            continue
        # No generar miles de trabajos históricos al importar una temporada.
        if aware(fixture.kickoff) < now - timedelta(days=2):
            continue
        league = s.get(League, ("api", fixture.league_id))
        coverage = (league.coverage.get("fixtures") or {}) if league else {}
        if coverage.get("statistics_fixtures") is not True:
            continue
        previous = s.get(FixtureStatistics, ("api", fixture.id))
        # Tras el cierre y una captura final no recrear tareas ya completadas.
        if fixture.status in FINISHED and previous and aware(previous.updated_at) >= aware(fixture.kickoff) + timedelta(hours=4):
            continue
        ensure_job(s, f"statistics:{fixture.id}", "statistics", {"fixture": fixture.id})


def live_ids(s, now, stale_before=None):
    # Refrescar por ID permite ver FT/PEN: un encuentro que termina desaparece de live=all.
    q = select(Fixture.id).where(
        Fixture.source == "api",
        Fixture.kickoff >= now - timedelta(hours=36),
        Fixture.kickoff <= now + timedelta(minutes=5),
        or_(
            Fixture.status.in_(LIVE),
            (Fixture.status.in_(["NS", "TBD"]))
            & (Fixture.kickoff >= now - timedelta(hours=4)),
        ),
    )
    if not settings.all_leagues:
        q = q.where(Fixture.league_id.in_(settings.league_ids))
    if stale_before:
        q = q.where(Fixture.updated_at < stale_before)
    return list(s.scalars(q.order_by(Fixture.updated_at, Fixture.id).limit(20)))


def execute_job(client, kind, params):
    if kind == "details":
        with session_scope() as s:
            fixture = s.get(Fixture, ("api", params["fixture"]))
            if not fixture or not settings.accepts_league(fixture.league_id):
                return None
            if settings.profile == "free" and s.get(FixtureDetails, ("api", fixture.id)):
                return None
            completed = fixture.status in FINISHED
        # Dos endpoints básicos, uno adicional de ratings solo en perfil amplio.
        events = client.get("/fixtures/events", {"fixture": params["fixture"]})
        lineups = client.get("/fixtures/lineups", {"fixture": params["fixture"]})
        ratings = (
            client.get("/fixtures/players", {"fixture": params["fixture"]})
            if settings.profile == "live" and completed else None
        )
        with session_scope() as s:
            store_details(s, params["fixture"], events, lineups, ratings)
        return None if settings.profile == "free" or completed else 600
    if kind == "statistics":
        with session_scope() as s:
            fixture = s.get(Fixture, ("api", params["fixture"]))
            if not fixture or not settings.accepts_league(fixture.league_id):
                return None
            league = s.get(League, ("api", fixture.league_id))
            if not league or (league.coverage.get("fixtures") or {}).get("statistics_fixtures") is not True:
                return None
            if aware(fixture.kickoff) < utcnow() - timedelta(days=2):
                return None
            terminal = fixture.status in FINISHED
            if fixture.status not in LIVE | FINISHED:
                return None
            close_snapshot = terminal and utcnow() >= aware(fixture.kickoff) + timedelta(hours=4)
        rows = client.get("/fixtures/statistics", {"fixture": params["fixture"]})
        with session_scope() as s:
            save_statistics(s, rows, params["fixture"])
        return None if close_snapshot else (3600 if terminal else settings.statistics_seconds)
    if kind == "catalog":
        rows = client.get("/leagues", {})
        log.info("provider_catalog_rows=%s", len(rows))
        with session_scope() as s:
            save_catalog(s, rows)
            count = s.scalar(select(func.count()).select_from(League).where(League.source == "api"))
        log.info("catalog_leagues_saved=%s", count)
        return 86400
    if kind == "day":
        offset = params["offset"]
        day = utcnow().astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date() + timedelta(days=offset)
        rows = client.get("/fixtures", {"date": day.isoformat(), "timezone": "America/Argentina/Buenos_Aires"})
        log.info("provider_day_rows offset=%s count=%s", offset, len(rows))
        with session_scope() as s:
            sync_fixture_rows(s, rows)
            fixture_count = s.scalar(select(func.count()).select_from(Fixture).where(Fixture.source == "api"))
        log.info("day_synced offset=%s total_fixtures=%s", offset, fixture_count)
        if settings.profile == "free":
            return 86400
        return 900 if offset == 0 else (3600 if abs(offset) == 1 else 86400)
    if kind == "live" and settings.all_leagues:
        rows = client.get("/fixtures", {"live": "all"})
        log.info("provider_live_rows=%s", len(rows))
        with session_scope() as s:
            sync_fixture_rows(s, rows)
        return settings.live_seconds
    if kind in {"live", "settle"}:
        with session_scope() as s:
            now = utcnow()
            ids = live_ids(s, now, now - timedelta(seconds=max(120, settings.live_seconds * 2)) if kind == "settle" else None)
        if not ids:
            return min(settings.live_seconds, 300)
        rows = client.get("/fixtures", {"ids": "-".join(map(str, ids))})
        with session_scope() as s:
            sync_fixture_rows(s, rows)
        return settings.live_seconds
    endpoint = {
        "fixtures": "/fixtures",
        "teams": "/teams",
        "standings": "/standings",
        "scorers": "/players/topscorers",
    }[kind]
    rows = client.get(endpoint, params)
    with session_scope() as s:
        if kind == "fixtures":
            sync_fixture_rows(s, rows)
        elif kind == "teams":
            save_teams(s, rows, params["league"], params["season"])
        elif kind == "standings":
            save_standings(s, rows, params["league"], params["season"])
        else:
            save_scorers(s, rows, params["league"], params["season"])
    interval = {
        "fixtures": settings.fixtures_seconds,
        "teams": 604800,
        "standings": settings.tables_seconds,
        "scorers": settings.scorers_seconds,
    }[kind]
    if settings.all_leagues and params["league"] not in settings.league_ids:
        # Miles de competiciones no deben multiplicar el refresco horario.
        interval = max(interval, 86400)
    return interval


def heartbeat(message):
    with session_scope() as s:
        upsert(
            s,
            WorkerState,
            dict(source=settings.mode, heartbeat=utcnow(), message=message),
        )


def tick(client):
    global background_turn
    # Turnos equilibrados: uno a importacion de temporadas, otro a
    # estadisticas/fichas y uno a resultados en vivo. Evita que una sola
    # categoria con muchos trabajos pendientes monopolice los turnos.
    background_turn = (background_turn + 1) % 3
    heartbeat("Actualización automática activa")
    realtime = ["live", "settle", "day"]
    bulk = ["standings", "scorers", "teams", "fixtures"]
    with session_scope() as s:
        job = s.scalar(
            select(SyncJob)
            .where(SyncJob.next_run <= utcnow())
            .order_by(
                case(
                    (SyncJob.kind == "catalog", 0),
                    (SyncJob.kind.in_(realtime), 1 if background_turn == 0 else 3),
                    (SyncJob.kind.in_(bulk), 1 if background_turn == 1 else 3),
                    (SyncJob.kind.in_(["statistics", "details"]), 1 if background_turn == 2 else 4),
                    else_=5,
                ),
                # Primero la competición prioritaria y la temporada actual;
                # después standings, goleadores, clubes y resultados.
                # Evita traer tablas de 2024 de decenas de ligas mientras
                # Champions 2026 sigue sin goleadores.
                case(
                    *[(SyncJob.params["league"].as_integer() == league_id, rank)
                      for rank, league_id in enumerate(settings.league_ids)],
                    else_=len(settings.league_ids) + 1,
                ),
                SyncJob.params["season"].as_integer().desc(),
                case(
                    (SyncJob.kind == "standings", 0),
                    (SyncJob.kind == "scorers", 1),
                    (SyncJob.kind == "teams", 2),
                    (SyncJob.kind == "fixtures", 3),
                    else_=4,
                ),
                SyncJob.next_run, SyncJob.key,
            )
            .limit(1)
        )
        if not job:
            return False
        key, kind, params, failures = job.key, job.kind, job.params, job.failures
    try:
        seconds = execute_job(client, kind, params)
        with session_scope() as s:
            job = s.get(SyncJob, key)
            if job and seconds is None:
                s.delete(job)
            elif job:
                job.next_run = utcnow() + timedelta(seconds=seconds)
                job.last_success, job.failures, job.message = utcnow(), 0, None
        log.info("sync_ok kind=%s key=%s", kind, key)
    except Deferred as exc:
        with session_scope() as s:
            job = s.get(SyncJob, key)
            job.next_run, job.message = exc.until, exc.message
        heartbeat(exc.message)
    except Exception as exc:
        # Restricciones de temporada/plan no se resuelven reintentando cada minuto.
        plan_blocked = isinstance(exc, ProviderError) and ": plan" in str(exc)
        delay = 86400 if plan_blocked else min(3600, 60 * 2 ** min(failures, 6))
        with session_scope() as s:
            job = s.get(SyncJob, key)
            job.failures += 1
            job.next_run = utcnow() + timedelta(seconds=delay)
            job.message = (
                str(exc)[:180]
                if isinstance(exc, ProviderError)
                else f"No se pudo actualizar ({type(exc).__name__}); se reintentará"
            )
        # Nunca volcar requests, headers o variables con secretos en logs.
        reason = str(exc) if isinstance(exc, ProviderError) else type(exc).__name__
        log.warning("sync_failed key=%s reason=%s retry_in=%s", key, reason, delay)
    return True


def run(once=False, max_seconds=120):
    deadline = time.monotonic() + max_seconds if once else float("inf")
    # Lock de sesión (no de transacción); liberar automáticamente al perder conexión.
    with engine.connect() as leader:
        if not leader.scalar(text("SELECT pg_try_advisory_lock(67120834)")):
            log.info("Ya existe un worker activo; este proceso finaliza")
            return
        with session_scope() as s:
            if settings.mode == "api":
                ensure_job(s, "catalog", "catalog", {})
                ensure_job(s, "live", "live", {}, utcnow() + timedelta(seconds=60))
                # Si el catálogo se creó antes del upgrade Free→Pro y aún no
                # existen trabajos por temporada, forzar su reconstrucción.
                # Es idempotente: al crear los trabajos deja de activarse.
                if settings.profile == "live":
                    bulk_count = s.scalar(select(func.count()).select_from(SyncJob).where(
                        SyncJob.kind.in_(("standings", "scorers", "teams", "fixtures"))
                    )) or 0
                    if bulk_count == 0:
                        catalog = s.get(SyncJob, "catalog")
                        if catalog:
                            catalog.next_run = utcnow()
                        log.info("pro_backfill_catalog_required: no season jobs queued")
                # Una única recuperación adicional: también adelantar tareas
                # por temporada que quedaron programadas para el día siguiente
                # cuando aún se usaba el perfil Free.
                if settings.profile == "live" and not s.get(WorkerState, "proback"):
                    now = utcnow()
                    pending = s.execute(update(SyncJob).where(
                        SyncJob.kind.in_(("standings", "scorers", "teams", "fixtures"))
                    ).values(next_run=now, failures=0, message=None))
                    s.add(WorkerState(
                        source="proback", heartbeat=now,
                        message="Importaciones Pro reprogramadas una sola vez"
                    ))
                    log.info("pro_season_recovery_jobs=%s", pending.rowcount)
                # Recuperación idempotente al activar Pro: reintentar trabajos
                # bloqueados previamente por el plan Free sin aguardar 24 h.
                if settings.profile == "live" and not s.get(WorkerState, "proboot"):
                    now = utcnow()
                    s.execute(update(SyncJob).where(
                        SyncJob.message.ilike("%plan%")
                    ).values(next_run=now, failures=0, message=None))
                    s.execute(update(ApiUsage).where(
                        ApiUsage.day == now.date(),
                        ApiUsage.provider_remaining == 0,
                    ).values(provider_remaining=None, blocked_until=None))
                    s.add(WorkerState(source="proboot", heartbeat=now, message="Pro habilitado"))
                # El plan gratuito solo consulta la ventana de días ya validada.
                # Limpiar trabajos heredados del perfil de pago tras un cambio de modo.
                if settings.all_leagues and settings.profile == "free":
                    s.execute(delete(SyncJob).where(
                        SyncJob.kind == "day",
                        SyncJob.key.not_in(("day:0", "day:-1", "day:1")),
                    ))
                    s.execute(delete(SyncJob).where(
                        SyncJob.kind.in_(("fixtures", "teams", "standings", "scorers", "statistics"))
                    ))
        client = FootballClient()
        try:
            if once and settings.mode == "api" and not settings.api_key:
                heartbeat("Falta configurar API_FOOTBALL_KEY")
                return
            while not stop.is_set() and time.monotonic() < deadline:
                # Fallar y reiniciar si se pierde la conexión que mantiene el liderazgo.
                leader.execute(text("SELECT 1"))
                if settings.mode == "demo":
                    from .demo import seed_demo

                    with session_scope() as s:
                        seed_demo(s)
                    heartbeat("Demostración: datos ficticios")
                    if once:
                        break
                    stop.wait(30)
                else:
                    worked = tick(client)
                    if once and not worked:
                        break
                    pause = settings.minimum_gap if once else 2
                    stop.wait(min(pause, max(0, deadline - time.monotonic())))
        finally:
            client.close()
            if not leader.invalidated:
                leader.execute(text("SELECT pg_advisory_unlock(67120834)"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Procesar pendientes y salir")
    parser.add_argument("--max-seconds", type=int, default=120)
    args = parser.parse_args()
    if args.max_seconds < 1:
        parser.error("--max-seconds debe ser positivo")
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    try:
        run(args.once, args.max_seconds)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
