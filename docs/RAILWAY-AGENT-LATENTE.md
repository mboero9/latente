# Railway Agent: prompts seguros para Latente

Railway Agent existe y puede operar el proyecto: crear/configurar servicios,
leer logs y métricas, investigar deployments e iniciar PRs. Se abre desde
el panel del proyecto, o con `railway agent -p "consulta"` en CLI autenticada
con OAuth. **No es un editor instantáneo de todo el sitio**: para cambios
de código (fixtures, ligas, SEO, F1, rugby y monetización), trabajamos mediante
un PR del repositorio `mboero9/latente` y pruebas de CI antes de
fusionar y desplegar. El agente no desbloquea por sí solo APIs/licencias
de terceros, ni crea datos deportivos no publicados.

## Prompt 1 — Auditoría de backup (no destructivo)

> En el proyecto Latente, entorno production, revisá el servicio Postgres,
> su volumen, si hay backups nativos programados y si hay alguna restauración
> de prueba reciente. Proponé Daily + Weekly + Monthly, explicá retención,
> costos y el estado actual. Primero hacé SOLO lectura; **no habilites
> backups ni PITR, no cambies variables, no reinicies ni restaures ninguna
> base** hasta que te confirme. Proponé además una prueba de restauración
> en una base nueva y aislada, nunca sobre producción.

## Prompt 2 — Diagnóstico de latencia / fallos

> Auditá Latente en production: nginx, api, ingest y Postgres.
> Revisá errores 5xx, reinicios, latencia p95, uso de memoria,
> conexiones y cron de ingesta. Priorizá hallazgos por riesgo.
> No cambies recursos, replicas, variables ni despliegues.
> Si encontrás cambios de código necesarios, prepará un Pull Request
> contra mboero9/latente para revisar; no hagas merge automático.

## Prompt 3 — Diagnóstico de datos deportivos

> En Latente, revisá logs del servicio ingest y API cuando falten partidos
> o rankings de Premier League, F1, NBA o URBA. Indicá si faltan
> peticiones al proveedor, cobertura de liga/temporada, claves, cron,
> cuota o errores de importación. No inventes resultados ni
> habilites fuentes sin permiso. Proponé un Pull Request probado
> en vez de cambiar production directamente.

## Prompt 4 — Costos y monetización (solo infraestructura)

> Revisá los costos y métricas de Railway para Latente en production:
> nginx, api, Postgres, ingest, tráfico, almacenamiento y buckets.
> Compará el gasto real con un presupuesto mensual de USD 40 para
> infraestructura, identificá optimizaciones sin pérdida de
> disponibilidad ni de datos. No realices cambios que generen gastos,
> redimensionamientos, borrados o cambios de DNS sin aprobación.
> La configuración y aprobación de AdSense/Google Ads no pertenece a Railway.

## Guía de operación segura

- En producción, **primero diagnóstico**, luego PR, CI y aprobación humana.
- Backups/restore: primero snapshot verificable; restauraciones destructivas
  se aprueban en forma individual.
- Para cambios de infraestructura, usar staged changes y revisión antes
  de Deploy; nunca borrar volúmenes, buckets o credenciales sin aprobación.
- Si Railway Agent propone instalar software, crear buckets o cambiar plan,
  revisar precio y accesos antes.
- Railway Agent consume tokens LLM y puede tener cargos; conectar un modelo
  propio en Bring Your Own Models puede trasladar la factura a su proveedor.

Referencias:
- https://docs.railway.com/ai/railway-agent
- https://docs.railway.com/cli/agent
- https://docs.railway.com/guides/postgres-backups-restores
