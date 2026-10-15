"""ESPN Rugby rejects full-year date ranges: use short, validated windows."""
from datetime import datetime, timezone
import httpx
from app import espn_scores


def test_top14_bounded_windows_fall_back_to_legacy_rugby_league(monkeypatch):
    calls=[]
    monkeypatch.setattr(espn_scores, "_cached", lambda key, ttl, producer: producer())
    now=datetime.now(timezone.utc)
    def get(url, params=None):
        calls.append((url, params))
        if "/scoreboard" in url:
            assert params and params.get("dates")
            a, b=params["dates"].split("-")
            assert (datetime.strptime(b, "%Y%m%d") - datetime.strptime(a, "%Y%m%d")).days <= 46
            if "/rugby/" in url:
                raise httpx.HTTPStatusError("unsupported range",request=httpx.Request("GET",url),response=httpx.Response(400))
            assert "/rugby-league/" in url
            return {"events":[{
                "id": "game-1", "date": now.isoformat(),
                "status": {"type": {"completed": False, "description": "Scheduled", "state": "pre"}},
                "competitions": [{"competitors": [
                    {"homeAway":"home", "team":{"displayName":"Toulouse",
                           "logo":"https://a.espncdn.com/i/teamlogos/rugby/teams/500/123.png"}},
                    {"homeAway":"away", "team":{"displayName":"Bayonne",
                           "logo":"https://a.espncdn.com/i/teamlogos/rugby/teams/500/456.png"}}
                ]}]
            }]}
        if "/standings" in url:
            return {"standings":{"entries":[{
                "team":{"id":"123","displayName":"Toulouse",
                        "logo":"https://a.espncdn.com/i/teamlogos/rugby/teams/500/123.png"},
                "stats":[{"name":"points","value":32},{"name":"playoffSeed","value":1}]
            }]}}
        raise AssertionError(url)
    monkeypatch.setattr(espn_scores,"_get",get)
    result=espn_scores.rugby_feed("top-14", now.year)
    assert result["games"]
    assert result["games"][0]["home"]=="Toulouse"
    assert result["games"][0]["home_logo"].startswith("https://a.espncdn.com/")
    assert result["official"][0]["points"]==32
    assert any("/rugby-league/" in url for url,_ in calls)
    assert not any(f"{now.year}0101-{now.year}1231" in str(params) for _,params in calls)
