"""Verify genuine indexable sports content without fabricated match facts."""
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "frontend/public"
SLUGS = (
    "futbol-argentino", "copa-argentina", "copa-libertadores",
    "champions-league", "premier-league", "liga-espanola",
    "serie-a-italiana", "bundesliga",
)


def test_sports_guides_have_unique_real_html_and_canonicals():
    urls = set()
    contents = set()
    for slug in SLUGS:
        path = PUBLIC / "guias" / f"{slug}.html"
        page = path.read_text(encoding="utf-8")
        url = f"https://latente.cfd/guias/{slug}.html"
        assert '<html lang="es">' in page
        assert f'<link rel="canonical" href="{url}"' in page
        assert 'name="description"' in page
        assert '<h1>' in page and page.count('<h2>') >= 4
        assert '<link rel="stylesheet" href="/editorial.css"' in page
        assert len(page) > 2500  # no generated one-sentence pages
        assert 'href="/#/league/' in page
        assert "Latente" in page and "Resultados y calendario" in page
        assert url not in urls
        urls.add(url)
        contents.add(page)
    assert len(contents) == len(SLUGS)


def test_sitemap_lists_only_real_html_pages_and_guides():
    path = PUBLIC / "sitemap.xml"
    tree = ElementTree.parse(path)
    urls = [node.text for node in tree.findall(
        ".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    assert len(urls) == len(set(urls))
    assert "https://latente.cfd/guias-de-futbol.html" in urls
    for slug in SLUGS:
        assert f"https://latente.cfd/guias/{slug}.html" in urls
    assert all("#/" not in url for url in urls)
    assert (PUBLIC / "guias-de-futbol.html").exists()


def test_navigation_links_to_editorial_hub():
    source = (ROOT / "frontend/src/main.tsx").read_text(encoding="utf-8")
    assert 'href="/guias-de-futbol.html"' in source


def test_adsense_verification_unchanged():
    html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    assert 'ca-pub-9760821039036895' in html
    assert html.count('client=ca-pub-9760821039036895') == 1
    assert "VITE_ADSENSE_ENABLED=false" in (ROOT / ".env.example").read_text(encoding="utf-8")
