"""Normalización idempotente; cada snapshot se confirma en una transacción."""

from datetime import datetime
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from .models import League, Team, Membership, Fixture, FixtureStatistics, Standing, Scorer, utcnow

LIVE = {"1H", "HT", "2H", "ET", "BT", "P", "LIVE", "INT"}
FINISHED = {"FT", "AET", "PEN", "AWD", "WO"}


def upsert(s, model, values):
    insert = sqlite_insert if s.bind.dialect.name == "sqlite" else pg_insert
    stmt = insert(model).values(**values)
    keys = [c.name for c in model.__table__.primary_key]
    changes = {k: getattr(stmt.excluded, k) for k in values if k not in keys}
    stmt = (
        stmt.on_conflict_do_update(index_elements=keys, set_=changes)
        if changes
        else stmt.on_conflict_do_nothing(index_elements=keys)
    )
    s.execute(stmt)


def team(s, raw, source="api", **extra):
    # Una respuesta abreviada de fixtures no borra el perfil completo.
    values = {"source": source, "id": int(raw["id"]), "name": raw["name"]}
    for key in ("code", "country", "founded"):
        if raw.get(key) is not None:
            values[key] = raw[key]
    values.update({k: v for k, v in extra.items() if v is not None})
    upsert(s, Team, values)


def membership(s, source, league, season, team_id):
    upsert(
        s,
        Membership,
        {"source": source, "league_id": league, "season": season, "team_id": team_id},
    )


def save_fixtures(s, rows, allowed, source="api"):
    for raw in rows:
        league, f, teams = raw["league"], raw["fixture"], raw["teams"]
        if (allowed is not None and league["id"] not in allowed) or not s.get(League, (source, league["id"])):
            continue
        # Los cruces futuros pueden tener un participante todavía sin definir.
        if not all(teams[side].get("id") and teams[side].get("name") for side in ("home", "away")):
            continue
        for side in ("home", "away"):
            team(s, teams[side], source)
            membership(s, source, league["id"], league["season"], teams[side]["id"])
        goals = raw.get("goals") or {}
        status = f["status"]
        upsert(
            s,
            Fixture,
            dict(
                source=source,
                id=f["id"],
                league_id=league["id"],
                season=league["season"],
                round=league.get("round"),
                kickoff=datetime.fromisoformat(f["date"].replace("Z", "+00:00")),
                home_id=teams["home"]["id"],
                away_id=teams["away"]["id"],
                status=status["short"],
                elapsed=status.get("elapsed"),
                extra=status.get("extra"),
                home_goals=goals.get("home"),
                away_goals=goals.get("away"),
                venue=(f.get("venue") or {}).get("name"),
                referee=f.get("referee"),
                score=raw.get("score") or {},
                updated_at=utcnow(),
            ),
        )


def save_teams(s, rows, league, season, source="api"):
    for row in rows:
        venue = row.get("venue") or {}
        team(
            s,
            row["team"],
            source,
            venue=venue.get("name"),
            city=venue.get("city"),
            capacity=venue.get("capacity"),
        )
        membership(s, source, league, season, row["team"]["id"])


def save_statistics(s, rows, fixture_id, source="api"):
    fixture = s.get(Fixture, (source, fixture_id))
    if not fixture:
        return
    data = []
    seen = set()
    for row in rows:
        team_id = (row.get("team") or {}).get("id")
        if team_id not in {fixture.home_id, fixture.away_id} or team_id in seen:
            continue
        statistics = [
            {"type": item["type"][:120], "value": item.get("value")}
            for item in (row.get("statistics") or [])[:100]
            if isinstance(item, dict) and isinstance(item.get("type"), str)
            and (item.get("value") is None or isinstance(item["value"], (str, int, float)))
        ]
        if statistics:
            data.append({"team_id": team_id, "statistics": statistics})
            seen.add(team_id)
    # Una respuesta vacía no borra el último snapshot válido.
    if data:
        upsert(s, FixtureStatistics, dict(source=source, fixture_id=fixture_id, data=data, updated_at=utcnow()))


def save_standings(s, rows, league, season, source="api"):
    # Vacío no significa borrar: puede faltar cobertura o la tabla aún no existe.
    groups = [g for r in rows for g in r.get("league", {}).get("standings", []) if g]
    if not groups:
        return
    s.execute(
        delete(Standing).where(
            Standing.source == source,
            Standing.league_id == league,
            Standing.season == season,
        )
    )
    for index, group in enumerate(groups):
        for row in group:
            team(s, row["team"], source)
            membership(s, source, league, season, row["team"]["id"])
            totals = row["all"]
            upsert(
                s,
                Standing,
                dict(
                    source=source,
                    league_id=league,
                    season=season,
                    group=row.get("group") or f"Grupo {index + 1}",
                    team_id=row["team"]["id"],
                    rank=row["rank"],
                    points=row["points"],
                    played=totals["played"],
                    won=totals["win"],
                    drawn=totals["draw"],
                    lost=totals["lose"],
                    goals_for=totals["goals"]["for"],
                    goals_against=totals["goals"]["against"],
                    difference=row["goalsDiff"],
                    form=row.get("form"),
                    description=row.get("description"),
                    updated_at=utcnow(),
                ),
            )


def save_scorers(s, rows, league, season, source="api"):
    if not rows:
        return
    normalized = []
    for rank, row in enumerate(rows, 1):
        for stats in row.get("statistics", []):
            if (
                stats["league"]["id"] != league
                or stats["league"].get("season", season) != season
            ):
                continue
            team(s, stats["team"], source)
            membership(s, source, league, season, stats["team"]["id"])
            normalized.append(
                dict(
                    source=source,
                    league_id=league,
                    season=season,
                    player_id=row["player"]["id"],
                    team_id=stats["team"]["id"],
                    name=row["player"]["name"],
                    rank=rank,
                    goals=stats["goals"].get("total") or 0,
                    assists=stats["goals"].get("assists"),
                    appearances=stats.get("games", {}).get("appearences"),
                    penalties=stats.get("penalty", {}).get("scored"),
                    updated_at=utcnow(),
                )
            )
    if normalized:
        s.execute(
            delete(Scorer).where(
                Scorer.source == source,
                Scorer.league_id == league,
                Scorer.season == season,
            )
        )
        for row in normalized:
            upsert(s, Scorer, row)
