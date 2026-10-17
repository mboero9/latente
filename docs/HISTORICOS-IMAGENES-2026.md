# Imágenes reales del archivo histórico — 17/10/2026

## Problema solucionado

Algunos navegadores de escritorio no dibujan los emoji de banderas; muestran
solamente las letras `PT`, `AR`, `EG`. Parte de los clubes no tenía teamId y
no se veía el escudo.

## Implementación

- `frontend/src/historic-flags.tsx`: imágenes PNG desde
  `https://flagcdn.com/{size}/{code}.png`, códigos de país allowlisted
  y banderas de Inglaterra / Irlanda del Norte específicas.
  En países con doble nacionalidad muestra dos imágenes.
- `frontend/src/historic-media.tsx`: retratos del proveedor para
  Messi (id 154) y Cristiano Ronaldo (id 874); para retirados sin
  retrato verificado se muestran iniciales, no fotografías falsas.
- `frontend/src/historical-honours.tsx`: club con escudo e indicador
  del país, selecciones con bandera real.
- `frontend/src/world-scorers.tsx`: retrato de jugador, bandera del país
  y escudo del club en columnas diferenciadas.
- `/api/history/club-crests`: recuperación de IDs desde clubes ya
  verificados en PostgreSQL. Se coteja nombre y país con alias
  conservadores; **nunca** se confunden Independiente de Argentina
  con otro homónimo ni Al Ahly Cairo con otro club.
- Los clubes que no existan en PostgreSQL o cuyo logo no cargue
  conservan las iniciales en vez de imágenes incorrectas.
- CSP actualizada en Railway, Nginx y Cloudflare Pages.

## Requisitos y alcance

- Ninguna solicitud adicional a API-Football por visitante;
  solo imágenes CDN y una lectura de la base de datos interna.
- El identificador de jugador/foto depende del proveedor. No reutilizar
  imágenes de exjugadores de Wikimedia/Google sin comprobar derechos.
- Escudos y fotografías pueden contener marcas registradas y derechos
  comerciales: verificar las condiciones de uso y redistribución del proveedor
  antes de habilitar AdSense.
- Fuente de imágenes deportivas: https://api-sports.io/documentation/football/v3
- Banderas: https://flagcdn.com/ y https://flagpedia.net/download/api
- Estado visual público: validar en móvil/escritorio tras el despliegue,
  incluidas políticas CSP de Cloudflare y caché.
