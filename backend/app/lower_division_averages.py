"""Averages (PTS / PJ) for Argentina lower divisions, NOT official relegation.

AFA's 2026 Primera Nacional, Primera B and Primera C regulations use
their 2026 standings/zone placement for relegation, not a 3-season
coefficient. Men's Primera D merged into Primera C in 2024.

Read ONLY persisted, provider-labelled standings for the requested season.
Never sum unrelated championship group/phase rows or invent missing games.
"""
from decimal import Decimal, ROUND_HALF_UP
import re
import unicodedata

REGULATIONS = {
    "nacional": "https://www.afa.com.ar/3204/reglaments/reglamento-general?s=1",
    "b": "https://assets1.afa.com.ar/2026/Lau/Boletin-Especial-6824---Reglamento-del-Campeonato-de-Primera-Division-B-2026.pdf",
    "c": "https://www.afa.com.ar/3204/reglaments/reglamento-general?s=1",
    "d": "https://www.afa.com.ar/3204/reglaments/reglamento-general?s=1",
}
RULES = {
    "nacional": "En 2026 bajan los dos últimos equipos de cada zona según la tabla final de posiciones, no por promedio histórico.",
    "b": "En 2026 descienden los dos últimos de la tabla final de posiciones; no se aplica promedio histórico.",
    "c": "En 2026 las zonas definen los clubes que juegan por la permanencia/desafiliación. El promedio no determina el descenso.",
    "d": "La Primera D masculina se fusionó con Primera C a partir de 2024. Solo se consulta información histórica disponible hasta 2023.",
}

def _slug(name):
    value = unicodedata.normalize("NFKD", str(name or "").casefold())
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in value if not unicodedata.combining(c))).strip()

def lower_division_key(name, country):
    """Restrict to the four specific Argentine men's football competitions."""
    if _slug(country) != "argentina":
        return None
    title = _slug(name)
    if title in ("primera nacional", "primera b nacional"):
        return "nacional"
    if title in ("primera b metropolitana", "prim b metro",
                 "primera b", "primera division b"):
        return "b"
    if title in ("primera c", "primera division c", "prim c"):
        return "c"
    if title in ("primera d", "primera division d", "prim d"):
        return "d"
    return None


def _val(row, attr):
    return row.get(attr) if isinstance(row, dict) else getattr(row, attr)

def performance_average(standings, teams, code, season):
    """Computed from each row's published points and games played.

    Rankings are separated by group because 2026 Nacional/C have distinct
    zones. Points deductions, playoffs, official tiebreaks, missing/zero
    matches are not reconstructed or guessed. Avoid self-created tie rules.
    """
    if code not in REGULATIONS:
        raise ValueError("Categoría no admitida")
    if code == "d" and season > 2023:
        return {"season": season, "category": code, "groups": [],
                "historic_only": True, "matches_available": False,
                "official_url": REGULATIONS[code], "rule": RULES[code],
                "note": "Primera D no disputa una temporada 2026; últimas ediciones históricas hasta 2023."}
    groups = {}
    for source in standings:
        team_id = _val(source, "team_id")
        played = _val(source, "played")
        points = _val(source, "points")
        if (team_id not in teams or
            not isinstance(played, int) or isinstance(played, bool) or played <= 0 or
            not isinstance(points, int) or isinstance(points, bool) or points < 0):
            continue
        group = (_val(source, "group") or "General").strip()
        quotient = (Decimal(points) / Decimal(played)).quantize(Decimal(".0001"),
                                                                rounding=ROUND_HALF_UP)
        groups.setdefault(group, []).append({
            "team_id": team_id, "team": teams[team_id], "points": points,
            "played": played, "won": _val(source, "won"),
            "drawn": _val(source, "drawn"), "lost": _val(source, "lost"),
            "average": float(quotient),
        })
    result = []
    for label, values in sorted(groups.items()):
        values.sort(key=lambda item: (-item["average"], -item["points"],
                                      item["team"]["name"].casefold(), item["team_id"]))
        for index, row in enumerate(values, 1):
            row["rank"] = index
        result.append({"name": label, "rows": values})
    return {
        "season": season, "category": code, "groups": result,
        "historic_only": code == "d",
        "matches_available": bool(result), "official_url": REGULATIONS[code],
        "rule": RULES[code],
        "note": "Indicador estadístico PTS/PJ de la tabla de posiciones importada; no es la tabla oficial de descensos ni un promedio histórico de tres temporadas.",
    }
