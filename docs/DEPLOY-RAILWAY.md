# Latente en Cloudflare + Railway, sin VPS

## Costo cero: alcance real

Configuración pensada para probar Latente sin contratar un plan pago. Al 12/10/2026, Railway documenta hasta 30 días de Trial con USD 5 de crédito; después ofrece Free con USD 1 mensual. **Es crédito de consumo, no cuatro servicios gratuitos ilimitados.** PostgreSQL, memoria, CPU, disco y tráfico consumen saldo. La base sola puede consumir una parte importante del crédito aunque no haya visitas. El alojamiento puede interrumpirse al agotarse y hay límites de retención de volúmenes del Trial. No debe usarse como única copia permanente de datos.

Conservá Free/Trial. No actives Hobby, Pro, facturación automática ni servicios pagos para seguir esta guía. Revisá el plan y el saldo de la cuenta antes de crear recursos. Si el panel exige pago, detené el despliegue. Activá las alertas de uso disponibles. Las condiciones vigentes de la cuenta prevalecen sobre esta guía.

La API deportiva tiene límites propios: alojar gratis no habilita resultados ilimitados ni temporadas fuera del plan del proveedor. `SYNC_PROFILE=free` reduce la frecuencia; no equivale a marcadores en tiempo real. El README explica la clave y cobertura de API-Football.

## 1. Crear el proyecto en Railway

En una cuenta Free/Trial, creá un **proyecto nuevo** llamado `Latente` y un ambiente `production`. Conectá el repositorio `mboero9/latente`, rama `main`. Todos los servicios deben estar en ese mismo ambiente. El proyecto usa cuatro servicios:

| Nombre | Fuente | Directorio raíz | Comando de inicio | Exposición |
| --- | --- | --- | --- | --- |
| `postgres` | PostgreSQL de Railway | — | Predeterminado del proveedor | Solo red privada |
| `api` | `mboero9/latente` | `/backend` | `python -m app.hosted api` | Solo red privada, puerto 8000 |
| `ingest` | `mboero9/latente` | `/backend` | `python -m app.hosted ingest` | Sin dominio; cron |
| `nginx` | `mboero9/latente` | `/` | Usar ENTRYPOINT del Dockerfile | Dominio HTTPS público, puerto 8080 |

Para `postgres`, elegí **New → Database → PostgreSQL**. Conservá el volumen persistente que aprovisiona el proveedor. No publiques un TCP Proxy para la base: la app usa la conexión privada. Si Railway crea el servicio con otro nombre, cambialo a `postgres` antes de agregar las referencias siguientes.

Para los tres servicios de código, podés elegir **New → GitHub Repo** y ajustar Settings antes de desplegar. `api` e `ingest` detectan `backend/Dockerfile` desde su directorio raíz. Para `nginx`, agregá `RAILWAY_DOCKERFILE_PATH=deploy/railway/Dockerfile`. El build de Nginx incorpora también una copia compilada del frontend; no necesita volúmenes compartidos.

No se incluye un `railway.json` antiguo: Railway documenta que esa modalidad está deprecada para servicios nuevos. Los valores de esta guía se configuran en Settings/Variables o mediante la integración oficial. La configuración no crea recursos hasta aplicarla en una cuenta.

## 2. Variables de API e ingesta

Agregá estas variables **en ambos servicios**, `api` e `ingest`:

```dotenv
DATABASE_URL=${{postgres.DATABASE_URL}}
DATA_MODE=demo
SYNC_PROFILE=free
API_DAILY_BUDGET=90
API_MIN_GAP_SECONDS=7
DB_POOL_MODE=none
WORKER_EXPECTED_INTERVAL_SECONDS=1800
LEAGUE_IDS=128,129,130,13,11,2,39,140,135,78,61,71
CORS_ORIGINS=https://latente.dimebag.workers.dev,https://latente.com.ar,https://www.latente.com.ar
```

La referencia `${{postgres.DATABASE_URL}}` se pega literalmente en Railway. No la reemplaces por una contraseña en GitHub. El backend admite las URLs `postgresql://`, `postgres://` y `postgresql+psycopg://` sin modificar manualmente la clave.

En `api`, agregá `PORT=8000`. Configurá el healthcheck `/api/health`, timeout de 180 segundos, una réplica y reinicio **On Failure**, máximo 3 intentos. Habilitá **Serverless** y volvé a desplegar para que se aplique. `DB_POOL_MODE=none` evita conservar conexiones inactivas, aunque las visitas y otras conexiones pueden mantener los servicios despiertos.

El comando de inicio espera la base y ejecuta `alembic upgrade head` antes de arrancar. Usa un bloqueo PostgreSQL para que API e ingesta no ejecuten migraciones simultáneamente. No hace falta un quinto servicio de migraciones.

## 3. Programar la ingesta

En `ingest`, configurá:

| Campo | Valor |
| --- | --- |
| Cron Schedule | `*/30 * * * *` |
| Start Command | `python -m app.hosted ingest` |
| Restart Policy | `Never` |
| Réplicas | `1` |
| Healthcheck HTTP | Ninguno |

Cada ejecución aplica migraciones pendientes, toma el bloqueo del worker, procesa tareas y termina. En demostración prepara los datos ficticios y sale. En modo API procesa un lote de pendientes durante unos 120 segundos, comprobando ese límite **entre trabajos**: una consulta paginada en curso puede extender la ejecución. Railway omite una nueva ejecución si la anterior sigue activa.

