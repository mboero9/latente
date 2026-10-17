"""Gambling marks must not masquerade as sponsors or evade locale checks."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT/path).read_text(encoding="utf-8")


def test_directory_has_resilient_real_site_icons():
    src=read("frontend/src/bookmaker-brands.tsx")
    for name in ("Betsson", "Betano", "bplay", "bet365", "BetWarrior",
                 "Sportsbet", "Stake"):
        assert f'label:"{name}"' in src
    assert "google.com/s2/favicons" in src
    assert "onError={()=>setFailed(true)}" in src
    assert "bookmaker-brand-initials" in src
    assert "compact?:boolean" in src


def test_age_confirmation_necessary_to_see_operator_cards_or_links():
    view=read("frontend/src/betting-guide.tsx")
    assert "const [adult,setAdult]=useState(false)" in view
    assert "saveBettingAudience" in view
    assert 'adult &&' in view
    assert "filtered.length && adult" in view
    assert "bookmaker-directory-grid" in view
    assert "rel=\"noopener noreferrer nofollow sponsored\"" in view
    assert "Sin cuotas" not in view  # no invented odds on brand directory
    assert "country===\"BR\"" in view
    assert 'name:"Sportsbet"' in view and 'name:"Stake"' in view
    assert 'province==="CABA"?AR_CABA:province==="PBA"?AR_PBA' in view
    assert "Ninguna casa mostrada patrocina" in view


def test_live_brand_strip_requires_opt_in_geo_and_has_no_operator_urls():
    src=read("frontend/src/live-bookmakers.tsx")
    assert 'geoCountry !== "AR"' in src
    assert "!audience?.adult" in src
    assert 'audience.province==="CABA"?CABA:PBA' in src
    assert "No patrocinado" in src
    assert "Sin cuotas atribuidas" in src
    assert 'href="#/bet"' in src
    assert "https://" not in src
    assert "price" not in src.lower()
    main=read("frontend/src/main.tsx")
    assert "const {result:visitor} = useApi" in main
    assert '"latente:betting-audience"' in main
    assert "readBettingAudience()" in main
    assert "active && <LiveBookmakers" in main
    assert "geoCountry={visitor?.data?.country}" in main
    assert main.count("geoCountry={visitor?.data?.country}")==2
    audience=read("frontend/src/betting-audience.ts")
    assert "sessionStorage" in audience
    assert 'country: "AR"' in audience
    assert 'adult: true' in audience
    assert "localStorage" not in audience


def test_live_strip_is_compact_and_not_promotional_by_default():
    css=read("frontend/src/style.css")
    assert ".live-bookmakers" in css
    assert ".bookmaker-directory-card" in css
    assert ".bookmaker-brand-compact" in css
    assert "font-size:.7rem" in css
    view=read("frontend/src/betting-guide.tsx")
    assert "Confirmo que soy mayor de 18 años." in view
    assert "No se muestran ofertas ni enlaces comerciales antes" in view
