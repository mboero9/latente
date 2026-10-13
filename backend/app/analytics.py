"""Statistics computed from saved events; coverage remains explicitly partial."""
from collections import defaultdict
from .ingest import FINISHED


def safe_div(numerator, denominator):
    return round(numerator / denominator, 3) if denominator else None


def summarize(fixtures, team_names, standings=(), scorers=(), season=None):
    rows = defaultdict(lambda: dict(played=0, won=0, drawn=0, lost=0, scored=0, conceded=0))
    count = 0
    for game in fixtures:
        if game.status not in FINISHED - {"AWD", "WO"}:
            continue
        if game.home_goals is None or game.away_goals is None:
            continue
        count += 1
        for tid, goals, against in ((game.home_id, game.home_goals, game.away_goals),
                                     (game.away_id, game.away_goals, game.home_goals)):
            item = rows[tid]
            item["played"] += 1
            item["scored"] += goals
            item["conceded"] += against
        if game.home_goals == game.away_goals:
            rows[game.home_id]["drawn"] += 1
            rows[game.away_id]["drawn"] += 1
        elif game.home_goals > game.away_goals:
            rows[game.home_id]["won"] += 1
            rows[game.away_id]["lost"] += 1
        else:
            rows[game.away_id]["won"] += 1
            rows[game.home_id]["lost"] += 1
    by_team = {r.team_id: r for r in standings}
    teams = []
    for team_id, r in rows.items():
        official = by_team.get(team_id)
        teams.append({
            "team_id": team_id, "name": team_names.get(team_id, str(team_id)),
            **r, "goal_difference": r["scored"] - r["conceded"],
            "goals_for_per_game": safe_div(r["scored"], r["played"]),
            "goals_against_per_game": safe_div(r["conceded"], r["played"]),
            "combined_goals_per_game": safe_div(r["scored"] + r["conceded"], r["played"]),
            "points_per_game_estimated": safe_div(r["won"] * 3 + r["drawn"], r["played"]),
            "win_rate_pct": round(100 * r["won"] / r["played"], 2),
            "official_points": official.points if official else None,
            "matches_complete_vs_standings": bool(official and official.played == r["played"]),
        })
    teams.sort(key=lambda x: (-x["played"], -x["points_per_game_estimated"], x["name"]))
    players = [{
        "player_id": s.player_id, "name": s.name, "team_id": s.team_id,
        "goals": s.goals, "appearances": s.appearances,
        "goals_per_appearance": safe_div(s.goals, s.appearances),
        "assists": s.assists
    } for s in scorers]
    return {
        "season": season, "finished_matches_available": count,
        "teams": teams, "players": players,
        "official_standings_loaded": bool(standings),
        "official_scorers_loaded": bool(scorers),
        "scope": "Solo partidos importados. No es una tabla oficial de descensos.",
    }
