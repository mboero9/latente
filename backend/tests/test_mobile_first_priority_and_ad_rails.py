"""Mobile-first Latente: rankings must remain legible and ads gated."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_f1_has_real_mobile_cards_with_full_driver_names():
    f1=read("frontend/src/reference-sports.tsx")
    styles=read("frontend/src/style.css")
    assert 'function F1MobileRows({data,tab}' in f1
    assert '<F1MobileRows data={data} tab={tab}/>' in f1
    assert '<strong>{d.name}</strong>' in f1
    assert '<strong>{t.name}</strong>' in f1
    assert '<strong>{d.driver}</strong>' in f1
    assert '<F1Portrait name={d.name} photo={d.photo}/>' in f1
    assert '<F1Nationality value={d.nationality}/>' in f1
    assert '<F1TeamLogo name={d.team}/>' in f1
    assert '<F1TeamLogo name={t.name}/>' in f1
    assert 'tab==="constructors"' in f1 and 'tab==="results"' in f1
    assert 'class="f1-mobile-rows"' in f1
    assert 'class="panel table-scroll f1-desktop-standings"' in f1
    assert 'tabIndex={0}' in f1
    assert '.f1-mobile-driver > strong' in styles
    assert 'word-break:normal;hyphens:none;' in styles
    assert '.f1-desktop-standings {display:none;}' in styles
    assert '.f1-mobile-rows {display:grid;' in styles
    assert '@media(max-width:360px)' in styles


def test_other_tables_do_not_force_mobile_viewport_to_shrink():
    css=read("frontend/src/style.css")
    page=read("frontend/index.html")
    assert 'name="viewport" content="width=device-width, initial-scale=1.0"' in page
    assert '.sport-landing .table-scroll > table' in css
    assert '.history-section .table-scroll' in css
    assert '.home-historics .table-scroll' in css
    assert 'overflow-x:auto;overscroll-behavior-inline:contain;' in css
    assert 'max-width:100%' in css
    assert '.sport-landing .sports-tabs button' in css
    assert '.argentina-conmebol-shortcuts' in css


def test_argentine_and_conmebol_links_and_editorial_priority():
    page=read("frontend/src/main.tsx")
    assert 'const LATENTE_PRIMARY_LEAGUES =' in page
    assert 'id:128,label:CURRENT_CLAUSURA_2026?' in page
    assert '🇦🇷 Torneo Clausura 2026' in page
    assert 'CURRENT_CLAUSURA_2026' in page
    for phrase in ('id:130,label:"🏆 Copa Argentina"',
                   'id:13,label:"🏆 Libertadores"',
                   'id:11,label:"🏆 Sudamericana"'):
        assert phrase in page
    assert 'LATENTE_PRIMARY_LEAGUES.filter(item=>leagues.some' in page
    assert 'leagues.find(l=>l.id===128)?.id || leagues[0]?.id || 128' in page
    assert 'const leagueOrder = (id: number)' in page
    assert 'leaguePriority(id)' in page
    assert 'a.name.localeCompare(b.name,"es")' in page
    assert "128: 1620" in page and "13: 1650" in page
    assert "130: 1560" in page and "11: 1580" in page
    # Keep global football, NBA and F1: this is navigation priority only.
    assert '...sports].sort(' in page
    assert 'href={link("/sport/f1")}' in page


def test_vertical_ads_are_prepared_not_served_to_unapproved_accounts():
    app=read("frontend/src/main.tsx")
    ads=read("frontend/src/ads.tsx")
    css=read("frontend/src/style.css")
    env=read(".env.example")
    assert 'placement="rail-left"' in app and 'placement="rail-right"' in app
    assert 'view !== "bet" && view !== "match"' in app
    assert 'VITE_ADSENSE_SLOT_RAIL_LEFT' in ads
    assert 'VITE_ADSENSE_SLOT_RAIL_RIGHT' in ads
    assert 'isRail ? "vertical"' in ads
    assert 'VITE_ADSENSE_ENABLED === "true"' in ads
    assert 'VITE_ADS_PRIVACY_READY === "true"' in ads
    assert 'const serveAds = enabled && /^\\d+$/.test(slotId)' in ads
    assert '.latente-ad--rail-left,.latente-ad--rail-right {display:none;}' in css
    assert '@media(min-width:1920px) and (min-height:680px)' in css
    assert 'display:none!important;' in css
    assert 'VITE_ADSENSE_ENABLED=false' in env
    assert 'VITE_ADS_PRIVACY_READY=false' in env


def test_unrelated_live_integrity_mechanisms_remain_in_place():
    page=read("frontend/src/main.tsx")
    assert 'if (m.stale) score -= 120' in page
    assert '"Cuota de consultas agotada"' in page
    assert "const warning =" in page
