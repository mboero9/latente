"""Rugby: full-season ESPN coverage, honest official tables, and complete UI lists."""
from datetime import date
from pathlib import Path

from app import espn_scores, public_sports
from app.rugby_api import espn_standings, ESPN_PRIORITY, public_catalog
from app.rugby_clubs import edition_clubs, source_url

ROOT=Path(__file__).resolve().parents[2]


def test_espn_month_windows_are_bounded_and_cover_entire_calendar():
    windows=list(espn_scores.season_windows(2026))
    assert windows[0][0]==date(2026,1,1)
    assert windows[-1][-1]==date(2026,12,31)
    assert len(windows)>=12
    assert all((b-a).days<30 for a,b in windows)
    assert all(windows[i][1].toordinal()+1==windows[i+1][0].toordinal()
               for i in range(len(windows)-1))


def test_espn_full_rugby_season_imports_old_and_future_matches(monkeypatch):
    public_sports._CACHE.clear()
    seen=[]
    def get(url,params=None):
        if "scoreboard" not in url:
            return {"children":[]}
        seen.append((url,dict(params or {})))
        dates=(params or {}).get("dates") or ""
        events=[]
        for id_,stamp in [("spring","2026-03-21T17:00:00Z"),
                          ("autumn","2026-10-17T18:00:00Z"),
                          ("future","2026-11-14T18:00:00Z")]:
            if dates and not dates[:8]<=stamp[:4]+stamp[5:7]+stamp[8:10]<=dates[-8:]:
                continue
            finished=id_!="future"
            events.append({
                "id":id_,"date":stamp,
                "competitions":[{"competitors":[
                    {"homeAway":"home","team":{"displayName":"Club A"},"score":"22" if finished else None},
                    {"homeAway":"away","team":{"displayName":"Club B"},"score":"11" if finished else None}],
                    "status":{"type":{"completed":finished,"description":
                        "Final" if finished else "Programado"}}}]
            })
        return {"events":events}
    monkeypatch.setattr(espn_scores,"_get",get)
    data=espn_scores.rugby_feed("urba",2026)
    assert {m["id"] for m in data["games"]}=={"spring","autumn","future"}
    assert len([m for m in data["games"] if m["completed"]])==2
    assert [m for m in data["games"] if m["id"]=="future"][0]["home_score"] is None
    assert len(seen)>=12
    assert all((p.get("dates") is None or
                (date.fromisoformat(p["dates"][:4]+"-"+p["dates"][4:6]+"-"+p["dates"][6:8])<=
                 date.fromisoformat(p["dates"][9:13]+"-"+p["dates"][13:15]+"-"+p["dates"][15:17])))
               for _,p in seen)


def test_full_calendar_backfill_is_not_blocked_by_old_short_window_diagnostics():
    from pathlib import Path
    src=(Path(__file__).resolve().parents[2]/"backend/app/rugby_api.py").read_text()
    assert src.count('"espn_diagnostic_v4"') == 3
    assert '"espn_diagnostic_v3"' not in src
    assert "if diag and _fresh(games, ESPN_REFRESH)" in src


def test_extra_rugby_espn_competition_ids_are_verified_and_whitelisted():
    assert espn_scores.RUGBY_LEAGUES["mlr"][1]=="289262"
    assert espn_scores.RUGBY_LEAGUES["challenge-cup"][1]=="272073"
    assert "mlr" in ESPN_PRIORITY and "challenge-cup" in ESPN_PRIORITY
    assert set(espn_scores.RUGBY_LEAGUES).issubset(set(ESPN_PRIORITY))


def test_espn_rankings_only_publish_with_real_rank_and_points():
    data=espn_standings([
        {"name":"Valid","rank":2,"points":16,"wins":4},
        {"name":"NoPoints","rank":1,"wins":9},
        {"name":"NoRank","points":27,"wins":8},
    ])
    assert len(data)==1
    assert data[0]["team"]=="Valid"
    assert data[0]["rank"]==2
    assert data[0]["points"]==16
    assert data[0]["won"]==4


def test_super_rugby_americas_is_source_backed_but_not_fabricated(monkeypatch):
    import app.rugby_api as rugby_api
    monkeypatch.setattr(rugby_api,"_snapshot",lambda *args:None)
    comps={x["slug"]:x for x in rugby_api.public_catalog()}
    row=comps["super-rugby-americas"]
    assert 2026 in row["seasons"]
    assert row["official_url"].startswith("https://www.superrugbyamericas.com/")
    assert len(edition_clubs("super-rugby-americas",2026))==8
    assert edition_clubs("super-rugby-americas",2025)==[]


def test_rugby_ui_can_load_all_matches_beyond_old_70_limit():
    view=(ROOT/"frontend/src/rugby-hub.tsx").read_text(encoding="utf-8")
    for needle in ('setShown(n=>n+70)', 'Todos ({allGames.length})',
                   'Buscar club o encuentro', 'games.slice(0,shown)',
                   'Mostrar' if False else 'Ver más partidos'):
        assert needle in view
    assert 'games.slice(0,70)' not in view
    table=(ROOT/"frontend/src/rugby-home-tables.tsx").read_text(encoding="utf-8")
    assert "URBA Top 14" in table
    assert "URBA Top 12" not in table
    featured=(ROOT/"frontend/src/rugby-league-tables.tsx").read_text(encoding="utf-8")
    assert '"super-rugby-americas"' in featured and '"interior-a"' in featured
