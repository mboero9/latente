"""Ad placements remain opt-in and do not spoof a publisher identity."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_three_advertising_positions_are_present():
    app = (ROOT / "frontend/src/main.tsx").read_text()
    ads = (ROOT / "frontend/src/ads.tsx").read_text()
    styles = (ROOT / "frontend/src/style.css").read_text()

    assert 'placement="top"' in app
    assert 'placement="side"' in app
    assert 'placement="bottom"' in app
    assert 'view !== "bet"' in app
    assert 'Anuncios' in ads
    assert 'latente-ad--side' in styles
    assert 'VITE_ADSENSE_ENABLED === "true"' in ads
    assert 'VITE_ADS_PRIVACY_READY === "true"' in ads


def test_no_fake_adsense_identity_or_ads_txt():
    example = (ROOT / ".env.example").read_text()
    assert "VITE_ADSENSE_ENABLED=false" in example
    assert "VITE_ADS_PRIVACY_READY=false" in example
    assert not (ROOT / "frontend/public/ads.txt").exists()
