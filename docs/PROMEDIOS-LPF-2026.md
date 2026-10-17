# Promedios Argentina 2026 — Latente

## Arquitectura aprobada

Mantener **API-Football** para fixture y resultados; procesar los partidos
ya importados en **PostgreSQL** con `backend/app/promedios.py`; validar los
totales contra una fotografía independiente de la **Liga Profesional**.
No aumentar consultas del proveedor por visitas al sitio.

- Endpoint `GET /api/leagues/128/promedios?season=2026` consulta
  `fixtures` y `memberships` en PostgreSQL, filtra únicamente la liga 128
  y años 2024, 2025 y 2026.
- `status=FT` y fases de liga/zonas reconocidas; **excluye** octavos,
  cuartos, semifinales, finales y desempates, que no se usan en el promedio.
- Fórmula por club: `sum(puntos de encuentros admitidos) /
  sum(partidos admitidos)`. Ganado 3, empatado 1, perdido 0.
- Muestra por separado puntos de 2024, 2025 y 2026, PJ, PTS, promedio,
  año sin datos y resultado de la comparación LPF cuando exista.
- No transforma ausencia de fixtures de un ascendido en "cero puntos";
  se informa temporada no verificada.
- Toda la tabla aparece como **parcial y no oficial**, incluso si coincide
  con ciertos totales: faltan verificar puntajes administrativos, sanciones,
  desempates y cobertura completa de años pasados.

## Advertencia importante sobre el historial

No basta importar solo la liga 128 de 2024: la LPF puede computar partidos
de **Copa de la Liga 2024** almacenados bajo otra competición de API-Football.
Antes de publicar una clasificación compatible con LPF, verificar ID,
programación y partidos válidos de cada temporada, todos los equipos y su
primera temporada en la categoría. Tampoco deben sumarse playoffs de 2025–26.

La tabla inicial es **provisional**; el motor funciona aunque falten
temporadas, pero sus cifras no equivalen a la tabla oficial. No resaltar
descensos ni puestos definitivos hasta validar toda la cobertura.

## Validación offline con la LPF

Las posiciones oficiales se leen en
https://www.ligaprofesional.ar/torneo-clausura-mercado-libre-2026/ .
El reglamento 2026:
https://www.ligaprofesional.ar/wp-content/uploads/2026/01/Reglamento-Torneos-LPF-Primera-2026-1.pdf
(Capítulo VII, artículos 24 y 26).

La web LPF no es tratada como una API pública reutilizable: no realizar
scraping automático en cada visita. Para contrastar resultados puede
prepararse manualmente un archivo JSON con IDs de club **comprobados** en
Latente y puntos/PJ de una misma fecha/hora oficial:

```json
{
  "season": 2026,
  "source_url": "https://www.ligaprofesional.ar/torneo-clausura-mercado-libre-2026/",
  "captured_at": "2026-10-17T19:00:00-03:00",
  "rows": [
    {"team_id": 123456, "played": 99, "points": 176}
  ]
}
```

**El ejemplo no es ejecutable:** `123456` es deliberadamente un ID ficticio;
no usarlo como identificación de Boca u otro club. Sustituirlo por el ID real
contrastado y por totales capturados en esa misma fecha/hora. No guardar
archivos de importación con datos no confirmados en la rama principal.

Diagnóstico **sin tocar PostgreSQL**:

```sh
cd backend
python -m app.promedios_reference /ruta/validacion-lpf.json
```

Solo **después de revisar** IDs, calendario, totales y cobertura, aplicar:

```sh
cd backend
python -m app.promedios_reference /ruta/validacion-lpf.json \
  --apply --confirm IMPORT_LPF_2026
```

Almacena `sport_snapshots(football,promedios_ref,2026)` con provider
`lpf_official`. El endpoint compara **puntos y PJ por club**,
sin modificar fixtures ni standings. Una diferencia puede deberse a
cobertura histórica incompleta, sanciones, edición de fixture o fecha
de captura distinta. Las discrepancias permanecen visibles para auditoría.

## Fases siguientes

1. Inventariar partidos completos y reglamentos 2024, 2025 y 2026, con
   inclusión formal de Copa de la Liga 2024 si corresponde y validación
   de equipos ascendidos.
2. Comparar totales/PJ con LPF, identificar diferencias y documentar
   correcciones sin sobreescribir marcadores deportivos.
3. Recién entonces considerar etiquetar tabla como validada y
   calcular riesgo de descenso, conservando los desempates oficiales.

Las consultas actuales solo usan PostgreSQL; no generan consumo
adicional de API-Football ni abren servicios/costos nuevos.
