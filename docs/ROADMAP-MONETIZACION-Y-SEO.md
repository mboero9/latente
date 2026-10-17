# Latente: hoja de ruta de crecimiento y monetización (2026–2028)

Última revisión: 16 de octubre de 2026. Documento de trabajo, no garantía de ingresos.

## Objetivo

Convertir Latente en un portal deportivo de consulta recurrente y un negocio medible. No copiar datos, diseño ni contenido editorial de Promiedos: usar su hábito de visita como referencia y diferenciarnos por cobertura multideporte, rapidez, estadísticas profundas, personalización y transparencia.

## Línea de base verificada

Fuente: GA4 y Google Ads consultados mediante Windsor.ai, 16 de septiembre a 15 de octubre de 2026:
- 932 usuarios activos, 998 sesiones, 1193 vistas de página (actividad de GA4 registrada principalmente el 13–15 de octubre).
- 904 sesiones atribuidas a Paid Search (90,6%); 59 Direct, 1 Organic Social.
- 454 usuarios activos desde India; 7 desde Argentina.
- Google Ads: ARS 11.368,49 en gasto, 1.120 clics, 688 conversiones de **vista de página** (NO ventas).
- GA4 no registra ingresos de compras en ese período.

Nota: sesiones, usuarios, visitas y páginas vistas no son medidas intercambiables. Los datos externos sobre Promiedos de Semrush/Similarweb son estimaciones independientes, no sus reportes privados.

## Fase 0 — Preparación de AdSense (ahora)

[x] Tres posiciones discretas en el frontend: banner superior, lateral desktop y banner inferior; opción desactivada.
[x] Documentación de activación y control de privacidad; pruebas de integración.
[x] Páginas informativas de **Sobre Latente** y **Fuentes y metodología** (sujeto a validación del PR).
[ ] Publicar una **política de privacidad precisa** con nombre/razón de responsable y canal privado de contacto verificado. No publicar un email inventado.
[ ] Comprobar HTTPS, accesibilidad, experiencia móvil, errores 404 y calidad de datos.
[ ] Crear o confirmar cuenta de editor en https://www.google.com/adsense/start/ (no confundir con Google Ads).
[ ] En AdSense > Sitios > Añadir `latente.cfd`, obtener meta de verificación/ID real, verificar propiedad y solicitar revisión.
[ ] Configurar CMP Google-certified (consentimiento EEE/Reino Unido/Suiza cuando corresponda).
[ ] Configurar CSP de Nginx/Cloudflare compatible con script de AdSense sin dejar el sitio abierto indiscriminadamente.
[ ] Publicar `/ads.txt` con la línea real del editor (no colocar ID de ejemplo).
[ ] Obtener ID del publicador y tres slots de AdSense; habilitar gradualmente **solo después** de aprobación y privacidad.
[ ] Medir impacto en Core Web Vitals, ingresos, vista de anuncios, porcentaje de usuarios recurrentes.

## Fase 1 — Ganar tráfico orgánico (primeros 90 días)

Prioridad P0: el frontend usa navegación de fragmentos `#/...` y sitemap con URL principal. Google Search Central recomienda History API y URLs reales, y preferiblemente HTML visible para indexación. **No agregar URLs hash al sitemap.** Diseñar:
- `/liga/{slug}` para fixture, posiciones, goleadores, estadísticas y contexto editorial;
- `/equipo/{slug}`, `/partido/{id}` y `/deporte/{slug}` con contenidos públicos individuales;
- títulos, descripciones, canonicals, H1 y enlaces internos por ruta;
- renderizado indexable (SSR/prerender) de páginas estables para no depender de JavaScript;
- sitemap dinámico desde PostgreSQL, excluyendo ligas o partidos sin información verificable;
- schema.org `SportsEvent` donde corresponda, sin datos inventados;
- estrategia de cache CDN, API y presupuesto de datos para evitar picos de costo.

Contenido diferencial: texto original de contexto para las ligas y cómo funcionan tablas/promedios, glosarios útiles, explicación estadística, rugby argentino e internacional, NBA, F1 y deportes menos atendidos, con revisión editorial humana.

