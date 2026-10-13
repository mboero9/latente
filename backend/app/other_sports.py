"""Otros deportes: consultas bajo demanda, claves separadas y caché en servidor.

No se llama a proveedores sin suscripción/clave. Cada deporte tiene una
cuota Free independiente: máximo 20 solicitudes por día y por instancia
(la página nunca debe producir una solicitud de proveedor por visitante).
"""
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any
import httpx

SPORTS = {
    "nhl": ("HOCKEY_API_KEY", "https://v1.hockey.api-sports.io", "games"),
    "mlb": ("BASEBALL_API_KEY", "https://v1.baseball.api-sports.io", "games"),
    "nba": ("NBA_API_KEY", "https://v2.nba.api-sports.io", "games"),
    "basketball": ("BASKETBALL_API_KEY", "https://v1.basketball.api-sports.io", "games"),
    "f1": ("FORMULA1_API_KEY", "https://v1.formula-1.api-sports.io", "races"),
    "nfl": ("NFL_API_KEY", "https://v1.american-football.api-sports.io", "games"),
    "rugby": ("RUGBY_API_KEY", "https://v1.rugby.api-sports.io", "games"),
    "afl": ("AFL_API_KEY", "https://v1.afl.api-sports.io", "games"),
}
_LOCK = threading.Lock()
_CACHE: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}
_COUNTS: dict[tuple[str, str], int] = {}


def status():
    return [{"name": sport, "configured": bool((os.getenv(key) or os.getenv("API_FOOTBALL_KEY", "")).strip()),
             "note": "Cuota gratuita independiente, cobertura según proveedor"}
            for sport, (key, _, _) in SPORTS.items()]


def games(sport: str, day: str):
    if sport not in SPORTS:
        raise ValueError("Deporte desconocido")
    datetime.strptime(day, "%Y-%m-%d")
    # Reutilizar snapshots persistidos antes de tocar API-Sports:
    # una visita nunca repite una llamada si el cron ya guardó el día.
    try:
        from .db import session_scope
        from .models import SportSnapshot
        with session_scope() as db:
            snapshot = db.get(SportSnapshot, (sport, "games", day))
            if snapshot:
                return {
                    "configured": True, "games": snapshot.data,
                    "message": snapshot.note,
                    "updated_at": snapshot.updated_at.isoformat(),
                    "provider": snapshot.provider,
                }
    except (ImportError, RuntimeError):
        # Sin capa de BD (ej. tests unitarios): conservar adaptador original.
        pass
    env, base, endpoint = SPORTS[sport]
    key = (os.getenv(env) or os.getenv("API_FOOTBALL_KEY", "")).strip()
    if not key:
        return {"configured": False, "games": [], "message": "Falta activar el plan Free y configurar su API Key"}
    stamp = datetime.now(timezone.utc).date().isoformat()
    cachekey = (sport, day)
    with _LOCK:
        cached = _CACHE.get(cachekey)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        countkey = (sport, stamp)
        if _COUNTS.get(countkey, 0) >= 20:
            return {"configured": True, "games": [], "message": "Límite conservador de consultas de prueba alcanzado"}
        _COUNTS[countkey] = _COUNTS.get(countkey, 0) + 1
    params = {"season": day[:4]} if sport == "f1" else {"date": day}
    # La NBA usa filtros de liga/temporada para algunas consultas del plan.
    if sport == "nba":
        params.update({"league": "standard", "season": day[:4]})
    try:
        with httpx.Client(timeout=9, follow_redirects=False) as client:
            response = client.get(f"{base}/{endpoint}", params=params,
                                  headers={"x-apisports-key": key})
            response.raise_for_status()
            payload = response.json()
            if payload.get("errors"):
                return {"configured": True, "games": [],
                        "message": "El plan o los filtros no permiten esta consulta"}
            rows = payload.get("response") or []
            if not isinstance(rows, list):
                rows = []
            clean = [_game_summary(sport, x) for x in rows[:120]]
            result = {"configured": True, "games": clean, "message": None}
            with _LOCK:
                _CACHE[cachekey] = (time.monotonic() + (21600 if sport == "f1" else 3600), result)
            return result
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        return {"configured": True, "games": [], "message": "No se pudo consultar el proveedor. Reintentá más tarde"}


def _trusted_logo(value):
    """Allow only known team-logo CDN hosts; never expose arbitrary image URLs."""
    from urllib.parse import urlparse
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in {
        "media.api-sports.io", "upload.wikimedia.org", "cdn.nba.com",
    }:
        return None
    return value


def _game_summary(sport: str, item: dict):
    if sport == "f1":
        race = item.get("competition") or {}
        return {"id": item.get("id"), "league": "Fórmula 1",
                "date": (item.get("date") or ""), "home": race.get("name") or "Gran Premio",
                "away": (item.get("circuit") or {}).get("name") or "",
                "home_logo": None, "away_logo": None, "league_logo": None,
                "home_score": None, "away_score": None,
                "status": ((item.get("status") or {}).get("short") if isinstance(item.get("status"), dict) else str(item.get("status") or "Programado"))}
    teams = item.get("teams") or {}
    # API-NBA uses 'visitors' instead of 'away' and scores.*.points;
    # numeric status.short 3 means finished, 2 live, 1 scheduled.
    if sport == "nba":
        home, away = teams.get("home") or {}, teams.get("visitors") or {}
        raw_scores = item.get("scores") or {}
        home_score = (raw_scores.get("home") or {}).get("points")
        away_score = (raw_scores.get("visitors") or {}).get("points")
        status = item.get("status") or {}
        short = str(status.get("short") or "")
        label = {"1": "NS", "2": "Live", "3": "FT"}.get(short, status.get("long") or short)
        return {
            "id": item.get("id"), "league": "NBA",
            "league_id": "standard", "country": "USA",
            "date": item.get("date"), "home": home.get("name") or "Local",
            "away": away.get("name") or "Visitante",
            "home_id": home.get("id"), "away_id": away.get("id"),
            "home_logo": _trusted_logo(home.get("logo")),
            "away_logo": _trusted_logo(away.get("logo")),
            "league_logo": None,
            "home_score": home_score if type(home_score) is int else None,
            "away_score": away_score if type(away_score) is int else None,
            "status": label,
        }
    home, away = teams.get("home") or {}, teams.get("away") or {}
    scores = item.get("scores") or {}
    h, a = scores.get("home"), scores.get("away")
    league = item.get("league") or {}
    state = item.get("status") or {}
    return {"id": item.get("id"), "league": league.get("name") if isinstance(league, dict) else str(league),
            "league_id": league.get("id") if isinstance(league, dict) else None,
            "country": (item.get("country") or {}).get("name") if isinstance(item.get("country"), dict) else None,
            "date": item.get("date"), "home": home.get("name") or "Local",
            "away": away.get("name") or "Visitante",
            "home_id": home.get("id"), "away_id": away.get("id"),
            "home_logo": _trusted_logo(home.get("logo")),
            "away_logo": _trusted_logo(away.get("logo")),
            "league_logo": _trusted_logo(league.get("logo") if isinstance(league, dict) else None),
            "home_score": h if isinstance(h, int) else (h or {}).get("total") if isinstance(h, dict) else None,
            "away_score": a if isinstance(a, int) else (a or {}).get("total") if isinstance(a, dict) else None,
            "status": (state.get("long") or state.get("short") or "") if isinstance(state, dict) else str(state)}
