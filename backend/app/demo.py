"""Dataset ficticio reproducible. Ninguna cifra representa resultados reales."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import delete
from .models import League, Fixture, FixtureStatistics, Standing, Scorer, Team, utcnow
from .ingest import upsert, team, membership

DEMO_LEAGUES = [
    (
        128,
        "Liga Profesional",
        "Argentina",
        [
            "River Plate",
            "Boca Juniors",
            "Racing Club",
            "Independiente",
            "San Lorenzo",
            "Vélez Sarsfield",
            "Estudiantes",
            "Huracán",
        ],
    ),
    (
        129,
        "Primera Nacional",
        "Argentina",
        ["Ferro", "Chacarita", "Quilmes", "Atlanta"],
    ),
    (
        130,
        "Copa Argentina",
        "Argentina",
        ["Rosario Central", "Newell’s", "Talleres", "Belgrano"],
    ),
    (
        13,
        "CONMEBOL Libertadores",
        "Sudamérica",
        ["Palmeiras", "Flamengo", "Peñarol", "Nacional"],
    ),
    (
        11,
        "CONMEBOL Sudamericana",
        "Sudamérica",
        ["Lanús", "Universidad de Chile", "Fortaleza", "América de Cali"],
    ),
    (
        2,
        "Champions League",
        "Europa",
        ["Real Madrid", "Bayern München", "Inter", "Paris Saint-Germain"],
    ),
    (
        39,
        "Premier League",
        "Inglaterra",
        ["Arsenal", "Liverpool", "Manchester City", "Chelsea"],
    ),
    (
        140,
        "La Liga",
        "España",
        ["Barcelona", "Atlético de Madrid", "Athletic Club", "Real Sociedad"],
    ),
    (135, "Serie A", "Italia", ["Napoli", "Milan", "Juventus", "Roma"]),
    (78, "Bundesliga", "Alemania", ["Dortmund", "Leverkusen", "Leipzig", "Frankfurt"]),
    (61, "Ligue 1", "Francia", ["Marseille", "Monaco", "Lille", "Lyon"]),
    (71, "Brasileirão", "Brasil", ["Botafogo", "Fluminense", "São Paulo", "Santos"]),
]


def seed_demo(s):
    now = utcnow()
    local = now.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    today = local.replace(hour=0, minute=0, second=0, microsecond=0)
    # Se genera una vez por día. No fingimos eventos en vivo ni progreso del reloj.
    existing = s.get(League, ("demo", 128))
    seeded_at = existing.updated_at if existing else None
    if seeded_at and seeded_at.tzinfo is None:
        seeded_at = seeded_at.replace(tzinfo=timezone.utc)
    if (
        seeded_at
        and seeded_at.astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date()
        == local.date()
        and s.get(Fixture, ("demo", 12800))
    ):
        return
    s.execute(delete(FixtureStatistics).where(FixtureStatistics.source == "demo"))
    s.execute(delete(Fixture).where(Fixture.source == "demo"))
    for li, (league_id, name, country, names) in enumerate(DEMO_LEAGUES):
        upsert(
            s,
            League,
            dict(
                source="demo",
                id=league_id,
                name=name,
                country=country,
                kind="Cup" if league_id in [130, 13, 11, 2] else "League",
                season=local.year,
                seasons=[local.year],
                coverage={"standings": True, "top_scorers": True},
                updated_at=now,
            ),
        )
        for i, name in enumerate(names):
            tid = league_id * 100 + i
            team(
                s,
                {
                    "id": tid,
                    "name": name,
                    "code": "".join(n[0] for n in name.split())[:3].upper(),
                },
                "demo",
                country=country,
            )
            membership(s, "demo", league_id, local.year, tid)
            group = "Zona A" if i < len(names) // 2 else "Zona B"
            rank = i % (len(names) // 2) + 1
            won, drawn, lost = 9 - rank, 3, rank
            upsert(
                s,
                Standing,
                dict(
                    source="demo",
                    league_id=league_id,
                    season=local.year,
                    group=group,
                    team_id=tid,
                    rank=rank,
                    points=won * 3 + drawn,
                    played=won + drawn + lost,
                    won=won,
                    drawn=drawn,
                    lost=lost,
                    goals_for=26 - i,
                    goals_against=12 + i,
                    difference=14 - 2 * i,
                    form=["WWDWW", "WLDWW", "DWLWD", "LLWDW"][i % 4],
                    description=None,
                    updated_at=now,
                ),
            )
            upsert(
                s,
                Scorer,
                dict(
                    source="demo",
                    league_id=league_id,
                    season=local.year,
                    player_id=tid,
                    team_id=tid,
                    name=[
                        "Mateo Fernández",
                        "Lucas Acosta",
                        "Tomás Romero",
                        "Santiago Medina",
                        "Julián Castro",
                        "Nicolás Silva",
                        "Bruno Torres",
                        "Franco Ríos",
                    ][i],
                    rank=i + 1,
                    goals=12 - i,
                    assists=3 + i % 3,
                    appearances=12,
                    penalties=i % 3,
                    updated_at=now,
                ),
            )
        for offset in [-1, 0, 1, 2]:
            for match in range(len(names) // 2):
                status = (
                    "FT"
                    if offset < 0
                    else (
                        "NS"
                        if offset > 0
                        else (
                            ["2H", "FT", "NS", "NS"][match]
                            if li == 0
                            else ["2H" if li in [5, 6] else "FT", "NS"][match % 2]
                        )
                    )
                )
                kickoff = today + timedelta(
                    days=offset, hours=16 + match * 2 + (li % 3)
                )
                upsert(
                    s,
                    Fixture,
                    dict(
                        source="demo",
                        id=league_id * 100 + (offset + 1) * 10 + match,
                        league_id=league_id,
                        season=local.year,
                        round="Fecha 13 · Demostración",
                        kickoff=kickoff,
                        home_id=league_id * 100 + match * 2,
                        away_id=league_id * 100 + match * 2 + 1,
                        status=status,
                        elapsed=(
                            67 if status == "2H" else 90 if status == "FT" else None
                        ),
                        extra=None,
                        home_goals=2 if status in ["FT", "2H"] else None,
                        away_goals=1 if status in ["FT", "2H"] else None,
                        venue="Estadio de demostración",
                        referee=None,
                        score={},
                        updated_at=now,
                    ),
                )
