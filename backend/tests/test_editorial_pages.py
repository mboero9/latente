"""Public editorial pages help provide transparency and crawlable pages."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

def test_editorial_pages_and_sitemap():
    public = ROOT / "frontend/public"
    sitemap = (public / "sitemap.xml").read_text(encoding="utf-8")
    app = (ROOT / "frontend/src/main.tsx").read_text(encoding="utf-8")
    for name in ("sobre-latente", "metodologia"):
        p = public / f"{name}.html"
        txt = p.read_text(encoding="utf-8")
        assert "<h1>" in txt and '<html lang="es">' in txt
        assert f"https://latente.cfd/{name}.html" in sitemap
        assert f"/{name}.html" in app
        assert f'https://latente.cfd/{name}.html' in txt
        assert '<link rel="stylesheet" href="/editorial.css"/>' in txt

def test_privacy_policy_not_falsely_claimed():
    assert not (ROOT / "frontend/public/privacidad.html").exists()
    assert "VITE_ADSENSE_ENABLED=false" in (ROOT / ".env.example").read_text()
