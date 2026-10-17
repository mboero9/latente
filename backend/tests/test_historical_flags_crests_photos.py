"""Regressions for country flags, historical logos and verified portraits."""
from pathlib import Path
from types import SimpleNamespace

from app.historic_crests import resolve_curated_clubs, normalized

ROOT = Path(__file__).resolve().parents[2]


def test_club_ids_use_exact_name_and_country_not_nearby_names():
    teams = [
        SimpleNamespace(id=541, name="Real Madrid", country="Spain"),
        SimpleNamespace(id=529, name="Barcelona", country="Spain"),
        SimpleNamespace(id=1001, name="Independiente", country="Ecuador"),
        SimpleNamespace(id=1002, name="Independiente", country="Argentina"),
        SimpleNamespace(id=2001, name="Al Ahly SC", country="Egypt"),
        SimpleNamespace(id=2002, name="Al Ahly", country="Sudan"),
    ]
    mapping = resolve_curated_clubs(teams)
    assert mapping["Real Madrid"] == 541
    assert mapping["FC Barcelona"] == 529
    assert mapping["Independiente"] == 1002
    assert mapping["Al Ahly"] == 2001
    assert normalized("España") == "espana"


def test_flags_are_actual_country_images_not_emoji_text():
    flags = (ROOT / "frontend/src/historic-flags.tsx").read_text()
    for name, code in (
        ("Argentina", "ar"), ("Portugal", "pt"), ("Egipto", "eg"),
        ("Brasil", "br"), ("Italia", "it"), ("Inglaterra", "gb-eng"),
        ("Irlanda del Norte", "gb-nir"), ("España", "es"),
    ):
        assert f'"{name}": "{code}"' in flags
    assert "https://flagcdn.com/" in flags
    assert 'onError={() => setFailed(true)}' in flags
    assert 'country.split("/")' in flags


def test_players_clubs_and_nations_all_use_real_media_components():
    scorers = (ROOT / "frontend/src/world-scorers.tsx").read_text()
    honours = (ROOT / "frontend/src/historical-honours.tsx").read_text()
    teammark = (ROOT / "frontend/src/team-mark.tsx").read_text()
    portraits = (ROOT / "frontend/src/historic-media.tsx").read_text()
    assert "playerId: 154" in scorers
    assert "playerId: 874" in scorers
    assert 'HistoricFlag country={p.country}' in scorers
    assert 'HistoricPlayerPortrait name={p.name}' in scorers
    assert "HistoricClubCrest name={p.club.split" in scorers
    assert "HistoricClubCrest name={club.name}" in honours
    assert "HistoricFlag country={nation.name}" in honours
    assert "HistoricFlag country={club.country}" in honours
    assert 'football: "football"' in teammark
    assert "playerId" in portraits and "onError={()=>setError(true)}" in portraits


def test_csp_allows_flag_images_in_both_nginx_and_cloudflare():
    for path in ("deploy/nginx/nginx.conf", "deploy/railway/nginx.conf.template",
                 "frontend/public/_headers"):
        text = (ROOT / path).read_text()
        assert "img-src 'self' data: https://flagcdn.com" in text
        assert "https://media.api-sports.io" in text


def test_historic_crest_endpoint_is_db_only():
    main = (ROOT / "backend/app/main.py").read_text()
    body = main.split('@app.get("/api/history/club-crests")')[1].split("@app.get(")[0]
    assert "Team.source == settings.mode" in body
    assert "resolve_curated_clubs(rows)" in body
    assert "select(Team)" in body
    assert "requests." not in body
    assert "httpx." not in body
