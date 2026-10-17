"""Recent verified team form for active football fixtures.

Batch query over PostgreSQL; never calls API-Football per page visit.
Only finished matches, oldest-to-newest last 5 per club.
"""
from datetime import timedelta
from sqlalchemy import select, union_all, func
from .models import Fixture, utcnow
from .ingest import LIVE

FINISHED = ("FT", "AET", "PEN")


def form_symbol(goals_for, goals_against):
    """Regulation/extra-time result (penalty shoot-outs not extrapolated)."""
    if goals_for is None or goals_against is None:
        return None
    return "W" if goals_for > goals_against else "L" if goals_for < goals_against else "D"


def recent_team_form(db, source, team_ids, cutoff=None, count=5):
    """One bounded, indexed per-team window query for the supplied live clubs."""
    if not team_ids:
        return {}
    now = cutoff or utcnow()
    earliest = now - timedelta(days=400)
    common = (
        Fixture.source == source, Fixture.status.in_(FINISHED),
        Fixture.kickoff < now, Fixture.kickoff >= earliest,
    )
    left = select(
        Fixture.home_id.label("team_id"),
        Fixture.id.label("fixture_id"),
        Fixture.kickoff.label("kickoff"),
        Fixture.home_goals.label("gf"),
        Fixture.away_goals.label("ga"),
    ).where(*common, Fixture.home_id.in_(team_ids))
    right = select(
        Fixture.away_id.label("team_id"),
        Fixture.id.label("fixture_id"),
        Fixture.kickoff.label("kickoff"),
        Fixture.away_goals.label("gf"),
        Fixture.home_goals.label("ga"),
    ).where(*common, Fixture.away_id.in_(team_ids))
    union = union_all(left, right).subquery("finished_team_results")
    ranked = select(
        union.c.team_id, union.c.gf, union.c.ga,
        func.row_number().over(
            partition_by=union.c.team_id,
            order_by=(union.c.kickoff.desc(), union.c.fixture_id.desc()),
        ).label("rn")
    ).subquery("ranked_team_form")
    rows = db.execute(select(
        ranked.c.team_id, ranked.c.gf, ranked.c.ga, ranked.c.rn,
    ).where(ranked.c.rn <= count).order_by(
        ranked.c.team_id, ranked.c.rn.desc(),
    )).all()
    output = {team_id: [] for team_id in team_ids}
    for row in rows:
        symbol = form_symbol(row.gf, row.ga)
        if symbol:
            output[row.team_id].append(symbol)
    return output


def live_form_summaries(db, source):
    """Return only source-backed samples for active games (max 150)."""
    live = list(db.scalars(select(Fixture).where(
        Fixture.source == source,
        Fixture.status.in_(LIVE),
    ).order_by(Fixture.kickoff.desc(), Fixture.id.desc()).limit(150)))
    clubs = {team for match in live for team in (match.home_id, match.away_id)}
    forms = recent_team_form(db, source, clubs)
    return [
        {"fixture_id": game.id,
         "home": forms.get(game.home_id, []),
         "away": forms.get(game.away_id, []),
         "sample_type": "five_finished_matches"}
        for game in live if forms.get(game.home_id) or forms.get(game.away_id)
    ]
