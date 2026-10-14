"""SEO essentials must remain indexable without fabricating crawlable hash URLs."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_index_head_contains_search_and_social_metadata():
    html=(ROOT/"frontend/index.html").read_text(encoding="utf-8")
    for fragment in ('name="description"','name="keywords"','name="robots"',
      'property="og:title"','property="og:url"','property="og:image"',
      'name="twitter:card"','type="application/ld+json"',
      'rel="canonical" href="https://latente.cfd/"'):
        assert fragment in html
    assert html.count('<title>')==1
    assert html.count('name="description"')==1
    assert html.count('GTM-PGJRQPZL')==2

def test_dynamic_titles_but_no_fake_crawlable_urls():
    main=(ROOT/"frontend/src/main.tsx").read_text(encoding="utf-8")
    robots=(ROOT/"frontend/public/robots.txt").read_text(encoding="utf-8")
    sitemap=(ROOT/"frontend/public/sitemap.xml").read_text(encoding="utf-8")
    assert "Resultados Deportivos en Vivo y Marcadores en Directo" in main
    assert 'document.querySelector<HTMLMetaElement>' in main
    assert "Hash routes are not independent crawlable URLs" in main
    assert 'Sitemap: https://latente.cfd/sitemap.xml' in robots
    assert 'https://latente.cfd/' in sitemap
    assert "/#/league/" not in sitemap
