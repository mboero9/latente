"""Scheduler persistente, un líder por PostgreSQL; no requiere Redis ni Celery."""

import logging
import argparse
import os
import signal
import threading
import time
from datetime import timedelta
from sqlalchemy import select, text, delete, or_
from .config import settings
from .db import engine, session_scope
from .models import League, Fixture, SyncJob, WorkerState, utcnow
from .ingest import (
    upsert,
    save_fixtures,
    save_teams,
    save_standings,
    save_scorers,
    LIVE,
)
from .provider import FootballClient, Deferred, ProviderError

log = logging.getLogger("latente.worker")
stop = threading.Event()


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
    matched = 0
    for row in rows:
        league = row["league"]
        if league["id"] not in settings.league_ids:
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
        for kind in ("fixtures", "teams", "standings", "scorers"):
            coverage = season.get("coverage") or {}
            if kind == "standings" and coverage.get("standings") is False:
                continue
            if kind == "scorers" and coverage.get("top_scorers") is False:
                continue
            key = f"{kind}:{league['id']}:{season['year']}"
            active_keys.add(key)
            ensure_job(s, key, kind, params)
        matched += 1
    if not matched:
        raise ValueError("El catálogo no contiene las ligas configuradas")
    s.execute(delete(SyncJob).where(SyncJob.key.not_in(active_keys)))


def live_ids(s, now):
    # Refrescar por ID permite ver FT/PEN: un encuentro que termina desaparece de live=all.
    q = select(Fixture.id).where(
        Fixture.source == "api",
        Fixture.league_id.in_(settings.league_ids),
        Fixture.kickoff >= now - timedelta(hours=36),
        Fixture.kickoff <= now + timedelta(minutes=5),
        or_(
            Fixture.status.in_(LIVE),
            (Fixture.status.in_(["NS", "TBD"]))
            & (Fixture.kickoff >= now - timedelta(hours=4)),
        ),
    )
    return list(s.scalars(q.order_by(Fixture.updated_at, Fixture.id).limit(20)))


def execute_job(client, kind, params):
    if kind == "catalog":
        rows = client.get("/leagues", {})
        with session_scope() as s:
            save_catalog(s, rows)
        return 86400
    if kind == "live":
        with session_scope() as s:
            ids = live_ids(s, utcnow())
        if not ids:
            return min(settings.live_seconds, 300)
        rows = client.get("/fixtures", {"ids": "-".join(map(str, ids))})
        with session_scope() as s:
            save_fixtures(s, rows, settings.league_ids)
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
            save_fixtures(s, rows, settings.league_ids)
        elif kind == "teams":
            save_teams(s, rows, params["league"], params["season"])
        elif kind == "standings":
            save_standings(s, rows, params["league"], params["season"])
        else:
            save_scorers(s, rows, params["league"], params["season"])
    return {
        "fixtures": settings.fixtures_seconds,
        "teams": 604800,
        "standings": settings.tables_seconds,
        "scorers": settings.scorers_seconds,
    }[kind]


def heartbeat(message):
    with session_scope() as s:
        upsert(
            s,
            WorkerState,
            dict(source=settings.mode, heartbeat=utcnow(), message=message),
        )


def tick(client):
    heartbeat("Actualización automática activa")
    with session_scope() as s:
        job = s.scalar(
            select(SyncJob)
            .where(SyncJob.next_run <= utcnow())
            .order_by(SyncJob.next_run, SyncJob.key)
            .limit(1)
        )
        if not job:
            return False
        key, kind, params, failures = job.key, job.kind, job.params, job.failures
    try:
        seconds = execute_job(client, kind, params)
        with session_scope() as s:
            job = s.get(SyncJob, key)
            if job:
                job.next_run = utcnow() + timedelta(seconds=seconds)
                job.last_success, job.failures, job.message = utcnow(), 0, None
        log.info("sync_ok kind=%s key=%s", kind, key)
    except Deferred as exc:
        with session_scope() as s:
            job = s.get(SyncJob, key)
            job.next_run, job.message = exc.until, exc.message
        heartbeat(exc.message)
    except Exception as exc:
        delay = min(3600, 60 * 2 ** min(failures, 6))
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