Objetivo *aspiracional*: 10.000 vistas/mes con 30%+ tráfico orgánico/directo; primero corregir datos de baja calidad antes de perseguir volumen.

## Fase 2 — Monetización inicial (3 a 6 meses)

- AdSense en máximo tres posiciones; medir RPM de página, cobertura y viewability sin clics incentivados ni anuncios engañosos.
- Una oferta de patrocinio directo para casas de equipamiento y servicios deportivos, no poner anuncios encubiertos.
- Crear `/publicidad` con inventario, audiencias y canal privado de contacto comercial, cuando se verifiquen identidad y email del proyecto.
- Medir ingresos netos después de comisiones, Cloudflare/Railway, proveedor deportivo y adquisición.
- Dejar campañas de adquisición activas **solo si el costo de adquirir tráfico tiene retorno medido**.
- Seguimiento mensual de ROI: ingreso ads + patrocinios + afiliados - costos de infra/API - gasto en adquisición.

## Fase 3 — Redes premium (6 a 18 meses)

- **Journey by Mediavine**: actualmente mínimo de 1.000 sesiones/30 días de mercados premium (EEE no implica premium automáticamente), además de contenido original, calidad e integridad.
- **Raptive**: 25.000+ páginas vistas/mes, 50% de US/UK/CA/AU/NZ (entre 25k y 99.999), 40% para 100k+, antigüedad de dominio y contenido editorial original, especialmente extenso.
- **Playwire**: sugiere 100.000+ páginas vistas mensuales para retorno de plataforma, con preferencia por un 20% de tráfico estadounidense.
- **Google Ad Manager/AdX**: evaluar partners verificados mediante contrato, porcentaje neto para editor, términos de exclusividad, mínimos, cobros y prueba A/B real de page RPM. Más demanda no garantiza más ingresos.
- No migrar entre redes solo por el eCPM prometido: comparar **page RPM neto** con control de geografía, temporada, velocidad y fill.

## Fase 4 — Escala nacional e internacional (12–36+ meses)

- Personalización: ligas y equipos favoritos, alertas consentidas, idioma y zona horaria.
- Aplicación/PWA sin autoplay invasivo y caché offline para fixtures consultados.
- Centro de datos con calidad verificada, histórico profundo, registro de cambios y estado de las fuentes.
- Infraestructura: cache/CDN, rate limiting, CDN de imágenes, monitoreo (latencia p95), costos por 1.000 vistas, límites de consultas externas, pruebas de carga, colas y resiliencia multi-sitio cuando tenga sentido económico.
- Aliados editoriales, SEO, comunidad, newsletters consentidos y acuerdos de marca.
- Con objetivos escalonados medidos **mensualmente**: 10.000 → 100.000 → 500.000 → 1M vistas → 5M visitas → 10M visitas. No se promete competir con Promiedos en 24 meses.

## Ingresos hipotéticos y punto de equilibrio

Modelo `ingreso bruto = páginas_vistas/1000 * RPM neto` (RPM neto por página hipotético USD 1/3/5):
- 1.193 vistas -> USD 1,19 / 3,58 / 5,97
- 10.000 vistas -> USD 10 / 30 / 50
- 100.000 vistas -> USD 100 / 300 / 500
- 500.000 vistas -> USD 500 / 1500 / 2500

Con USD 40 de costos operativos mensuales estimados (sin gasto adicional en adquisición), para USD 250 netos se requieren USD 290 brutos: 290.000 vistas a USD 1 RPM, 96.667 a USD 3 y 58.000 a USD 5. Validar costos y RPM reales antes de fijar presupuestos.

## Referencias

- https://support.google.com/adsense/answer/12169212?hl=es
- https://support.google.com/adsense/answer/9724?hl=es
- https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
- https://www.mediavine.com/application-requirements/
- https://help.raptive.com/hc/en-us/articles/360032840891-Who-is-eligible-for-Raptive
- https://www.playwire.com/qualification-criteria
