// Lightweight bilingual presentation layer; original Spanish content remains canonical.
// Avoids extra translation services or external API usage.
const dictionary: Record<string, string> = {
  "Partidos": "Matches",
  "Ligas": "Leagues",
  "Posiciones": "Standings",
  "Goleadores": "Top scorers",
  "Equipos": "Teams",
  "COMPETICIONES": "COMPETITIONS",
  "ARGENTINA": "ARGENTINA",
  "INTERNACIONAL": "INTERNATIONAL",
  "Todos los partidos": "All matches",
  "Buscar liga": "Search leagues",
  "Buscar una liga o un país": "Search for a league or country",
  "Buscar equipo": "Search teams",
  "Explorar todas las ligas": "Explore all leagues",
  "FÚTBOL, DE ACÁ Y DEL MUNDO": "FOOTBALL, HERE AND WORLDWIDE",
  "LA JORNADA": "MATCHDAY",
  "EN FOCO": "SPOTLIGHT",
  "En juego": "Live",
  "En vivo": "Live",
  "Todos": "All",
  "Hoy": "Today",
  "Ayer": "Yesterday",
  "Mañana": "Tomorrow",
  "Horarios": "Time zone",
  "Hora argentina": "Argentina time",
  "Tabla": "Table",
  "Temporada": "Season",
  "Ligas y copas": "Leagues and cups",
  "EL MAPA DEL FÚTBOL": "THE FOOTBALL MAP",
  "Mostrar más ligas": "Show more leagues",
  "Equipo": "Team",
  "Jugador": "Player",
  "Goles": "Goals",
  "Asist.": "Assists",
  "Penales": "Penalties",
  "Estadio": "Stadium",
  "Ciudad": "City",
  "Fundación": "Founded",
  "Capacidad": "Capacity",
  "Próximos partidos": "Upcoming matches",
  "Últimos partidos": "Recent matches",
  "Últimos 5": "Last 5",
  "Cargando datos…": "Loading data…",
  "Reintentar": "Retry",
  "Sin datos": "No data",
  "Ver partido": "View match",
  "Datos demorados": "Delayed data",
  "Demorado": "Delayed",
  "Siguiente": "Next",
  "Anterior": "Previous",
  "Ver equipo": "View team",
  "Volver a partidos": "Back to matches",
  "Sin partidos para esta fecha": "No matches on this date",
  "Todavía no hay una tabla disponible": "Standings are not available yet",
  "Sin goleadores disponibles": "Top scorers are not available",
  "No encontramos equipos": "No teams found",
  "No hay ligas disponibles": "No leagues available",
  "Estadísticas del partido": "Match statistics",
  "Todavía no hay estadísticas": "Statistics not available yet",
  "Sin cobertura estadística": "No statistics coverage",
  "Los resultados se actualizan solos": "Scores update automatically",
  "La carrera por el gol": "Top scorer race",
  "Partido": "Match",
  "Resultados": "Results",
  "Saltar al contenido": "Skip to content",
  "Navegación principal": "Main navigation",
  "Secciones de": "Sections of",
  "Elegir fecha de partidos": "Choose match date",
  "Filtrar competiciones": "Filter competitions",
  "No hay partidos sincronizados": "No synchronized matches",
  "Actualización automática detenida": "Automatic updates stopped",
  "Algunas actualizaciones están demoradas": "Some updates are delayed",
  "API-Football limita algunas fechas o temporadas de tu plan": "API-Football restricts some dates or seasons on your plan",
  "No hay partidos disponibles para hoy": "No matches available today",
  "La clave funciona, pero el proveedor rechazó ciertas consultas por el plan contratado. Railway Hobby no amplía la cobertura de API-Football.": "The API key works, but your API-Football plan restricts some queries. Railway Hobby does not extend API-Football coverage.",
  "Mostramos los últimos datos recibidos. Revisá la hora de actualización.": "Showing the latest received data. Check the last update time.",
  "El catálogo puede estar cargado, aunque API-Football todavía no haya entregado encuentros para esta fecha.": "The league catalog is available, but API-Football has not provided matches for this date.",
  "Los marcadores se consultan automáticamente. La frescura depende de la cobertura y del plan de datos.": "Scores refresh automatically. Freshness depends on provider coverage and your data plan.",
  "Revisá la búsqueda o el estado de la sincronización.": "Check your search or synchronization status.",
  "Probá otro nombre o esperá a la primera sincronización.": "Try another name or wait for the first synchronization.",
  "Puede tratarse de una copa eliminatoria o de datos pendientes de sincronización.": "This may be a knockout competition or data awaiting synchronization.",
  "Las estadísticas aparecerán al completar la sincronización.": "Statistics will appear when synchronization completes.",
  "La fuente de datos puede tener cobertura limitada.": "The data provider may have limited coverage.",
  "La información no está disponible todavía.": "Information is not available yet.",
  "Los valores ausentes no se cuentan como cero.": "Missing values are not treated as zero.",
  "Esperando datos del proveedor": "Waiting for provider data",
  "Datos ficticios de demostración": "Fictional demo data",
  "Hora": "Time",
  "Fecha": "Date",
  "Minutos": "Minutes",
  "País": "Country",
  "Ver más": "See more",
  "Puntos": "Points",
  "Ganados": "Won",
  "Empatados": "Drawn",
  "Perdidos": "Lost",
  "Diferencia": "Difference",
  "Ligas disponibles": "Available leagues",
  "Ver tabla": "View standings",
  "Todos los derechos reservados.": "All rights reserved.",
  "Algunas fechas o temporadas no están disponibles": "Some dates or seasons are unavailable",
  "Algunos datos están restringidos por el plan de cobertura contratado.": "Some data is restricted by the current coverage plan.",
  "Las ligas están disponibles, pero todavía no hay partidos recibidos para esta fecha.": "Leagues are available, but no matches have been received for this date yet.",
  "Tabla parcial, no oficial.": "Partial, unofficial standings.",
  "Goles, tarjetas y jugadas": "Goals, cards and incidents",
  "Formación y táctica en cancha": "Starting lineup and tactical formation",
  "Jugador destacado": "Featured player",
  "Once inicial": "Starting XI",
  "Esquema sin informar": "Formation unavailable",
  "No hay posiciones en cancha informadas.": "Pitch positions not available.",
  "Once inicial todavía no disponible.": "Starting XI is not available yet.",
  "Ocultar suplentes": "Hide substitutes",
  "Las alineaciones y el dibujo táctico aparecerán cuando estén disponibles en los datos del encuentro.": "Lineups and tactics will appear when match data is available.",
  "Todavía no hay incidencias confirmadas para este encuentro.": "No confirmed match events are available yet.",
  "No hay calificaciones de jugadores para identificar un destacado. No asignamos un MVP sin datos.": "No player ratings are available. We do not select an MVP without data.",
  "Calificación del proveedor, no necesariamente MVP oficial.": "Provider rating; not necessarily the official MVP.",
  "Tarjeta": "Card",
  "Gol": "Goal",
  "Gol de penal": "Penalty goal",
  "Gol en contra": "Own goal",
  "Cambio": "Substitution",
  "Incidencia": "Event",
  "Último dato": "Last update"
};
// Brand copyright refers to the Latente website, not ownership of third-party club marks.
const originals = new WeakMap<Text, { original: string; translated: string }>();
const placeholders = new WeakMap<Element, string>();
const translate = (value: string) => {
  const trim = value.trim();
  if (!trim) return value;
  let target = dictionary[trim];
  if (!target) {
    target = trim.replace(/(\d+) partidos\b/g, "$1 matches")
      .replace(/(\d+) torneos\b/g, "$1 tournaments")
      .replace(/^Página (\d+)$/, "Page $1")
      .replace(/^Temporada (\d+)$/, "Season $1")
      .replace(/^Último dato: /, "Last update: ")
      .replace(/^Explorar todas las ligas \((\d+)\)$/, "Explore all leagues ($1)");
  }
  return value.replace(trim, target);
};
export function localizePage(language: "es" | "en") {
  document.documentElement.lang = language;
  const root = document.getElementById("app") || document.body;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node: Node | null;
  while ((node = walker.nextNode())) {
    const text = node as Text;
    if (!text.parentElement || ["SCRIPT", "STYLE", "TEXTAREA"].includes(text.parentElement.tagName)) continue;
    const saved = originals.get(text);
    const original = saved && text.data === saved.translated ? saved.original : text.data;
    const desired = language === "en" ? translate(original) : original;
    if (text.data !== desired) text.data = desired;
    originals.set(text, { original, translated: desired });
  }
  root.querySelectorAll("input[placeholder], input[aria-label], button[aria-label]").forEach((el) => {
    for (const attr of ["placeholder", "aria-label"]) {
      const current = el.getAttribute(attr);
      if (!current) continue;
      const key = attr === "placeholder" ? "placeholder" : "aria-label";
      const original = placeholders.get(el) || current;
      if (key === "placeholder") placeholders.set(el, original);
      el.setAttribute(attr, language === "en" ? translate(original) : original);
    }
  });
}
export function observeLanguage(language: "es" | "en") {
  localizePage(language);
  const root = document.getElementById("app") || document.body;
  let working = false;
  const observer = new MutationObserver(() => {
    if (working) return;
    working = true;
    observer.disconnect();
    try { localizePage(language); }
    finally { observer.observe(root, { subtree: true, childList: true, characterData: true }); working = false; }
  });
  observer.observe(root, { subtree: true, childList: true, characterData: true });
  return () => observer.disconnect();
}
