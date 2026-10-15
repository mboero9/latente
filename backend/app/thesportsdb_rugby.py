"""Public TheSportsDB rugby calendar backup (no guessed competitions).

Only the scheduled cron calls the provider; /api/rugby routes read PostgreSQL.
TheSportsDB's free v1 key '123' covers a limited sample of season events,
NOT official rugby standings or complete schedules.
League IDs verified against TheSportsDB's rugby competition pages.
"""
from datetime import datetime, timezone
from urllib.parse import urlparse
import httpx

BASE="https://www.thesportsdb.com/api/v1/json/123"
LEAGUES={
    "top-14": (4430, "split"),
    "premiership": (4414, "split"),
    "urc": (4446, "split"),
    "super-rugby": (4551, "annual"),
    "six-nations": (4714, "annual"),
    "champions": (4550, "split"),
    "world-cup": (4574, "annual"),
}
ALLOWED_IMAGE_HOSTS={"www.thesportsdb.com","r2.thesportsdb.com","thesportsdb.com"}
def logo(value):
    if not isinstance(value,str):
        return None
    url=urlparse(value)
    return value if url.scheme=="https" and url.hostname in ALLOWED_IMAGE_HOSTS else None

def dates(year, mode):
    return [str(year)] if mode=="annual" else [f"{year-1}-{year}", f"{year}-{year+1}"]

def normalize(items,year):
    from .rugby_api import _num
    unique={}
    for row in items or []:
        if not isinstance(row,dict) or not row.get("idEvent"):
            continue
        home=str(row.get("strHomeTeam") or "").strip()
        away=str(row.get("strAwayTeam") or "").strip()
        if not home or not away:
            continue
        stamp=str(row.get("strTimestamp") or "").strip()
        day=str(row.get("dateEvent") or "").strip()
        hour=str(row.get("strTime") or "").strip()
        if not stamp and day:
            stamp=day+"T"+(hour[:8] if hour else "00:00:00")+"Z"
        if not stamp.startswith(str(year)):
            continue
        h,a=_num(row.get("intHomeScore")),_num(row.get("intAwayScore"))
        status=str(row.get("strStatus") or "").strip()
        completed=status.upper() in {"FT","FINISHED","FINAL","AFTER EXTRA TIME","AET"} or (
            h is not None and a is not None and status.upper() not in {"NS","PST","POSTPONED","CANCELLED"})
        item={
            "id": "tsdb-"+str(row["idEvent"]), "date": stamp,
            "home":home, "away":away, "home_logo":logo(row.get("strHomeTeamBadge")),
            "away_logo":logo(row.get("strAwayTeamBadge")),
            "home_score":h,"away_score":a,
            "completed":completed,"status":status or ("Finalizado" if completed else "Programado"),
        }
        unique[item["id"]]=item
    return sorted(unique.values(),key=lambda r:(r["date"],r["id"]))

def fetch(slug,year,get=None):
    if slug not in LEAGUES:
        return []
    year=int(year)
    if not 2018<=year<=datetime.now(timezone.utc).year+1:
        raise ValueError("Invalid sports year")
    league_id,mode=LEAGUES[slug]
    def request(params):
        with httpx.Client(timeout=8,follow_redirects=False,trust_env=False) as client:
            res=client.get(BASE+"/eventsseason.php",params=params)
            res.raise_for_status()
            return res.json()
    get=get or request
    records=[]
    for season in dates(year,mode):
        try:
            obj=get({"id":league_id,"s":season})
            if isinstance(obj,dict) and isinstance(obj.get("events"),list):
                records.extend(obj["events"])
        except (httpx.HTTPError,ValueError,TypeError):
            continue
    return normalize(records,year)
