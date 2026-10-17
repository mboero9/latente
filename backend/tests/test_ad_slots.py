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


def test_verified_publisher_and_disabled_ad_placements():
    example = (ROOT / ".env.example").read_text()
    home = (ROOT / "frontend/index.html").read_text()
    ads = (ROOT / "frontend/src/ads.tsx").read_text()
    seller = (ROOT / "frontend/public/ads.txt").read_text()
    publisher = "9760821039036895"

    assert "VITE_ADSENSE_ENABLED=false" in example
    assert "VITE_ADS_PRIVACY_READY=false" in example
    assert f'content="ca-pub-{publisher}"' in home
    assert home.count(f"client=ca-pub-{publisher}") == 1
    assert home.index(f"client=ca-pub-{publisher}") < home.index("</head>")
    assert seller == f"google.com, pub-{publisher}, DIRECT, f08c47fec0942fa0\\n"
    assert 'if (verifiedLoader) return Promise.resolve();' in ads

    for name in ("deploy/railway/nginx.conf.template", "deploy/nginx/nginx.conf", "frontend/public/_headers"):
        csp = (ROOT / name).read_text()
        assert "script-src" in csp
        assert "https://pagead2.googlesyndication.com; style-src" in csp
