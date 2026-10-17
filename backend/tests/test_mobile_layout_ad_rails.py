"""Mobile responsive regressions and safe prospective side advertising."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def source(path):
    return (ROOT/path).read_text(encoding="utf-8")

def test_f1_names_never_collapse_into_vertical_letters():
    view=source("frontend/src/reference-sports.tsx")
    css=source("frontend/src/style.css")
    assert 'class="panel table-scroll f1-standings-scroll"' in view
    assert 'role="region" tabIndex={0}' in view
    assert "Deslizá la tabla" in view
    assert "f1-standings-table--${tab}" not in view  # must be a JS expression
    assert 'f1-standings-table--${tab}' not in view
    assert 'f1-standings-table--${tab}' not in css
    assert "f1-standings-table--drivers {min-width:1000px;}" in css
    assert "f1-standings-table--constructors {min-width:690px;}" in css
    assert ".f1-standings-table th:nth-child(2) {min-width:235px;" in css
    assert "overflow-wrap:normal;word-break:normal;" in css
    assert "white-space:nowrap;" in css
    assert "overscroll-behavior-x:contain" in css
    assert ".f1-champions-table table {min-width:750px;" in css


def test_football_argentina_conmebol_first_on_mobile_and_desktop():
    ui=source("frontend/src/main.tsx")
    css=source("frontend/src/style.css")
    assert "<ArgentinaFootballLinks leagues={leagues}/>" in ui
    assert ui.index("<ArgentinaFootballLinks leagues={leagues}/>") < ui.index('class="f1-home-mobile-link"')
    for label in ("Liga Argentina","Libertadores","Copa Argentina","Sudamericana","Primera Nacional"):
        assert f'text:"{label}"' in ui
    assert "editorialLeaguePriority" in ui
    assert ".sort((a,b)=>editorialLeaguePriority(a)-editorialLeaguePriority(b))" in ui
    assert "editorialLeaguePriority(a[1][0].league)" in ui
    assert "score=Math.max(score,2170)" in ui
    assert ".home-argentina-links {display:flex;flex-wrap:nowrap;overflow-x:auto;" in css


def test_vertical_ad_rails_off_without_cpm_approval_and_never_on_phone():
    ads=source("frontend/src/ads.tsx")
    css=source("frontend/src/style.css")
    ui=source("frontend/src/main.tsx")
    docs=source("docs/MONETIZACION-PUBLICIDAD.md")
    assert 'VITE_ADSENSE_SLOT_SIDE_LEFT' in ads
    assert 'VITE_ADSENSE_SLOT_SIDE_RIGHT' in ads
    assert '"side-left" | "side-right"' in ads
    assert 'VITE_ADSENSE_ENABLED === "true"' in ads
    assert 'VITE_ADS_PRIVACY_READY === "true"' in ads
    assert '&& /^\\d+$/.test(slotId)' in ads
    assert "latente-outer-ad-rails" in ui
    assert 'placement="side-left"' in ui and 'placement="side-right"' in ui
    assert 'view !== "bet" && view !== "match" && view !== "watch"' in ui
    assert ".latente-outer-ad-rails {display:none;}" in css
    assert "@media(min-width:1980px) and (min-height:720px)" in css
    assert "Nunca" not in docs or "nunca" in docs.lower()
    assert "no activar publicidad todavía" in docs


def test_public_delay_badges_not_rendered_but_internal_stale_remains():
    main=source("frontend/src/main.tsx")
    incidents=source("frontend/src/live-incidents.tsx")
    assert 'm.stale) score -= 120' in main
    assert 'class="stale">Demorado' not in main
    assert "Datos demorados" not in main
    assert "Las estadísticas están demoradas" not in main
    assert "Datos demorados" not in incidents
    assert "checked_at" in incidents
