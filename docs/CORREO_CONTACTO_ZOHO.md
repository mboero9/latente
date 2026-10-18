# Correo comercial de Latente · contacto@latente.cfd

Estado: **pendiente de alta en Zoho y verificación de DNS**. Esta documentación no implica que la casilla funcione ni que se haya cambiado el DNS.

## Alta segura

1. Consultar el plan **Forever Free** en https://www.zoho.com/es-xl/mail/zohomail-pricing.html . Ofrece 1 dominio, hasta 5 usuarios y 5 GB por usuario, solo webmail y **solo en centros de datos seleccionados**. Confirmar disponibilidad para la región del titular antes de continuar.
2. Crear la organización en Zoho Mail y vincular **latente.cfd** en la consola de administración: https://mailadmin.zoho.com/ . Crear el usuario **contacto@latente.cfd**.
3. Verificar la propiedad del dominio. Zoho ofrece autorización DNS de Cloudflare («Login to my DNS», Domain Connect) o TXT/CNAME de verificación; copiar **solo los valores concretos** que muestre Zoho para esa organización.
4. Revisar en Cloudflare el servicio **Email Routing** y los MX existentes. **No combinar MX de Cloudflare Routing con MX de Zoho para el mismo dominio** y no borrar reenvíos sin comprobar qué direcciones dependen de ellos. Preparar la transición y respaldar registros.
5. Tras confirmar el usuario y el plan, activar los MX indicados por Zoho para el centro de datos correspondiente (no asumir que siempre terminan en .com). Configurar **un solo SPF TXT** en el dominio combinando emisores legítimos, DKIM con el selector y clave exactos provistos por Zoho y DMARC inicialmente en modo observación. En Cloudflare, registros mail en DNS only si corresponde.
6. Ejecutar pruebas en ambos sentidos (Gmail -> contacto@, contacto@ -> Gmail), confirmar SPF/DKIM/DMARC alineados y que ninguna dirección anterior dejó de recibir mensajes. Solo entonces publicar la dirección como contacto comercial o remitir propuestas.

Documentación: https://www.zoho.com/mail/help/adminconsole/cloudflare.html .

## Propuesta de apertura comercial

Asunto: Propuesta de colaboración publicitaria · Latente.cfd

Hola, equipo de Partnerships:

Les escribimos desde Latente.cfd, un portal deportivo independiente de resultados, estadísticas, tablas de posiciones y seguimiento del fútbol argentino e internacional.

Estamos evaluando colaboraciones con operadores autorizados que cumplan los requisitos legales y publicitarios aplicables. Queríamos conocer sus condiciones para patrocinio, acuerdos directos y, si corresponde, afiliación con una prueba inicial de 30 días.

¿Podrían indicarnos el contacto adecuado de Marketing, Partnerships o Afiliados?

Muchas gracias.
Equipo Latente

> No enviar propuestas desde contacto@latente.cfd antes de validar recepción, envío y autenticación del dominio.
