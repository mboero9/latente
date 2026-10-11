# Verificación de la entrega

Fecha: 7–8 de octubre de 2026. No se utilizó una clave privada de fútbol ni se realizaron consultas autenticadas al proveedor.

## Ejecutado satisfactoriamente

| Verificación | Resultado |
| --- | --- |
| Build TypeScript estricto + Vite | Correcto |
| Bundle inicial | Aproximadamente 40 KB JS / 14.3 KB gzip y 25 KB CSS / 5.8 KB gzip |
| Suite backend | 14 pruebas aprobadas contra PostgreSQL embebido PGlite, accesible mediante el protocolo PostgreSQL y psycopg |
| Migraciones | Upgrade inicial, comparación sin diferencias con modelos, downgrade a base y nuevo upgrade completados |
| Versión rápida de pruebas SQLite | 11 aprobadas; 3 exclusivas de PostgreSQL omitidas |
| Navegación en Chromium | Partidos, filtro en vivo, detalle de partido, ficha de equipo, tablas por grupos, goleadores y búsquedas |
| Modo claro/oscuro | Cambio y persistencia comprobados |
| Responsive | 1440 px, 390 px y 320 px; sin desbordamiento horizontal de la página |
| Tablas en móvil | Desplazamiento horizontal limitado al contenedor de tabla |
| CSP del frontend y consola | Navegación sin errores de ejecución ni bloqueos de recursos del frontend |
| Scripts y YAML | Sintaxis Bash y lectura YAML verificadas |
| Imágenes | Capturas reales del frontend con datos ficticios; revisadas visualmente |

La suite comprueba idempotencia, transición de partido a resultado final, marcadores nulos, conservación de múltiples zonas, sustitución de snapshots, filtros de temporada/competición, aislamiento demo/API, fechas, cambio horario y cambio de día en Argentina, presupuesto diario persistente, HTTP 429, cuota remota agotada, paginación y API de solo lectura. Las respuestas del proveedor se simulan en las pruebas de transporte.

## Actualización de marca: Latente

El 8 de octubre de 2026 se cambió la marca a Latente y se incorporó `latente.com.ar` a los metadatos, Nginx, variables de ejemplo y guía de Cloudflare. Se repitieron el build estricto del frontend y las comprobaciones de navegación en Chromium, incluido modo oscuro y anchos de 390 y 320 px; todas pasaron. Las tres capturas incluidas corresponden a Latente. La revisión de Alembic sigue siendo `0001`; solo cambió el nombre del archivo, sin modificar el esquema.

## Limitaciones de esta verificación

- El entorno de construcción no dispone de Docker Engine. **No se ejecutó aquí `docker compose up` ni se validaron las imágenes y Nginx en contenedores.** La configuración fue revisada y se incluyó un job de GitHub Actions que construye y levanta el stack completo cuando se suba el repositorio.
- PGlite utiliza un motor PostgreSQL embebido con conexiones multiplexadas; no reemplaza una validación de concurrencia, recuperación o alta disponibilidad contra un servidor PostgreSQL 17. CI incorpora PostgreSQL 17 para esa integración básica.
- El proveedor se integró según documentación oficial y con respuestas simuladas. No se verificaron la clave del operador, la cobertura efectiva de su plan ni encuentros reales en curso.
- No se ejecutaron pruebas de carga, auditoría exhaustiva de seguridad ni certificación WCAG. Se incluyeron navegación por teclado, focos visibles, semántica de tablas, etiquetas accesibles, reducción de movimiento y contraste de estados.
- La validación original del 7–8 de octubre se realizó antes de publicar en GitHub. El repositorio de continuación es `mboero9/latente`; los resultados de CI se consultan en su pestaña Actions. El despliegue en Cloudflare, el VPS y el acceso al proveedor requieren la cuenta e infraestructura del operador.

## Capturas

- [Escritorio claro](preview-desktop.png)
- [Escritorio oscuro](preview-dark.png)
- [Móvil](preview-mobile.png)

Los resultados y estadísticas que aparecen en estas capturas son ficticios; la aplicación los identifica como demostración.
