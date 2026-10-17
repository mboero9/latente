"""Compact, provider-verified live football incidents for the matchday.

Only Goal / Card rows already imported in PostgreSQL are exposed.
Missed/disallowed goals and unsupported incident types are not displayed.
This module never calls API-Football (no provider request per visitor).
"""
from __future__ import annotations

def compact_live_incidents(events: list | None) -> list[dict]:
    result: list[dict] = []
    for raw in events or []:
        if not isinstance(raw, dict):
            continue
        kind = str(raw.get("type") or "").strip().casefold()
        detail = str(raw.get("detail") or "").strip().casefold()
        if kind == "goal":
            if any(token in detail for token in (
                "missed", "disallow", "cancel", "annul", "no goal",
            )):
                continue
        elif kind == "card":
            if not any(token in detail for token in ("yellow", "red")):
                continue
        else:
            continue
        team_id = raw.get("team_id")
        if type(team_id) is not int:
            continue
        minute = raw.get("minute")
        extra = raw.get("extra")
        result.append({
            "kind": "goal" if kind == "goal" else (
                "red" if "red" in detail or "second yellow" in detail else "yellow"
            ),
            "minute": minute if type(minute) is int and 0 <= minute <= 150 else None,
            "extra": extra if type(extra) is int and 0 < extra <= 60 else None,
            "team_id": team_id,
            "player": str(raw.get("player") or "")[:120],
            "own_goal": kind == "goal" and "own goal" in detail,
            "penalty": kind == "goal" and "penalty" in detail,
        })
    return sorted(result, key=lambda e: (
        e["minute"] if e["minute"] is not None else 999,
        e["extra"] or 0,
    ))[:50]
