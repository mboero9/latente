"""2026 competition entry lists verified against URBA/UAR publications.

These are *participants*, NOT standings or API results. No club logos, scores,
league points or kickoff times are inferred from this file. Only display
the edition explicitly documented by its governing union.
"""
from __future__ import annotations

URBA_2026 = (
    "Alumni",
    "Atlético del Rosario",
    "Belgrano Athletic",
    "Buenos Aires Cricket & Rugby Club",
    "CASI",
    "Champagnat",
    "CUBA",
    "Hindú",
    "La Plata Rugby Club",
    "Los Matreros",
    "Los Tilos",
    "Newman",
    "Regatas Bella Vista",
    "SIC",
)

INTERIOR_A_2026 = {
    "Zona 1": ("Marista RC", "Gimnasia y Esgrima de Rosario", "Mendoza RC", "Tucumán Rugby"),
    "Zona 2": ("Tala RC", "Estudiantes de Paraná", "CURNE", "Urú Curé"),
    "Zona 3": ("Jockey Club de Rosario", "Universitario de Córdoba", "Córdoba Athletic", "Santa Fe Rugby"),
    "Zona 4": ("Duendes RC", "Jockey Club de Córdoba", "La Tablada", "Old Resian"),
}

# These fourteen logos are linked from the URBA's official 2026 home page,
# under https://api.urba.org.ar/img/clubs/. No guessing file names or rehosting.
URBA_TOP14_OFFICIAL_LOGOS = {
    "Alumni": "alumni.png",
    "Atlético del Rosario": "rosario.png",
    "Belgrano Athletic": "belgrano.png",
    "Buenos Aires Cricket & Rugby Club": "bacrc.png",
    "CASI": "casi.png",
    "Champagnat": "champagnat.png",
    "CUBA": "cuba.png",
    "Hindú": "hindu.png",
    "La Plata Rugby Club": "laplata.png",
    "Los Matreros": "losmatreros.png",
    "Los Tilos": "lostilos.png",
    "Newman": "newman.png",
    "Regatas Bella Vista": "regatasbellavista.png",
    "SIC": "sic.png",
}

# Official 2026 Córdoba Top 10 fixture (Unión Cordobesa de Rugby).
CORDOBA_TOP10_2026 = (
    "San Martín de Villa María", "Córdoba Athletic Club",
    "Carlos Paz RC", "Palermo Bajo", "Universitario de Córdoba",
    "La Tablada", "Urú Curé", "Jockey Club de Villa María",
    "Tala RC", "Jockey Club de Córdoba",
)

# First division entrants, per URR/USR/UER 2026 official TRL regulations.
LITORAL_TOP10_2026 = (
    "Gimnasia y Esgrima de Rosario", "Duendes RC",
    "Jockey Club de Rosario", "Old Resian",
    "Jockey Club de Venado Tuerto", "Universitario de Rosario",
    "Santa Fe Rugby Club", "CRAI", "Estudiantes de Paraná",
    "Paraná Rowing",
)

# These are just the four TDI-B 2026 qualification pairings; the final
# TDI-B competition groups were announced after qualification.
INTERIOR_B_REPECHAJE_2026 = (
    "Cardenales RC", "Taragüí RC", "Jockey Club de Tucumán",
    "Universitario de San Juan", "Sociedad Sportiva", "Neuquén RC",
    "Tigres RC", "Jockey de Venado Tuerto",
)

