# APIs para la próxima etapa de Latente

Verificación: 12 de octubre de 2026. Fútbol continúa siendo la prioridad. Estos proveedores fueron investigados; todavía no están integrados ni contratados.

| Proveedor | Cobertura verificada | Aplicación posible en Latente | Consideración |
| --- | --- | --- | --- |
| [BALLDONTLIE](https://www.balldontlie.io/docs/) | NBA, WNBA, MLB, NHL; también EuroLeague y otras ligas de básquet | Opción inicial para las cuatro ligas estadounidenses solicitadas | Validar el plan que habilita estadísticas, vivo y endpoints por liga; no asumir que el acceso gratuito incluye todo |
| [API-SPORTS](https://api-sports.io/) | API de NBA; básquet internacional; MLB en Baseball y NHL en Hockey | Reutilizar parte del adaptador que ya usa fútbol, conservando hosts y cuotas por deporte | La cobertura detallada depende de competición, temporada y endpoint; no se confirmó WNBA en su catálogo público de Basketball |
| [Tank01](https://www.tank01.com/) | NBA, WNBA, MLB, NHL y NFL, con box scores, calendarios y posiciones | Alternativa para estadísticas norteamericanas | Se distribuye por RapidAPI y sus planes son por liga; revisar cargos por excedentes antes de contratar |

Fuentes oficiales de cobertura: [Basketball API-SPORTS](https://api-sports.io/sports/basketball), [MLB en Baseball](https://api-sports.io/sports/baseball), [NHL en Hockey](https://api-sports.io/sports/hockey), [WNBA BALLDONTLIE](https://wnba.balldontlie.io/), [MLB BALLDONTLIE](https://mlb.balldontlie.io/), [NHL BALLDONTLIE](https://nhl.balldontlie.io/).

Recomendación provisional: evaluar BALLDONTLIE para NBA/WNBA/MLB/NHL con una prueba de endpoints reales, cobertura histórica y latencia; API-SPORTS para sumar básquet internacional al mismo ecosistema de fútbol. Esta recomendación requiere revisar precios y permisos de publicación al momento de activar cada deporte. No hay compromiso de compra.

La actualización de la pantalla puede seguir siendo cada cinco segundos. Eso no convierte en datos cada cinco segundos un feed publicado con otra frecuencia. Comparar fecha del evento, fecha de actualización del proveedor y fecha de ingesta para medir la latencia efectiva.

Antes de ampliar: nombres de deporte/proveedor en las claves, cuotas separadas, score por cuartos/innings/sets, estadísticas y posiciones específicas por disciplina. No mezclar identificadores o reglas de fútbol con otras ligas.
