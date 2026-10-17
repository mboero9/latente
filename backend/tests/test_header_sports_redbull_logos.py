"""Header order only, and both independent Red Bull F1 team badges."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def test_header_reorders_without_changing_other_sports_catalog():
    main=(ROOT/"frontend/src/main.tsx").read_text(encoding="utf-8")
    sports=(ROOT/"frontend/src/other-sports.tsx").read_text(encoding="utf-8")
    opening=main.split('<NavRail activePath={route}>',1)[1].split('</NavRail>',1)[0]
    prefix=[
        '["/", "Partidos"]', '["/leagues", "Ligas"]',
        '"Posiciones"', '"Goleadores"', '["/league/253",',
        '["/tv", "📺 Dónde ver"]', '["/bet", "18+ Dónde apostar"]',
        '...[...sports].sort(',
    ]
    positions=[opening.index(marker) for marker in prefix]
    assert positions==sorted(positions)
    priority=main.split("const SPORT_NAV_ORDER: string[] = [",1)[1].split("];",1)[0]
    slugs=[word for word in priority.replace('"',"").replace("\n","").split(",") if word.strip()]
    slugs=[s.strip() for s in slugs]
    assert slugs[:2]==["nba","f1"]
    assert sorted(slugs)==sorted(["nba","f1","cricket","nfl","rugby","mlb",
                                  "nhl","wnba","basketball","volleyball","handball"])
    assert 'sports.map(' not in opening
    assert 'export const sports = [' in sports
    # Do not move the existing desktop/mobile F1 home cards.
    assert 'class="f1-home-feature panel"' in main
    assert 'class="f1-home-mobile-link"' in main


def test_redbull_racing_and_racing_bulls_logos_are_distinct():
    media=(ROOT/"frontend/src/f1-media.tsx").read_text(encoding="utf-8")
    redbull="https://upload.wikimedia.org/wikipedia/en/f/fa/Red_Bull_Racing_Logo_2026.svg"
    racingbulls="https://upload.wikimedia.org/wikipedia/en/2/2b/VCARB_F1_logo.svg"
    assert redbull in media
    assert racingbulls in media
    # Source names used in 2026 Jolpica can vary.
    for alias in ('"red bull"', '"red bull racing"', '"rb f1 team"',
                  '"racing bulls"', '"visa cash app racing bulls"'):
        assert alias in media
    assert 'f1-redbull-logo' in media
    assert '"racing bulls":"#4681d7"' in media
    standings=(ROOT/"frontend/src/reference-sports.tsx").read_text(encoding="utf-8")
    assert '<F1TeamLogo name={d.team}/>' in standings
    assert '<F1TeamLogo name={t.name}/>' in standings
    assert '<F1TeamLogo name={p.team}/>' in standings
    css=(ROOT/"frontend/src/style.css").read_text(encoding="utf-8")
    assert '.f1-identity .f1-redbull-logo' in css


def test_redbull_source_images_are_permitted_by_all_csp_layers():
    for path in ("frontend/public/_headers","deploy/railway/nginx.conf.template",
                 "deploy/nginx/nginx.conf"):
        content=(ROOT/path).read_text(encoding="utf-8")
        assert "https://upload.wikimedia.org" in content
