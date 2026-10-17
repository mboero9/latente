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


def _tie_groups(matches):
    """Unordered pairs group the two legs of a confirmed knockout tie.

    Never coalesce placeholders with null team IDs: two unknown matches
    cannot be shown as the same fixture merely because both contain TBD.
    """
    groups = {}
    for fixture in matches:
        left = (fixture.get("home") or {}).get("id")
        right = (fixture.get("away") or {}).get("id")
        if left is None or right is None or left == right:
            key = ("unknown", fixture["id"])
            teams = set()
        else:
            key = tuple(sorted((left, right)))
            teams = {left, right}
        if key not in groups:
            groups[key] = {"matches": [], "teams": teams}
        groups[key]["matches"].append(fixture)
    return list(groups.values())


def bracket_rows(fixtures):
    """Only draw edges corroborated by actual participants in BOTH rounds.

    Copa Argentina typically has one game per tie. Libertadores and
    Sudamericana play two legs: winning the first leg does NOT decide the
    qualifier. Instead connect a full tie only if exactly one of its teams
    occurs in exactly one tie of the immediately following round. The same
    destination ID is set on both legs for a single visual connector.
    """
    stages = {}
    for fixture in fixtures:
        stage = classify_round(fixture.get("round"))
        if stage is None:
            continue
        title, order = stage
        # Avoid retaining stale linkage keys when a caller reuses payloads.
        row = {k: v for k, v in fixture.items()
               if k not in ("next_match_id", "qualified_team_id", "winner_id")}
        stages.setdefault(order, {"name": title, "order": order, "matches": []})["matches"].append(row)

    ordered = [stages[k] for k in sorted(stages)]
    grouped = []
    for stage in ordered:
        stage["matches"].sort(key=lambda x: (x["kickoff"], x["id"]))
        groups = _tie_groups(stage["matches"])
        for group in groups:
            group["matches"].sort(key=lambda x: (x["kickoff"], x["id"]))
        grouped.append(groups)
        stage["tie_count"] = len(groups)

    # Work backwards: order each round by its confirmed destination so
    # connectors don't cross needlessly when API-Football's kickoff order
    # differs from the actual bracket branch.
    for index in range(len(ordered) - 2, -1, -1):
        stage = ordered[index]
        next_stage = ordered[index + 1]
        current_groups = grouped[index]
        next_groups = grouped[index + 1]
        if next_stage["order"] == stage["order"] + 1:
            by_team = {}
            for target_idx, target in enumerate(next_groups):
                for team_id in target["teams"]:
                    by_team.setdefault(team_id, set()).add(target_idx)

            for group in current_groups:
                # Only one next tie and one common participant.
                # If both rivals progress to separate fixtures, the relation
                # is ambiguous and no edge may be drawn.
                candidates = set().union(
                    *(by_team.get(team_id, set()) for team_id in group["teams"]))
                if len(candidates) != 1:
                    continue
                target_idx = next(iter(candidates))
                matching = group["teams"].intersection(next_groups[target_idx]["teams"])
                if len(matching) != 1:
                    continue
                target = next_groups[target_idx]
                group["target_idx"] = target_idx
                team_id = next(iter(matching))
                for match in group["matches"]:
                    match["next_match_id"] = target["matches"][0]["id"]
                    match["qualified_team_id"] = team_id

            current_groups.sort(key=lambda g: (
                g.get("target_idx", len(next_groups)),
                g["matches"][0]["kickoff"], g["matches"][0]["id"],
            ))
        grouped[index] = current_groups
        stage["matches"] = [match for group in current_groups for match in group["matches"]]

    return ordered
