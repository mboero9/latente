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

# These are just the four TDI-B 2026 qualification pairings; the final
# TDI-B competition groups were announced after qualification.
INTERIOR_B_REPECHAJE_2026 = (
    "Cardenales RC", "Taragüí RC", "Jockey Club de Tucumán",
    "Universitario de San Juan", "Sociedad Sportiva", "Neuquén RC",
    "Tigres RC", "Jockey de Venado Tuerto",
)

OFFICIAL_SOURCES = {
    "urba": "https://urba.org.ar/fixture",
    "interior-a": "https://uar.com.ar/se-confirmo-el-fixture-del-torneo-del-interior-2026/",
    "interior-b": "https://uar.com.ar/se-confirmo-el-fixture-del-torneo-del-interior-2026/",
    "top-14": "https://www.lnr.fr/",
    "pro-d2": "https://www.lnr.fr/",
    "premiership": "https://www.premiershiprugby.com/",
    "premiership-cup": "https://www.premiershiprugby.com/",
    "champions": "https://www.epcrugby.com/",
    "challenge-cup": "https://www.epcrugby.com/",
    "championship": "https://www.sanzarrugby.com/",
    "urc": "https://www.unitedrugby.com/",
}


def edition_clubs(slug: str, year: int) -> list[dict[str, str]]:
    if year != 2026:
        return []
    if slug == "urba":
        return [{"team": name, "group": "URBA Top 14"} for name in URBA_2026]
    if slug == "interior-a":
        return [{"team": name, "group": group}
                for group, names in INTERIOR_A_2026.items() for name in names]
    if slug == "interior-b":
        return [{"team": name, "group": "Reválida (no plantel definitivo)"}
                for name in INTERIOR_B_REPECHAJE_2026]
    return []


def source_url(slug: str) -> str | None:
    return OFFICIAL_SOURCES.get(slug)
