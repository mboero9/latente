"""Importar una fotografía de los promedios LPF sin scraping en vivo.

Uso:
 python -m app.promedios_reference /ruta/referencia.json          # dry run
 python -m app.promedios_reference /ruta/referencia.json --apply \
   --confirm "IMPORT_LPF_2026"                                  # revisión humana

El archivo contiene team_id de API-Football explícitamente contrastado por
un operador humano contra nombre/club LPF. Jamás adivinar IDs por parecidos.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path
from urllib.parse import urlparse


def parse_reference(document):
    if not isinstance(document, dict) or document.get("season") != 2026:
        raise ValueError("Referencia LPF: solo se admite temporada 2026")
    url = document.get("source_url")
    if (not isinstance(url, str) or urlparse(url).scheme != "https" or
            urlparse(url).hostname not in {"ligaprofesional.ar", "www.ligaprofesional.ar"}):
        raise ValueError("La referencia debe proceder del sitio oficial LPF")
    captured = document.get("captured_at")
    try:
        timestamp = datetime.fromisoformat(captured)
        if timestamp.tzinfo is None:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("captured_at debe ser ISO-8601 con zona horaria") from None
    rows = document.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Referencia LPF sin filas")
    output, seen = [], set()
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("Cada fila debe ser un objeto")
        team_id, points, played = (item.get("team_id"),
                                   item.get("points"), item.get("played"))
        if (not all(isinstance(x, int) and not isinstance(x, bool)
                    for x in (team_id, points, played))
                or team_id <= 0 or points < 0 or played <= 0
                or points > 3 * played or team_id in seen):
            raise ValueError("Team ID duplicado o puntos/partidos inconsistentes")
        seen.add(team_id)
        output.append({"team_id": team_id, "played": played, "points": points})
    return output, timestamp, url


def main():
    parser = argparse.ArgumentParser(description="Reference LPF 2026, dry run por defecto")
    parser.add_argument("path", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    rows, captured_at, url = parse_reference(json.loads(args.path.read_text("utf-8")))
    print(f"Referencia: {len(rows)} equipos, capturada {captured_at.isoformat()}")
    print(f"URL oficial: {url}")
    if not args.apply:
        print("Modo diagnóstico: NO se modificó PostgreSQL.")
        return
    if args.confirm != "IMPORT_LPF_2026":
        parser.error("Para guardar, indicar --apply --confirm IMPORT_LPF_2026")
    from sqlalchemy import select
    from .db import session_scope
    from .models import SportSnapshot, Team
    from .config import settings
    from .models import utcnow
    with session_scope() as s:
        known_ids = set(s.scalars(select(Team.id).where(
            Team.source == settings.mode, Team.id.in_([r["team_id"] for r in rows]))))
        if known_ids != {r["team_id"] for r in rows}:
            raise ValueError("IDs no registrados en Latente; no importar referencia")
        snapshot = s.get(SportSnapshot, ("football", "promedios_ref", "2026"))
        if snapshot is None:
            snapshot = SportSnapshot(sport="football", dataset="promedios_ref",
                                     ref="2026", provider="lpf_official", data=[],
                                     source_count=0, updated_at=utcnow())
            s.add(snapshot)
        snapshot.data = rows
        snapshot.source_count = len(rows)
        snapshot.provider = "lpf_official"
        snapshot.note = f"LPF {captured_at.isoformat()}"[:250]
        snapshot.updated_at = utcnow()
    print("Referencia validada almacenada. No se alteraron fixtures ni standings.")


if __name__ == "__main__":
    main()
