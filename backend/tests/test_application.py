from datetime import timedelta, datetime, timezone
from dataclasses import replace
import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.main import app, date_window
from app.db import session_scope
from app.models import League, Fixture, Standing, Scorer, SyncJob, ApiUsage, utcnow
from app.ingest import upsert, save_fixtures, save_standings, save_scorers
from app import provider, worker


def league(s):
    upsert(
        s,
        League,
        dict(
            source="api",
            id=128,
            name="Liga de prueba",
            country="Argentina",
            kind="League",
            season=2026,
            seasons=[2026],
            coverage={},
            updated_at=utcnow(),
        ),
    )


def fixture(id=1, status="NS", when=None, goals=None):
    return {
        "fixture": {
            "id": id,
            "date": (when or utcnow()).isoformat(),
            "status": {"short": status, "elapsed": None},
            "venue": {},
        },
        "league": {"id": 128, "season": 2026},
        "teams": {
            "home": {"id": 1, "name": "Local"},
            "away": {"id": 2, "name": "Visitante"},
        },
        "goals": goals or {"home": None, "away": None},
        "score": {},
    }


def test_demo_api_flow_and_validation():
    with TestClient(app) as client:
        leagues = client.get("/api/leagues").json()
        assert leagues["meta"]["mode"] == "demo" and len(leagues["data"]) == 12
        assert client.get("/api/health").status_code == 200
        assert (
            client.get("/api/leagues/128/standings").json()["data"][0]["group"]
            == "Zona A"
        )
        assert len(client.get("/api/leagues/128/scorers").json()["data"]) == 8
        assert len(client.get("/api/teams?league_id=128").json()["data"]) == 8
        assert client.get("/api/teams/12800").json()["data"]["name"] == "River Plate"
        assert client.get("/api/teams/1").status_code == 404
        assert client.get("/api/fixtures?date=mal").status_code == 422
        assert (
            client.get("/api/fixtures?date=2026-10-08&tz=No/Existe").status_code == 422
        )
        assert client.get("/api/leagues/128/standings?season=1800").status_code == 422
        assert client.get("/api/health").headers["cache-control"] == "no-store"


def test_date_window_handles_dst_and_argentina():
    from datetime import date

    start, end = date_window(date(2026, 3, 8), "America/New_York")
    assert (end - start).total_seconds() == 23 * 3600
    start, end = date_window(date(2026, 10, 8), "America/Argentina/Buenos_Aires")
    assert start.hour == 3 and end.hour == 3


def test_fixture_upsert_null_scores_and_final_status(db):
    league(db)
    save_fixtures(db, [fixture()], [128])
    assert db.get(Fixture, ("api", 1)).home_goals is None
    save_fixtures(db, [fixture(status="2H", goals={"home": 1, "away": 0})], [128])
    save_fixtures(db, [fixture(status="FT", goals={"home": 2, "away": 0})], [128])
    db.expire_all()
    assert db.get(Fixture, ("api", 1)).status == "FT"
    assert db.get(Fixture, ("api", 1)).home_goals == 2
    assert db.scalar(select(func.count()).select_from(Fixture)) == 1
    assert db.get(Fixture, ("demo", 1)) is None


def standing_group(group, team_id):
    return {
        "rank": 1,
        "team": {"id": team_id, "name": f"Club {team_id}"},
        "points": 3,
        "goalsDiff": 1,
        "group": group,
        "form": "W",
        "all": {
            "played": 1,
            "win": 1,
            "draw": 0,
            "lose": 0,
            "goals": {"for": 1, "against": 0},
        },
    }


def test_all_standing_groups_and_empty_does_not_erase(db):
    league(db)
    rows = [
        {"league": {"standings": [[standing_group("A", 1)], [standing_group("B", 2)]]}}
    ]
    save_standings(db, rows, 128, 2026)
    save_standings(db, [], 128, 2026)
    assert db.scalar(select(func.count()).select_from(Standing)) == 2
    save_standings(
        db, [{"league": {"standings": [[standing_group("Final", 1)]]}}], 128, 2026
    )
    assert db.scalar(select(func.count()).select_from(Standing)) == 1
    assert db.scalar(select(Standing.group)) == "Final"


def test_scorers_ignore_other_competitions_and_keep_nulls(db):
    league(db)
    stats = {
        "team": {"id": 1, "name": "Club"},
        "league": {"id": 128, "season": 2026},
        "goals": {"total": 5, "assists": None},
        "games": {"appearences": 8},
        "penalty": {"scored": 1},
    }
    save_scorers(
        db,
        [
            {
                "player": {"id": 4, "name": "Jugador"},
                "statistics": [stats, {**stats, "league": {"id": 39, "season": 2026}}],
            }
        ],
        128,
        2026,
    )
    assert db.scalar(select(func.count()).select_from(Scorer)) == 1
    row = db.scalar(select(Scorer))
    assert row.goals == 5 and row.assists is None and row.appearances == 8


