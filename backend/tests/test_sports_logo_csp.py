"""Provider team logos are only useful when Railway/Cloudflare CSP permits them."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ESPN_HOSTS=("https://a.espncdn.com","https://a1.espncdn.com",
            "https://a2.espncdn.com","https://cdn.espn.com")
API_HOST="https://media.api-sports.io"

def test_real_team_logo_cdns_allowed_in_all_frontend_hosting_configs():
    for path in ("deploy/nginx/nginx.conf", "deploy/railway/nginx.conf.template",
                 "frontend/public/_headers"):
        source=(ROOT/path).read_text(encoding="utf-8")
        policy=next(s for s in source.splitlines() if "img-src 'self'" in s)
        for host in (*ESPN_HOSTS,API_HOST):
            assert host in policy, (path,host)
        assert "object-src 'none'" in source

def test_real_badges_or_explicit_placeholder_in_nonfootball_views():
    code=(ROOT/"frontend/src/team-mark.tsx").read_text(encoding="utf-8")
    assert 'allowed.has(parsed.hostname)' in code
    assert 'team-mark-placeholder' in code
    assert 'onError={()=>setBad(true)}' in code
