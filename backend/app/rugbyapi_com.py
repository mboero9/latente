"""rugbyAPI.com adapter: verified catalogue, current fixtures/results and tables.

Distinct from API-Sports API-Rugby (v1.rugby.api-sports.io).
Only called from Railway cron after RUGBYAPI_COM_KEY has been configured.
The Free tier permits 50 calls/day and current standings, *not* season lookup.
Current season IDs are learned from actual fixture/result records, never guessed.
"""
import os
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlparse
import httpx

BASE = "https://api.rugbyapi.com/v1"
COMPETITION_SLUGS = {
    "top 12": "urba",
    "rugby championship": "championship",
    "six nations": "six-nations",
    "super rugby": "super-rugby",
    "premiership": "premiership",
    "top 14": "top-14",
    "united rugby championship": "urc",
    "european rugby champions cup": "champions",
    "friendly international": "test-matches",
    "test matches": "test-matches",
    "world cup": "world-cup",
    "national provincial championship": "npc-nz",
    "currie cup": "currie-cup",
    "rugby europe championship": "europe-championship",
    "pro d2": "pro-d2",
    "challenge cup": "challenge-cup",
    "top10": "top10-italia",
    "nations championship": "nations-championship",
    "nations cup": "nations-cup",
    "pacific nations cup": "pacific-nations",
    "premiership rugby cup": "premiership-cup",
    "premiership women's rugby": "premiership-women",
    "super rugby aupiki": "super-rugby-aupiki",
    "major league rugby": "mlr",
    "women's six nations": "six-nations-women",
    "autumn nations series": "autumn-series",
    "lions tour": "lions-tour",
    "world rugby u20 championship": "world-u20",
    "wxv 1": "wxv1",
    "women's world cup": "world-cup-women",
    "farah palmer cup": "farah-palmer",
    "super w women": "super-w",
    "nationale": "nationale",
    "europe super cup": "europe-super-cup",
    "rugby europe trophy": "europe-trophy",
    "rugby europe conference": "europe-conference",
    "sevens world series: australia": "sevens-australia",
    "supersevens": "supersevens",
    "supersevens 2": "supersevens-2",
    "supersevens 3": "supersevens-3",
    "the greatest rivalry": "greatest-rivalry",
}
# We display country flags by region where available, but no invented matches
# for Japan League One, Uruguayan or Chilean domestic leagues.
REGIONS = {
    "urba":"Argentina", "npc-nz":"Nueva Zelanda", "currie-cup":"Sudáfrica",
    "pro-d2":"Francia", "top-14":"Francia", "top10-italia":"Italia",
    "europe-championship":"Europa", "europe-trophy":"Europa",
    "europe-conference":"Europa", "europe-super-cup":"Europa",
    "challenge-cup":"Europa", "champions":"Europa",
    "six-nations":"Europa", "six-nations-women":"Europa",
    "super-rugby":"Hemisferio sur", "super-rugby-aupiki":"Nueva Zelanda",
    "premiership":"Inglaterra", "premiership-cup":"Inglaterra",
    "premiership-women":"Inglaterra", "urc":"Europa / Sudáfrica",
    "mlr":"Estados Unidos", "farah-palmer":"Nueva Zelanda",
    "super-w":"Australia",
}


def normalize_name(value):
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())


def slug_for(name):
    label=normalize_name(name)
    if label in COMPETITION_SLUGS:
        return COMPETITION_SLUGS[label]
    ascii_name=unicodedata.normalize("NFKD",label).encode("ascii","ignore").decode("ascii")
    return "rg-"+re.sub(r"[^a-z0-9]+","-",ascii_name).strip("-")[:65]


def configured():
    return bool(os.getenv("RUGBYAPI_COM_KEY","").strip())


