"""Cross-sport rates only within one competition and verified final games.

Scores represent sport-specific points, runs or goals; never mixed globally.
No player-leader or historical champion claim is inferred from team totals.
"""
from collections import defaultdict


FINAL = {"ft", "aot", "ap", "final", "finished", "ended",
         "after overtime", "after penalties", "completed"}


def compute_rates(games, sport, league_id=None):
    by_team = defaultdict(lambda: {"games": 0, "wins": 0, "draws": 0,
                                   "losses": 0, "scored": 0, "conceded": 0})
    count = 0
    leagues = set()
    for game in games:
        if league_id is not None and str(game.get("league_id")) != str(league_id):
            continue
        if str(game.get("status") or "").casefold() not in FINAL:
            continue
        home_score, away_score = game.get("home_score"), game.get("away_score")
        if type(home_score) is not int or type(away_score) is not int:
            continue
        game_league = str(game.get("league_id") or game.get("league") or "unknown")
        leagues.add(game_league)
        count += 1
        for side, score, against in (
            ("home", home_score, away_score),
            ("away", away_score, home_score),
        ):
            team_id = game.get(side + "_id")
            name = game.get(side) or "unknown"
            # Keep scope and provider ID; same-name clubs in different
            # sports or competitions must never merge.
            identity = (game_league, str(team_id) if team_id is not None else "name:" + name.casefold())
            r = by_team[(identity, name)]
            r["games"] += 1
            r["scored"] += score
            r["conceded"] += against
            if score > against:
                r["wins"] += 1
            elif score == against:
                r["draws"] += 1
            else:
                r["losses"] += 1
    out = []
    for (identity, name), r in by_team.items():
        n = r["games"]
        out.append({
            "league_key": identity[0], "team_key": identity[1], "team": name,
            **r,
            "scoring_avg": round(r["scored"] / n, 2) if n else None,
            "conceding_avg": round(r["conceded"] / n, 2) if n else None,
            "win_pct": round(100 * r["wins"] / n, 2) if n else None,
        })
    out.sort(key=lambda r: (r["league_key"], -r["wins"], -r["scored"], r["team"]))
    return {"sport": sport, "league_id": league_id,
            "finished_matches_counted": count,
            "leagues_observed": sorted(leagues), "teams": out,
            "partial": True,
            "note": "Promedios calculados solo con resultados finales almacenados en Latente. No es clasificación oficial ni histórico completo."}
