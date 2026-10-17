# Investigación de fuentes de rugby y roadmap para Latente — 17/10/2026

## Diagnóstico comprobado

- Railway producción `ingest` no declara variables independientes `RUGBY_API_KEY` ni `RUGBYAPI_COM_KEY`. Sí usa `API_FOOTBALL_KEY`, que el adaptador intenta reutilizar pero **no demuestra autorización de Rugby**.
- Los logs del worker muestran `api_rugby_attempts=0`, `rugbyapi_com_attempts=0` y varios ESPN `HTTP 400` para el scoreboard rugby en determinadas ventanas.
- El código usa rutas API-Rugby, ESPN, TheSportsDB y rugbyAPI.com, con caché PostgreSQL y cuotas. Tener integraciones escritas no implica que estén conectadas a un proveedor.
- Las vistas `#/sport/rugby` no mostraban clubes al no existir snapshots. Se añadió listado 2026 verificado de URBA Top 14, Torneo del Interior A (16 equipos en 4 grupos), reválidas TDI B (8 aspirantes, **NO** participantes finales), más 48 cruces publicados para las 6 fechas de TDI A. Los calendarios NO tienen resultados o puntos inventados.
- URBA pasó de **Top 12 2025 a Top 14 2026**. “Top 13” no corresponde al campeonato oficial superior 2026. Top 14 francés es una competición completamente distinta.

## API/Proveedor: precio, cobertura y uso recomendado

| Fuente | Cobertura demostrable | Condición / recomendación |
| --- | --- | --- |
| **API-Sports API-Rugby** https://api-sports.io/sports/rugby | Catálogo público 144 ligas/copas; URBA figura como `Top 12` histórico, Premiership inglés, Top14 francés, Pro D2, Champions Cup, Challenge Cup, URC, selecciones, etc. | Free 100 consultas/día cuando la cuenta habilita Rugby. Pro publicitado a USD 15/mes (intervalo promocional variable, verificar checkout). Se necesita autorización/plan de Rugby independiente del de fútbol. Backend preparado para `RUGBY_API_KEY`. Identificadores se resuelven mediante /leagues, no se adivinan. |
| **rugbyAPI.com** https://rugbyapi.com/ | 41 competiciones, incluyendo Top14 FR, Premiership, Pro D2, EPCR Champions y Challenge Cup, URC, Super Rugby y selecciones. *No* acredita clubes URBA ni TDI. | Clave Free (sin tarjeta) con 50 consultas/día y calendario actual; Archive USD49/mes; Live USD99/mes, según proveedor 17/10/2026. `RUGBYAPI_COM_KEY` en Railway `ingest`, nunca en navegador. Adaptador ya implementado. |
| **URBA oficial** https://urba.org.ar/fixture | URBA Top14 2026 con clubes, fixture y resultados | Fuente pública de **referencia**, no API JSON pública documentada de redistribución. Para ingesta automática negociá acceso/licencia con URBA; no hacer scraping agresivo ni reusar fotos/logos sin derechos. |
| **UAR oficial** https://uar.com.ar/se-confirmo-el-fixture-del-torneo-del-interior-2026/ | TDI A con 16 clubes, 4 zonas, 48 partidos de grupos; TDI B reválidas; noticias de campeones | Datos mínimos de calendario/clubes contrastados. No hay API JSON pública licenciada confirmada; automatización de resultados requiere acuerdo o proveedor comercial. |
| **LNR (Francia)** https://www.lnr.fr/presse/calendrier-des-competitions | Calendarios oficiales TOP14/ProD2; liga y fichas de clubes | Sitio web público y PDFs oficiales; no se verificó un endpoint API público autorizado con derechos de redistribución. API-Sports o rugbyAPI.com para datos comerciales. |
| **Premiership Rugby / EPCR** https://www.premiershiprugby.com/ / https://www.epcrugby.com/ | Fixtures, scores, clubes, EPCR Champions/Challenge | Páginas oficiales de referencia; no se confirmó API pública documentada con permiso comercial. Preferir proveedor con licencia. |
| **ESPN público / TheSportsDB** | Algunas ligas, temporadas y scores | Fallback no contractual, puede fallar o variar; marcar cobertura y no depender de ellos para datos en vivo. |

## Proveedores premium y acceso federativo (investigación complementaria)

- **Sportradar Rugby Union v3** documenta `GET /rugby-union/{trial|production}/v3/en/competitions.json`, calendario, temporadas, jugadores, resultados y push de eventos. Es un candidato **empresarial** para ampliar cobertura y SLA, pero hay que solicitar trial/cotización y comprobar mediante catálogo si URBA y UAR están incluidos: https://developer.sportradar.com/rugby/reference/rugby-competitions. No se contratará ahora.
- **URBA, 31/08/2026** anunció una plataforma nueva de video y estadísticas utilizada por clubes/URBA, también para Top14 y Primera A/B/C. Esto crea una vía concreta para **solicitar acceso comercial a datos** directamente a la Unión: https://urba.org.ar/noticias/nueva-plataforma-de-analisis-de-video-y-estadisticas-de-la-urba. No se verificó API pública ni licencia para terceros.
- **LNR** manifestó que su operador de estadísticas suministra datos estructurados a sus socios autorizados mediante API/portales. Eso no equivale a una API anónima de libre consumo para Latente: https://www.lnr.fr/actualite/consultation-pour-la-selection-de-loperateur-de-statistiques-sportives-de-la-lnr.
- rugbyAPI.com es ideal para ligas internacionales de clubes; no muestra URBA/TDI en su catálogo de 41 competiciones.
- Para competencia nacional conviene primero **API-Sports Rugby**, validar si su antiguo rótulo `Top12` tiene partidos nuevos de URBA 2026 sin asumir que cambió automáticamente a 14 participantes.

