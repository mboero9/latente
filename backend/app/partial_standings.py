"""Tablas parciales calculadas SOLO con resultados finales ya almacenados.

Nunca sustituir la clasificación oficial por esta estimación sin etiquetarla:
la API gratuita puede entregar apenas algunas fechas de la temporada.
"""
from collections import defaultdict

REGULAR_FINAL = {"FT"}


def partial_standings(fixtures, teams):
    board = defaultdict(lambda: dict(
        played=0, won=0, drawn=0, lost=0, goals_for=0, goals_against=0, points=0,
    ))
    completed = 0
    for fixture in fixtures:
        if fixture.status not in REGULAR_FINAL or fixture.home_goals is None or fixture.away_goals is None:
            continue
        if fixture.home_id == fixture.away_id:
            continue
        home, away = board[fixture.home_id], board[fixture.away_id]
        hg, ag = fixture.home_goals, fixture.away_goals
        if hg < 0 or ag < 0:
            continue
        completed += 1
        home["played"] += 1
        away["played"] += 1
        home["goals_for"] += hg
        home["goals_against"] += ag
        away["goals_for"] += ag
        away["goals_against"] += hg
        if hg == ag:
            home["drawn"] += 1
            away["drawn"] += 1
            home["points"] += 1
            away["points"] += 1
        elif hg > ag:
            home["won"] += 1
            away["lost"] += 1
            home["points"] += 3
        else:
            away["won"] += 1
            home["lost"] += 1
            away["points"] += 3

    ordered = sorted(
        board.items(),
        key=lambda pair: (
            -pair[1]["points"],
            -(pair[1]["goals_for"] - pair[1]["goals_against"]),
            -pair[1]["goals_for"],
            teams.get(pair[0], {}).get("name", "").lower(),
            pair[0],
        ),
    )
    output = []
    for rank, (team_id, record) in enumerate(ordered, 1):
        if team_id not in teams:
            continue
        output.append({
            **record,
            "team_id": team_id,
            "team": teams[team_id],
            "group": "Parcial · partidos disponibles",
            "rank": rank,
            "difference": record["goals_for"] - record["goals_against"],
            "form": None,
            "description": "Cálculo parcial: no es la clasificación oficial",
            "updated_at": None,
        })
    return output, completed
