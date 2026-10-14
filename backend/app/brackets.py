"""Fases eliminatorias verificadas. Nunca deducir rivales o cruces sin datos."""
import re

ROUNDS = [
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
    # No automatic connections: without an official match-slot ID, pairing
    # adjacent games by their order would show fictitious paths to the final.
    return ordered
