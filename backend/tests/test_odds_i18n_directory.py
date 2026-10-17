"""Coverage and compliance regressions for bilingual odds UI."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_bilingual_odds_and_major_sports_labels():
    extra = read("frontend/src/i18n-extended.ts")
    base = read("frontend/src/i18n.ts")
    for spanish, english in [
        ("Cuotas 1X2 · Comparación entre casas", "Bookmaker comparison"),
        ("Operadores privados", "Private operators"),
        ("Operadores públicos", "State-run operators"),
        ("País", "Country"),
        ("Goles y tarjetas", "Goals and cards"),
        ("Rugby", "Rugby"),
        ("Campeonato de pilotos", "Drivers"),
        ("Posiciones oficiales", "Official standings"),
        ("Clubes participantes", "Participating clubs"),
        ("No hay datos disponibles para esta edición.", "No data available"),
        ("Destacados en vivo", "Live highlights"),
    ]:
        if spanish != "Rugby":
            assert spanish in extra, spanish
            assert english in extra, english
    assert 'import { EXTENDED_EN } from "./i18n-extended"' in base
    assert "...EXTENDED_EN," in base
    assert "translateText(value:" in base
    assert '"title","aria-description","data-tooltip","alt"' in base
    assert "attributeOriginals" in base


def test_percent_bar_is_not_probability_or_fixed_returns():
    ui = read("frontend/src/match-odds.tsx")
    assert "payoutUplift" in ui
    assert "offer / lowest - 1" in ui
    assert "q.prices[o.key]" in ui
    assert "q.bookmaker" in ui
    assert "Number.isFinite" in ui
    assert "Se necesita otra casa para comparar" in ui
    assert "probabilidades" in ui or "probabilidad" in ui


def test_public_authority_not_mislabelled_as_bookmaker():
    directory = read("frontend/src/betting-guide.tsx")
    assert "Una autoridad pública no es una casa de apuestas" in directory
    assert "country===\"BR\"" in directory
    assert "1.394/2026" in directory
    assert 'kind:"public"' in directory
    assert 'kind:"private"' in directory
    assert "LICENSED[country]" in directory
    assert "AUTHORITIES[country]" in directory
    assert "SELAE · La Quiniela" in directory
