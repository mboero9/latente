# Latente · Rugby 2026: fixtures completos y fuentes de tablas

## Cambio del 17 de octubre de 2026

Problema detectado: la web solo renderizaba los **primeros 70** encuentros
de una competencia; además, el puente ESPN consultaba únicamente dos
ventanas de unos 45 días alrededor de «hoy». Por eso una competición con
partidos de marzo a octubre parecía vacía o incompleta.

### Solución implementada

- El importador ESPN usa ventanas de 28 días de **enero a diciembre**
  dentro de la temporada elegida, con límite de 250 eventos por ventana.
  Deduplica por identificador ESPN, mantiene fechas, marcador, estado y
  escudos publicados, y registra únicamente partidos verificados.
- El backend solo llama ESPN mediante el **cron/worker** y almacena el
  resultado en `SportSnapshot` de PostgreSQL. Sin requests ESPN desde el
  navegador; lecturas web desde el caché. ESPN limita /scoreboard a ventanas
  y no garantiza una API pública comercial documentada.
- Se mantiene la ruta rugby principal con fallback independiente por tipo
  de información: rugbyAPI.com, API-Sports, ESPN y TheSportsDB.
  **No se calculan puntos de tabla ni bonus** a partir de los tanteadores;
  la tabla se muestra solamente con valores de posición y puntos provistos
  por una API. Para URBA Primera A/B/C, regionales, Córdoba, Litoral y
  Torneo del Interior, si no existe feed utilizable el sitio enlaza la fuente
  oficial, pero no simula resultados.
- ESPN conoce explícitamente los IDs **MLR 289262** y **EPCR Challenge Cup
  272073**, incorporados a la lista de competiciones aptas para consultas.
  La URI de rugby para cada torneo es distinta de IDs API-Sports.
- Se añadió **Súper Rugby Américas 2026** con sus 8 franquicias y enlace al
  fixture publicado por la organización. No se publica ninguna clasificación
  ni resultado propio para esa liga si no llega un feed válido.
- La pantalla de rugby muestra las pestañas **Todos / Resultados /
  Programados**, un buscador por club y un botón **Ver más partidos** que
  permite visualizar todos los registros importados, no solo 70.
- Se corrige el rótulo de la home de «URBA Top 12» a **URBA Top 14** y se
  priorizan las competiciones argentinas en la grilla de tablas.

### Límites y próximos pasos

**No es exacto afirmar que ESPN ofrece una API utilizable para TODO el rugby
argentino.** Su web editorial muestra URBA Top 14 y categorías inferiores,
pero ello no certifica cobertura en un endpoint JSON ni derechos de
redistribución. Las tablas de URBA/Interior/regionales se mantienen
pendientes si no existen datos estructurados autorizados.

1. Comprobar en los logs de `ingest` qué concursos ESPN devolvieron
   eventos y posiciones; el servicio alterna ligas según prioridad y
   vigencia de caché. El despliegue no prueba por sí solo cobertura.
2. Validar licencias y términos de ESPN antes de explotar resultados
   comerciales a escala. Para URBA y las uniones regionales, negociar
   acceso oficial si no se ofrece API pública reutilizable.
3. Revisar visualmente la pestaña de Rugby en móvil y escritorio,
   la temporada correcta y que las tablas oficiales no se infieran.

### Fuentes contrastadas

- ESPN Top 14 URBA 2026 y competiciones:
  https://espndeportes.espn.com/rugby/
- ESPN Major League Rugby, ID 289262:
  https://www.espn.com/rugby/results/_/league/289262
- ESPN Challenge Cup, ID 272073:
  https://www.espn.com/rugby/lineups/_/gameId/602974/league/272073
- Súper Rugby Américas 2026, fixture federativo:
  https://www.superrugbyamericas.com/habemus-fixture-22?nid=650
- URBA:
  https://urba.org.ar/fixture
