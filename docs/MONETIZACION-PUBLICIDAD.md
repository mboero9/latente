# Monetización publicitaria de Latente

## Etapa inicial: tres espacios discretos

Este cambio prepara **tres ubicaciones** en el frontend, sin afectar el contenido deportivo:
1. `top`: horizontal debajo de la barra de utilidades y antes de los resultados.
2. `side`: rectángulo en la columna de resúmenes, solo en la vista de partidos en escritorio.
3. `bottom`: horizontal antes del pie de página.

La vista móvil muestra dos espacios horizontales y oculta el lateral. No se agregan anuncios en `#/bet`, por la sensibilidad de las secciones de apuestas. Los anuncios se etiquetan **Anuncios**, se mantienen separados de enlaces y botones, y se cargan solo al acercarse al viewport. Los demás módulos de deportes y estadísticas no se alteran.

## Estado actual y activación

**La verificación del sitio AdSense está instalada con el publisher ID que entregó el propietario; las tres ubicaciones de anuncios permanecen apagadas por defecto.**
Durante `npm run dev` se muestra una representación neutral para comprobar ubicaciones. En producción permanece invisible hasta una aprobación real y configuración explícita.

Valores de compilación (públicos, jamás inventar ni usar claves privadas):

```dotenv
VITE_AD_SLOTS_PREVIEW=false
VITE_ADSENSE_CLIENT=ca-pub-9760821039036895
VITE_ADSENSE_SLOT_TOP=XXXXXXXXXX
VITE_ADSENSE_SLOT_SIDE=XXXXXXXXXX
VITE_ADSENSE_SLOT_BOTTOM=XXXXXXXXXX
VITE_ADS_PRIVACY_READY=false
VITE_ADSENSE_ENABLED=false
```

`VITE_ADSENSE_ENABLED=true` + `VITE_ADS_PRIVACY_READY=true` + ID publicador y ID del espacio válidos activan solicitudes de publicidad en el frontend. **No cambies esos dos flags aún**.

Antes de activarlos:
- Completar la verificación/revisión de `https://latente.cfd/` en Google AdSense. ID del publicador ya confirmado: `ca-pub-9760821039036895`; faltan los IDs reales de los tres espacios. Google Ads (campañas pagas) y AdSense (ingresos del sitio) son servicios separados.
- `/ads.txt` está publicado con el registro directo Google para `pub-9760821039036895`. Validar en Google AdSense si se exige alguna otra línea o corrección.
- Crear o adaptar una **política de privacidad** y configurar una CMP certificada por Google cuando corresponda a tráfico EEE, Reino Unido o Suiza; la bandera `VITE_ADS_PRIVACY_READY` no reemplaza la implementación de consentimiento.
- Para verificación, CSP de Nginx/Cloudflare **solo habilita el script inicial** `pagead2.googlesyndication.com` y se agregó meta de propiedad adicional. Para servir anuncios completos hay que migrar a la **CSP estricta con nonces por respuesta** recomendada por Google; una simple lista de dominios no es suficiente. No habilitar los tres bloques aún.
- Comprobar la experiencia real en móvil, la estabilidad visual, carga y la política de ubicaciones publicitarias; usar report-only durante la puesta en marcha.
- Configurar los `VITE_` durante **build**, no después de generar `frontend/dist`. Si se usa Docker, pasar `--build-arg` o usar argumentos de build del proveedor; nunca añadir una cuenta inventada al código.


### Estado de verificación (17/10/2026)

- Código en el `<head>` de `frontend/index.html`:
  `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9760821039036895`.
- Verificación adicional con meta `google-adsense-account`.
- Archivo `frontend/public/ads.txt`: `google.com, pub-9760821039036895, DIRECT, f08c47fec0942fa0`.
- **Acción del titular:** en AdSense > Sitios > `latente.cfd`, marcar que ya instalaste el código, elegir `Verificar` y luego `Solicitar revisión`. Si AdSense dice que falla, guardar captura o mensaje exacto. No se puede aprobar el sitio desde GitHub/Railway.
- **Advertencia:** el código AdSense global puede llegar a mostrar anuncios automáticos si el usuario habilitó *Auto ads* en el panel; dejar apagada esa opción y no activar los tres slots hasta completar privacidad/CMP y la CSP estricta. Los componentes manuales están deshabilitados mediante flags.

## Estrategia de comercialización

Comenzar con AdSense **solo cuando esté aprobado** y antes de contratar intermediarios de AdX que cobren una comisión de ingresos. Considerar Google Ad Manager y un partner MCM/AdX si el inventario llega a un volumen suficiente para negociar y medir mejoras reales. Validar al partner en la [lista de Google Certified Publishing Partners](https://www.google.com/ads/publisher/partners/find-a-partner/).

Situación medida de Latente en GA4, 16/09 al 15/10 de 2026: 932 usuarios activos, 998 sesiones y 1193 páginas vistas. El 90,6% de sesiones se atribuye a búsqueda paga y buena parte proviene de India, Bangladesh e Indonesia. Sin tráfico orgánico y visitas recurrentes no conviene aumentar la cantidad de anuncios.

Calcular ingresos sobre páginas vistas y RPM neto real: `ingreso = páginas_vistas / 1000 * RPM`.
Ejemplo hipotético con un RPM de USD 1/3/5:
- 1.193 vistas: USD 1,19 / 3,58 / 5,97 mensuales.
- 100.000 vistas: USD 100 / 300 / 500 mensuales.
No hay ingresos garantizados ni un RPM uniforme entre países.

## Seguimiento

Comparar semanalmente: páginas vistas totales, orgánicas vs. pagas, porcentaje de usuarios recurrentes, impresiones efectivamente monetizables, viewability, RPM de página, ingreso neto, margen luego de campañas/costos de API/Railway, y Core Web Vitals. Deshabilitar las posiciones que empeoren UX sin mejora de rendimiento.

**No tomar estimaciones de ingresos de promiedos.com.ar como facturación real**: los sitios de valoración externa publican proyecciones incompatibles entre sí, sin datos de sus cuentas publicitarias.

## Referencias oficiales

- AdSense elegibilidad: https://support.google.com/adsense/answer/9724
- Ubicaciones publicitarias: https://support.google.com/adsense/answer/1346295
- Etiquetado de anuncios: mismo documento de ubicaciones.
- Integrar AdSense con CSP: https://support.google.com/adsense/answer/16283098
- Requisitos CMP: https://support.google.com/adsense/answer/13554116
- Partners certificados: https://www.google.com/ads/publisher/partners/find-a-partner/