# International 2026/27 entrants from the named competition organizers.
# These are NOT dynamically refreshed standings, scores or fixtures.
TOP14_FR_2026_27 = (
    "LOU Rugby", "Stade Toulousain", "Union Bordeaux-Bègles",
    "Section Paloise", "Montpellier Hérault Rugby", "Aviron Bayonnais",
    "Castres Olympique", "Stade Rochelais", "ASM Clermont",
    "USA Perpignan", "Stade Français Paris", "Racing 92",
    "RC Toulon", "RC Vannes",
)
PREM_2026_27 = (
    "Bath Rugby", "Bristol Bears", "Exeter Chiefs", "Gloucester Rugby",
    "Harlequins", "Leicester Tigers", "Newcastle Red Bulls",
    "Northampton Saints", "Sale Sharks", "Saracens",
)
CHAMPIONS_CUP_2026_27 = {
    "Pool 1": ("Leinster Rugby", "Glasgow Warriors", "Section Paloise",
               "Sale Sharks", "Leicester Tigers", "ASM Clermont Auvergne"),
    "Pool 2": ("Stade Toulousain", "Lions", "Saracens", "Stade Rochelais",
               "Exeter Chiefs", "Connacht Rugby"),
    "Pool 3": ("Union Bordeaux Bègles", "DHL Stormers", "Racing 92",
               "Munster Rugby", "Bristol Bears", "Gloucester Rugby"),
    "Pool 4": ("Northampton Saints", "Bath Rugby", "Cardiff Rugby",
               "Montpellier Hérault Rugby", "Stade Français Paris", "Vodacom Bulls"),
}
CHALLENGE_CUP_2026_27 = {
    "Pool 1": ("Toyota Cheetahs", "Ulster Rugby", "USAP",
               "Dragons RFC", "Aviron Bayonnais", "Zebre Parma"),
    "Pool 2": ("Benetton Rugby", "Lyon Olympique Universitaire",
               "Newcastle Red Bulls", "Hollywoodbets Sharks",
               "Castres Olympique", "Scarlets"),
    "Pool 3": ("Ospreys", "Edinburgh Rugby", "Black Lion",
               "Harlequins", "RC Toulon", "RC Vannes"),
}

OFFICIAL_SOURCES = {
    "urba": "https://urba.org.ar/fixture",
    "urba-primera-a": "https://urba.org.ar/fixture",
    "urba-primera-b": "https://urba.org.ar/fixture",
    "urba-primera-c": "https://urba.org.ar/fixture",
    "urba-segunda": "https://urba.org.ar/fixture",
    "urba-tercera": "https://urba.org.ar/fixture",
    "urba-desarrollo": "https://urba.org.ar/fixture",
    "litoral-top10": "https://usr.org.ar/wp-content/uploads/2026/03/2026-Reglamento-General-TRL.pdf",
    "litoral-segunda": "https://urr.org.ar/programacion-semanal-arranca-el-trl-%F0%9F%92%A5/",
    "cordoba-top10": "https://unioncordobesaderugby.com.ar/fixtures-2026/",
    "cordoba-super9": "https://unioncordobesaderugby.com.ar/fixtures-2026/",
    "interior-a": "https://uar.com.ar/se-confirmo-el-fixture-del-torneo-del-interior-2026/",
    "interior-b": "https://uar.com.ar/se-confirmo-el-fixture-del-torneo-del-interior-2026/",
    "top-14": "https://top14.lnr.fr/classement/2026-2027/j3",
    "pro-d2": "https://www.lnr.fr/",
    "premiership": "https://www.premiershiprugby.com/match-centre/288986/standings",
    "premiership-cup": "https://www.premiershiprugby.com/",
    "champions": "https://www.epcrugby.com/challenge-cup/content/official-investec-champions-cup-and-epcr-challenge-pools-confirmed-for-202627-season",
    "challenge-cup": "https://www.epcrugby.com/challenge-cup/content/official-investec-champions-cup-and-epcr-challenge-pools-confirmed-for-202627-season",
    "championship": "https://www.sanzarrugby.com/",
    "urc": "https://www.unitedrugby.com/",
}


def edition_clubs(slug: str, year: int) -> list[dict[str, str]]:
    if year != 2026:
        return []
    if slug == "urba":
        return [{"team": name, "group": "URBA Top 14",
                 "logo": "https://api.urba.org.ar/img/clubs/" +
                         URBA_TOP14_OFFICIAL_LOGOS[name]}
                for name in URBA_2026]
    if slug == "cordoba-top10":
        return [{"team": name, "group": "Top 10 A · Córdoba"}
                for name in CORDOBA_TOP10_2026]
    if slug == "litoral-top10":
        return [{"team": name, "group": "Top 10 · Litoral"}
                for name in LITORAL_TOP10_2026]
    if slug == "interior-a":
        return [{"team": name, "group": group}
                for group, names in INTERIOR_A_2026.items() for name in names]
    if slug == "interior-b":
        return [{"team": name, "group": "Reválida (no plantel definitivo)"}
                for name in INTERIOR_B_REPECHAJE_2026]
    if slug == "top-14":
        return [{"team": name, "group": "Top 14 · Francia (2026/27)"}
                for name in TOP14_FR_2026_27]
    if slug == "premiership":
        return [{"team": name, "group": "Gallagher PREM (2026/27)"}
                for name in PREM_2026_27]
    if slug == "champions":
        return [{"team": name, "group": group}
                for group, teams in CHAMPIONS_CUP_2026_27.items() for name in teams]
    if slug == "challenge-cup":
        return [{"team": name, "group": group}
                for group, teams in CHALLENGE_CUP_2026_27.items() for name in teams]
    return []


