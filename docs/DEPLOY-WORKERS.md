# Latente en Cloudflare Workers

Frontend previsto: `https://latente.dimebag.workers.dev/`. Dominio final: `https://latente.com.ar/`.

## 1. Corregir la pantalla en blanco

El 11 de octubre se observó que la página publicada cargaba `/src/main.tsx` y no incluía estilos compilados. Ese es el HTML de desarrollo: el navegador no compila TypeScript/JSX ni resuelve las dependencias de Preact. Agregar una base de datos no corrige este error.

Publicá el contenido de `frontend/dist`, incluyendo `index.html`, `assets/`, `favicon.svg` y `theme.js`. No publiques solo `index.html`, ni la carpeta `frontend` sin compilar, ni el ZIP del código fuente.

### Desde GitHub y Workers Builds

En la configuración de build del Worker existente `latente`, conectá `mboero9/latente` y usá:

| Campo | Valor |
| --- | --- |
| Rama | `main` |
| Root directory | Raíz del repositorio (`/`) |
| Build command | Vacío: el archivo `wrangler.jsonc` ejecuta la instalación y el build |
| Deploy command | `npx wrangler deploy` |
| Variable de build `NODE_VERSION` | `24` |
| Variable de build `VITE_API_BASE_URL` | `https://api.latente.com.ar`, cuando esa API ya esté disponible |

El `wrangler.jsonc` incluido compila con Vite y publica únicamente `frontend/dist`. Quitá argumentos anteriores como `--assets .` o `--assets frontend`, porque reemplazan el directorio correcto. Volvé a desplegar el último commit.

### Desde una computadora con Node y Git

```bash
git clone https://github.com/mboero9/latente.git
cd latente
npx wrangler login
npx wrangler deploy
```

El comando usa el nombre de Worker `latente`. Verificá que la cuenta seleccionada sea la que administra `latente.dimebag.workers.dev`. Si ya tenés el repositorio, actualizalo con `git pull --ff-only` en lugar de clonarlo de nuevo.

### Si preferís subir archivos manualmente

Abrí [Actions](https://github.com/mboero9/latente/actions), elegí la última ejecución correcta de **Verificar Latente** y descargá el artifact **latente-cloudflare**. Su ZIP contiene el frontend ya compilado, con `index.html` en la raíz. Extraé el ZIP y subí todos sus archivos y la carpeta `assets/` al servicio de estáticos; conservá su estructura.

El artifact de CI no contiene una URL de API externa ni resultados precargados: al principio mostrará la interfaz y un aviso de servicio no disponible. Para conectarlo a una API en otro dominio hay que compilar con `VITE_API_BASE_URL`, como se explica debajo. Este artifact corrige la publicación del frontend; no instala el backend.

## 2. Levantar PostgreSQL, API e ingesta

La implementación de este repositorio necesita los cuatro servicios siguientes fuera del alojamiento estático:

| Servicio | Función |
| --- | --- |
| PostgreSQL | Guarda ligas, equipos, partidos, posiciones, goleadores y estado de ingesta |
| FastAPI | Expone los endpoints de lectura `/api/*` |
| Worker Python | Consulta API-Football y actualiza PostgreSQL sin depender de visitas |
| Nginx | Proxy HTTP de la API; también puede servir el frontend |

La opción documentada es un VPS Linux con Docker, disco persistente y salida a Internet. Crear una base aislada en un proveedor no ejecuta FastAPI ni la ingesta. No se configura PostgreSQL desde el navegador y sus credenciales nunca llevan prefijo `VITE_`.

En el VPS:

```bash
git clone https://github.com/mboero9/latente.git
cd latente
cp .env.example .env
chmod 600 .env
```

Antes del primer arranque, configurá una contraseña de PostgreSQL propia y larga. Conservá `DATA_MODE=demo` para verificar la conexión con datos ficticios; para resultados reales usá `DATA_MODE=api` y `API_FOOTBALL_KEY=TU_CLAVE_API_FOOTBALL`. La clave y los límites de tu plan se explican en el README.

La variable del backend debe incluir el origen actual:

```dotenv
CORS_ORIGINS=https://latente.dimebag.workers.dev,https://latente.com.ar,https://www.latente.com.ar
```

Arrancá el stack y verificá la base y la API:

```bash
docker compose up -d --build
docker compose ps -a
docker compose run --rm migrate alembic current
curl --fail http://127.0.0.1:8080/api/health
curl --fail http://127.0.0.1:8080/api/status
```

Compose crea PostgreSQL y aplica las migraciones automáticamente. `migrate` y `frontend` terminan con código 0; es su funcionamiento esperado. No uses `down -v` para actualizar: borra los volúmenes.

## 3. Publicar la API y conectar el frontend

Seguí la sección **VPS + Cloudflare Tunnel** del README. Creá la ruta pública `api.latente.com.ar` hacia `http://nginx:8080`, con el token del túnel solo en `.env` del VPS, y levantá:

```bash
docker compose -f docker-compose.yml -f deploy/compose.tunnel.yml up -d --build
```

`https://api.latente.com.ar/api/health` debe responder JSON por HTTPS antes de conectar el frontend. El Worker estático no reemplaza esta API.

Después agregá **la variable de build** `VITE_API_BASE_URL=https://api.latente.com.ar` al Worker de Cloudflare y ejecutá un nuevo build y deploy. Una variable agregada solo en tiempo de ejecución no modifica el JavaScript ya compilado.

Para compilar y publicar desde una terminal Bash:

```bash
VITE_API_BASE_URL=https://api.latente.com.ar npx wrangler deploy
```

No agregues `/api` al final de esa variable: el frontend ya incluye ese prefijo en cada consulta. Si usás otro dominio para el backend, reemplazá la URL y configurá sus DNS/HTTPS. Conservá `api.latente.com.ar` en el túnel cuando agregues `latente.com.ar` al Worker del frontend.

## Fuentes oficiales

- [Workers Static Assets](https://developers.cloudflare.com/workers/static-assets/).
- [Configuración del directorio de assets](https://developers.cloudflare.com/workers/static-assets/binding/).
- [Build personalizado de Wrangler](https://developers.cloudflare.com/workers/wrangler/custom-builds/).

Estas instrucciones preparan el despliegue; no crean por sí solas un VPS, una cuenta de datos ni una base remota.