def test_catalog_rollover_and_coverage(db, monkeypatch):
    monkeypatch.setattr(worker, "settings", replace(worker.settings, league_ids=(128,)))
    rows = [
        {
            "league": {"id": 128, "name": "Liga", "type": "League"},
            "country": {"name": "Argentina"},
            "seasons": [
                {"year": 2025, "current": False, "coverage": {}},
                {
                    "year": 2026,
                    "current": True,
                    "coverage": {"standings": True, "top_scorers": False},
                },
            ],
        }
    ]
    worker.save_catalog(db, rows)
    db.flush()
    assert db.get(League, ("api", 128)).season == 2026
    assert db.get(SyncJob, "standings:128:2026")
    assert not db.get(SyncJob, "scorers:128:2026")
    rows[0]["seasons"][1]["current"] = False
    rows[0]["seasons"].append({"year": 2027, "current": True, "coverage": {}})
    worker.save_catalog(db, rows)
    db.flush()
    db.expire_all()
    assert not db.get(SyncJob, "fixtures:128:2026")
    assert db.get(SyncJob, "fixtures:128:2027")


def test_live_discovery_and_final_reconciliation_candidates(db):
    league(db)
    now = utcnow()
    rows = [
        fixture(1, "2H", now - timedelta(hours=2)),
        fixture(2, "NS", now),
        fixture(3, "FT", now - timedelta(hours=2)),
        fixture(4, "NS", now + timedelta(days=1)),
    ]
    save_fixtures(db, rows, [128])
    assert set(worker.live_ids(db, now)) == {1, 2}


def test_provider_rejects_errors_inside_http_200():
    with pytest.raises(provider.ProviderError):
        provider.validate_payload({"errors": {"plan": "not allowed"}, "response": []})
    with pytest.raises(provider.ProviderError):
        provider.validate_payload({"errors": [], "response": None})
    assert provider.validate_payload({"errors": [], "response": []}) == []


def test_daily_budget_persists(postgres, monkeypatch):
    monkeypatch.setattr(
        provider, "settings", replace(provider.settings, daily_budget=2, minimum_gap=1)
    )
    provider.reserve()
    with session_scope() as s:
        s.get(ApiUsage, utcnow().date()).last_request = utcnow() - timedelta(seconds=10)
    provider.reserve()
    with pytest.raises(provider.Deferred) as exc:
        provider.reserve()
    assert exc.value.until.date() > utcnow().date()
    with session_scope() as s:
        assert s.get(ApiUsage, utcnow().date()).requests == 2


def test_http_429_and_retry_after(postgres, monkeypatch):
    monkeypatch.setattr(
        provider, "settings", replace(provider.settings, api_key="test-placeholder")
    )
    transport = httpx.MockTransport(
        lambda req: httpx.Response(429, headers={"Retry-After": "120"}, json={})
    )
    client = provider.FootballClient(transport)
    with pytest.raises(provider.Deferred) as exc:
        client.get("/fixtures", {})
    assert (exc.value.until - utcnow()).total_seconds() > 115
    with session_scope() as s:
        assert s.get(ApiUsage, utcnow().date()).requests == 1
        assert s.get(ApiUsage, utcnow().date()).blocked_until is not None
    client.close()


def test_provider_zero_remaining_blocks_next_request(postgres):
    day = provider.reserve()
    provider.record_headers(day, {"x-ratelimit-requests-remaining": "0"}, 200)
    with pytest.raises(provider.Deferred):
        provider.reserve()


def test_fixture_api_respects_local_date_and_never_returns_demo(monkeypatch):
    from app import main

    monkeypatch.setattr(
        main, "settings", replace(main.settings, mode="api", league_ids=(128,))
    )
    with session_scope() as s:
        league(s)
        save_fixtures(
            s,
            [
                fixture(1, "FT", datetime(2026, 10, 8, 2, 30, tzinfo=timezone.utc)),
                fixture(2, "NS", datetime(2026, 10, 8, 3, 30, tzinfo=timezone.utc)),
            ],
            [128],
        )
    with TestClient(app) as client:
        response = client.get(
            "/api/fixtures?date=2026-10-07&tz=America/Argentina/Buenos_Aires"
        )
        assert [r["id"] for r in response.json()["data"]] == [1]
        assert response.json()["meta"]["mode"] == "api"


def test_pagination_and_authless_readonly_api():
    with TestClient(app) as client:
        from zoneinfo import ZoneInfo

        day = utcnow().astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date()
        first = client.get(f"/api/fixtures?date={day}&limit=2").json()
        second = client.get(f"/api/fixtures?date={day}&limit=2&offset=2").json()
        assert first["meta"]["total"] > 2
        assert {r["id"] for r in first["data"]}.isdisjoint(
            r["id"] for r in second["data"]
        )
        assert client.post("/api/fixtures").status_code == 405


def test_demo_rolls_over_at_argentina_midnight(db, monkeypatch):
    from app import demo
    from zoneinfo import ZoneInfo

    monkeypatch.setattr(
        demo, "utcnow", lambda: datetime(2026, 10, 8, 2, 50, tzinfo=timezone.utc)
    )
    demo.seed_demo(db)
    before = db.get(Fixture, ("demo", 12810)).kickoff
    monkeypatch.setattr(
        demo, "utcnow", lambda: datetime(2026, 10, 8, 3, 10, tzinfo=timezone.utc)
    )
    demo.seed_demo(db)
    db.expire_all()
    after = db.get(Fixture, ("demo", 12810)).kickoff
    assert (after - before).total_seconds() == 86400
