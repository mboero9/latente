# Básquet FIBA, Vóley y Handball — países y ligas argentinas

Estado: 17/10/2026.

## Navegación

- Las páginas `/#/sport/basketball`, `/#/sport/volleyball` y
  `/#/sport/handball` abren inicialmente con **Argentina**.
- El selector permite cambiar a otro país, Europa o Internacional, o a
  **Todos los países**, y luego a una competición específica.
- `/api/sports/{sport}/competitions` consulta **solo PostgreSQL**:
  combina un conjunto reducido de competiciones verificadas en webs
  federativas con los nombres, países, temporadas e IDs **reales** del
  catálogo `/leagues` de API-Sports que importa el cron.
- Un nombre de liga encontrado en el catálogo NO prueba que el plan
  contratado permita importar fixtures o clasificaciones. Cada ficha
  distingue «Fuente federativa · sin feed confirmado», «En catálogo API ·
  resultados no confirmados» y «Datos importados».
- Los partidos, equipos, rendimientos parciales y tablas se filtran
  de acuerdo al país/competición. No se muestran como argentinos
  los encuentros sin país verificado, salvo que el catálogo real
  permita resolver su ID de liga sin ambigüedad.
- En celular las ligas usan tarjetas de una columna y los controles
  de filtro se apilan verticalmente.

## Argentina: competiciones respaldadas por organizadores

**Básquet** (Confederación y Asociación de Clubes):
- Liga Nacional de Básquet: https://www.laliganacional.com.ar/
- Liga Argentina de Básquet (ascenso):
  https://www.laliganacional.com.ar/ligaargentina/

**Vóley** (ACLAV y FeVA):
- Superliga Argentina de Vóley 2026/27, nombre que reemplaza a la LVA:
  https://www.aclav.com/public/web/noticia/4481
  Calendario: https://aclav.com/public/web/calendario/100
- Liga Argentina Femenina (LAF):
  https://feva.org.ar/torneos/ligas-feva/liga-argentina-femenina
- Liga Nacional Masculina y Liga Nacional Femenina (FeVA):
  https://feva-web.dataproject.com/MainHome.aspx

**Handball** (Confederación Argentina y FeMeBal):
- Torneos Nacionales de Clubes Adultos A y B:
  https://handballargentina.org/cah/calendario-de-competencias-2026/
- Liga de Honor Hipotecario Seguros y Liga de Honor Plata,
  metropolitanas, ambas ramas:
  https://femebal.com/fixtures-disponibles-para-la-liga-hipotecario-seguros-y-la-liga-plata/

## Qué no se hizo

No se contrató ninguna API ni servicio nuevo, no se publicó scraping
automático de portales federativos y no se inventó ningún resultado,
posición, fixture, plantel ni ID de API. Si un torneo tiene un calendario
oficial pero todavía no aparece en la API, la web enlaza al organizador
y sigue mostrando ese estado hasta sincronizar datos autorizados.

El cron existente descubre ligas por nombre **y país**, priorizando
en cada disciplina los IDs argentinos encontrados y manteniendo
competencias internacionales, con un máximo de tres objetivos
automáticos para estas disciplinas y una cuota conservadora por deporte.
Este ajuste no garantiza que la fuente cubra la temporada o el endpoint.
