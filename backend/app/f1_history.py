"""Season-scoped visual profiles from OpenF1 and historical champions.

No calls from browsers to third-party APIs; cached requests are made by the
backend. OpenF1 media are optional and must not be displayed if unverified.
"""
import re
import unicodedata
from datetime import datetime, timezone
import httpx

from .public_sports import F1, _cached, _get

OPENF1_DRIVERS = "https://api.openf1.org/v1/drivers"


def norm(value):
    plain = "".join(c for c in unicodedata.normalize("NFKD", str(value or "").casefold())
                    if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", plain).strip()


def permitted_photo(url):
    if not isinstance(url, str):
        return None
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return url if parsed.scheme == "https" and parsed.hostname in (
        "media.formula1.com", "www.formula1.com"
    ) else None


def enrich_driver_rows(rows, openf1):
    """Match unique last names from this season, never a partial substring."""
    by_surname = {}
    for raw in openf1 or []:
        if not isinstance(raw, dict):
            continue
        surname = norm(raw.get("last_name"))
        if not surname:
            continue
        by_surname.setdefault(surname, []).append(raw)
    out = []
    for row in rows:
        value = dict(row)
        surname = norm(value.get("family_name") or value.get("name", "").split(" ")[-1])
        matches = by_surname.get(surname) or []
        # A repeated surname is ambiguous: do not attach a wrong picture.
        if len(matches) == 1:
            record = matches[0]
            picture = permitted_photo(record.get("headshot_url"))
            if picture:
                value["photo"] = picture
            colour = record.get("team_colour")
            if isinstance(colour, str) and re.fullmatch(r"[a-fA-F0-9]{6}", colour):
                value["team_colour"] = "#" + colour
            # Preserve Jolpica team names and nationalities as source of truth.
        out.append(value)
    return out


def current_driver_media(year):
    """OpenF1 /drivers?session_key=latest is only relevant for current season."""
    if year != datetime.now(timezone.utc).year:
        return []
    def produce():
        with httpx.Client(timeout=9, follow_redirects=False, trust_env=False,
                          headers={"User-Agent":"Latente/1.0 (https://latente.cfd)"}) as client:
            resp = client.get(OPENF1_DRIVERS, params={"session_key":"latest"})
            resp.raise_for_status()
            items = resp.json()
            if not isinstance(items, list):
                raise ValueError("Invalid OpenF1 driver list")
            return {"available":True,"rows":items[:40]}
    return _cached(("openf1_driver_media",year),86400,produce).get("rows", [])


def _champion_rows(kind, end_year):
    # World titles are the *season-final* position 1, not live leaderboards.
    path = "driverstandings" if kind == "drivers" else "constructorstandings"
    raw = _get(F1 + "/" + path + "/1.json", {"limit":100})
    standings = (raw.get("MRData") or {}).get("StandingsTable") or {}
    records = []
    key = "DriverStandings" if kind == "drivers" else "ConstructorStandings"
    for item in standings.get("StandingsLists") or []:
        year = int(item.get("season") or 0)
        if year < (1950 if kind == "drivers" else 1958) or year > end_year:
            continue
        leaders = item.get(key) or []
        if not leaders:
            continue
        leader = leaders[0]
        info = leader.get("Driver" if kind == "drivers" else "Constructor") or {}
        name = (info.get("givenName","") + " " + info.get("familyName","")).strip() if kind == "drivers" else info.get("name","")
        if not name or str(leader.get("position","1")) != "1":
            continue
        records.append({"year":year,"name":name,"nationality":info.get("nationality"),
                        "wins":int(leader.get("wins") or 0),
                        "points":float(leader.get("points") or 0),
                        "team":", ".join(c.get("name","") for c in leader.get("Constructors",[]) if c.get("name")) if kind == "drivers" else None})
    return sorted(records,key=lambda item:item["year"],reverse=True)


def f1_champions():
    current = datetime.now(timezone.utc).year
    # Do not call a provisional 2026 point leader a world champion.
    end_year = current - 1
    def produce():
        driver_rows = _champion_rows("drivers",end_year)
        constructor_rows = _champion_rows("constructors",end_year)
        if not driver_rows:
            return {"available":False,"message":"Historial de campeones no disponible"}
        return {"available":True,"through":end_year,
                "drivers":driver_rows,"constructors":constructor_rows,
                "provider":"Jolpica/Ergast, temporadas finalizadas"}
    return _cached(("f1_historical_champions",end_year),7*86400,produce)
