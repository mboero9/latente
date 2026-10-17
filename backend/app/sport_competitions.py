"""Country-scoped basketball, volleyball and handball competitions.

Federation-published leagues are discoverable even when API-Sports does not
cover them. Catalogue IDs are assigned ONLY on strict provider name/country
matches. No imagined scores, standings, API coverage or team rosters.
"""
import re
import unicodedata

# (name, federation page, exact-name aliases used to match the API catalogue)
ARGENTINE_LEAGUES = {
    "basketball": (
        ("Liga Nacional de Básquet (LNB)", "https://www.laliganacional.com.ar/",
         ("liga nacional", "liga nacional de basquet", "liga nacional a", "lnb argentina")),
        ("Liga Argentina de Básquet (ascenso)", "https://www.laliganacional.com.ar/ligaargentina/",
         ("liga argentina", "liga argentina de basquet", "la liga argentina")),
    ),
    "volleyball": (
        ("Superliga Argentina de Vóley (ACLAV) 2026/27",
         "https://aclav.com/public/web/calendario/100",
         ("superliga argentina", "liga de voleibol argentina", "liga argentina de voleibol",
          "liga argentina masculina", "lva")),
        ("Liga Argentina Femenina (LAF)", "https://feva.org.ar/torneos/ligas-feva/liga-argentina-femenina",
         ("liga argentina femenina", "liga argentina femenina de voleibol", "laf")),
        ("Liga Nacional Masculina (FeVA)", "https://feva.org.ar/",
         ("liga nacional masculina", "liga nacional de voleibol masculina",
          "liga nacional masculina de voley", "lnvm")),
        ("Liga Nacional Femenina (FeVA)", "https://feva-web.dataproject.com/MainHome.aspx",
         ("liga nacional femenina", "liga nacional de voleibol femenina", "lnvf")),
    ),
    "handball": (
        ("Nacional de Clubes Adultos A", "https://handballargentina.org/cah/calendario-de-competencias-2026/",
         ("nacional de clubes adultos a", "nacional de clubes a",
          "torneo nacional a", "torneo nacional de clubes a")),
        ("Nacional de Clubes Adultos B", "https://handballargentina.org/cah/calendario-de-competencias-2026/",
         ("nacional de clubes adultos b", "nacional de clubes b",
          "torneo nacional b", "torneo nacional de clubes b")),
        ("Liga de Honor Hipotecario Seguros (FeMeBal)",
         "https://femebal.com/fixtures-disponibles-para-la-liga-hipotecario-seguros-y-la-liga-plata/",
         ("liga de honor", "liga de honor metropolitana", "liga de honor femebal",
          "liga de honor hipotecario seguros")),
        ("Liga de Honor Plata (FeMeBal)",
         "https://femebal.com/fixtures-disponibles-para-la-liga-hipotecario-seguros-y-la-liga-plata/",
         ("liga de honor plata",)),
    ),
}

COUNTRY_NAMES = {
    "argentina": "Argentina", "argentinian": "Argentina",
    "world": "Internacional", "international": "Internacional",
    "fiba": "Internacional", "europe": "Europa", "european": "Europa",
    "usa": "Estados Unidos", "united states": "Estados Unidos",
    "spain": "España", "espana": "España", "brazil": "Brasil",
    "brasil": "Brasil", "italy": "Italia", "germany": "Alemania",
    "france": "Francia", "poland": "Polonia", "turkey": "Turquía",
    "greece": "Grecia", "japan": "Japón", "portugal": "Portugal",
    "chile": "Chile", "uruguay": "Uruguay", "mexico": "México",
}

def _normalize(text):
    folded = "".join(ch for ch in unicodedata.normalize("NFKD", str(text or "").casefold())
                     if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", folded).strip()


def display_country(country):
    value = str(country or "").strip()
    return COUNTRY_NAMES.get(_normalize(value), value or "Sin país informado")


def _available_seasons(entries):
    result = []
    for item in entries or []:
        candidate = item.get("season", item.get("year")) if isinstance(item, dict) else item
        try:
            year = int(candidate)
            if 1900 <= year <= 2100:
                result.append(year)
        except (TypeError, ValueError):
            pass
    return sorted(set(result), reverse=True)


def build_competitions(sport, catalogue, stored_matches=(), standings_refs=()):
    if sport not in ARGENTINE_LEAGUES:
        return []
    provider_rows = []
    for item in catalogue or []:
        if not isinstance(item, dict) or not isinstance(item.get("id"), int):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        country = display_country(item.get("country"))
        provider_rows.append({
            "id": item["id"], "name": name, "country": country,
            "seasons": _available_seasons(item.get("seasons")),
        })

    verified_ids = {str(m.get("league_id")) for m in stored_matches
                    if isinstance(m, dict) and m.get("league_id") is not None}
    verified_ids |= {str(ref).split(":")[0] for ref in standings_refs}
    used = set()
    rows = []
    for name, url, aliases in ARGENTINE_LEAGUES[sport]:
        candidates = [
            item for item in provider_rows
            if item["country"] == "Argentina"
            and _normalize(item["name"]) in {_normalize(alias) for alias in aliases}
        ]
        # Multiple catalogue entries with same league name/region are
        # ambiguous; show the official link but no guessed provider ID.
        provider = candidates[0] if len(candidates) == 1 else None
        if provider:
            used.add(provider["id"])
        rows.append({
            "name": name, "country": "Argentina", "provider_id": provider["id"] if provider else None,
            "seasons": provider["seasons"] if provider else [],
            "official_url": url, "verified_source": "federation",
            "has_imported_data": str(provider["id"]) in verified_ids if provider else False,
        })

    for item in provider_rows:
        if item["id"] in used:
            continue
        rows.append({
            "name": item["name"], "country": item["country"], "provider_id": item["id"],
            "seasons": item["seasons"], "official_url": None,
            "verified_source": "api_sports_catalog",
            "has_imported_data": str(item["id"]) in verified_ids,
        })

    rows.sort(key=lambda r: (
        0 if r["country"] == "Argentina" else 1,
        0 if r["verified_source"] == "federation" else 1,
        0 if r["has_imported_data"] else 1,
        r["country"].casefold(), r["name"].casefold(),
    ))
    return rows
