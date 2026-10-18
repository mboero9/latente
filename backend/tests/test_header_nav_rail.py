"""Regression tests: header sports remain visible via arrows and slider."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_header_renders_all_sports_in_scrollable_rail():
    main=(ROOT/"frontend/src/main.tsx").read_text(encoding="utf-8")
    sports=(ROOT/"frontend/src/other-sports.tsx").read_text(encoding="utf-8")
    assert 'import { NavRail } from "./nav-rail";' in main
    assert '<NavRail activePath={route}>' in main
    assert '...[...sports].sort(' in main
    assert 'SPORT_NAV_ORDER.indexOf(a.slug)' in main
    assert '.map(sport =>' in main
    assert 'aria-current={active ? "page" : undefined}' in main
    assert '["/league/253", "🇺🇸 MLS"]' in main
    for key in ["nhl","mlb","nba","wnba","basketball","handball",
                "volleyball","f1","nfl","rugby","cricket"]:
        assert f'slug: "{key}"' in sports, key

def test_header_rail_has_buttons_slider_touch_and_resize():
    nav=(ROOT/"frontend/src/nav-rail.tsx").read_text(encoding="utf-8")
    css=(ROOT/"frontend/src/style.css").read_text(encoding="utf-8")
    for name in ["Ver actividades anteriores","Ver más actividades",
                 'type="range"',"scrollBy(","scrollWidth - node.clientWidth",
                 "ResizeObserver","activePath","aria-label=\"Navegación principal\""]:
        assert name in nav, name
    assert "overflow-x: auto" in css
    assert ".header .top-nav-items" in css
    assert ".header .nav-rail-slider input" in css
    assert ".header .nav-rail-arrow" in css
    assert "scroll-snap-type: x proximity" in css
    assert "@media (max-width: 800px)" in css


def test_header_uses_spaced_pill_selection_and_compact_progress_control():
    nav=(ROOT/"frontend/src/nav-rail.tsx").read_text(encoding="utf-8")
    css=(ROOT/"frontend/src/style.css").read_text(encoding="utf-8")
    assert 'style={`--nav-progress:${percentage}%`}' in nav
    assert ".header .top-nav-items > a.active" in css
    assert "background: var(--green-soft);" in css
    assert "border-radius: 999px;" in css
    assert "justify-content: flex-end;" in css
    assert "margin-top: 6px;" in css
    assert "var(--nav-progress, 0%)" in css
    assert "height: 3px;" in css
    assert "width: 13px;" in css
    assert "min-width: 90px;" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert 'onClick={() => shift(-1)}' in nav
    assert 'onClick={() => shift(1)}' in nav


def test_copa_argentina_libertadores_sudamericana_only_in_home_shortcuts():
    main=(ROOT/"frontend/src/main.tsx").read_text(encoding="utf-8")
    header=main.split('<NavRail activePath={route}>',1)[1].split('</NavRail>',1)[0]
    assert "LATENTE_PRIMARY_LEAGUES" not in header
    assert '["/", "Partidos"]' in header
    assert '["/leagues", "Ligas"]' in header
    assert '["/tv", "📺 Dónde ver"]' in header
    assert '["/bet", "18+ Dónde apostar"]' in header
    assert '...[...sports].sort(' in header

    # The homepage still displays real, functional shortcuts to all cups.
    shortcuts=main.split('<nav class="argentina-conmebol-shortcuts"',1)[1].split('</nav>',1)[0]
    assert "LATENTE_PRIMARY_LEAGUES.filter" in shortcuts
    assert '/league/${item.id}' in shortcuts
    for ident in (130,13,11):
        assert f'{{id:{ident},label:' in main
    assert "leaguePriority" in main
