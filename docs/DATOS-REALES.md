# Datos reales y catálogo global

## Estado y activación

Latente se aloja íntegramente en Railway. El dominio principal `latente.cfd` ya está asociado al servicio nginx de Railway. **Railway Hobby paga infraestructura, no datos deportivos.** Hasta incorporar una clave válida, el modo de demostración sigue indicando que sus resultados son ficticios.

1. Crear o abrir una cuenta de acceso directo en [API-Football](https://dashboard.api-football.com/register). En **Account → My Access** se encuentra la clave. El adaptador usa `x-apisports-key`, no las cabeceras de RapidAPI.
2. En el Live Tester del proveedor consultar `/leagues` y `/fixtures` para la fecha actual. Comprobar que el plan permite la temporada actual, especialmente Argentina. El catálogo no garantiza acceso a todos los datos enumerados.
3. En Railway → proyecto **Latente** → **production** → **Variables compartidas**, guardar `API_FOOTBALL_KEY` como secreto. No publicarla en GitHub, el frontend ni el chat.
4. En los servicios `api` e `ingest`, usar las referencias y valores siguientes:

   ```dotenv
   API_FOOTBALL_KEY=${{shared.API_FOOTBALL_KEY}}
   DATA_MODE=auto
   LEAGUE_SCOPE=all
   ```

   `auto` usa demostración si la clave está vacía y cambia a datos reales al recibir una clave. Una clave inválida produce un error de sincronización: nunca activa resultados ficticios como si fueran reales. `DATA_MODE=api` fuerza modo real incluso sin clave y muestra que falta configurar el proveedor.
5. Aplicar los cambios y esperar el redeploy de ambos servicios. Consultar `/api/status`: `mode=api`, `provider_configured=true`, `league_scope=all`, `last_success` reciente y ausencia de fallos. `leagues_loaded` mide lo cargado, no una promesa de cobertura. Revisar después partidos, posiciones y goleadores en la web.

## Cuota y frecuencia

El 12/10/2026, [API-Football](https://www.api-football.com/pricing/) anuncia Free con 100 consultas/día y temporadas limitadas, Pro con 7.500/día por USD 19/mes, Ultra con 75.000/día por USD 29/mes y Mega con 150.000/día por USD 39/mes. No se contrata ni se modifica un plan desde este proyecto. La cuenta del proveedor y su cobertura efectiva prevalecen.

El perfil conservador `SYNC_PROFILE=free`, presupuesto 90 y cron cada 30 minutos sirve para comprobar acceso. **No permite completar y refrescar todo el catálogo global en un día.** Los trabajos pendientes continúan en ciclos posteriores; las cuotas y reintentos sobreviven a reinicios.

Para una clave con al menos 7.500 consultas diarias, configurar en `api` e `ingest`:

```dotenv
SYNC_PROFILE=live
API_DAILY_BUDGET=7000
API_MIN_GAP_SECONDS=7
LIVE_INTERVAL_SECONDS=60
FIXTURES_INTERVAL_SECONDS=86400
TABLES_INTERVAL_SECONDS=21600
SCORERS_INTERVAL_SECONDS=86400
WORKER_EXPECTED_INTERVAL_SECONDS=0
```

En `ingest`, quitar **Cron Schedule**, usar `python -m app.hosted worker`, una réplica, reinicio **On Failure**, sin healthcheck HTTP y sin Serverless. Es un worker continuo y consume recursos de Railway mientras está activo. `api` y `nginx` pueden conservar Serverless; desactivarlo elimina el arranque en frío a costa de consumo continuo. No cambiar a esta frecuencia antes de comprobar el plan deportivo.

## Qué significa «todas las ligas»

- `LEAGUE_SCOPE=all` incorpora el catálogo completo devuelto por API-Football. No equivale a todos los torneos del mundo ni garantiza estadísticas para cada uno.
- Los partidos se sincronizan con una ventana móvil de dos días previos y siete próximos. Se conserva lo ya descargado. La jornada de hoy se consulta cada 15 minutos en perfil `live`; ayer y mañana cada hora, el resto cada día.
- Una consulta `live=all` actualiza todos los encuentros en juego. Otro trabajo reconcilia los partidos que desaparecen del vivo usando lotes de hasta 20 IDs para confirmar su finalización. Así, un partido terminado no queda indefinidamente como «en vivo».
- Posiciones y goleadores se consultan únicamente cuando la cobertura de la temporada no los excluye. Las competiciones vigentes no prioritarias se refrescan como máximo una vez al día. Las competiciones antiguas del catálogo quedan sin trabajos recurrentes, salvo selección explícita.
- `LEAGUE_IDS` indica ligas prioritarias: reciben el fixture completo de la temporada y perfiles de equipos, además del flujo global. Las demás reciben equipos desde sus partidos, posiciones y goleadores. Argentina aparece primero y el catálogo tiene buscador y carga progresiva para no renderizar miles de tarjetas juntas.
- La primera sincronización es gradual. El perfil gratuito consulta ayer, hoy y mañana (días verificados con la suscripción actual); otras fechas pueden ser rechazadas por `plan`. Las respuestas rechazadas por el plan se postergan 24 horas para no consumir la cuota reintentándolas cada minuto. El planificador prioriza catálogo, jornadas y vivo; tablas y goleadores se completan según la cuota. No hay una llamada al proveedor por cada visitante.
- El modo `selected` conserva la selección original y permite `SEASON_OVERRIDES` para temporadas históricas. En modo global, los overrides afectan tablas y tareas de esas ligas; los partidos globales siguen siendo de fechas actuales.

## Estadísticas de partido y refresco de cinco segundos

La pantalla consulta la API propia cada **5 segundos**, incluyendo resultados, posiciones, goleadores y estadísticas. Las peticiones se suspenden al ocultar la pestaña y nunca se superponen. Esto no multiplica las consultas del servidor al proveedor.

La [guía oficial de API-Football](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide) indica aproximadamente **15 s para marcadores**, **60 s para estadísticas de partido** y **1 h para posiciones**. Son frecuencias orientativas, sujetas a cobertura y demora. No existe una garantía de datos nuevos cada cinco segundos para todos los torneos.

`/api/fixtures/{id}/statistics` sirve snapshots de PostgreSQL: posesión, tiros, córners, faltas, tarjetas, pases y otras métricas publicadas. Los valores `null` se muestran como ausentes, nunca como cero. La migración `0002` crea `fixture_statistics` sin modificar los resultados existentes. El worker genera trabajos solo para partidos con cobertura de estadísticas, en juego o finalizados recientemente. Tras la captura de cierre deja de consultarlos de forma recurrente. La cola alterna estadísticas con tablas para que ninguna monopolice los trabajos.

`STATISTICS_INTERVAL_SECONDS=60` es el mínimo útil documentado del proveedor. Para marcadores, `LIVE_INTERVAL_SECONDS=15` sigue la frecuencia del origen; `5` está permitido si se elige expresamente y existe cuota, pero no produce datos adicionales cuando la API aún no cambió. Solo un poll global cada 5 s durante 24 h representa **17.280 consultas diarias**, antes de tablas o estadísticas. A 15 s son 5.760. Las estadísticas cuestan una consulta por partido y refresco: 100 partidos simultáneos a 60 s necesitan unas 100 consultas por minuto adicionales. El intervalo mínimo global y la cuota pueden retrasar trabajos; no se promete un SLA.

Mantener presupuesto 90/pausa 7 s hasta validar la clave y el plan. Para cobertura amplia y estadísticas en vivo hay que dimensionar el plan deportivo; los ejemplos de presupuesto no garantizan que alcance para todas las ligas en todas las jornadas. No aumentar límites ni contratar planes automáticamente.

## Otros deportes: siguiente etapa

La ampliación propuesta incluye básquet, NBA, WNBA, MLB, NHL y luego otros deportes, cada uno con su pantalla de resultados, calendario y estadísticas apropiadas. Esta versión implementa **fútbol**; no muestra pestañas que prometan datos inexistentes. Ver la [comparación de APIs verificada](APIS-MULTIDEPORTE.md).

[API-SPORTS](https://api-sports.io/) publica APIs separadas para básquet/NBA, rugby, vóley, Fórmula 1 y otros deportes. Comprobar plan y cobertura de cada API antes de activarla. Para tenis hay que seleccionar otro proveedor legítimo si sigue fuera de ese catálogo; no simularlo mediante la API de fútbol.

La implementación debe incorporar `sport` y `provider` a las identidades, tablas de participantes/competiciones/eventos por deporte, parciales (sets, cuartos, vueltas) y estadísticas tipadas. Las cuotas se separan por API para que básquet no consuma el presupuesto de fútbol. No reutilizar IDs, reglas de posiciones o goles de fútbol para otros deportes. La ingesta, PostgreSQL, Nginx y la interfaz base sí se pueden compartir.

No se agregaron suscripciones deportivas ni se modificó DNS.


## Comparador informativo de cuotas deportivas (1X2)

Latente integra un panel en el detalle de cada partido y una franja informativa en
las filas **En vivo** con precio decimal, probabilidad implícita porcentual
(100 / cuota), hora de captura y proveedor.

- Los precios de `/odds/live` son del mercado general de API-Football;
  **no indican la casa de apuestas**. No atribuirlos a Betano, bplay ni
  a ningún operador concreto.
- Los precios de `/odds?fixture=ID` son **previos al partido** y sí
  pueden incluir el nombre de cada bookmaker. En un partido ya iniciado
  se muestran expresamente como anteriores, nunca como cotización vigente.
- El worker alterna una sola solicitud al proveedor por ejecución de cron,
  evitando el choque de `API_MIN_GAP_SECONDS`. Las respuestas se guardan
  en `fixture_odds` en PostgreSQL; la web nunca consulta directamente
  API-Football y no necesita exponer `API_FOOTBALL_KEY`.
- `/api/odds/live` devuelve únicamente snapshots de partidos actualmente
  en juego con menos de 15 minutos de antigüedad. Si no hay datos, las
  filas enlazan al detalle sin inventar importes.
- Los porcentajes son **probabilidades implícitas con margen**, no un
  pronóstico de éxito. Los precios pueden cambiar en segundos o
  suspenderse. Una cuota de 2.50 corresponde a 40% implícito.
- Los enlaces externos a Betano y bplay son **genéricos**, no deeplinks al
  mismo evento ni prueba de que alguna casa ofrece el precio mostrado.
  Sus servicios requieren mayoría de edad y disponibilidad legal por jurisdicción.
  Latente no recibe apuestas.
- El feed en vivo de API-Football puede no cubrir un torneo o un encuentro.
  En ese caso se muestra falta de cobertura; no se usan cifras ficticias.

API: `GET /api/fixtures/{id}/odds` y `GET /api/odds/live`.
