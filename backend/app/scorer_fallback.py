"""Cálculo PARCIAL de goleadores con autores confirmados en eventos.

No sustituye tablas oficiales: solo contabiliza goles de partidos con
eventos ya importados. Autogoles no se acreditan al futbolista.
"""
from collections import defaultdict
from hashlib import blake2b
from sqlalchemy import select, and_
from .models import Fixture, FixtureDetails, Team


def partial_scorers(s, source, league_id, season, public):
    stmt = (
        select(Fixture, FixtureDetails)
        .join(
            FixtureDetails,
            and_(
                FixtureDetails.source == Fixture.source,
                FixtureDetails.fixture_id == Fixture.id,
            ),
        )
        .where(
            Fixture.source == source,
            Fixture.league_id == league_id,
            Fixture.season == season,
            FixtureDetails.events_checked_at.is_not(None),
        )
    )
    fixtures = list(s.execute(stmt))
    counts = defaultdict(lambda: {"goals": 0, "penalties": 0})
    for fixture, details in fixtures:
        for event in details.events or []:
            if str(event.get("type") or "").lower() != "goal":
                continue
            detail = str(event.get("detail") or "").lower()
            # No atribuir goles en propia puerta al jugador como máximo goleador.
            if "own goal" in detail:
                continue
            name = str(event.get("player") or "").strip()
            team_id = event.get("team_id")
            if not name or team_id not in (fixture.home_id, fixture.away_id):
                continue
            rec = counts[(team_id, name.casefold(), name)]
            rec["goals"] += 1
            rec["penalties"] += int("penalty" in detail)
    ids = {key[0] for key in counts}
    teams = {
        team.id: public(team)
        for team in s.scalars(
            select(Team).where(Team.source == source, Team.id.in_(ids))
        )
    } if ids else {}
    rows = []
    for (team_id, _, name), count in counts.items():
        if team_id not in teams:
            continue
        digest = blake2b(f"{team_id}:{name.casefold()}".encode(), digest_size=6).digest()
        # El identificador negativo distingue estos agregados de los ID oficiales.
        fallback_id = -int.from_bytes(digest, "big")
        rows.append({
            "player_id": fallback_id, "name": name, "team": teams[team_id],
            "goals": count["goals"], "assists": None,
            "appearances": None, "penalties": count["penalties"],
        })
    rows.sort(key=lambda r: (-r["goals"], r["name"].casefold(), r["team"]["id"]))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return rows, len(fixtures)
