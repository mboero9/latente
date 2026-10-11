# Latente

**Dominio de producción: [latente.com.ar](https://latente.com.ar).**

**¿Publicaste en Workers y se ve en blanco?** Seguí [la guía de Workers](docs/DEPLOY-WORKERS.md). Hay que publicar `frontend/dist` después de compilar. El ZIP del código fuente no es una publicación estática lista para subir. El frontend compilado también se genera como artifact `latente-cloudflare` en GitHub Actions.

Aplicación de resultados de fútbol en español: partidos por fecha, marcadores en vivo, posiciones por zona/grupo, goleadores, ligas y fichas de equipos. Prioriza Argentina y suma las principales competiciones internacionales. Diseño original, responsive, con modo claro/oscuro, controles de teclado y horarios seleccionables.

**No scrapea Promiedos.** Obtiene datos de API-Football / API-SPORTS, los persiste en PostgreSQL y los sirve desde una API propia. El navegador nunca consulta al proveedor ni recibe su clave.

**Arranca en demostración.** Todos los resultados, fechas, tablas y jugadores de ese modo son ficticios y están señalados en pantalla. Con `DATA_MODE=api` solo se muestran datos del proveedor; una falla nunca se oculta sustituyéndolos por datos inventados.

![Latente en escritorio, datos ficticios](docs/preview-desktop.png)

## 1. Stack y arquitectura

| Componente | Elección | Motivo |
| --- | --- | --- |
| Frontend | Preact 11 + TypeScript 7 + Vite 8 | Interfaz reactiva pequeña, sin librería de UI ni fuentes externas; salida estática |
| API | Python 3.13 + FastAPI | API tipada, validaciones, documentación OpenAPI y despliegue sencillo |
| Persistencia | PostgreSQL 17 + SQLAlchemy + Alembic | Integridad referencial, consultas indexadas y migraciones versionadas |
| Ingesta | Proceso Python dedicado + HTTPX | Planificador persistente sin agregar Redis ni Celery |
| Entrada | Nginx | Sirve estáticos, comprime respuestas y enruta `/api/` |
| Borde público | Cloudflare DNS/CDN + Tunnel | HTTPS público y acceso al VPS sin abrir puertos de origen |

```mermaid
flowchart TD
  U["Navegador"] --> C["Cloudflare · HTTPS y CDN"]
  C --> T["Cloudflare Tunnel"]
  T --> N["Nginx · estáticos y /api"]
  N --> A["FastAPI · consultas"]
  A --> P[("PostgreSQL")]
  W["Worker · sincronización"] --> P
  W --> F["API-Football"]
```

El servicio `frontend` de Compose compila el sitio en una imagen multietapa y copia los archivos al volumen de estáticos; **termina correctamente con código 0**. Nginx los sirve sin mantener un servidor Node. `migrate` también finaliza después de aplicar Alembic. Los servicios permanentes son `db`, `api`, `worker` y `nginx`.

## 2. Ejecutar localmente, en orden

Requisitos: Docker Engine/Desktop con **Docker Compose v2**, Git y un puerto local 8080 libre. En Windows, los scripts `.sh` se ejecutan desde WSL o Git Bash. Para usar la interfaz no necesitás instalar Python ni Node en el host.

1. Descomprimí el proyecto y entrá en su carpeta:

   ```bash
   cd latente
   cp .env.example .env
   ```

2. Iniciá el stack:

   ```bash
   docker compose up -d --build
   docker compose ps -a
   ```

   PostgreSQL debe estar saludable; `migrate` y `frontend`, finalizados con código 0. La API espera las migraciones; Nginx espera la API y el frontend. En el primer inicio se descargan y compilan imágenes.

3. Abrí [http://localhost:8080](http://localhost:8080). Se verán datos ficticios de ayer, hoy y los próximos dos días. Los monogramas de equipos son elementos de la interfaz, no escudos oficiales. Documentación interactiva: [http://localhost:8080/api/docs](http://localhost:8080/api/docs).

4. Verificá servicios y sincronización:

   ```bash
   bash scripts/smoke.sh
   curl http://localhost:8080/api/status
   docker compose logs --tail=100 worker
   ```

5. Detener y volver a iniciar:

   ```bash
   docker compose down
   docker compose up -d
   ```

   `down` conserva PostgreSQL. **`down -v` elimina la base y los volúmenes**; no se usa como parte del despliegue o actualización.

**Si ya ejecutaste la versión anterior (Cancha):** conservá tu `.env` con sus valores `POSTGRES_*` y agregá `COMPOSE_PROJECT_NAME=cancha` para seguir usando los volúmenes existentes. El cambio de marca no requiere borrar ni migrar los datos. En una instalación nueva, usá los valores Latente incluidos.

Para probar desde otro dispositivo de tu LAN, configurá `HTTP_BIND=0.0.0.0`, recreá Nginx y abrí `http://IP_DE_TU_PC:8080`. Para producción con Tunnel conservá `127.0.0.1`.

## 3. Activar datos reales

1. Registrate en [API-Football](https://dashboard.api-football.com/register). En el dashboard, sección **Account → My Access**, copiá la clave del acceso **directo API-SPORTS**. Este adaptador no usa las cabeceras de RapidAPI.

2. Consultá en el Live Tester del proveedor los IDs, temporadas y cobertura de las competiciones elegidas. `leagues` informa `current`, años y capacidades; una temporada enumerada no garantiza que tu plan permita consultarla. La disponibilidad efectiva se confirma al consultar fixtures/estadísticas.

3. Editá `.env`:

   ```dotenv
   DATA_MODE=api
   API_FOOTBALL_KEY=TU_CLAVE_API_FOOTBALL
   SYNC_PROFILE=free
   API_DAILY_BUDGET=90
   ```

4. Recreá los servicios que leen esas variables:

   ```bash
   docker compose up -d --force-recreate api worker
   docker compose logs -f worker
   ```

   La primera carga avanza por etapas: catálogo, fixtures de temporada, equipos, posiciones y goleadores. Con la pausa por defecto entre consultas, puede tardar varios minutos. La información ficticia permanece en su namespace `demo`, pero **no aparece en modo `api`**.

5. Revisá `http://localhost:8080/api/status` y las fechas de actualización. Si tu plan restringe la temporada actual, elegí años efectivamente permitidos:

   ```dotenv
   # Ejemplo de sintaxis, no garantía de acceso a esos años:
   SEASON_OVERRIDES=128:2024,39:2024
   ```

   Para aplicar cambios de ligas o temporadas inmediatamente, recreá el worker y adelantá el catálogo:

   ```bash
   docker compose up -d --force-recreate worker
   docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "UPDATE sync_jobs SET next_run = now() WHERE key = '\''catalog'\'';"'
   ```

   Si solo sincronizás temporadas históricas, seleccioná sus fechas en el calendario: no habrá partidos actuales ni marcadores en vivo. El selector de temporada de posiciones/equipos/goleadores muestra temporadas ya cargadas, no promete acceso a todo el catálogo.

### Cuota gratuita y vivo

Al verificar el proveedor, el plan gratuito anunciaba **100 consultas por día**, con limitaciones en las temporadas disponibles. No alcanza para mantener un servicio de muchas ligas con actualizaciones cada 30 segundos durante todo el día. Revisá las condiciones vigentes de tu cuenta antes de elegir un plan.

| Trabajo | Perfil `free` | Perfil `live` |
| --- | --- | --- |
| Catálogo y temporada actual | Cada 24 h | Cada 24 h |
| Fixtures de temporada | Cada 24 h por liga | Cada 6 h por liga |
| Equipos y estadio | Cada 7 días por liga | Cada 7 días por liga |
| Posiciones | Cada 24 h por liga | Cada 1 h por liga |
| Goleadores | Cada 24 h por liga | Cada 6 h por liga |
| Partidos en ventana de juego | Cada 30 minutos, hasta 20 IDs por llamada | Cada 30 segundos, hasta 20 IDs por llamada |
| Navegador → API propia | Cada 30 s para marcadores | Cada 30 s para marcadores |

Con 12 ligas, el mantenimiento diario de referencia puede consumir aproximadamente 37 consultas (1 + 12 + 12 + 12), más equipos cuando corresponde y llamadas de vivo. El primer arranque requiere más consultas. `API_DAILY_BUDGET=90` reserva un margen y detiene la ingesta al alcanzarlo; **no garantiza que todos los trabajos completen ese día**. La cantidad de usuarios del sitio no multiplica el consumo del proveedor.

Para seguimiento frecuente con un plan suficiente, por ejemplo:

```dotenv
SYNC_PROFILE=live
API_DAILY_BUDGET=7000
API_MIN_GAP_SECONDS=7
```

**No configures 7000 con una cuenta de 100 consultas.** Usá un presupuesto inferior al contratado y revisá el límite por minuto. A modo de dimensionamiento, un único lote cada 30 s durante 12 h consume 1440 consultas, además de las de referencia. Más de 20 partidos concurrentes se refrescan en lotes rotativos; el intervalo efectivo por partido aumenta. La demora final incluye al proveedor, al scheduler y hasta 30 s del navegador: no se promete tiempo real instantáneo.

El worker redescubre encuentros cada vez que refresca el fixture de temporada y atiende partidos conocidos desde 5 minutos antes del inicio. Consulta por ID también al finalizar, para capturar `FT`, `AET` y `PEN`, aunque el partido desaparezca del endpoint de vivo. La sincronización de temporada corrige posteriormente reprogramaciones y resultados.

### Cobertura configurada

| ID API-Football | Competición objetivo |
| --- | --- |
| 128 | Primera División / Liga Profesional argentina |
| 129 | Primera Nacional |
| 130 | Copa Argentina |
| 13 | Copa Libertadores |
| 11 | Copa Sudamericana |
| 2 | UEFA Champions League |
| 39 | Premier League |
| 140 | La Liga |
| 135 | Serie A |
| 78 | Bundesliga |
| 61 | Ligue 1 |
| 71 | Série A de Brasil |

Los nombres efectivos se leen del catálogo, porque pueden cambiar. `LEAGUE_IDS` es una lista de IDs separados por comas; el catálogo autoritativo es el del proveedor. La cobertura de posiciones y goleadores se verifica por temporada. Las copas pueden no tener tabla; la interfaz lo informa. No se calcula una tabla argentina anual, promedios o desempates a partir de reglas supuestas: se muestran los grupos y puntos del proveedor. Tampoco se incluyen apuestas, videos, noticias, alineaciones ni eventos minuto a minuto.

## 4. Configuración

| Variable | Valor / uso |
| --- | --- |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Credenciales internas. Cambiá `latente_local_only` antes del primer arranque productivo |
| `DATA_MODE` | `demo` o `api` |
| `API_FOOTBALL_KEY` | `TU_CLAVE_API_FOOTBALL`, solo backend |
| `SYNC_PROFILE` | `free` o `live` |
| `API_DAILY_BUDGET` | Tope persistido de intentos/día UTC |
| `API_MIN_GAP_SECONDS` | Separación global entre consultas; 7 s por defecto |
| `LEAGUE_IDS` | Competiciones que se sincronizan y publican |
| `SEASON_OVERRIDES` | Opcional: `ID:AÑO,ID:AÑO`; vacío usa `current` del catálogo |
| `LIVE_INTERVAL_SECONDS` | Opcional; mínimo 15 s |
| `FIXTURES_INTERVAL_SECONDS` | Opcional; mínimo 60 s |
| `TABLES_INTERVAL_SECONDS`, `SCORERS_INTERVAL_SECONDS` | Opcional; mínimo 3600 s |
| `HTTP_BIND`, `HTTP_PORT` | Por defecto `127.0.0.1:8080` |
| `CORS_ORIGINS` | Orígenes completos separados por comas, sin barra final ni comodines |
| `VITE_API_BASE_URL` | Vacío en un único origen; `https://api.latente.com.ar` en Pages, **sin `/api`** |
| `CLOUDFLARE_TUNNEL_TOKEN` | Token secreto del túnel, solo en `.env` del VPS |
| `DATABASE_URL` | Opcional para PostgreSQL externo: URL SQLAlchemy `postgresql+psycopg://...`; si no existe, se construye con `POSTGRES_*` |

No agregues claves o contraseñas con prefijo `VITE_`: Vite incluye esas variables en el navegador. `VITE_API_BASE_URL` se resuelve **al compilar**; si cambia, reconstruí el frontend. Los secretos del proveedor se leen al iniciar el backend.

Cambiar la contraseña en `.env` **no cambia la de un PostgreSQL ya inicializado**. Para rotarla, modificá primero el rol en PostgreSQL, luego `.env` y recreá API/worker/migrate. Guardá los secretos fuera del repositorio.

## 5. Repositorio y publicación de cambios

Repositorio del proyecto: [mboero9/latente](https://github.com/mboero9/latente). Incluye el código completo, lockfiles, migraciones, Docker Compose y GitHub Actions. Los secretos permanecen fuera de Git.

Para obtener una copia:

```bash
git clone https://github.com/mboero9/latente.git
cd latente
cp .env.example .env
```

Para publicar cambios desde una copia clonada, revisá primero el diff:

```bash
git diff
git add .
git status
git commit -m "Describir el cambio realizado"
git push origin main
```

Usá GitHub CLI (`gh auth login`), un credential manager o SSH para autenticarte. No pegues tokens en la URL del remoto ni subas `.env`. Las comprobaciones de backend, frontend y contenedores se ejecutan en [Actions](https://github.com/mboero9/latente/actions) con cada push a `main` y en pull requests.

El script `scripts/publish-github.sh` queda como utilidad para crear **otro repositorio nuevo** a partir del ZIP. No lo ejecutes para volver a crear `mboero9/latente`: ya existe, y el script no reemplaza repositorios ni remotos existentes.

**Despliegue:** publicar el código en GitHub no publica la aplicación. Cloudflare requiere vincular tu cuenta y configurar el origen que aloja Nginx, API, worker y PostgreSQL según los pasos siguientes.

## 6. Despliegue recomendado: VPS + Cloudflare Tunnel

Cumple PostgreSQL y Nginx sin forzarlos dentro de Workers. Para una aplicación inicial es más simple operar un único origen con todos los contenedores. Cloudflare aporta el borde HTTPS/CDN; el VPS ejecuta los procesos y conserva la base. Necesitás tu dominio y una máquina Linux con Docker. Como punto de partida, 2 vCPU, 2 GB de RAM y disco persistente; dimensioná según tráfico, volumen de datos y retención.

### A. DNS y cuenta

1. Agregá `latente.com.ar` a tu cuenta Cloudflare y reemplazá los nameservers en tu registrador por los asignados. Esperá a que la zona figure activa.
2. En **SSL/TLS → Edge Certificates**, verificá Universal SSL y activá **Always Use HTTPS**. La emisión del certificado puede demorar.
3. Conservá el modo de zona **Full (strict)** para los orígenes HTTPS convencionales. Con Tunnel, el transporte Cloudflare ↔ `cloudflared` ya va cifrado; el servicio configurado abajo es HTTP dentro de la red local de Docker. No uses Flexible ni desactives verificaciones de TLS.

### B. Preparar el VPS

```bash
git clone https://github.com/mboero9/latente.git
cd latente
cp .env.example .env
chmod 600 .env
```

Si el repositorio es privado, autenticá Git con una clave de despliegue de solo lectura o GitHub CLI. Editá `.env` **antes de inicializar PostgreSQL**:

```dotenv
POSTGRES_PASSWORD=TU_PASSWORD_POSTGRES_LARGO_Y_ALEATORIO
DATA_MODE=api
API_FOOTBALL_KEY=TU_CLAVE_API_FOOTBALL
SYNC_PROFILE=free
API_DAILY_BUDGET=90
HTTP_BIND=127.0.0.1
CORS_ORIGINS=https://latente.com.ar
VITE_API_BASE_URL=
```

### C. Crear y conectar el túnel

1. En el panel Cloudflare, abrí **Networking → Tunnels** (en algunas cuentas aparece en Cloudflare One / Networks / Connectors), creá un túnel administrado llamado `latente` y seleccioná Docker como entorno.
2. Copiá únicamente el token mostrado por el comando de instalación y guardalo en `.env`:

   ```dotenv
   CLOUDFLARE_TUNNEL_TOKEN=TU_TOKEN_DEL_TUNEL
   ```

3. Iniciá el stack con el archivo adicional:

   ```bash
   docker compose -f docker-compose.yml -f deploy/compose.tunnel.yml up -d --build
   docker compose -f docker-compose.yml -f deploy/compose.tunnel.yml logs --tail=100 cloudflared
   ```

4. En el túnel, agregá una **Published application route**:

   | Campo | Valor |
   | --- | --- |
   | Hostname público | `latente.com.ar` |
   | Domain | `latente.com.ar` |
   | Subdomain | Vacío (dominio raíz) |
   | Service / tipo | `HTTP` |
   | Service URL | `nginx:8080` (URL completa: `http://nginx:8080`) |
   | Path | Vacío |

   Dentro del contenedor del túnel, **`localhost` no es Nginx**. Usá el nombre de servicio `nginx`.

5. El panel crea el CNAME proxied del hostname al túnel (nombre `@` para `latente.com.ar`). Si lo configurás manualmente, el destino es `ID_DEL_TUNEL.cfargotunnel.com`, con proxy activado. No agregues además un registro A/AAAA para el mismo nombre.
6. Esperá el estado Healthy del túnel y abrí [https://latente.com.ar](https://latente.com.ar). Probá `/api/health` y `/api/status` por HTTPS.
7. Opcional: agregá también `www.latente.com.ar` al túnel y una Redirect Rule de Cloudflare que redirija permanentemente `www.latente.com.ar` a `https://latente.com.ar`, conservando la ruta y los parámetros de consulta.

No abras PostgreSQL, FastAPI ni 8080 a Internet. Permití únicamente tu acceso administrativo al VPS y la salida de `cloudflared` requerida por Cloudflare (puerto 7844); el túnel no necesita puertos de entrada web. Si agregás Cloudflare Access, afectará a los visitantes: omitilo para un sitio público.

### D. Caché y límites

- En **Caching → Cache Rules**, creá una regla con expresión `starts_with(http.request.uri.path, "/api/")` y acción **Bypass cache**. Evitá una regla global “Cache Everything” sobre la API.
- Los assets con hash bajo `/assets/` tienen caché larga. El HTML se revalida, y la API responde `Cache-Control: no-store`.
- Aplicá WAF/rate limiting de Cloudflare según tu plan y tráfico. No hay autenticación porque todos los endpoints públicos son de lectura; no existen rutas públicas para disparar sincronizaciones o cambiar datos.
- El límite del proveedor y el límite de visitantes son controles distintos. Para tráfico alto, agregá caché breve controlada de respuestas y medí la carga de PostgreSQL.

### E. Actualizar

```bash
git pull --ff-only
bash scripts/backup.sh
docker compose -f docker-compose.yml -f deploy/compose.tunnel.yml up -d --build
bash scripts/smoke.sh https://latente.com.ar
```

La migración corre antes de iniciar la API nueva. El despliegue por Compose es sencillo, pero no promete cero interrupciones. El volumen de estáticos conserva assets anteriores con hash para permitir que pestañas abiertas terminen de cargarlos; puede limpiarse durante una ventana de mantenimiento si crece mucho. En producción fijá las imágenes a digest después de verificarlas, especialmente `cloudflare/cloudflared:latest`, y actualizalas de forma controlada.

## 7. Alternativa: frontend en Cloudflare Pages

Reutiliza el backend anterior y sirve JS/CSS desde Pages. Separa despliegues y descarga estáticos del VPS, a cambio de configurar un segundo dominio, CORS y la URL de API en cada build.

1. En el mismo túnel, agregá `api.latente.com.ar` → `http://nginx:8080`. Nginx sigue siendo el proxy de FastAPI y puede seguir sirviendo los estáticos como origen alternativo.
2. En Cloudflare **Workers & Pages → Create application → Pages → Connect to Git**, conectá tu repositorio `mboero9/latente` y elegí la rama `main`.
3. Configurá el build:

   | Opción | Valor |
   | --- | --- |
   | Root directory | `frontend` |
   | Framework preset | Vite o None |
   | Build command | `npm run build` |
   | Build output directory | `dist` |
   | Variable `NODE_VERSION` | `24` |
   | Variable `VITE_API_BASE_URL` | `https://api.latente.com.ar` |

4. Publicá y anotá la URL `TU_PROYECTO.pages.dev`. En Pages → **Custom domains**, agregá `latente.com.ar`. Si ese hostname estaba en el túnel de la alternativa anterior, quitá primero su ruta/registro del túnel. Pages y Tunnel no deben competir por el mismo nombre.
5. Completá la validación DNS desde el panel de Pages. Para el dominio raíz `latente.com.ar`, la zona debe estar activa en la misma cuenta Cloudflare, con sus nameservers delegados. Pages configura el CNAME `@` hacia `TU_PROYECTO.pages.dev`; Cloudflare resuelve el registro raíz mediante CNAME flattening. Agregá primero el dominio al proyecto, no solo un CNAME. Cloudflare provisiona su certificado HTTPS. Si querés admitir `www.latente.com.ar`, agregalo también como dominio personalizado y configurá la redirección al dominio raíz.
6. Cambiá en el VPS:

   ```dotenv
   CORS_ORIGINS=https://latente.com.ar,https://www.latente.com.ar,https://TU_PROYECTO.pages.dev
   ```

   ```bash
   docker compose up -d --force-recreate api
   ```

7. Probá la página desde ambos orígenes y revisá Network: consultas a `https://api.latente.com.ar/api/...`, sin errores CORS ni contenido mixto. Si usás previews de PR, agregá sus orígenes exactos de forma deliberada; no habilites `*` automáticamente.

**No pongas** `API_FOOTBALL_KEY`, `POSTGRES_PASSWORD` ni `CLOUDFLARE_TUNNEL_TOKEN` en las variables de Pages. Solo necesita la URL pública de la API. La ingesta sigue funcionando en el VPS aunque nadie abra la página.

### Origen público con HTTPS, sin Tunnel

También es posible usar un A/AAAA proxied `api.latente.com.ar` hacia un VPS con Nginx en 443, certificado válido (Let's Encrypt u Origin CA), firewall que acepte HTTP(S) solo desde los rangos de Cloudflare y **Full (strict)**. Requiere mantener certificado, lista de IP y puertos. El Compose entregado usa Tunnel y no incluye ese terminador TLS; no expongas su listener HTTP creyendo que Full (strict) lo convierte en HTTPS.

### ¿Todo dentro de Cloudflare?

Workers + Cron Triggers + Hyperdrive puede conectarse a un PostgreSQL administrado externo. Reduce operación del VPS, pero exige adaptar el backend y scheduler al runtime de Workers. Hyperdrive no aloja PostgreSQL. D1 usa SQLite y no cumple el requisito de PostgreSQL. Nginx deja de tener una función natural en una arquitectura Workers/Pages. Por esos motivos, **VPS + Tunnel es la implementación entregada**, y Pages es una variante del frontend documentada, no un despliegue ya realizado.

## 8. Esquema, migraciones e ingesta

Ver [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Migración inicial: `backend/migrations/versions/0001_esquema_inicial_latente.py`.

```bash
docker compose run --rm migrate alembic current
docker compose run --rm migrate alembic history
docker compose run --rm migrate alembic upgrade head
```

No se usa `create_all` en producción; solo en las pruebas. Los cambios de modelo futuros requieren una nueva revisión Alembic, revisada antes de aplicar. Los datos se actualizan con upsert y transacciones. Se conservan históricos y se separan los namespaces `demo`/`api` en claves y relaciones.

El presupuesto se persiste en `api_usage`, cuenta intentos incluso si hay fallas y se reinicia por fecha UTC para el acceso directo API-SPORTS. Los errores de red usan espera exponencial hasta 1 h. Se respeta `Retry-After`, cabeceras de cuota y errores dentro de HTTP 200. El scheduler no marca un snapshot parcial como actualizado. Las cuotas compartidas con otras aplicaciones se detectan con el saldo informado por el proveedor; es preferible dedicar una clave/cuenta a esta aplicación.

## 9. Desarrollo y pruebas

La verificación realizada para esta entrega figura en [docs/VALIDATION.md](docs/VALIDATION.md). CI ejecuta las pruebas contra PostgreSQL real en GitHub Actions y levanta Compose. La suite no necesita una clave de fútbol.

Para desarrollo sin reconstruir Docker (PostgreSQL debe ser accesible solo para tu entorno):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL='postgresql+psycopg://TU_USUARIO:TU_PASSWORD@localhost:5432/latente_dev'
export DATA_MODE=demo
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

En otra terminal:

```bash
cd frontend
npm ci
npm run dev
```

Vite proxya `/api` a `127.0.0.1:8000`. Los comandos directos de Python **no cargan `.env` automáticamente**: exportá las variables necesarias o usá Compose. Para worker real: `python -m app.worker` con `DATA_MODE=api` y la clave en el entorno.

Pruebas contra una base **exclusiva de pruebas**:

```bash
cd backend
export TEST_DATABASE_URL='postgresql+psycopg://TU_USUARIO:TU_PASSWORD@localhost:5432/latente_test'
python -m pytest -q
```

La suite limpia las tablas de esa base: **nunca apuntes `TEST_DATABASE_URL` a producción**. Sin esta variable usa SQLite temporal para pruebas rápidas y omite los casos exclusivos de PostgreSQL. Para frontend: `cd frontend && npm ci && npm run build` (incluye chequeo estricto de TypeScript).

## 10. Copias, restauración y diagnóstico

```bash
bash scripts/backup.sh
```

Genera un dump comprimido en `backups/`, ignorado por Git y con permisos restringidos. Programá ese comando en el cron del VPS, por ejemplo a las 03:00 UTC, y copiá los backups cifrados a otro almacenamiento. Probá restauraciones periódicas; un volumen Docker no es una copia de seguridad.

Para verificar un dump en una base nueva, sin sobreescribir la original:

```bash
docker compose exec db sh -c 'createdb -U "$POSTGRES_USER" latente_restore'
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d latente_restore --no-owner --no-acl' < backups/TU_BACKUP.dump
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d latente_restore -c "SELECT count(*) FROM fixtures;"'
```

| Síntoma | Qué revisar |
| --- | --- |
| API vacía al activar datos reales | Clave, temporada disponible, `/api/status`, logs del worker; no hay fallback ficticio |
| HTTP 200 del proveedor pero sin datos | `errors`, cobertura y plan; el adaptador distingue error de lista vacía |
| Un torneo no tiene tabla/goleadores | Capacidades de la temporada; copas eliminatorias pueden no ofrecerlos |
| Cuota agotada | Se conserva la última copia; baja ligas/frecuencia o aumentá la cuota del plan |
| Worker sin heartbeat | `docker compose logs worker`; conexión a DB, migraciones y proceso |
| `frontend` / `migrate` en Exited (0) | Normal: son inicializadores de una sola ejecución |
| 502 en Cloudflare | Tunnel Healthy y ruta `http://nginx:8080`, API/Nginx saludables |
| CORS en Pages | Origen exacto en `CORS_ORIGINS`; recrear API; URL de API sin `/api` al final |
| Cambio de URL API no se refleja | Recompilar y volver a desplegar el frontend |
| Una tabla argentina tiene zonas distintas | Se preservan las agrupaciones y nombres del proveedor; no se fusionan tablas incompatibles |

## 11. Fuentes y alcance

Documentación consultada el 7–8 de octubre de 2026:

- [API-Football: documentación v3](https://www.api-football.com/documentation-v3), [guía de integración](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide), [planes](https://www.api-football.com/pricing), [condiciones de uso](https://www.api-football.com/terms).
- [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/get-started/), [Pages y Vite](https://developers.cloudflare.com/pages/framework-guides/deploy-a-vite3-project/), [dominios en Pages](https://developers.cloudflare.com/pages/configuration/custom-domains/), [Hyperdrive](https://developers.cloudflare.com/hyperdrive/).

La cuenta de datos, la autorización de uso/redistribución según el plan, el dominio, el VPS y las credenciales de publicación son del operador. Se evita reutilizar logos, imágenes o contenido editorial de terceros. La aplicación está inspirada en el tipo de información de sitios de resultados, con diseño y código propios. La cobertura y la exactitud final dependen del proveedor.

El dominio definido para este proyecto es `latente.com.ar`; la variante Pages utiliza además `api.latente.com.ar`. No se modificaron DNS ni se desplegó infraestructura desde esta entrega. La cuenta Cloudflare, el VPS, la clave de fútbol y los demás secretos se completan siguiendo esta secuencia.
