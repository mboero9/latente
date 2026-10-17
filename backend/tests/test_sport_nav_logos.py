"""Sport-brand marks must be accurate, mobile-readable and optional."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

def test_all_branded_leagues_include_confirmed_assets():
    nav=read("frontend/src/sport-nav-logo.tsx")
    mapping={
        "nba":"National Basketball Association logo 2017-present.svg",
        "f1":"Formula One logo.svg",
        "nfl":"NFL wordmark logo 2008.svg",
        "nhl":"National Hockey League shield.svg",
        "mlb":"Major League Baseball logo.svg",
        "wnba":"WNBA logo.png",
        "cricket":"ICC logo (2026).svg",
        "basketball":"FIBA logo.svg",
        "handball":"Internationalen Handballföderation.png",
        "volleyball":"Fédération Internationale de Volleyball logo.svg",
    }
    for slug,file in mapping.items():
        assert f"{slug}: {{file:\"{file}\"" in nav
    # Rugby is a sport, not one single league or trademark; its ball remains.
    assert "rugby:" not in nav
    assert "commons.wikimedia.org/wiki/Special:FilePath/" in nav
    assert "onError={()=>setFailed(true)}" in nav
    assert "sport-nav-pictogram" in nav
    assert 'loading="lazy"' in nav
    assert "referrerPolicy=\"no-referrer\"" in nav

def test_header_keeps_routes_order_and_accessible_labels():
    main=read("frontend/src/main.tsx")
    assert 'import { SportNavLogo } from "./sport-nav-logo";' in main
    assert "navSport && <SportNavLogo" in main
    assert 'fallback={navSport.emoji}' in main
    assert "sport.name])," in main
    assert '"nba", "f1", "cricket", "nfl"' in main
    assert 'href={link(path)}' in main
    assert 'aria-current={active ? "page" : undefined}' in main
    assert 'SPORT_NAV_ORDER.indexOf(a.slug)' in main
    assert '.map(sport =>' in main
    assert '"18+ Dónde apostar"' in main

def test_mobile_nav_remains_scrollable_and_names_do_not_wrap():
    css=read("frontend/src/style.css")
    for marker in (
        ".header .sport-nav-logo", ".header .sport-nav-logo--tall",
        ".header .sport-nav-logo--wide",".header .sport-nav-logo--shield",
        ".header .sport-nav-pictogram", "white-space:nowrap;word-break:normal",
        "@media (max-width:560px)", "scroll-snap-type: x proximity",
    ):
        assert marker in css,marker
    assert 'class="nav-rail"' in read("frontend/src/nav-rail.tsx") or         'nav-rail' in read("frontend/src/nav-rail.tsx")
    # Previous correction of broken-up vertical driver names must stay active.
    assert ".f1-mobile-rows {display:grid" in css
    assert ".f1-desktop-standings {display:none;" in css
