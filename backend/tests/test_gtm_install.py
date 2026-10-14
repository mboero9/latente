"""Validate GTM install and CSP integrity at build time."""
import base64
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GTM_ID = "GTM-PGJRQPZL"


def test_gtm_snippets_and_csp_hash():
    page = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    match = re.search(r"<script>(\(function\(w,d,s,l,i\).*?GTM-PGJRQPZL'\);)</script>", page, re.DOTALL)
    assert match, "GTM bootstrap script missing"
    digest = base64.b64encode(hashlib.sha256(match.group(1).encode("utf-8")).digest()).decode()
    csp_hash = f"'sha256-{digest}'"
    assert page.index("<!-- Google Tag Manager -->") > page.index("<head>")
    assert page.index("<!-- Google Tag Manager -->") < page.index('<meta charset')
    assert page.index("<!-- Google Tag Manager (noscript) -->") > page.index("<body>")
    assert page.count("GTM-PGJRQPZL") == 2
    for file in ("deploy/railway/nginx.conf.template", "deploy/nginx/nginx.conf", "frontend/public/_headers"):
        config = (ROOT / file).read_text(encoding="utf-8")
        assert csp_hash in config, f"GTM script blocked in {file}"
        assert "frame-src https://www.googletagmanager.com" in config, f"noscript iframe blocked in {file}"


def test_google_measurement_kept_outside_gtm_until_migration():
    page = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    direct = (ROOT / "frontend/public/google-tag.js").read_text(encoding="utf-8")
    assert page.count("/google-tag.js") == 1
    assert "gtag('config', 'G-WGKG57N8FD')" in direct
    assert "gtag('config', 'AW-18447823536')" in direct
