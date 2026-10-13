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
        q = select(Fixture).where(
            Fixture.source == settings.mode,
            Fixture.kickoff >= start,
            Fixture.kickoff < end,
        )
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


@app.get("/api/fixtures/{fixture_id}")
def fixture(fixture_id: int):
    with session_scope() as s:
        row = s.get(Fixture, (settings.mode, fixture_id))
        if not row:
            raise HTTPException(404, "Partido no encontrado")
        league_or_404(s, row.league_id)
        return {"data": match_payload(s, [row])[0], "meta": meta([row])}


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
            "meta": meta(rows, coverage=league.coverage.get("standings")),
        }


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
            "meta": meta(rows, coverage=league.coverage.get("top_scorers")),
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
