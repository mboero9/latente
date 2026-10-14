from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func, or_, text
from .config import settings
from .db import session_scope
from .models import (
    League,
    Fixture,
    FixtureStatistics,
    FixtureDetails,
    Team,
    Standing,
    Scorer,
    Membership,
    SyncJob,
    ApiUsage,
    WorkerState,
    utcnow,
)
from .ingest import LIVE
from .provider import aware
from .partial_standings import partial_standings


@asynccontextmanager
async def lifespan(app):
    if settings.mode == "demo":
        from .demo import seed_demo

        with session_scope() as s:
            seed_demo(s)
    yield


app = FastAPI(
    title="Latente API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.origins),
    allow_methods=["GET"],
    allow_headers=["Accept"],
    allow_credentials=False,
)


@app.middleware("http")
async def cache_policy(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def public(row):
    return {
        c.name: getattr(row, c.name)
        for c in row.__table__.columns
        if c.name != "source"
    }


def meta(rows=(), **extra):
    updated = [aware(r.updated_at) for r in rows if getattr(r, "updated_at", None)]
    return dict(
        mode=settings.mode,
        provider="Demostración" if settings.mode == "demo" else "API-Football",
        fetched_at=utcnow(),
        updated_at=max(updated) if updated else None,
        **extra
    )


def league_or_404(s, league_id):
    league = s.get(League, (settings.mode, league_id))
    if not league or (settings.mode == "api" and not settings.accepts_league(league_id)):
        raise HTTPException(404, "Liga no encontrada")
    return league


def match_payload(s, rows):
    if not rows:
        return []
    team_ids = {i for r in rows for i in (r.home_id, r.away_id)}
    league_ids = {r.league_id for r in rows}
    teams = {
        t.id: public(t)
        for t in s.scalars(
            select(Team).where(Team.source == settings.mode, Team.id.in_(team_ids))
        )
    }
    leagues = {
        l.id: public(l)
        for l in s.scalars(
            select(League).where(
                League.source == settings.mode, League.id.in_(league_ids)
            )
        )
    }
    now = utcnow()
    return [
        {
            **public(r),
            "home": teams[r.home_id],
            "away": teams[r.away_id],
            "league": leagues[r.league_id],
            "stale": settings.mode == "api"
            and r.status in LIVE
            and (now - aware(r.updated_at)).total_seconds()
            > max(120, settings.live_seconds * 2),
        }
        for r in rows
    ]


def date_window(day: date, tz: str):
    try:
        zone = ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(422, "Zona horaria inválida")
    start = datetime.combine(day, time.min, zone)
    return start.astimezone(timezone.utc), (start + timedelta(days=1)).astimezone(
        timezone.utc
    )


@app.get("/api/health")
def health():
    with session_scope() as s:
        s.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/api/status")
def status():
    with session_scope() as s:
        state = s.get(WorkerState, settings.mode)
        usage = s.get(ApiUsage, utcnow().date()) if settings.mode == "api" else None
        failures = (
            s.scalar(
                select(func.count()).select_from(SyncJob).where(SyncJob.failures > 0)
            )
            if settings.mode == "api"
            else 0
        )
        success = (
            s.scalar(select(func.max(SyncJob.last_success)))
            if settings.mode == "api"
            else None
        )
        healthy = bool(
            state
            and (utcnow() - aware(state.heartbeat)).total_seconds()
            < settings.worker_heartbeat_timeout
        )
        fixture_total = s.scalar(
            select(func.count()).select_from(Fixture).where(Fixture.source == settings.mode)
        )
        start, end = date_window(utcnow().astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date(), "America/Argentina/Buenos_Aires")
        fixture_today = s.scalar(
            select(func.count()).select_from(Fixture).where(
                Fixture.source == settings.mode,
                Fixture.kickoff >= start,
                Fixture.kickoff < end,
            )
        )
        restricted_jobs = s.scalar(
            select(func.count()).select_from(SyncJob).where(
                SyncJob.message.ilike("%plan%")
            )
        ) if settings.mode == "api" else 0
        return {
            "data": {
                "mode": settings.mode,
                "worker_online": healthy,
                "heartbeat": state.heartbeat if state else None,
                "message": (
                    state.message if state else "Esperando primera sincronización"
                ),
                "last_success": success,
                "failed_jobs": failures,
                "requests_today": usage.requests if usage else 0,
                "daily_budget": settings.daily_budget,
                "quota_exhausted": bool(
                    usage
                    and (
                        usage.requests >= settings.daily_budget
                        or usage.provider_remaining == 0
                    )
                ),
                "live_interval_seconds": settings.live_seconds,
                "statistics_interval_seconds": settings.statistics_seconds,
                "display_refresh_seconds": 5,
                "profile": settings.profile,
                "configured": settings.mode == "demo" or bool(settings.api_key),
                "provider_configured": bool(settings.api_key),
                "league_scope": settings.league_scope,
                "leagues_loaded": s.scalar(select(func.count()).select_from(League).where(League.source == settings.mode)),
                "fixtures_loaded": fixture_total,
                "fixtures_today": fixture_today,
                "restricted_jobs": restricted_jobs,
            },
            "meta": meta(),
        }


@app.get("/api/leagues")
def leagues():
    with session_scope() as s:
        q = select(League).where(League.source == settings.mode)
        if settings.mode == "api" and not settings.all_leagues:
            q = q.where(League.id.in_(settings.league_ids))
        rows = list(s.scalars(q))
        order = {id: i for i, id in enumerate(settings.league_ids)}
        rows.sort(key=lambda r: (0 if r.country == "Argentina" else 1, order.get(r.id, 1000), r.country, r.name))
        known = {}
        for league_id, season in s.execute(
            select(Membership.league_id, Membership.season)
            .where(Membership.source == settings.mode)
            .distinct()
        ):
            known.setdefault(league_id, []).append(season)
        return {
            "data": [
                {
                    **public(r),
                    "loaded_seasons": sorted(known.get(r.id, [r.season]), reverse=True),
                }
                for r in rows
            ],
            "meta": meta(rows),
        }


@app.get("/api/fixtures")
def fixtures(
    day: date = Query(alias="date"),
    tz: str = "America/Argentina/Buenos_Aires",
    league_id: int | None = None,
    live: bool = False,
    limit: int = Query(150, ge=1, le=300),
    offset: int = Query(0, ge=0),
):
    start, end = date_window(day, tz)
    with session_scope() as s:
        # El filtro «En vivo» muestra encuentros activos de cualquier zona
        # horaria, aunque su fecha local sea ayer o mañana.
        q = select(Fixture).where(Fixture.source == settings.mode)
        if not live:
            q = q.where(Fixture.kickoff >= start, Fixture.kickoff < end)
        if settings.mode == "api" and not settings.all_leagues:
            q = q.where(Fixture.league_id.in_(settings.league_ids))
        if league_id:
            q = q.where(Fixture.league_id == league_id)
        if live:
            q = q.where(Fixture.status.in_(LIVE))
        total = s.scalar(select(func.count()).select_from(q.subquery()))
        rows = list(
            s.scalars(
                q.order_by(Fixture.kickoff, Fixture.id).offset(offset).limit(limit)
            )
        )
        return {
            "data": match_payload(s, rows),
            "meta": meta(rows, total=total, offset=offset, limit=limit),
        }


@app.get("/api/leagues/{league_id}/bracket")
def league_bracket(league_id: int, season: int | None = None):
    """Bracket de encuentros realmente importados, no un fixture inventado."""
    from .brackets import bracket_rows
    with session_scope() as db:
        league = league_or_404(db, league_id)
        year = season or league.season
        fixtures = list(db.scalars(select(Fixture).where(
            Fixture.source == settings.mode,
            Fixture.league_id == league_id,
            Fixture.season == year,
        ).order_by(Fixture.kickoff, Fixture.id)))
        matches = match_payload(db, fixtures)
        stages = bracket_rows(matches)
        return {
            "data": {"stages": stages, "season": year, "league": league.name},
            "meta": meta(fixtures, coverage=bool(stages),
                         verified_matches=sum(len(x["matches"]) for x in stages),
                         note="Etapas verificadas; conexiones entre cruces no inferidas"),
        }


@app.get("/api/leagues/{league_id}/recent")
def league_recent(league_id: int, season: int | None = None):
    """Últimos partidos terminados y próximos encuentros de la temporada almacenada."""
    with session_scope() as s:
        league = league_or_404(s, league_id)
        year = season or league.season
        base = (Fixture.source == settings.mode, Fixture.league_id == league_id,
                Fixture.season == year)
        done = list(s.scalars(select(Fixture).where(
            *base, Fixture.status.in_(["FT", "AET", "PEN"]),
        ).order_by(Fixture.kickoff.desc(), Fixture.id.desc()).limit(12)))
        upcoming = list(s.scalars(select(Fixture).where(
            *base, Fixture.kickoff >= utcnow(),
            Fixture.status.in_(["NS", "TBD"]),
        ).order_by(Fixture.kickoff, Fixture.id).limit(12)))
        return {"data": {
            "recent": match_payload(s, done),
            "upcoming": match_payload(s, upcoming),
        }, "meta": meta(done + upcoming, season=year)}


@app.get("/api/fixtures/{fixture_id}")
def fixture(fixture_id: int):
    with session_scope() as s:
        row = s.get(Fixture, (settings.mode, fixture_id))
        if not row:
            raise HTTPException(404, "Partido no encontrado")
        league_or_404(s, row.league_id)
        return {"data": match_payload(s, [row])[0], "meta": meta([row])}


@app.get("/api/fixtures/{fixture_id}/details")
def fixture_details(fixture_id: int):
    """Lectura exclusiva de PostgreSQL: abrir la ficha no gasta cuota."""
    with session_scope() as s:
        fixture = s.get(Fixture, (settings.mode, fixture_id))
        if not fixture:
            raise HTTPException(404, "Partido no encontrado")
        league_or_404(s, fixture.league_id)
        snapshot = s.get(FixtureDetails, (settings.mode, fixture_id))
        players = snapshot.player_ratings if snapshot else []
        # "Mejor calificado" solo con valor comunicado por proveedor;
        # nunca confundirlo con un premio MVP oficialmente adjudicado.
        best = max(players, key=lambda x: x.get("rating", 0)) if players else None
        return {
            "data": {
                "events": snapshot.events if snapshot else [],
                "lineups": snapshot.lineups if snapshot else [],
                "best_rated_player": best,
            },
            "meta": meta([snapshot] if snapshot else [], available=bool(snapshot), source="provider_cache"),
        }


@app.get("/api/fixtures/{fixture_id}/statistics")
def fixture_statistics(fixture_id: int):
    with session_scope() as s:
        fixture = s.get(Fixture, (settings.mode, fixture_id))
        if not fixture:
            raise HTTPException(404, "Partido no encontrado")
        league = league_or_404(s, fixture.league_id)
        snapshot = s.get(FixtureStatistics, (settings.mode, fixture_id))
        coverage = (league.coverage.get("fixtures") or {}).get("statistics_fixtures")
        teams = {t.id: public(t) for t in s.scalars(select(Team).where(
            Team.source == settings.mode, Team.id.in_([fixture.home_id, fixture.away_id])
        ))}
        data = [{"team": teams[r["team_id"]], "statistics": r["statistics"]}
                for r in (snapshot.data if snapshot else []) if r["team_id"] in teams]
        stale = bool(snapshot and fixture.status in LIVE and
                     (utcnow() - aware(snapshot.updated_at)).total_seconds() > max(120, settings.statistics_seconds * 2))
        return {"data": data, "meta": meta([snapshot] if snapshot else [], coverage=coverage, stale=stale)}


@app.get("/api/coverage")
def audit_coverage(country: str = Query("Argentina", max_length=60),
                   limit: int = Query(150, ge=1, le=250)):
    """Auditoría agregada: diferencia catálogo de datos realmente importados."""
    with session_scope() as db:
        query = select(League).where(League.source == settings.mode)
        if country:
            query = query.where(League.country.ilike(country))
        leagues = list(db.scalars(query.order_by(League.name).limit(limit)))
        ids = [l.id for l in leagues]
        if not ids:
            return {"data": [], "meta": meta([], scope=country)}
        def counts(model):
            return {(lid, year): count for lid, year, count in db.execute(
                select(model.league_id, model.season, func.count()).where(
                    model.source == settings.mode, model.league_id.in_(ids),
                ).group_by(model.league_id, model.season)
            )}
        matches = counts(Fixture)
        standings = counts(Standing)
        scorers = counts(Scorer)
        memberships = counts(Membership)
        rows = []
        for l in leagues:
            for year in sorted(set(l.seasons or [l.season]), reverse=True):
                key = (l.id, year)
                row = {"league_id": l.id, "league": l.name, "country": l.country,
                       "season": year, "fixtures": matches.get(key, 0),
                       "standings_rows": standings.get(key, 0),
                       "scorers_rows": scorers.get(key, 0),
                       "teams_rows": memberships.get(key, 0)}
                row["missing"] = [name for name, count in (
                    ("fixtures", row["fixtures"]),
                    ("standings", row["standings_rows"]),
                    ("scorers", row["scorers_rows"]),
                    ("teams", row["teams_rows"]),
                ) if not count]
                rows.append(row)
        return {"data": rows, "meta": meta([], scope=country,
            note="Cobertura real importada; cero no significa que el proveedor no cubra ese dato.")}


@app.get("/api/sports/status")
def sports_status():
    from .other_sports import status
    return {"data": status(), "meta": meta([])}


@app.get("/api/sports/{sport}/datasets")
def sport_datasets(sport: str):
    """Lista las temporadas/días disponibles sin consultar al proveedor."""
    from .other_sports import SPORTS
    from .models import SportSnapshot
    if sport not in SPORTS:
        raise HTTPException(404, "Deporte no disponible")
    with session_scope() as s:
        rows = list(s.scalars(select(SportSnapshot).where(
            SportSnapshot.sport == sport
        ).order_by(SportSnapshot.updated_at.desc()).limit(120)))
        return {"data": [{
            "kind": row.dataset, "ref": row.ref, "updated_at": row.updated_at,
            "count": row.source_count, "note": row.note,
        } for row in rows], "meta": meta(rows)}


@app.get("/api/sports/{sport}/overview")
def sport_overview(sport: str):
    """Calendario de 15 días desde PostgreSQL, sin consultas por visitante."""
    from .other_sports import SPORTS
    from .models import SportSnapshot
    from datetime import timedelta
    from zoneinfo import ZoneInfo
    if sport not in SPORTS:
        raise HTTPException(404, "Deporte no disponible")
    today = utcnow().astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    from_date = (today - timedelta(days=7)).isoformat()
    to_date = (today + timedelta(days=7)).isoformat()
    with session_scope() as s:
        records = list(s.scalars(select(SportSnapshot).where(
            SportSnapshot.sport == sport,
            SportSnapshot.dataset == "games",
            SportSnapshot.ref >= from_date,
            SportSnapshot.ref <= to_date,
        ).order_by(SportSnapshot.ref)))
        # En F1 el calendario del año se consulta de una sola vez.
        if sport == "f1":
            records = list(s.scalars(select(SportSnapshot).where(
                SportSnapshot.sport == sport,
                SportSnapshot.dataset == "games",
                SportSnapshot.ref.like(f"{today.year}%"),
            ).order_by(SportSnapshot.ref)))
        matches = []
        seen = set()
        for record in records:
            for item in record.data or []:
                if not isinstance(item, dict):
                    continue
                match_id = item.get("id")
                identity = match_id if match_id is not None else (record.ref, item.get("home"), item.get("away"))
                if identity in seen:
                    continue
                seen.add(identity)
                matches.append({**item, "queried_date": record.ref})
        return {"data": {
            "matches": matches,
            "dates_checked": [r.ref for r in records],
            "snapshot_count": len(records),
            "period": {"from": from_date, "to": to_date},
        }, "meta": meta(records, coverage=bool(records))}


@app.get("/api/sports/{sport}/analytics")
def sport_analytics(sport: str, league_id: str | None = Query(None, max_length=40)):
    from .other_sports import SPORTS
    from .models import SportSnapshot
    from .sports_metrics import compute_rates
    if sport not in SPORTS:
        raise HTTPException(404, "Deporte no disponible")
    with session_scope() as s:
        snapshots = list(s.scalars(select(SportSnapshot).where(
            SportSnapshot.sport == sport, SportSnapshot.dataset == "games"
        ).order_by(SportSnapshot.updated_at.desc()).limit(10)))
        games = {}
        for snap in snapshots:
            for game in snap.data:
                if isinstance(game, dict) and game.get("id") is not None:
                    games[str(game["id"])] = game
        data = compute_rates(games.values(), sport, league_id)
        data["snapshots_used"] = len(snapshots)
        return {"data": data, "meta": meta(snapshots, coverage=bool(snapshots),
                                           provisional=True)}


@app.get("/api/sports/{sport}/dataset")
def sport_dataset(sport: str, kind: str = Query(..., pattern="^(games|standings|drivers|leagues)$"),
                  ref: str = Query(..., max_length=90)):
    """El cliente lee SOLO PostgreSQL, no consume cuota de API-Sports."""
    from .other_sports import SPORTS
    from .models import SportSnapshot
    if sport not in SPORTS:
        raise HTTPException(404, "Deporte no disponible")
    with session_scope() as s:
        row = s.get(SportSnapshot, (sport, kind, ref))
        if not row:
            return {"data": [], "meta": meta([], coverage=False,
                note="Importación pendiente o endpoint no cubierto")}
        return {"data": row.data, "meta": meta([row], coverage=True,
            count=row.source_count, source="api_sports_snapshot",
            note=row.note, ref=ref)}


@app.get("/api/sports/{sport}/games")
def sport_games(sport: str, date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$")):
    from .other_sports import SPORTS, games
    if sport not in SPORTS:
        raise HTTPException(404, "Deporte no disponible")
    try:
        return {"data": games(sport, date), "meta": meta([])}
    except ValueError:
        raise HTTPException(422, "Fecha inválida")


@app.get("/api/leagues/{league_id}/history")
def league_history(league_id: int):
    """Resumen histórico solo a partir de temporadas verificadas en DB."""
    with session_scope() as s:
        league = league_or_404(s, league_id)
        years = list(sorted(set(league.seasons or [league.season]), reverse=True))
        history = []
        for year in years:
            fixtures = list(s.scalars(select(Fixture).where(
                Fixture.source == settings.mode,
                Fixture.league_id == league_id,
                Fixture.season == year,
                Fixture.status.in_(["FT", "AET", "PEN"]),
            )))
            official = s.scalar(select(Standing).where(
                Standing.source == settings.mode,
                Standing.league_id == league_id,
                Standing.season == year,
                Standing.rank == 1,
            ).order_by(Standing.group))
            top = s.scalar(select(Scorer).where(
                Scorer.source == settings.mode, Scorer.league_id == league_id,
                Scorer.season == year,
            ).order_by(Scorer.rank))
            official_team = s.get(Team, (settings.mode, official.team_id)) if official else None
            top_team = s.get(Team, (settings.mode, top.team_id)) if top else None
            if not fixtures and not official and not top:
                continue
            history.append({
                "season": year, "matches_loaded": len(fixtures),
                "official_leader": {"team": public(official_team), "group": official.group} if official_team else None,
                "leading_scorer": {"name": top.name, "goals": top.goals, "team": public(top_team)} if top and top_team else None,
                "complete": bool(official and top and fixtures),
            })
        return {"data": history, "meta": meta([], archived=True, seasons_known=len(years))}


@app.get("/api/leagues/{league_id}/standings")
def standings(league_id: int, season: int | None = Query(None, ge=1900, le=2200)):
    with session_scope() as s:
        league = league_or_404(s, league_id)
        rows = list(
            s.scalars(
                select(Standing)
                .where(
                    Standing.source == settings.mode,
                    Standing.league_id == league_id,
                    Standing.season == (season or league.season),
                )
                .order_by(Standing.group, Standing.rank)
            )
        )
        if not rows and league.kind.lower() == "league":
            # Los datos pueden incluir solo una parte de las fechas.
            # Nunca representar este cálculo como una clasificación oficial.
            finals = list(s.scalars(
                select(Fixture).where(
                    Fixture.source == settings.mode,
                    Fixture.league_id == league_id,
                    Fixture.season == (season or league.season),
                    Fixture.status == "FT",
                )
            ))
            ids = {team_id for f in finals for team_id in (f.home_id, f.away_id)}
            partial_teams = {
                t.id: public(t) for t in s.scalars(
                    select(Team).where(Team.source == settings.mode, Team.id.in_(ids))
                )
            } if ids else {}
            provisional, matches_used = partial_standings(finals, partial_teams)
            if provisional:
                return {
                    "data": provisional,
                    "meta": meta(finals, coverage=False, provisional=True, matches_used=matches_used),
                }
        teams = {
            t.id: public(t)
            for t in s.scalars(
                select(Team).where(
                    Team.source == settings.mode, Team.id.in_([r.team_id for r in rows])
                )
            )
        }
        return {
            "data": [{**public(r), "team": teams[r.team_id]} for r in rows],
            "meta": meta(rows, coverage=league.coverage.get("standings"), provisional=False),
        }


@app.get("/api/leagues/{league_id}/analytics")
def league_analytics(league_id: int, season: int | None = Query(None, ge=1900, le=2200)):
    """Métricas derivadas reproducibles de partidos realmente importados."""
    from .analytics import summarize
    with session_scope() as s:
        league = league_or_404(s, league_id)
        year = season or league.season
        fixtures = list(s.scalars(select(Fixture).where(
            Fixture.source == settings.mode,
            Fixture.league_id == league_id, Fixture.season == year,
        )))
        standings_rows = list(s.scalars(select(Standing).where(
            Standing.source == settings.mode, Standing.league_id == league_id,
            Standing.season == year,
        )))
        scoring_rows = list(s.scalars(select(Scorer).where(
            Scorer.source == settings.mode, Scorer.league_id == league_id,
            Scorer.season == year,
        )))
        tids = {t for f in fixtures for t in (f.home_id, f.away_id)}
        names = {t.id: t.name for t in s.scalars(select(Team).where(
            Team.source == settings.mode, Team.id.in_(tids),
        ))} if tids else {}
        data = summarize(fixtures, names, standings_rows, scoring_rows, season=year)
        return {"data": data, "meta": meta(fixtures, partial=not (
            data["official_standings_loaded"] and data["official_scorers_loaded"]))}


@app.get("/api/leagues/{league_id}/analytics/history")
def league_analytics_history(league_id: int):
    """Serie por año importado. No implica historia deportiva exhaustiva."""
    from .analytics import summarize
    with session_scope() as s:
        league = league_or_404(s, league_id)
        years = list(dict.fromkeys(sorted(league.seasons or [league.season], reverse=True)))
        output = []
        for year in years:
            fixtures = list(s.scalars(select(Fixture).where(
                Fixture.source == settings.mode, Fixture.league_id == league_id,
                Fixture.season == year,
            )))
            score_count = s.scalar(select(func.count()).select_from(Scorer).where(
                Scorer.source == settings.mode, Scorer.league_id == league_id,
                Scorer.season == year,
            )) or 0
            output.append({
                "season": year,
                "final_matches_loaded": sum(1 for f in fixtures
                    if f.status in {"FT", "AET", "PEN"} and f.home_goals is not None
                    and f.away_goals is not None),
                "official_scorer_records": score_count,
                "champion": None,
                "complete": False,
            })
        return {"data": {
            "seasons": output, "scope": "solo datos importados",
            "champions_note": "Los campeones históricos necesitan una fuente oficial; no se infieren del ranking."
        }, "meta": meta([])}


@app.get("/api/leagues/{league_id}/scorers")
def scorers(league_id: int, season: int | None = Query(None, ge=1900, le=2200)):
    with session_scope() as s:
        league = league_or_404(s, league_id)
        rows = list(
            s.scalars(
                select(Scorer)
                .where(
                    Scorer.source == settings.mode,
                    Scorer.league_id == league_id,
                    Scorer.season == (season or league.season),
                )
                .order_by(Scorer.rank, Scorer.player_id)
            )
        )
        if not rows and settings.mode == "api":
            from .scorer_fallback import partial_scorers
            provisional, checked = partial_scorers(
                s, settings.mode, league_id, (season or league.season), public
            )
            if provisional:
                return {
                    "data": provisional,
                    "meta": meta([], coverage=False, provisional=True, matches_used=checked),
                }
        teams = {
            t.id: public(t)
            for t in s.scalars(
                select(Team).where(
                    Team.source == settings.mode, Team.id.in_([r.team_id for r in rows])
                )
            )
        }
        return {
            "data": [{**public(r), "team": teams[r.team_id]} for r in rows],
            "meta": meta(rows, coverage=league.coverage.get("top_scorers"), provisional=False),
        }


@app.get("/api/teams")
def teams(
    league_id: int,
    season: int | None = Query(None, ge=1900, le=2200),
    q: str = Query("", max_length=80),
):
    with session_scope() as s:
        league = league_or_404(s, league_id)
        query = (
            select(Team)
            .join(
                Membership,
                (Membership.source == Team.source) & (Membership.team_id == Team.id),
            )
            .where(
                Team.source == settings.mode,
                Membership.league_id == league_id,
                Membership.season == (season or league.season),
            )
        )
        if q:
            query = query.where(Team.name.icontains(q, autoescape=True))
        rows = list(s.scalars(query.order_by(Team.name)))
        return {"data": [public(r) for r in rows], "meta": meta()}


@app.get("/api/teams/{team_id}")
def team_detail(team_id: int):
    with session_scope() as s:
        row = s.get(Team, (settings.mode, team_id))
        if not row:
            raise HTTPException(404, "Equipo no encontrado")
        q = select(Fixture).where(
            Fixture.source == settings.mode,
            or_(Fixture.home_id == team_id, Fixture.away_id == team_id),
        )
        if settings.mode == "api" and not settings.all_leagues:
            q = q.where(Fixture.league_id.in_(settings.league_ids))
        recent = list(
            s.scalars(
                q.where(Fixture.kickoff < utcnow())
                .order_by(Fixture.kickoff.desc())
                .limit(8)
            )
        )
        upcoming = list(
            s.scalars(
                q.where(Fixture.kickoff >= utcnow()).order_by(Fixture.kickoff).limit(8)
            )
        )
        comps = s.execute(
            select(Membership.league_id, Membership.season).where(
                Membership.source == settings.mode, Membership.team_id == team_id
            )
        ).all()
        return {
            "data": {
                **public(row),
                "recent": match_payload(s, recent),
                "upcoming": match_payload(s, upcoming),
                "competitions": [{"league_id": l, "season": y} for l, y in comps],
            },
            "meta": meta(),
        }


@app.get("/api/reference/{sport}")
def reference_sport(sport: str, season: int | None = Query(None, ge=1950, le=2100),
                    competition: str = Query("ipl", max_length=32)):
    """Cached reference rankings independent of paid API-Sports subscriptions."""
    from .public_sports import formula_one, nba, cricket, us_league
    try:
        if sport == "f1":
            data = formula_one(season)
        elif sport == "nba":
            data = nba(season)
        elif sport == "cricket":
            data = cricket(competition)
        elif sport in {"nhl", "mlb", "nfl", "wnba"}:
            data = us_league(sport, season)
        else:
            raise HTTPException(404, "Deporte no disponible")
    except ValueError:
        raise HTTPException(422, "Temporada o competición inválida")
    return {"data": data, "meta": meta([], coverage=data.get("available", False))}


@app.get("/api/leagues/128/annual")
def argentina_annual_table(season: int = Query(2026, ge=2024, le=2100)):
    """Tabla anual parcial: solo partidos completados e importados de Primera."""
    with session_scope() as s:
        season_games = list(s.scalars(select(Fixture).where(
            Fixture.source == settings.mode,
            Fixture.league_id == 128,
            Fixture.season == season,
            Fixture.status == "FT",
        )))
        ids = {team for game in season_games for team in (game.home_id, game.away_id)}
        club_names = {t.id: public(t) for t in s.scalars(select(Team).where(
            Team.source == settings.mode, Team.id.in_(ids)
        ))} if ids else {}
        result, matches_used = partial_standings(season_games, club_names)
        return {"data": result, "meta": meta(
            season_games, provisional=True, matches_used=matches_used,
            disclaimer="Tabla parcial calculada con partidos almacenados; no equivale a la clasificación anual oficial ni contempla deducciones o reglamentos especiales.",
        )}


@app.get("/api/leagues/128/alltime")
def argentina_historic_table():
    """Historical index from actually imported Argentine Primera fixtures only.

    Uses uniform 3 points per win; never claims complete first division
    history, official adjusted points or regulation-specific points.
    """
    from collections import defaultdict
    from .ingest import FINISHED
    with session_scope() as s:
        matches = s.execute(select(
            Fixture.home_id, Fixture.away_id, Fixture.home_goals,
            Fixture.away_goals, Fixture.season,
        ).where(
            Fixture.source == settings.mode,
            Fixture.league_id == 128,
            Fixture.status.in_(FINISHED),
            Fixture.home_goals.is_not(None),
            Fixture.away_goals.is_not(None),
        )).all()
        ids = {club for match in matches for club in (match[0], match[1])}
        teams = {team.id: team.name for team in s.scalars(select(Team).where(
            Team.source == settings.mode, Team.id.in_(ids)))}
    rows = defaultdict(lambda: dict(pj=0, pg=0, pe=0, pp=0, gf=0, gc=0))
    seasons = set()
    for home, away, gh, ga, season in matches:
        if home not in teams or away not in teams:
            continue
        seasons.add(season)
        for club, scored, conceded in ((home, gh, ga), (away, ga, gh)):
            row = rows[club]
            row["pj"] += 1
            row["gf"] += scored
            row["gc"] += conceded
            row["pg" if scored > conceded else "pe" if scored == conceded else "pp"] += 1
    ranking = sorted(({
        "team": teams[id], "team_id": id,
        **values, "points_3v": 3 * values["pg"] + values["pe"],
        "difference": values["gf"] - values["gc"],
        "win_pct": round(values["pg"] * 100 / values["pj"], 1),
    } for id, values in rows.items()), key=lambda x:
        (-x["points_3v"], -x["difference"], -x["gf"], x["team"]))
    return {"data": {
        "rows": ranking,
        "seasons": sorted(seasons),
        "matches": len(matches), "partial": True,
        "note": "Tabla parcial construida solo con partidos importados en Latente; 3 puntos por victoria. No equivale a la tabla histórica completa desde 1891, ni aplica descuentos o puntajes antiguos.",
    }, "meta": meta([], coverage=bool(ranking), provisional=True)}
