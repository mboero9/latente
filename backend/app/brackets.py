"""Fases eliminatorias verificadas. Nunca deducir rivales o cruces sin datos."""
import re

ROUNDS = [
    ("64avos de final", -1, (r"round of 128", r"1/64", r"64avos")),
    ("32avos de final", 0, (r"round of 64", r"1/32", r"32avos", r"thirty.two")),
    ("16avos de final", 1, (r"round of 32", r"1/16", r"16avos")),
    ("Octavos de final", 2, (r"round of 16", r"last 16", r"1/8", r"octavos")),
    ("Cuartos de final", 3, (r"quarter.final", r"cuartos", r"1/4")),
    ("Semifinales", 4, (r"semi.final", r"semifinal")),
    ("Final", 5, (r"(?<!semi)\bfinal\b", r"\bfinal\s*-\s*final\b")),
]


def classify_round(label):
    normalized = (label or "").strip().lower()
    # API-Sports also emits Spanish/French stage labels for some tournaments.
    for title, order, patterns in ROUNDS:
        if any(re.search(pattern, normalized) for pattern in patterns):
            return title, order
    return None


def winner_id(match):
    """No adjudicar empates ni llaves de ida/vuelta sin marcador definitorio."""
    if match.get("status") not in ("FT", "AET", "PEN"):
        return None
    home, away = match.get("home_goals"), match.get("away_goals")
    if home is None or away is None:
        return None
    if home == away:
        penalties = (match.get("score") or {}).get("penalty") or {}
        home, away = penalties.get("home"), penalties.get("away")
        if home is None or away is None or home == away:
            return None
    return (match.get("home") or {}).get("id") if home > away else (match.get("away") or {}).get("id")


def bracket_rows(fixtures):
    stages = {}
    for fixture in fixtures:
        stage = classify_round(fixture.get("round"))
        if stage is None:
            continue
        title, order = stage
        stages.setdefault(order, {"name": title, "order": order, "matches": []})["matches"].append(fixture)
    ordered = [stages[k] for k in sorted(stages)]
    for stage in ordered:
        stage["matches"].sort(key=lambda x: (x["kickoff"], x["id"]))
    # Dibujar solo enlaces con certeza: ganador comprobado, presente en
    # exactamente un partido de la fase siguiente. Con empate/ida y vuelta
    # ambiguo, no atribuir avance.
    for index, stage in enumerate(ordered[:-1]):
        next_stage = ordered[index + 1]
        if next_stage["order"] != stage["order"] + 1:
            continue  # Nunca conectar dos rondas si falta una intermedia.
        for match in stage["matches"]:
            winner = winner_id(match)
            candidates = [r for r in next_stage["matches"]
                          if winner and winner in (
                              (r.get("home") or {}).get("id"),
                              (r.get("away") or {}).get("id"))]
            if len(candidates) == 1:
                match["next_match_id"] = candidates[0]["id"]
                match["winner_id"] = winner
    return ordered
