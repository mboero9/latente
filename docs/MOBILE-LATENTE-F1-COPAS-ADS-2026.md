# Mobile first de Latente — auditoría de layout y monetización 2026-10-17

## Problema reportado

En un Android angosto, la tabla de pilotos de F1 comprimía la columna
`Piloto` por debajo del largo de una palabra. La regla
`.f1-identity>span:last-child {overflow-wrap:anywhere}` cortaba
«Andrea Kimi Antonelli» letra por letra mientras conservaba otras seis
columnas, la bandera y el logo. La captura del usuario confirma el defecto.

## Solución incorporada

- **F1 móvil (<761px)**: una tarjeta por piloto (puesto, foto opcional real,
  nombre completo, bandera, escudería, puntos y victorias); también formato
  equivalente para tabla de constructores y resultados de la última carrera.
  CSS impide cortar palabras en letras. Tabla original íntegra en desktop
  (ancho mínimo, scroll propio y foco teclado); fotos/logos conservan fallback.
- **Resto del sitio**: scroll horizontal contenido para tablas y archivos
  deportivos en pantallas estrechas; tamaño táctil y salto de línea del título
  mejorados; menú/estadísticas y fechas no deben ensanchar el documento.
- **Prioridad editorial Argentina/CONMEBOL**: accesos rápidos en home para la
  Primera División (128), Copa Argentina (129), Libertadores (13) y
  Sudamericana (11); se renderizan **solo si están presentes en el catálogo**.
  El orden del menú, catálogo y grupos del día prioriza esas competiciones
  sin borrar ninguna liga ni inventar resultados. Distinguir ranking editorial
  de mediciones de tráfico real.
- **Monetización**: dos slots verticales independientes `rail-left` y
  `rail-right`, visibles **solo en monitores ≥1920px** con altura ≥680px;
  no ocupan espacio en móvil, tablet ni equipos comunes. Permanecen totalmente
  **inactivos en producción** si faltan aprobación, consentimiento y slots.
  El sitio ya disponía de posiciones opcionales superior, central derecha
  y pie; no se agregan campañas activas ni scripts repetidos.
- **Desfase de datos**: badges "Demorado" habían sido retirados en otra
  corrección; se preserva `m.stale` para priorización, timestamps y
  alertas de caída del sincronizador.

## Para habilitar AdSense en el futuro

1. Comprobar aprobación del sitio: AdSense → Sitios → latente.cfd → **Listo**,
   `ads.txt` accesible y aprobaciones regulatorias/políticas aplicables.
2. Evaluar consentimiento CMP, geografía, privacidad y contenido de apuestas;
   **no habilitar anuncios automáticamente con el estado Preparando**.
3. Crear unidades (si AdSense permite ese formato) y obtener IDs individuales
   para `VITE_ADSENSE_SLOT_RAIL_LEFT` y `VITE_ADSENSE_SLOT_RAIL_RIGHT`.
4. Con previa aprobación y despliegue explícito: configurar
   `VITE_ADSENSE_CLIENT`, `VITE_ADSENSE_ENABLED=true`,
   `VITE_ADS_PRIVACY_READY=true` y slot IDs mediante variables de frontend.
   Verificar que no desborden/oculten contenido y revisar las políticas.
5. Medir CLS/LCP y densidad publicitaria antes de crecer; no mostrar
   anuncios en vistas de apuestas ni alterar resultados editoriales.

## Validación recomendada

Páginas: home `/#/`, F1 `/#/sport/f1`, NBA, rugby, tabla argentina
`/#/table/128`, Libertadores `/#/league/13`,
Sudamericana `/#/league/11`, Copa Argentina `/#/league/129`,
llaves y fichas de partidos.

Anchuras: **320, 360, 390, 430, 768, 1024, 1280, 1920px** en modo claro
y oscuro. Verificar nombre de cada piloto, menús táctiles, tablas deslizando
sin desplazamiento horizontal de toda la página, fechas y scoreboards.
Comprobar viewport real con navegador móvil/Playwright antes de dar por
cerrada una auditoría visual: los tests CI revisan compilación y estructura,
pero **no sustituyen una prueba manual en un celular**.
