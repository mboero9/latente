// Bilingual presentation: Spanish content remains canonical, with explicit English
// phrases and safe rules for dynamic UI strings. No paid translation API.
import { EXTENDED_EN } from "./i18n-extended";
const dictionary: Record<string, string> = {
  "LATENTE.CFD - Clubes, Fútbol y Deportes": "LATENTE.CFD - Clubs, Football and Sports",
  "Dónde ver el partido": "Where to watch the match",
  "📺 Dónde ver · Plataformas oficiales": "📺 Watch · Official platforms",
  "📺 Ver": "📺 Watch",
  "← Volver al partido": "← Back to match",
  "Plataformas oficiales para consultar": "Official streaming platforms",
  "Otras agendas legales": "Other legal viewing schedules",
  "LATENTE.CFD · TRANSMISIONES LEGALES": "LATENTE.CFD · OFFICIAL STREAMING",
  "Pago": "Paid",
  "Gratis según evento": "Free for selected events",
  "Registro / TV paga": "Sign-in / paid TV",
  "Cargando partido…": "Loading match…",
  "Por ahora no hay una plataforma asignada a esta liga en nuestra guía. Consultá las agendas oficiales que aparecen abajo.": "We haven't mapped a platform to this league yet. Check the official schedules below.",
  "No son transmisiones confirmadas de este partido: son catálogos donde podés encontrar eventos disponibles y comprobar opciones gratuitas o de pago.": "These are not confirmed broadcasts of this match. Check the official catalogs for free or paid events.",
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
  "latente.cfd - Clubes, Fútbol y Deportes": "latente.cfd - Clubs, Football & Sports",
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
  "Último dato": "Last update",
  ...EXTENDED_EN,
};
// Brand copyright refers to the Latente website, not ownership of third-party club marks.
const originals = new WeakMap<Text, { original: string; translated: string }>();
const attributeOriginals = new WeakMap<Element, Map<string,string>>();
export function translateText(value: string): string {
  const trimmed=value.trim();
  if (!trimmed) return value;
  let translation=dictionary[trimmed];
  if (!translation) {
    translation=trimmed
      .replace(/(\d+) partidos\b/g, "$1 matches")
      .replace(/(\d+) torneos\b/g, "$1 tournaments")
      .replace(/(\d+) competiciones\b/g, "$1 competitions")
      .replace(/(\d+) goles\b/g, "$1 goals")
      .replace(/(\d+) más\b/g, "$1 more")
      .replace(/^Página (\d+)$/, "Page $1")
      .replace(/^Temporada (\d+)$/, "Season $1")
      .replace(/^Edición (\d+)$/, "Edition $1")
      .replace(/^Clubes participantes · Edición /, "Participating clubs · Season ")
      .replace(/^Resultados y próximos partidos/, "Results and upcoming fixtures")
      .replace(/^Posiciones oficiales · /, "Official standings · ")
      .replace(/^Fuente: /, "Source: ")
      .replace(/^Última importación: /, "Last import: ")
      .replace(/^Último dato: /, "Last update: ")
      .replace(/^Última consulta: /, "Last request: ")
      .replace(/^Última captura previa: /, "Last pre-match snapshot: ")
      .replace(/^Actualizado: /, "Updated: ")
      .replace(/^Importación pendiente\./, "Import pending.")
      .replace(/^Cuota decimal · /, "Decimal odds · ")
      .replace(/^Local · 1 · cuota /, "Home · 1 · odds ")
      .replace(/^Empate · X · cuota /, "Draw · X · odds ")
      .replace(/^Visitante · 2 · cuota /, "Away · 2 · odds ")
      .replace(/^M(\d+) · /, "R$1 · ")
      .replace(/^Partidos reales disponibles: /, "Available verified matches: ")
      .replace(/ · fechas consultadas: /, " · dates checked: ")
      .replace(/^La importación gratuita se completa progresivamente\./,
        "Free-tier imports are completed progressively.")
      .replace(/^Sin tabla oficial sincronizada /, "No official standings synchronized ")
      .replace(/^Esperando datos del proveedor/, "Waiting for provider data")
      .replace(/^Ver información de cuotas/, "View odds information")
      .replace(/^Catálogo temporalmente no disponible: /, "Catalogue temporarily unavailable: ")
      .replace(/^No hay partidos finalizados disponibles/, "No completed matches available")
      .replace(/^No hay partidos programados disponibles/, "No scheduled matches available")
      .replace(/^La cobertura depende de /, "Coverage depends on ")
      .replace(/^Última actualización /, "Last updated ")
      .replace(/^Datos importados, cobertura según competición/,
        "Imported data, coverage varies by competition")
      .replace(/^Archivo parcial; no es un historial completo/,
        "Partial archive; not a complete history")
      .replace(/^Cuota /, "Odds ");
  }
  return value.replace(trimmed,translation);
}
export function localizePage(language: "es" | "en") {
  document.documentElement.lang=language;
  const root=document.getElementById("app") || document.body;
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  let node:Node|null;
  while((node=walker.nextNode())) {
    const txt=node as Text;
    if(!txt.parentElement ||
        ["SCRIPT","STYLE","TEXTAREA","CODE","PRE"].includes(txt.parentElement.tagName) ||
        txt.parentElement.closest('[data-no-translate], [translate="no"]')) continue;
    const previous=originals.get(txt);
    const original=previous && txt.data===previous.translated ? previous.original : txt.data;
    const desired=language==="en"?translateText(original):original;
    if(txt.data!==desired)txt.data=desired;
    originals.set(txt,{original,translated:desired});
  }
  root.querySelectorAll(
    "[placeholder],[aria-label],[title],[aria-description],[data-tooltip],img[alt]"
  ).forEach(el=>{
    for(const attr of ["placeholder","aria-label","title","aria-description","data-tooltip","alt"]) {
      const current=el.getAttribute(attr);
      if(current==null||current==="")continue;
      let history=attributeOriginals.get(el);
      if(!history){history=new Map();attributeOriginals.set(el,history);}
      const old=history.get(attr);
      const expected=old ? translateText(old) : "";
      // If UI updated its label, treat the new string as the canonical Spanish.
      const original=old && (current===expected||current===old)?old:current;
      history.set(attr,original);
      const value=language==="en"?translateText(original):original;
      if(current!==value)el.setAttribute(attr,value);
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
