"""Resolve club crests against teams that API-Football already verified and
stored in PostgreSQL. No scraping, no per-visitor external API requests.
"""
from __future__ import annotations

import unicodedata

# Conservative exact aliases: never attach a similarly named club's crest.
CLUB_ALIASES: dict[str, tuple[str, ...]] = {
    "Real Madrid": ("Real Madrid", "Real Madrid CF"),
    "Al Ahly": ("Al Ahly", "Al Ahly SC", "Al Ahly Cairo"),
    "AC Milan": ("AC Milan", "Milan"),
    "Boca Juniors": ("Boca Juniors",),
    "Independiente": ("Independiente",),
    "FC Barcelona": ("Barcelona", "FC Barcelona"),
    "Liverpool": ("Liverpool",),
    "Bayern Múnich": ("Bayern München", "Bayern Munich"),
    "Chelsea": ("Chelsea",),
    "Ajax": ("Ajax",),
    "Sevilla": ("Sevilla",),
    "Al Nassr": ("Al-Nassr", "Al Nassr"),
    "Inter Miami CF": ("Inter Miami", "Inter Miami CF"),
    "Santos": ("Santos", "Santos FC"),
    "Vasco da Gama": ("Vasco DA Gama", "Vasco da Gama"),
    "Slavia Praga": ("Slavia Praha", "Slavia Prague", "Slavia Praga"),
    "Glenavon": ("Glenavon FC", "Glenavon"),
    "Linfield": ("Linfield FC", "Linfield"),
    "SC Heerenveen": ("Heerenveen", "SC Heerenveen"),
    "Benfica": ("Benfica", "SL Benfica"),
}

EXPECTED_COUNTRIES: dict[str, tuple[str, ...]] = {
    "Real Madrid": ("spain", "espana"),
    "Al Ahly": ("egypt", "egipto"),
    "AC Milan": ("italy", "italia"),
    "Boca Juniors": ("argentina",),
    "Independiente": ("argentina",),
    "FC Barcelona": ("spain", "espana"),
    "Liverpool": ("england", "inglaterra"),
    "Bayern Múnich": ("germany", "alemania"),
    "Chelsea": ("england", "inglaterra"),
    "Ajax": ("netherlands", "paises bajos"),
    "Sevilla": ("spain", "espana"),
    "Al Nassr": ("saudi arabia", "arabia saudita"),
    "Inter Miami CF": ("usa", "united states", "estados unidos"),
    "Santos": ("brazil", "brasil"),
    "Vasco da Gama": ("brazil", "brasil"),
    "Slavia Praga": ("czech republic", "czechia", "republica checa"),
    "Glenavon": ("northern ireland", "irlanda del norte"),
    "Linfield": ("northern ireland", "irlanda del norte"),
    "SC Heerenveen": ("netherlands", "paises bajos"),
    "Benfica": ("portugal",),
}


def normalized(value: str) -> str:
    return "".join(
        letter for letter in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(letter)
    ).strip()


def resolve_curated_clubs(team_rows) -> dict[str, int]:
    """Team rows have id, name, country. Exact alias and country are required."""
    result: dict[str, int] = {}
    for canonical, aliases in CLUB_ALIASES.items():
        expected = EXPECTED_COUNTRIES[canonical]
        for alias in aliases:
            match = next(
                (row for row in team_rows
                 if normalized(row.name) == normalized(alias)
                 and normalized(row.country or "") in expected),
                None,
            )
            if match:
                result[canonical] = match.id
                break
    return result
