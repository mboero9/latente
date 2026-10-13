# Latente — pipeline de datos deportivos (2026-10-13)

## Arquitectura existente y ampliación

API-Sports / Football Pro -> adaptadores Python -> persistencia PostgreSQL
-> endpoints FastAPI solo lectura -> vistas Preact con indicador de cobertura.

- `backend/app/worker.py`: cron Railway de fútbol; liga, temporada, fixture, evento,
  goleador y estadística; lock PostgreSQL; reintento sin duplicados.
- `backend/app/analytics.py`: promedios de equipos y jugadores a partir de
  `fixtures`/`scorers`, separando puntos oficiales y estimaciones.
- `backend/app/sports_sources.py`: API-Sports de rugby, NFL, NHL, NBA, baseball,
  basketball, F1, AFL; valida el JSON, normaliza clubes por **ID del proveedor**
  y rechaza respuestas paginadas no implementadas.
- `backend/app/sports_scheduler.py`: dentro del cron de Railway importa datos
  de hoy/ayer, posiciones con ligas configuradas, y rankings de F1.
  PostgreSQL guarda snapshots + contadores de solicitudes por deporte/día.
- `backend/app/sports_metrics.py`: promedios de anotación a favor/en contra,
  victorias y derrotas a partir de partidos terminados de **la misma liga**.
- `frontend/src/football-analytics.tsx` y `sports-standings.tsx`:
  muestran cifras y alcance, evitando inventar líderes históricos.

### Auditoría y datos faltantes

`GET /api/coverage?country=Argentina` presenta, por liga/temporada, cantidades
de partidos, equipos, posiciones y goleadores guardados, y un arreglo `missing`.
Señala ausencia en nuestra BD: **no prueba ausencia en API-Sports**.
Para revisar el resto del catálogo `?country=` (valor vacío) y `limit=250`.
Todas las categorías argentinas aparecen en el catálogo API-Football si el
proveedor las ofrece, y las ligas relevantes se importan progresivamente. El
Torneo Federal debe verificarse por su nombre, ID y temporada vigente.

`GET /api/leagues/128/analytics?season=2026` calcula GF/PJ, GC/PJ,
goles totales por partido, partidos ganados, perdidos, empatados, porcentaje de
victorias, puntos por partido **estimados** y goles por aparición de jugadores
que ya figuran en los goleadores oficiales. Se excluyen partidos no finalizados
o con adjudicación administrativa. `GET /api/leagues/128/analytics/history`
enumera temporadas de la BD, sus partidos cargados y cobertura de goleadores,
sin atribuir títulos por acabar primero en una clasificación.

### Origen y cobertura de cada disciplina

| Disciplina | Fuente principal | Fuente secundaria por validar | Restricción |
|---|---|---|---|
| Fútbol A/B/C/Federal y demás divisiones argentinas | API-Football Pro | LPF/AFA/Consejo Federal según competición | Cobertura varía por temporada y endpoint |
| Primera A de Argentina: promedios de descenso | Reglamento + tabla oficial LPF/AFA | Archivo anual de fixtures reconciliados | No estimar descenso si faltan fases, sanciones o reglamento |
| NBA | API-NBA v2 | NBA oficial, sujeto a licencia | Temporada `2025` y `2026` identifican cursos 2025-26 y 2026-27 |
| NHL | API-Hockey v1 | NHL oficial, sujeto a licencia | ID de liga por verificar |
| MLB | API-Baseball v1 | MLB oficial, sujeto a licencia | MLB ID `1` según documentación |
| NFL | API-American-Football v1 | NFL oficial, sujeto a licencia | NFL ID `1` según documentación |
| Básquet países | API-Basketball v1 | Federaciones nacionales según derechos | Crear un `SPORTS_TARGETS_JSON` por país y liga |
| Rugby | API-Rugby v1 | World Rugby/uniones nacionales según derechos | Requiere que el plan Rugby esté activo |
| Fórmula 1 | API-Formula-1 v1 | FIA/F1 oficial, sujeto a licencia | Rankings por temporada, no promedios fútbol |
| AFL | API-AFL v1 | AFL oficial, sujeto a licencia | Verificar endpoints cubiertos antes de dar estadísticas |

No se implementa scraping de Promiedos ni otros portales. Para agregar un
scraper solo cuando API no exista: revisar licencia, TOS, robots.txt y
prohibiciones de republicación; identificar fuente y versión, usar If-Modified-
Since/ETag si disponibles, rate limit y backoff, no evadir autenticación,
CAPTCHA o bloqueos; validar esquema de origen antes de incorporar datos.

### Configuración de Railway (secreto solo en backend)