def source_url(slug: str) -> str | None:
    return OFFICIAL_SOURCES.get(slug)


# Official 2026 TDI-A *published schedule*, not live scores. Only regulation
# group-stage rounds, confirmed 22/12/2025 by the UAR.
INTERIOR_A_SCHEDULE_2026 = (
    ("2026-03-28", (
        ("Gimnasia y Esgrima de Rosario", "Marista RC"),
        ("Tucumán Rugby", "Mendoza RC"), ("Estudiantes de Paraná", "Tala RC"),
        ("Urú Curé", "CURNE"), ("Universitario de Córdoba", "Jockey Club de Rosario"),
        ("Santa Fe Rugby", "Córdoba Athletic"),
        ("Jockey Club de Córdoba", "Duendes RC"), ("Old Resian", "La Tablada"),
    )),
    ("2026-04-25", (
        ("Marista RC", "Tucumán Rugby"), ("Mendoza RC", "Gimnasia y Esgrima de Rosario"),
        ("Tala RC", "Urú Curé"), ("CURNE", "Estudiantes de Paraná"),
        ("Jockey Club de Rosario", "Santa Fe Rugby"),
        ("Córdoba Athletic", "Universitario de Córdoba"),
        ("Duendes RC", "Old Resian"), ("La Tablada", "Jockey Club de Córdoba"),
    )),
    ("2026-05-30", (
        ("Mendoza RC", "Marista RC"), ("Tucumán Rugby", "Gimnasia y Esgrima de Rosario"),
        ("CURNE", "Tala RC"), ("Urú Curé", "Estudiantes de Paraná"),
        ("Córdoba Athletic", "Jockey Club de Rosario"),
        ("Santa Fe Rugby", "Universitario de Córdoba"),
        ("La Tablada", "Duendes RC"), ("Old Resian", "Jockey Club de Córdoba"),
    )),
    ("2026-06-27", (
        ("Marista RC", "Mendoza RC"), ("Gimnasia y Esgrima de Rosario", "Tucumán Rugby"),
        ("Tala RC", "CURNE"), ("Estudiantes de Paraná", "Urú Curé"),
        ("Jockey Club de Rosario", "Córdoba Athletic"),
        ("Universitario de Córdoba", "Santa Fe Rugby"),
        ("Duendes RC", "La Tablada"), ("Jockey Club de Córdoba", "Old Resian"),
    )),
    ("2026-07-25", (
        ("Tucumán Rugby", "Marista RC"), ("Gimnasia y Esgrima de Rosario", "Mendoza RC"),
        ("Urú Curé", "Tala RC"), ("Estudiantes de Paraná", "CURNE"),
        ("Santa Fe Rugby", "Jockey Club de Rosario"),
        ("Universitario de Córdoba", "Córdoba Athletic"),
        ("Old Resian", "Duendes RC"), ("Jockey Club de Córdoba", "La Tablada"),
    )),
    ("2026-08-01", (
        ("Marista RC", "Gimnasia y Esgrima de Rosario"), ("Mendoza RC", "Tucumán Rugby"),
        ("Tala RC", "Estudiantes de Paraná"), ("CURNE", "Urú Curé"),
        ("Jockey Club de Rosario", "Universitario de Córdoba"),
        ("Córdoba Athletic", "Santa Fe Rugby"),
        ("Duendes RC", "Jockey Club de Córdoba"), ("La Tablada", "Old Resian"),
    )),
)


def published_schedule(slug: str, year: int) -> list[dict[str, str | int]]:
    if slug != "interior-a" or year != 2026:
        return []
    return [
        {"round": round_index, "date": kickoff, "home": home, "away": away}
        for round_index, (kickoff, pairings) in enumerate(INTERIOR_A_SCHEDULE_2026, start=1)
        for home, away in pairings
    ]
