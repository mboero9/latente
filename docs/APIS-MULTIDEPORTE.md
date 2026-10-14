# APIs para la próxima etapa de Latente

Verificación: 14 de octubre de 2026. Fútbol continúa siendo la prioridad. Los proveedores comerciales de la tabla siguen sin estar contratados; se incorporaron fuentes de referencia públicas y caché servidor para que las vistas no dependan exclusivamente de API-Sports.

| Proveedor | Cobertura verificada | Aplicación posible en Latente | Consideración |
| --- | --- | --- | --- |
| [BALLDONTLIE](https://www.balldontlie.io/docs/) | NBA, WNBA, MLB, NHL; también EuroLeague y otras ligas de básquet | Opción inicial para las cuatro ligas estadounidenses solicitadas | Validar el plan que habilita estadísticas, vivo y endpoints por liga; no asumir que el acceso gratuito incluye todo |
| [API-SPORTS](https://api-sports.io/) | API de NBA; básquet internacional; MLB en Baseball y NHL en Hockey | Reutilizar parte del adaptador que ya usa fútbol, conservando hosts y cuotas por deporte | La cobertura detallada depende de competición, temporada y endpoint; no se confirmó WNBA en su catálogo público de Basketball |
| [Tank01](https://www.tank01.com/) | NBA, WNBA, MLB, NHL y NFL, con box scores, calendarios y posiciones | Alternativa para estadísticas norteamericanas | Se distribuye por RapidAPI y sus planes son por liga; revisar cargos por excedentes antes de contratar |

Fuentes oficiales de cobertura: [Basketball API-SPORTS](https://api-sports.io/sports/basketball), [MLB en Baseball](https://api-sports.io/sports/baseball), [NHL en Hockey](https://api-sports.io/sports/hockey), [WNBA BALLDONTLIE](https://wnba.balldontlie.io/), [MLB BALLDONTLIE](https://mlb.balldontlie.io/), [NHL BALLDONTLIE](https://nhl.balldontlie.io/).

Recomendación provisional: evaluar BALLDONTLIE para NBA/WNBA/MLB/NHL con una prueba de endpoints reales, cobertura histórica y latencia; API-SPORTS para sumar básquet internacional al mismo ecosistema de fútbol. Esta recomendación requiere revisar precios y permisos de publicación al momento de activar cada deporte. No hay compromiso de compra.

La actualización de la pantalla puede seguir siendo cada cinco segundos. Eso no convierte en datos cada cinco segundos un feed publicado con otra frecuencia. Comparar fecha del evento, fecha de actualización del proveedor y fecha de ingesta para medir la latencia efectiva.

Antes de ampliar: nombres de deporte/proveedor en las claves, cuotas separadas, score por cuartos/innings/sets, estadísticas y posiciones específicas por disciplina. No mezclar identificadores o reglas de fútbol con otras ligas.


## Integraciones añadidas (14-10-2026)

- `/api/reference/f1?season=2026`: Jolpica/Ergast, tabla completa de pilotos y constructores, último Gran Premio y próximo evento si el proveedor lo entrega.
- `/api/reference/nba?season=2025`: clasificaciones de temporada regular de ESPN, temporadas históricas disponibles desde 2010 (año de inicio de la temporada). Campeones recientes verificados en NBA.com.
- `/api/reference/nhl`, `/api/reference/mlb`, `/api/reference/nfl`, `/api/reference/wnba`: tablas deportivas mediante ESPN, con temporadas desde 2015. **No equivalen a resultados en vivo ni garantizan la disponibilidad de archivos antiguos.**
- `/api/reference/cricket?competition=ipl`: solicita a ESPN clasificaciones de IPL/ICC si esa competición está cubierta; opcionalmente consulta partidos en CricketData si `CRICKETDATA_API_KEY` está configurada **solo en el backend**. Sin clave se muestra la tabla ICC T20 fechada del 13/10/2026, como referencia histórica y no como ranking en vivo.
- `/api/leagues/128/alltime`: tabla argentina acumulada construida con resultados reales **ya importados**, usando 3 puntos por victoria en todas las épocas. Es **parcial** y no equivale a una tabla completa desde 1891. Se enlaza a Promiedos como fuente externa para la historia completa.

Las peticiones de referencia quedan en un caché en memoria del proceso: una actualización por vencimiento (60 min F1 y cricket, 3 h NBA y ligas de EE.UU.; 5 min cuando la fuente no está disponible). No se crean datos simulados cuando un proveedor devuelve error. El caché de memoria se reinicia al desplegar o escalar; para más réplicas conviene pasarlo a Redis/PostgreSQL.

La interfaz muestra claramente la temporada, procedencia y limitaciones. Los proveedores ESPN/Jolpica son fuentes públicas con endpoints no garantizados contractualmente; revisar condiciones de uso y licencia de publicación antes de monetizar o incrementar tráfico.
