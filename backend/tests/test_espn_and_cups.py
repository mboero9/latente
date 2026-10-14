"""ESPN sport normalization and knockout bracket regression tests."""
from app import espn_scores
from app import public_sports
from app.brackets import bracket_rows, classify_round
from app import main
from fastapi.testclient import TestClient

FIXTURE = {
    "events": [{
        "id": "390", "date": "2026-10-14T17:00:00Z",
        "competitions": [{
            "competitors": [
                {"homeAway": "home", "team": {"displayName": "Argentina"}, "score": "29"},
                {"homeAway": "away", "team": {"displayName": "South Africa"}, "score": "20"}
            ],
            "status": {"type": {"completed": True, "state": "post", "description": "Final"}}
        }]
    }]
}

def test_espn_scoreboard_uses_actual_final_scores(monkeypatch):
    public_sports._CACHE.clear()
    seen=[]
    def fake(url, params=None):
        seen.append((url, params))
        return FIXTURE
    monkeypatch.setattr(espn_scores, "_get", fake)
    first=espn_scores.us_scoreboard("nba", "2026-10-14")
    second=espn_scores.us_scoreboard("nba", "2026-10-14")
    assert first == second
    assert len(seen) == 1
    assert first["games"][0]["home_score"] == 29
    assert first["games"][0]["away"] == "South Africa"

def test_espn_rugby_result_and_partial_stats(monkeypatch):
    public_sports._CACHE.clear()
    def fake(url, params=None):
        if "scoreboard" in url:
            return FIXTURE
        return {"children": []}
    monkeypatch.setattr(espn_scores, "_get", fake)
    info=espn_scores.rugby_feed("championship", 2026)
    assert info["games"][0]["home"] == "Argentina"
    assert info["statistics"][0]["team"] == "Argentina"
    assert info["statistics"][0]["g"] == 1
    assert info["official"] == []
    assert info["league_name"].startswith("Rugby Championship")

def test_rugby_rejects_unknown_competitions(monkeypatch):
    with TestClient(main.app) as client:
        assert client.get("/api/rugby/unknown").status_code == 422
        assert client.get("/api/scoreboard/afl").status_code == 422
        r=client.get("/api/rugby/catalog")
        assert r.status_code == 200
        assert any(c["slug"] == "urba" for c in r.json()["data"])

def test_cup_bracket_does_not_link_non_adjacent_rounds():
    def m(i, label, home, away, status="FT"):
        return {"id": i, "round":label,"home":{"id":home},
                "away":{"id":away},"home_goals":2,"away_goals":0,
                "status":status,"kickoff":f"2026-10-14T{i:02d}:00:00Z"}
    stages=bracket_rows([
        m(1,"Round of 64",10,11),m(2,"Round of 16",10,12),
    ])
    assert len(stages)==2
    assert "next_match_id" not in stages[0]["matches"][0]
    assert classify_round("Round of 128")[1] == -1