El scheduler sigue guardando en PostgreSQL los próximos vencimientos, reintentos y cuota diaria. Los partidos activos tienen prioridad temporal por su intervalo de 30 minutos; fixtures, tablas y goleadores se consultan con intervalos mayores. La primera carga de todas las ligas puede requerir varios ciclos. Cron no garantiza precisión al segundo.

El estado del worker permite el intervalo de 30 minutos más 3 minutos de tolerancia; después advierte que la actualización está detenida. No confunde una pausa normal entre ejecuciones con un fallo inmediato.

Para datos reales, agregá `API_FOOTBALL_KEY=TU_CLAVE_API_FOOTBALL` **como secreto del servidor** y cambiá `DATA_MODE=api` en ambos servicios; luego redesplegá. En modo real, una clave ausente o cobertura restringida produce un aviso y nunca se reemplaza por resultados inventados. No uses nombres `VITE_` para claves o credenciales.

## 4. Publicar Nginx

Variables de `nginx`:

```dotenv
RAILWAY_DOCKERFILE_PATH=deploy/railway/Dockerfile
PORT=8080
API_HOST=${{api.RAILWAY_PRIVATE_DOMAIN}}
API_PORT=8000
```

Healthcheck: `/api/health`, timeout 180 segundos, una réplica, reinicio On Failure (3 intentos). Habilitá Serverless y desplegá. En **Networking → Generate Domain**, generá el dominio público con puerto de destino `8080`. Usá la URL exacta que devuelve Railway: en los ejemplos siguientes, `TU_NGINX.up.railway.app` es un marcador.

Nginx consulta la API por la red privada y resuelve su DNS de nuevo al cambiar de contenedor. Esta configuración utiliza IPv4 privado de los proyectos nuevos de Railway. Un ambiente antiguo con red exclusivamente IPv6 requiere adaptar el listener de API y el resolver de Nginx.

Antes de conectar Cloudflare, verificá:

```bash
curl --fail https://TU_NGINX.up.railway.app/api/health
curl --fail https://TU_NGINX.up.railway.app/api/status
curl --fail https://TU_NGINX.up.railway.app/api/leagues
```

`health` debe dar `{"status":"ok"}`. `status` declara `mode: demo` mientras se usen datos ficticios. También podés abrir la raíz del dominio de Nginx para comprobar frontend y API juntos. La primera petición después de dormir puede demorar o devolver 502 temporalmente; reintentá después del arranque.

## 5. Conectar Cloudflare

En el Worker existente `latente`, conectá GitHub con raíz `/`, deploy command `npx wrangler deploy` y `NODE_VERSION=24`. `wrangler.jsonc` ya ejecuta el build. Añadí **como variable de build**:

```dotenv
VITE_API_BASE_URL=https://TU_NGINX.up.railway.app
```

Volvé a compilar y desplegar. No agregues `/api` al final. El dominio de Railway ya incluye HTTPS; permite probar todo con `latente.dimebag.workers.dev` sin comprar ni configurar otro dominio. Agregar la variable solo en runtime no cambia un frontend ya compilado.

Para subir archivos manualmente desde GitHub Actions, ejecutá **Compilar frontend para Cloudflare** e indicá esa URL pública en `api_base_url`. Descargá el artifact `latente-cloudflare` de **esa ejecución**, extraelo y publicá todos sus archivos. El artifact del CI ordinario usa la API del mismo origen y no conoce tu dominio Railway.

Cuando `latente.com.ar` esté en tu cuenta de Cloudflare, añadilo como Custom Domain del Worker y conservá HTTPS. El backend puede seguir usando su dominio `up.railway.app`; no es obligatorio crear `api.latente.com.ar`. Para un dominio propio del backend, seguí los registros que Railway indique, esperá el certificado y usá SSL/TLS **Full (strict)** en Cloudflare antes de activar el proxy.

## 6. Qué está validado y qué depende de la cuenta

El CI prueba migraciones en PostgreSQL, ejecución única del cron, Nginx con frontend compilado, conexión privada de prueba y CORS para el Worker. Esto verifica los contenedores; **no acredita un despliegue en tu cuenta Railway ni en Cloudflare**. Para eso deben observarse servicios sanos y respuestas HTTPS desde los dominios publicados.

Prueba local equivalente (base desechable):

```bash
docker compose -f deploy/railway/compose.test.yml up -d --build
curl --fail http://localhost:8088/api/health
docker compose -f deploy/railway/compose.test.yml wait ingest
curl --fail http://localhost:8088/api/status
docker compose -f deploy/railway/compose.test.yml down -v
```

El último comando elimina **solo los recursos de ese proyecto de prueba**. No lo uses para limpiar una base real.

## Referencias oficiales

- [Trial y Free de Railway](https://docs.railway.com/pricing/free-trial).
- [Precios y consumo](https://docs.railway.com/pricing/plans).
- [Cron](https://docs.railway.com/cron-jobs).
- [Serverless](https://docs.railway.com/deployments/serverless).
- [Dockerfiles](https://docs.railway.com/builds/dockerfiles).
- [Red privada y dominios](https://docs.railway.com/networking/domains/working-with-domains).
