# Fórmula 1 en Latente: pilotos, banderas, logos y campeones

Implementación 17/10/2026.

## Cobertura técnica

- Tablas de pilotos y constructores: Jolpica/Ergast, API existente `/api/reference/f1?season=2026`, sin inventar puntos.
- Retratos actuales: perfil `headshot_url` en `https://api.openf1.org/v1/drivers?session_key=latest`. Cache 24h servidor; jamás por visitante, con lista de hosts HTTPS permitidos, cruce por apellido único, sin usar `country_code` deprecado. Las fotos son optativas; pueden no aparecer por derechos o CDN.
- Banderas: imágenes `flagcdn.com` en vez de emojis que muestran IT/GB/DE en escritorio. Nacionalidad viene de Jolpica, no de OpenF1.
- Escuderías: recursos de marcas documentados en Wikimedia Commons para Mercedes, McLaren, Alpine, Haas, Williams, Audi, Cadillac y Red Bull Racing; el escudo de Ferrari se referencia mediante SVG Repo (vector CC0 identificado, sujeto a derechos marcarios), seleccionados por título exacto. Otras escuderías mantienen siglas diferenciadas por color si no hay un recurso verificable. Los logos actuales NO representan necesariamente la marca vigente de un constructor de décadas anteriores.
- Campeones: Jolpica `/driverstandings/1.json?limit=100` y `/constructorstandings/1.json?limit=100` (ruta compatible con Ergast), con cache de siete días. Exclusión de temporada en curso; pilotos desde 1950 y constructores desde 1958. Si proveedor devuelve datos incompletos, el historial debe indicar ausencia, no inventar campeones.
- Portada: tarjeta permanente `Fórmula 1 · Pilotos y constructores` debajo de «En foco», con enlace a la sección. La barra principal conserva su enlace a Fórmula 1.

## Restricciones de uso y responsabilidad editorial

Jolpica y OpenF1 son proveedores de terceros. **Se deben revisar sus condiciones comerciales**, especialmente porque Latente busca monetizar. La licencia de datos de Jolpica/Ergast puede imponer restricciones a usos comerciales; no se presume permiso de explotación por ser gratuita la API. Las fotos distribuidas a través de dominios asociados a Formula1 y los logotipos de terceros pueden estar protegidos por derechos de autor o de marca. La inclusión técnica de un enlace de imagen no constituye licencia comercial. Antes de monetizar áreas de F1, obtener confirmación de derechos; sustituir imágenes si el titular lo exige.

Fuentes:
- https://openf1.org/docs/#drivers
- https://github.com/jolpica/jolpica-f1/blob/main/docs/README.md
- https://commons.wikimedia.org/wiki/File:McLaren_logo_(2026).svg
- https://commons.wikimedia.org/wiki/File:Mercedes-AMG_Petronas_F1_Team_logo_(2026).svg
- https://commons.wikimedia.org/wiki/File:Red_Bull_Racing-Logo.png
- https://www.formula1.com/en/information/guidelines.4EOKE9RRqevL4niTK9kWyt

## Validación posterior

- Probar /#/sport/f1, 2026 y temporada anterior; sin mostrar retratos del año incorrecto.
- Verificar flags/caras/logo desde navegador, CSP y estado de red, especialmente links de Wikimedia Commons.
- Verificar all-time champions con 2026 excluido, carreras recientes reales, y que «En foco» no sea tapado por tarjeta F1.

## Ajuste visual del 17/10/2026: dos equipos Red Bull y orden de menú

- Header: primero fútbol (Partidos, Ligas, Posiciones, Goleadores y MLS),
  luego Dónde ver / Dónde apostar; entre los demás deportes van NBA y F1
  consecutivos y más adelante Cricket, NFL, Rugby, MLB y NHL.
  Es una **prioridad editorial**, no se afirma que proceda de estadísticas
  auditadas de audiencia global. Se reordena exclusivamente la navegación;
  no se cambian las rutas, la sección de F1 ni el acceso existente en la home.
- Red Bull Racing 2026 (Reino Unido) y Racing Bulls/VCARB (Italia)
  son dos constructores diferentes. Los nombres `Red Bull` y `Red Bull Racing`
  identifican al primero; `Racing Bulls` y `RB F1 Team` al segundo.
- Se utilizan fuentes de identificación visual de Wikipedia para ambos:
  https://en.wikipedia.org/wiki/File:Red_Bull_Racing_Logo_2026.svg
  y https://en.wikipedia.org/wiki/File:VCARB_F1_logo.svg .
  **Estas imágenes tienen restricciones de derechos declaradas por Wikipedia**,
  especialmente la del equipo italiano. La hotlink de los archivos no supone
  licencia de reutilización comercial; revisar autorización antes de explotar
  publicidad relacionada con estos emblemas. Son recursos opcionales:
  si no se cargan, permanece el fallback con iniciales.
- Los logos se aplican en las filas de pilotos, constructores, podios y
  resultados mediante el componente compartido `F1TeamLogo`.
