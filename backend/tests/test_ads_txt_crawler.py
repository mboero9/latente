"""AdSense seller authorization must be a real root plain-text file."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECORD = "google.com, pub-9760821039036895, DIRECT, f08c47fec0942fa0"


def test_ads_txt_is_single_correct_direct_record():
    content = (ROOT / "frontend/public/ads.txt").read_text(encoding="utf-8")
    assert content.strip() == RECORD
    assert content.endswith("\n")
    assert "ca-pub-" not in content


def test_crawlers_allowed_to_fetch_ads_txt():
    robots = (ROOT / "frontend/public/robots.txt").read_text(encoding="utf-8")
    assert "User-agent: *" in robots
    assert "Allow: /" in robots
    assert "Disallow: /ads.txt" not in robots


def test_both_nginx_variants_serve_real_ads_txt_without_spa_fallback():
    for name in ("deploy/railway/nginx.conf.template", "deploy/nginx/nginx.conf"):
        config = (ROOT / name).read_text(encoding="utf-8")
        assert config.count("location = /ads.txt {") == 1
        route = config.split("location = /ads.txt {", 1)[1].split("}", 1)[0]
        assert "default_type text/plain;" in route
        assert "try_files /ads.txt =404;" in route
        assert "index.html" not in route
        assert "location / { try_files $uri $uri/ /index.html; }" in config or "try_files $uri $uri/ /index.html;" in config


def test_adsense_ownership_marker_consistent_with_ads_txt():
    head = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    assert '<meta name="google-adsense-account" content="ca-pub-9760821039036895"' in head
    assert "client=ca-pub-9760821039036895" in head
