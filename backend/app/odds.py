"""Mercado 1X2 verificado. En vivo API-Football no identifica casas individuales.

No atribuir precios a Betano u otro operador sin que el feed lo confirme.
La probabilidad implícita 1/cuota contiene margen; normalizada no pronostica.
"""
from datetime import datetime, timezone
from .models import FixtureOdds, utcnow
from .ingest import upsert


def price(raw):
    try:
        n = float(raw)
    except (ValueError, TypeError):
        return None
    if not (1.001 <= n <= 1000):
        return None
    return round(n, 4)


def outcomes(values):
    found = {}
    for item in values or []:
        if item.get("suspended") is True:
            continue
        tag = str(item.get("value", "")).strip().lower()
        target = {"home": "home", "1": "home", "draw": "draw",
                  "x": "draw", "away": "away", "2": "away"}.get(tag)
        if target is None:
            continue
        odd = price(item.get("odd"))
        if odd is not None:
            found[target] = odd
    if set(found) != {"home", "draw", "away"}:
        return None
    weight = sum(1 / odd for odd in found.values())
    return {
        "prices": found,
        "implied": {key: round(100 / val, 1) for key, val in found.items()},
        "normalized": {key: round(100 / val / weight, 1) for key, val in found.items()},
    }


def prematch(rows):
    out = []
    for fixture in rows[:1]:
        for bookmaker in (fixture.get("bookmakers") or [])[:60]:
            name = str(bookmaker.get("name") or "").strip()
            if not name:
                continue
            for bet in bookmaker.get("bets") or []:
                if str(bet.get("name") or "").lower() not in {"match winner", "1x2", "full time result"}:
                    continue
                obj = outcomes(bet.get("values"))
                if obj:
                    out.append({"bookmaker": name[:90], "source": "prematch",
                                "captured_at": fixture.get("update"), **obj})
                break
    return out[:30]


def inplay(rows):
    out = []
    for fixture in rows[:1]:
        state = fixture.get("status") or {}
        if state.get("blocked") or state.get("stopped") or state.get("finished"):
            continue
        for bet in fixture.get("odds") or []:
            name = str(bet.get("name") or "").lower()
            if name not in {"match winner", "1x2", "full time result"}:
                continue
            obj = outcomes(bet.get("values"))
            if obj:
                out.append({"bookmaker": None, "source": "live",
                            "captured_at": fixture.get("update"), **obj})
            break
    return out


def persist(s, fixture_id, kind, quotes):
    existing = s.get(FixtureOdds, ("api", fixture_id, kind))
    if not quotes and existing and existing.quotations:
        return False
    upsert(s, FixtureOdds, {
        "source": "api", "fixture_id": fixture_id, "market": kind,
        "quotations": quotes, "updated_at": utcnow(),
    })
    return True