## Prioridad técnica 30 días

1. Conectar Free API-Sports Rugby **con autorización válida** y validar `GET /leagues`, `/games?league=...&season=2026`, `/standings` contra URBA, Top14 francés, Premiership, EPCR y URC; verificar primer snapshot en PostgreSQL. Si la URBA no publica el Top14 2026 actualizado, no mostrar Top12 histórico como torneo vigente.
2. Opcionalmente generar Free key en rugbyAPI.com y añadir `RUGBYAPI_COM_KEY` a Railway ingestion. No suscribirse a Archive/Live sin prueba de valor y licencia.
3. Negociar con URBA/UAR por API o export periódico autorizado para fixture/resultados locales; mientras tanto usar enlaces oficiales y club rosters 2026.
4. Pantallas de datos: tablas con bonus points entregados por proveedor, últimas novedades y clubes, sin fabricar escudos oficiales ni partidos.
5. Medir latencia, cuota y cobertura por liga por 7 días. Resolver discrepancias de alias/country del proveedor mediante IDs verificados.

## Monetización y riesgo

- AdSense muestra anuncios **solo** cuando sitio/cuenta están aprobados. La etiqueta en el HTML no significa `READY`; verificar en panel AdSense > Sitios > `latente.cfd`. La prueba de este estado **no** se puede realizar con Google Ads ni con Windsor.ai.
- Google Publisher Policies restringe inventario sin contenido editorial significativo; estadística replicada sin aporte de valor y páginas “en construcción” pueden obstaculizar aprobación. Publicar contenido explicativo original, fuentes, metodología, política de privacidad real, información del responsable, verificación, consentimiento y control de publicidad.
- Se prepararon tres espacios de anuncio, sin activarlos ni cargar IDs de ubicaciones inventados; no incluir AdSense en sección de apuestas.
- Para conseguir ingresos antes del tráfico orgánico, ofrecer patrocinio de clubes, academias, equipamiento, tiendas deportivas y marcas regionales con contactos directos. No prometer impresiones sin medición.
- Afiliados de equipamiento: evaluar Sovrn Commerce/Netshoes Argentina, Decathlon, programas de tiendas deportivas (sujeto a aprobación); **no** publicar URL de tracking que no pertenezca a una cuenta afiliada aprobada.
- Evitar automatizar campañas pagas con conversión = pageview. Gastos de Google Ads se restan, no se registran como facturación. No activar servicios pagos ni acuerdos exclusivos sin aprobación.
- Riesgos legales y AdSense: sección de cuotas/apuestas necesita auditoría separada por políticas y licencias en Argentina.

Referencias: 
- https://api-sports.io/sports/rugby
- https://rugbyapi.com/coverage y https://rugbyapi.com/pricing
- https://urba.org.ar/fixture
- https://uar.com.ar/se-confirmo-el-fixture-del-torneo-del-interior-2026/
- https://www.lnr.fr/presse/calendrier-des-competitions
- https://support.google.com/adsense/answer/12170222
- https://support.google.com/adsense/answer/10502938
- https://commerce.sovrn.com/merchants/38140/netshoes.com-affiliate-program

### Meta 90 días, escenarios NO GARANTIZADOS
Con tráfico actual solo 1.193 vistas entre 16/9 y 15/10, en realidad concentradas 13–15/10, no hay una serie mensual orgánica estable.
- Conservador: 2k, 4k, 8k vistas por mes, primer mes sin aprobación, RPM USD0,5 desde mes 2, 0 patrocinios = USD6 en 90 días.
- Base: 4k, 12k, 30k, RPM USD1,5 desde mes 2, primer patrocinio hipotético USD40 en mes 3 = USD103.
- Optimista (exigente): 8k, 25k, 60k, RPM USD2,5 desde mes 2, patrocinio hipotético USD100 mes 3 = USD312,50.
- Suponiendo USD40/mes de costo operativo, 90 días cuestan USD120, **sin** Google Ads, proveedores extra, impuestos ni comisiones. Tres escenarios netos aproximados: -USD114, -USD17, +USD192,50.
- Estos escenarios no predicen visitas y el RPM puede ser significativamente menor dependiendo de geografía. Hasta que AdSense diga `READY`, ingreso publicitario real puede ser cero. La meta neta USD250/mes requiere ventas directas o mucho mayor tráfico.