El servicio `ingest` ejecuta `python -m app.hosted ingest` con cron.
Las nuevas migraciones se aplican en `app.hosted` mediante Alembic.

```dotenv
DATA_MODE=api
SYNC_PROFILE=live
LEAGUE_SCOPE=all
# Sigue usando API_FOOTBALL_KEY existente, NO duplicar en el frontend.
SPORTS_AUTOSYNC=nhl,mlb,nba,basketball,f1,nfl,afl,rugby
# Máximo 20 solicitudes por disciplina por día, conservador.
# Si un torneo está fuera de temporada: SPORTS_OFFSEASON=mlb,rugby
# Sólo configurar IDs comprobados en GET /leagues de la API correspondiente:
SPORTS_TARGETS_JSON={"nba":[{"season":2025},{"season":2026}],"mlb":[{"league":1,"season":2026,"country":"USA"}],"nfl":[{"league":1,"season":2026,"country":"USA"}],"f1":[{"season":2026}]}
```

Para sumar NHL, rugby y básquet por país: consultar el catálogo `/leagues`
del deporte en su dashboard, verificar la temporada y agregar entradas
`{"league": ID_CONFIRMADO, "season": ANIO, "country":"Argentina"}`.
Una liga id=1 de NFL **no es** id=1 de MLB. Identidad interna:
`(proveedor, deporte, liga, temporada, equipo)`.
Los nombres visibles se preservan, sin unificar equipos por similitud textual.
No activar automáticamente deportes no suscritos; Rugby puede mostrar
`provider unavailable` sin detener al resto.

### Programación y cuotas

- Cron de Railway existente, cada 10 minutos.
- Cada ejecución procesa como máximo 3 consultas nuevas de otros deportes.
- Temporada activa: partidos de hoy cada 6 h; ayer cada 24 h; tablas 24 h.
- Fuera de temporada: configurar `SPORTS_OFFSEASON`; consultas semanales.
- Máximo conservador de 20 pedidos por deporte/día en tabla persistente
  `sport_quotas` (por debajo del plan Free 100/día).
- Los resultados previos se conservan si el proveedor falla, no autoriza una
  temporada, devuelve página incompleta o un vacío transitorio.
- El número de visitas y el polling frontend de 5 s **no** desencadenan nuevas
  llamadas al proveedor cuando el snapshot existe.
- Las clasificaciones necesitan una liga/temporada comprobada; no se inventan.

### Endpoints de lectura

```bash
curl -sS https://latente.cfd/api/coverage?country=Argentina
curl -sS 'https://latente.cfd/api/leagues/128/analytics?season=2026'
curl -sS 'https://latente.cfd/api/leagues/128/analytics/history'
curl -sS 'https://latente.cfd/api/sports/nba/datasets'
curl -sS 'https://latente.cfd/api/sports/nba/dataset?kind=standings&ref=standard:2025'
curl -sS 'https://latente.cfd/api/sports/nba/analytics'
```

La respuesta es JSON `{"data": ..., "meta": ...}` con fecha y origen.
CSV puede generarse a partir de JSON, pero todavía no se implementó export CSV.
Los rankings individuales completos, récords históricos absolutos y campeones
necesitan endpoints por jugador / temporada y una fuente de campeonatos
autorizada. El agregador de resultados de 2 días **no** es historia completa.

### Pruebas y puesta en marcha

1. `cd backend && pytest -q`, y `cd frontend && npm ci && npm run build`.
2. Verificar éxito de CI y redeploy de `api`, `ingest` y `nginx`.
3. Añadir solo `SPORTS_TARGETS_JSON` con IDs/temporadas comprobados.
4. Revisar logs de `ingest` y `/api/coverage`, `/api/sports/{sport}/datasets`;
   los errores de proveedores nunca deben borrar información previa.
5. Validar manualmente 3 partidos de Primera Nacional y de NBA/MLB;
   verificar que el mismo partido no se duplique al reimportar.
6. Antes de campañas pagas o publicación masiva, revisar los derechos de
   redistribución comercial y política de logos de cada proveedor.

### Supuestos pendientes

- Plan API-Football Pro y clave ya configurada en backend.
- Railway Hobby, PostgreSQL y dominio `latente.cfd` existentes.
- Los planes Free de otros deportes están activos salvo Rugby (no confirmado).
- Los IDs de NHL, básquet por país y torneos de rugby deben confirmarse.
- Los campeones históricos y los récords de todos los tiempos requieren datos
  más extensos que el archivo 2024-2026 hoy importado en fútbol.
- Los promedios de descenso de AFA requieren la reglamentación vigente y los
  puntos completos por temporada; **no** equivalen a GF/PJ o puntos/PJ.
