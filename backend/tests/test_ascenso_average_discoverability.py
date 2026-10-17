"""Ascenso league PTS/PJ exposed from sidebar and tables without false descensos."""
from pathlib import Path

from app.lower_division_averages import lower_division_key, performance_average

ROOT=Path(__file__).resolve().parents[2]


def test_all_four_requested_argentine_leagues_support_points_per_game():
    names=("Primera Nacional","Primera B Metropolitana","Primera C","Primera D")
    assert [lower_division_key(name,"Argentina") for name in names]==[
        "nacional","b","c","d",
    ]


def test_sidebar_exposes_distinct_average_routes_and_preserves_league_urls():
    ui=(ROOT/"frontend/src/main.tsx").read_text()
    assert 'class="league-nav-item"' in ui
    assert 'class="league-nav-average"' in ui
    assert 'lowerLeagueCode(l) &&' in ui
    assert 'href={link(`/promedios/${l.id}`)}' in ui
    assert 'href={link(`/league/${l.id}`)}' in ui
    assert 'aria-label={`Promedios de puntos por partido: ${l.name}`}' in ui


def test_standings_show_numeric_average_only_on_request_leagues():
    ui=(ROOT/"frontend/src/main.tsx").read_text()
    assert 'const ascensoAverage = lowerLeagueCode(league)' in ui
    assert '...(ascensoAverage ? ["PTS/PJ"] : [])' in ui
    assert 'r.played>0 && Number.isFinite(r.points)' in ui
    assert 'r.points/r.played' in ui
    assert 'class="ascenso-ppg-cell"' in ui
    assert 'no es un promedio oficial de descenso' in ui
    assert 'class="ascenso-promedios-quick-link"' in ui
    assert 'ascensoAverage==="d"' in ui
    assert 'Primera D · archivo hasta 2023' in ui
    assert 'toLocaleString("es-AR"' in ui


def test_sidebar_and_table_link_responsive_styles_are_present():
    css=(ROOT/"frontend/src/style.css").read_text()
    assert ".league-nav-item" in css
    assert ".league-nav-average" in css
    assert ".ascenso-promedios-quick-link" in css
    assert ".ascenso-ppg-cell" in css
    assert "@media(max-width:640px)" in css


def test_regulation_links_and_relegation_distinction():
    from app.lower_division_averages import REGULATIONS, RULES
    assert "Boletin-Especial-6823" in REGULATIONS["nacional"]
    assert "Boletin-Especial-6824" in REGULATIONS["b"]
    assert "dos últimos equipos de cada zona" in RULES["nacional"].lower()
    d=performance_average([],{},"d",2026)
    assert d["historic_only"] and not d["groups"]
    assert "2026" in d["note"]


def test_empty_standings_never_produce_fake_average_rows():
    groups=performance_average([],{},"c",2026)["groups"]
    assert not groups
