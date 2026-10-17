"""Motor de promedios LPF 2026: cálculo propio SOLO con PostgreSQL.

API-Football aporta fixtures ya importados; el proveedor NO decide
descensos, denominadores ni validaciones. Las tablas incompletas no pueden
presentarse como oficiales. El algoritmo excluye instancias finales y usa
una referencia LPF verificada (importada de manera independiente) cuando
está disponible.
"""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import re

LEAGUE_ID = 128
BASE_YEARS = (2024, 2025, 2026)
OFFICIAL_URL = "https://www.ligaprofesional.ar/torneo-clausura-mercado-libre-2026/"
REGULAR = re.compile(
    r"regular\s*season|apertura|clausura|primera\s*fase|"
    r"first\s*phase|1st\s*phase|fase\s*de\s*zonas|group\s*stage|"
    r"copa\s*de\s*la\s*liga",
    flags=re.I,
)
KNOCKOUT = re.compile(
    r"\bplay\s*-?\s*offs?\b|\bknock\s*-?\s*out\b|"
    r"round\s+of\s+\d+|\boctavos\b|\bcuartos\b|"
    r"\bquarter\s*-?\s*final\w*\b|\bsemi\s*-?\s*final\w*\b|"
    r"\bfinal(?:s)?\b|\bdesempate\b|\btie\s*-?\s*break\b",
    flags=re.I,
)


def regular_phase(round_name):
    """Conservative include-list; unknown rounds require human verification."""
    return isinstance(round_name, str) and bool(REGULAR.search(round_name)) \
        and not KNOCKOUT.search(round_name)


def value(row, key, default=None):
    return row.get(key, default) if isinstance(row, dict) else getattr(row, key, default)


def compute_promedios(fixtures, teams, current_team_ids, official_reference=()):
    """One id per imported result. Never assign point deductions or relegation.

    official_reference is a list of independently captured LPF entries with
    team_id, played, points. It validates the *aggregate* total only.
    A reference snapshot can become obsolete as fixtures are played;
    mismatches must remain visible instead of being overwritten.

    For newly promoted clubs, absence of old-season data is NOT assumed
    to mean 'the club did not play in Primera': only known matches count,
    and the table is always provisional until officially verified.
    """
    ids = set(current_team_ids)
    result_by_team = {team_id: {year: {"played": 0, "points": 0}
                               for year in BASE_YEARS} for team_id in ids}
    used_ids = set()
    excluded = {"unverified_round": 0, "not_final": 0, "invalid": 0}
    season_counts = {year: 0 for year in BASE_YEARS}
    for row in fixtures:
        fid = value(row, "id")
        year = value(row, "season")
        if value(row, "league_id") != LEAGUE_ID or year not in BASE_YEARS:
            continue
        if fid is None or fid in used_ids:
            continue
        used_ids.add(fid)
        if value(row, "status") != "FT":
            excluded["not_final"] += 1
            continue
        if not regular_phase(value(row, "round")):
            excluded["unverified_round"] += 1
            continue
        home, away = value(row, "home_id"), value(row, "away_id")
        hg, ag = value(row, "home_goals"), value(row, "away_goals")
        if (home is None or away is None or home == away or
                not isinstance(hg, int) or not isinstance(ag, int) or
                isinstance(hg, bool) or isinstance(ag, bool) or
                min(hg, ag) < 0):
            excluded["invalid"] += 1
            continue
        season_counts[year] += 1
        for team_id, points in (
            (home, 3 if hg > ag else (1 if hg == ag else 0)),
            (away, 3 if ag > hg else (1 if hg == ag else 0)),
        ):
            if team_id not in ids:
                continue
            record = result_by_team[team_id][year]
            record["played"] += 1
            record["points"] += points

    refs = {}
    for item in official_reference or []:
        if not isinstance(item, dict):
            continue
        team_id = item.get("team_id")
        played, points = item.get("played"), item.get("points")
        if (team_id in ids and
            isinstance(played, int) and not isinstance(played, bool) and played > 0
            and isinstance(points, int) and not isinstance(points, bool) and points >= 0):
            refs[team_id] = {"played": played, "points": points}

    rows = []
    for team_id in ids:
        seasons = result_by_team[team_id]
        played = sum(record["played"] for record in seasons.values())
        points = sum(record["points"] for record in seasons.values())
        if not played:
            continue
        official = refs.get(team_id)
        matches_official = bool(official and official["played"] == played
                                and official["points"] == points)
        average = Decimal(points) / Decimal(played)
        rows.append({
            "team_id": team_id,
            "team": teams[team_id],
            "seasons": {str(year): {
                "played": record["played"] if record["played"] else None,
                "points": record["points"] if record["played"] else None,
                "has_imported_games": bool(record["played"]),
            } for year, record in seasons.items()},
            "played": played,
            "points": points,
            "average": float(average.quantize(Decimal(".0001"), rounding=ROUND_HALF_UP)),
            "verified": matches_official,
            "reference": official,
            "missing_seasons": [year for year, record in seasons.items()
                                if not record["played"]],
            "difference": None if not official else {
                "played": played - official["played"],
                "points": points - official["points"],
            },
        })
    rows.sort(key=lambda row: (-Decimal(row["points"])/Decimal(row["played"]),
                                -row["points"],
                                row["team"]["name"].casefold(), row["team_id"]))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return {
        "rows": rows,
        "matches_used": sum(season_counts.values()),
        "matches_by_season": {str(y): n for y,n in season_counts.items()},
        "excluded": excluded,
        "reference_count": len(refs),
        "verified_count": sum(row["verified"] for row in rows),
        "provisional": True,  # Even matching totals do not cover AFA tiebreaks/deductions.
        "note": "Cálculo parcial con partidos importados; no determina descensos ni reemplaza la LPF.",
    }
