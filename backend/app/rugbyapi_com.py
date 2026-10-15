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

def sync_once(max_calls=3, fetch=None):
    """Iterative bounded ingestion. No HTTP on user requests.

    A RugbyAPI.com free key grants 50 lookups/day. Reserve at most 40/day
    globally in PostgreSQL so multiple cron runs cannot exceed free allowance.
    Tournament-specific current standings use season IDs from actual events;
    /competitions/{id}/seasons requires Archive (not called on Free).
    """
    from datetime import timedelta
    from .db import session_scope
    from .models import SportSnapshot, utcnow
    from .provider import aware
    from .sports_scheduler import reserve_quota
    from .rugby_api import _snapshot, _write, _fresh

    outcome={"attempted":[],"updated":[],"unavailable":[]}
    if not configured():
        outcome["unavailable"].append("RUGBYAPI_COM_KEY not configured")
        return outcome
    fetch=fetch or request
    now=utcnow()
    year=now.year

    def call(endpoint, params, dataset, ref, ttl):
        if len(outcome["attempted"])>=max_calls or _fresh(_snapshot(dataset,ref),ttl):
            return None
        if not reserve_quota("rugbyapi",cap=40):
            return None
        outcome["attempted"].append(endpoint)
        try:
            return fetch(endpoint,params)
        except (httpx.HTTPError, ValueError, TypeError, KeyError):
            outcome["unavailable"].append(endpoint)
            return None

    raw_cats=call("competitions",{},"rugbyapi_cats","current",timedelta(hours=24))
    if raw_cats is not None:
        cats=catalogue(raw_cats["data"])
        if cats:
            _write("rugbyapi_cats","current",cats,len(cats),"rugbyAPI.com catalogue of verified rugby competitions")
            outcome["updated"].append("competitions")

    cached_cats=_snapshot("rugbyapi_cats","current")
    if not cached_cats or not cached_cats.data:
        return outcome
    by_id={r["competition_id"]:r["slug"] for r in cached_cats.data if r.get("competition_id")}
    season_cache=_snapshot("rugbyapi_seasons","current")
    seasons={item["slug"]:item for item in (season_cache.data if season_cache else [])
             if isinstance(item,dict) and item.get("slug")}

    for endpoint, params, ref, ttl in (
        ("fixtures",{"days":60},"fixtures",timedelta(hours=8)),
        ("results",{},"results",timedelta(hours=8)),
    ):
        if len(outcome["attempted"])>=max_calls:
            break
        response=call(endpoint,params,"rugbyapi_runs",ref,ttl)
        if response is None:
            continue
        records=[]
        for game in response["data"]:
            if not isinstance(game,dict):
                continue
            cid=(game.get("competition") or {}).get("id") if isinstance(game.get("competition"),dict) else None
            slug=by_id.get(cid)
            if slug:
                records.append({**game,"_latente_slug":slug})
        matches,seasons_by_game=match_rows(records)
        # Record successful feed even when no competition has a match today.
        _write("rugbyapi_runs",ref,[{"checked":True,"matches":len(records)}],1)
        touched={}
        for (slug,y,_),item in matches.items():
            touched.setdefault((slug,y),[]).append(item)
        for (slug,y),items in touched.items():
            key=f"{slug}:{y}"
            old=_snapshot("rugbyapi_games",key)
            known={g["id"]:g for g in (old.data if old else []) if isinstance(g,dict) and g.get("id")}
            known.update({g["id"]:g for g in items})
            # keep the current/next calendar year, without erasing prior verified games
            merged=sorted(known.values(),key=lambda g:(g["date"],g["id"]))[-450:]
            _write("rugbyapi_games",key,merged,len(merged),"rugbyAPI.com: recent fixtures/results, Free coverage")
        for (slug,y),season_id in seasons_by_game.items():
            entry=seasons.get(slug)
            if entry is None or y>=entry.get("year",0):
                seasons[slug]={"slug":slug,"year":y,"season_id":season_id}
        if seasons:
            _write("rugbyapi_seasons","current",list(seasons.values()),len(seasons),
                   "Current season IDs learned only from actual published rugbyAPI.com matches")
        outcome["updated"].append(endpoint)

    if len(outcome["attempted"])>=max_calls:
        return outcome
    # Current-season official tables, prioritized by oldest successful sync.
    options=[]
    for slug,entry in seasons.items():
        sid=entry.get("season_id")
        if not isinstance(sid,str) or not re.fullmatch(r"ss_[A-Z0-9]+",sid):
            continue
        ref=f"{slug}:{year}"
        snapshot=_snapshot("rugbyapi_tables",ref)
        # Season can change, e.g. 2026-27 replaces 2025-26.
        diagnostic=_snapshot("rugbyapi_diag",sid)
        if _fresh(diagnostic,timedelta(hours=16)):
            continue
        if _fresh(snapshot,timedelta(hours=16)):
            continue
        stamp=snapshot.updated_at if snapshot else datetime(2000,1,1,tzinfo=timezone.utc)
        options.append((aware(stamp),slug,sid,ref))
    for _,slug,sid,ref in sorted(options):
        if len(outcome["attempted"])>=max_calls:
            break
        resp=call(f"seasons/{sid}/standings",{},"rugbyapi_diag",sid,timedelta(hours=16))
        if resp is None:
            continue
        data=tables(resp["data"])
        # Free provider may have no table for elimination-format cups.
        if data:
            _write("rugbyapi_tables",ref,data,len(data),
                   f"Standings provided by rugbyAPI.com; season {sid}")
            outcome["updated"].append(f"standings:{slug}")
        _write("rugbyapi_diag",sid,[{"checked":True,"count":len(data)}],1)
    return outcome
