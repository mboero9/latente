"""English editorial pages must not silently fall back to Spanish."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_all_editorial_pages_have_complete_english_alternates():
    for slug in ("sobre-latente", "metodologia", "publicidad"):
        spanish = (ROOT / f"frontend/public/{slug}.html").read_text()
        english = (ROOT / f"frontend/public/en/{slug}.html").read_text()
        assert 'lang="es"' in spanish
        assert 'lang="en"' in english
        assert f"/en/{slug}.html" in spanish
        assert f'content="https://latente.cfd/en/{slug}.html"' not in english
        assert f'href="https://latente.cfd/en/{slug}.html"' in english
        assert f'href="/{slug}.html"' in english
        assert len(english) > 1400
    sitemap = (ROOT / "frontend/public/sitemap.xml").read_text()
    for slug in ("sobre-latente", "metodologia", "publicidad"):
        assert f"https://latente.cfd/en/{slug}.html" in sitemap


def test_editorial_links_follow_language_choice():
    home = (ROOT / "frontend/src/main.tsx").read_text()
    assert 'language === "en" ? "/en/sobre-latente.html"' in home
    assert 'language === "en" ? "/en/metodologia.html"' in home
    assert 'language === "en" ? "/en/publicidad.html"' in home
    assert 'view !== "bet" && view !== "match"' in home