def request(endpoint, params=None, transport=None):
    """Safe fixed host and endpoints; keys are sent only as request headers."""
    key=os.getenv("RUGBYAPI_COM_KEY","").strip()
    if not key:
        raise ValueError("RUGBYAPI_COM_KEY not configured")
    if endpoint not in {"competitions","fixtures","results"} and not re.fullmatch(r"seasons/ss_[A-Z0-9]+/standings",endpoint):
        raise ValueError("RugbyAPI endpoint not allowed")
    with httpx.Client(timeout=12,transport=transport,follow_redirects=False,trust_env=False) as client:
        res=client.get(f"{BASE}/{endpoint}",params=params or {},
                       headers={"Authorization":f"Bearer {key}"})
        res.raise_for_status()
        data=res.json()
    if not isinstance(data,dict) or not isinstance(data.get("data"),list):
        raise ValueError("RugbyAPI malformed JSON response")
    return data


def catalogue(rows):
    known={}
    for entry in rows:
        if not isinstance(entry,dict):
            continue
        ident=entry.get("id")
        name=entry.get("name")
        if (not isinstance(ident,str) or not re.fullmatch(r"cp_[A-Z0-9]+",ident) or
                not isinstance(name,str) or not name.strip()):
            continue
        slug=slug_for(name)
        if slug in known:
            # An accidental slug collision must not assign two competitions the
            # same backend route.
            continue
        region=str(entry.get("country") or entry.get("region") or REGIONS.get(slug) or "").strip()
        known[slug]={
            "slug":slug,"name":name.strip(),"competition_id":ident,
            "region":REGIONS.get(slug,region),
            "country":region,"seasons":[],
            "published_seasons":entry.get("seasons") if isinstance(entry.get("seasons"),int) else None,
            "coverage":entry.get("coverage") if isinstance(entry.get("coverage"),dict) else {},
        }
    return list(known.values())


def match_rows(rows):
    """Match schema returned by /v1/results and /v1/fixtures."""
    matches={}
    seasons={}
    for item in rows:
        if not isinstance(item,dict):
            continue
        match_id=item.get("id")
        cid=(item.get("competition") or {}).get("id") if isinstance(item.get("competition"),dict) else None
        home,away=item.get("home") or {},item.get("away") or {}
        if not (isinstance(match_id,str) and match_id.startswith("mt_") and
                isinstance(cid,str) and isinstance(home,dict) and isinstance(away,dict) and
                home.get("name") and away.get("name")):
            continue
        slug = item.get("_latente_slug")
        if not slug:
            continue
        date=str(item.get("kickoff_utc") or item.get("date") or "")
        if not re.match(r"^\d{4}-\d{2}-\d{2}",date):
            continue
        y=int(date[:4])
        season=item.get("season") or {}
        if isinstance(season,dict) and re.fullmatch(r"ss_[A-Z0-9]+",str(season.get("id") or "")):
            # Every season identifier is sourced from an actual match.
            seasons[(slug,y)]=str(season["id"])
        status=str(item.get("status") or "scheduled")
        result={
            "id":"rgapi-"+match_id, "date":date,
            "home":str(home["name"]),"away":str(away["name"]),
            "home_logo":None,"away_logo":None,
            "home_score":home.get("score") if type(home.get("score")) is int else None,
            "away_score":away.get("score") if type(away.get("score")) is int else None,
            "completed":status=="finished","status":status,
        }
        matches[(slug,y,match_id)]=result
    return matches,seasons


def tables(rows):
    """True rugby league points, bonus points and PD from /standings."""
    data=[]
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get("team"),dict):
            continue
        team=row["team"]
        if not team.get("name") or not isinstance(row.get("pos"),int):
            continue
        def value(k):
            v=row.get(k)
            return int(v) if isinstance(v,int) and not isinstance(v,bool) else None
        if value("pts") is None:
            continue
        data.append({
            "team":str(team["name"]),"team_id":team.get("id"),"logo":None,
            "rank":value("pos"),"group":"General",
            "played":value("p"),"won":value("w"),"drawn":value("d"),"lost":value("l"),
            "points":value("pts"),"bonus":value("bp"),"difference":value("pd"),
            "for":value("pf"),"against":value("pa"),
        })
    return sorted(data,key=lambda r:(r["rank"],r["team"]))
