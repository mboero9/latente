import { useState } from "preact/hooks";
import { useApi } from "./api";
import { SportsStandings } from "./sports-standings";
import { RugbyCompetitions } from "./rugby-competitions";
import { ReferenceSportPage } from "./reference-sports";
import type { League, Team } from "./types";
export const sports = [
  { slug: "nhl", name: "NHL · Hockey", emoji: "🏒" },
  { slug: "mlb", name: "MLB · Béisbol", emoji: "⚾" },
  { slug: "nba", name: "NBA", emoji: "🏀" },
  { slug: "basketball", name: "Básquet", emoji: "🏀" },
  { slug: "f1", name: "Fórmula 1", emoji: "🏎️" },
  { slug: "nfl", name: "NFL", emoji: "🏈" },
  { slug: "rugby", name: "Rugby", emoji: "🏉" },
  { slug: "afl", name: "AFL · Fútbol australiano", emoji: "🏉" },
  { slug: "cricket", name: "Cricket", emoji: "🏏" },
] as const;
/** Consultas oficiales: no se conoce la señal del partido individual. */
const officialStreaming: Record<string, { name: string; url: string; access: string }> = {
  nba: { name: "NBA League Pass", url: "https://www.nba.com/watch/league-pass-stream/", access: "Pago" },
  nfl: { name: "NFL Game Pass · DAZN", url: "https://www.dazn.com/", access: "Pago" },
  nhl: { name: "NHL · dónde ver", url: "https://www.nhl.com/info/how-to-watch-and-stream-nhl-games", access: "Guía oficial" },
  mlb: { name: "MLB.TV", url: "https://www.mlb.com/live-stream-games", access: "Pago" },
  f1: { name: "F1 TV", url: "https://f1tv.formula1.com/", access: "Pago" },
  rugby: { name: "RugbyPass TV", url: "https://info.rugbypass.tv/", access: "Gratis según evento" },
  afl: { name: "Watch AFL", url: "https://www.watchafl.com.au/", access: "Pago" },
  basketball: { name: "Disney+ · ESPN", url: "https://www.disneyplus.com/es-ar", access: "Pago / según torneo" },
};
type SportStatus = { name: string; configured: boolean; note: string };
type Archive = { season: number; matches_loaded: number; official_leader: {team: Team;group: string}|null;leading_scorer:{name:string;goals:number;team:Team}|null;complete:boolean };
type OtherGame = {id:number|null;league:string;date:string|{start?:string};home:string;away:string;home_logo?:string|null;away_logo?:string|null;league_logo?:string|null;home_score:number|null;away_score:number|null;status:string};
type OtherGamesResponse = {configured:boolean;games:OtherGame[];message:string|null};
export function SportPage({ slug }: { slug: string }) {
  const sport = sports.find(x => x.slug === slug);
  const [tab, setTab] = useState<"past" | "today" | "future">("today");
  const localToday = new Date().toLocaleDateString("en-CA", { timeZone: "America/Argentina/Buenos_Aires" });
  const shift = (days: number) => {
    const date = new Date(localToday + "T12:00:00Z");
    date.setUTCDate(date.getUTCDate() + days);
    return date.toISOString().slice(0, 10);
  };
  const {result, loading, error, retry} = useApi<{
    matches: OtherGame[]; dates_checked: string[]; snapshot_count: number;
    period: {from:string;to:string};
  }>(sport && !["f1", "nba", "cricket"].includes(slug) ? `/api/sports/${sport.slug}/overview` : null, 120000);
  const all = result?.data.matches || [];
  const dateOf = (game: OtherGame) =>
    typeof game.date === "string"
      ? game.date.slice(0,10)
      : game.date?.start?.slice(0,10) || "";
  const visible = all.filter(game => {
    const day = dateOf(game);
    if (tab === "past") return day < localToday;
    if (tab === "future") return day > localToday;
    return day === localToday;
  }).sort((a,b) => tab === "past"
    ? dateOf(b).localeCompare(dateOf(a))
    : dateOf(a).localeCompare(dateOf(b)));
  const clubs = new Map<string, string | null>();
  for (const game of all) {
    if (game.home && game.home !== "Local") clubs.set(game.home, game.home_logo || clubs.get(game.home) || null);
    if (game.away && game.away !== "Visitante") clubs.set(game.away, game.away_logo || clubs.get(game.away) || null);
  }
  // Estadísticas derivadas exclusivamente de resultados finales reales
  // presentes en la ventana de ayer/hoy/mañana. No son tablas oficiales.
  const results = all.filter(game =>
    typeof game.home_score === "number" &&
    typeof game.away_score === "number" &&
    /(^ft$|final|finished|ended|completed|after overtime|after penalties|full time)/i.test(game.status || "")
  );
  const recent = new Map<string, { wins: number; played: number; scored: number; conceded: number }>();
  if (slug !== "f1") for (const game of results) {
    for (const [team, own, against] of [
      [game.home, game.home_score!, game.away_score!],
      [game.away, game.away_score!, game.home_score!],
    ] as const) {
      if (!team || team === "Local" || team === "Visitante") continue;
      const item = recent.get(team) || { wins: 0, played: 0, scored: 0, conceded: 0 };
      item.played++;
      item.scored += own;
      item.conceded += against;
      if (own > against) item.wins++;
      recent.set(team, item);
    }
  }
  const ranking = Array.from(recent.entries()).sort((a, b) =>
    b[1].wins - a[1].wins || b[1].scored - a[1].scored || a[0].localeCompare(b[0])
  ).slice(0, 12);
  if (!sport) return <p>Deporte no disponible.</p>;
  if (["f1", "nba", "cricket"].includes(slug)) return <ReferenceSportPage slug={slug} />;
  return <section class="sport-landing">
    <div class="view-heading"><div><span class="eyebrow">LATENTE · DEPORTES</span>
      <h1>{sport.emoji} {sport.name}</h1>
      <p>Partidos, equipos y resultados recientes con información real del proveedor.</p></div></div>
    <div class="sports-tabs" role="group" aria-label="Elegir fecha de partidos">
      <button class={tab === "past" ? "active" : ""} onClick={() => setTab("past")}>Resultados</button>
      <button class={tab === "today" ? "active" : ""} onClick={() => setTab("today")}>Hoy</button>
      <button class={tab === "future" ? "active" : ""} onClick={() => setTab("future")}>Próximos</button>
    </div>
    {loading ? <p>Cargando partidos del archivo…</p> : error ? <p>{error} <button onClick={retry}>Reintentar</button></p>
    : <>
      <p class="updated">Partidos reales disponibles: {all.length} · fechas consultadas: {result?.data.dates_checked.length ?? 0}. La importación gratuita se completa progresivamente.</p>
      <h2 class="sport-section-title">{tab === "past" ? "Últimos resultados" : tab === "today" ? "Partidos de hoy" : "Próximos encuentros"}</h2>
      {visible.length ? <div class="sports-games">{visible.map((game, idx) => <article class="panel sport-game" key={game.id ?? idx}>
        <small class="sport-game-league">{game.league_logo && <img src={game.league_logo} alt="" loading="lazy" onError={e => {e.currentTarget.style.display = "none";}}/>}{game.league || "Competición"}</small>
        <div class="sport-game-teams">
          <strong class="sport-team">{game.home_logo && <img src={game.home_logo} alt="" loading="lazy" onError={e => {e.currentTarget.style.display = "none";}}/>}{game.home}</strong>
          <span>{game.home_score ?? "—"} : {game.away_score ?? "—"}</span>
          <strong class="sport-team sport-team-away">{game.away_logo && <img src={game.away_logo} alt="" loading="lazy" onError={e => {e.currentTarget.style.display = "none";}}/>}{game.away}</strong>
        </div>
        <small>{game.status || "Estado no informado"}</small>
        {officialStreaming[slug] && <a class="sport-watch-link"
          href={officialStreaming[slug].url} target="_blank" rel="noopener noreferrer"
          title="Plataforma oficial: este partido concreto puede no estar incluido en su programación">
          📺 Consultar {officialStreaming[slug].name} ↗
          <span>({officialStreaming[slug].access}; señal del partido sin confirmar)</span>
        </a>}
      </article>)}</div> : <article class="panel sport-intro"><h2>No hay encuentros para esta fecha</h2>
        <p>Probá Resultados o Próximos. El proveedor puede no cubrir esta competencia o temporada en el plan gratuito.</p>
      </article>}
      <h2 class="sport-section-title">Equipos encontrados ({clubs.size})</h2>
      {clubs.size ? <div class="sports-clubs">{Array.from(clubs.entries()).map(([name, logo]) => <span class="sports-club" key={name}>{logo && <img src={logo} alt="" loading="lazy" onError={e=>{e.currentTarget.style.display="none";}}/>}{name}</span>)}</div> :
      <p class="match-details-unavailable">Los equipos aparecerán cuando haya encuentros verificados.</p>}
      <h2 class="sport-section-title">Rendimiento reciente · datos parciales</h2>
      <p class="updated">Ranking calculado solo con resultados finales verificados de los días consultados; no representa las posiciones de la temporada ni los récords históricos.</p>
      {ranking.length ? <div class="panel sport-record-table" role="table" aria-label="Victorias en la ventana disponible">
        <div class="sport-record-row sport-record-heading" role="row"><span>Equipo</span><span>PJ</span><span>G</span><span>A favor</span></div>
        {ranking.map(([name, data]) => <div class="sport-record-row" role="row" key={name}>
          <strong>{name}</strong><span>{data.played}</span><span>{data.wins}</span><span>{data.scored}</span>
        </div>)}
      </div> : <p class="match-details-unavailable">No hay suficientes resultados finales en la ventana para calcular estadísticas fiables.</p>}
      {slug === "rugby" && <RugbyCompetitions />}
      <SportsStandings sport={sport.slug} />
    </>}
  </section>;
}
export function HistoryPage({ league }: { league: League }) {
  const { result, loading, error } = useApi<Archive[]>(`/api/leagues/${league.id}/history`, 60_000);
  return <section class="history-section">
    <div class="view-heading"><div><span class="eyebrow">ARCHIVO DEPORTIVO</span><h1>{league.name} · Históricos</h1></div></div>
    {loading ? <p>Cargando temporadas…</p> : error ? <p>{error}</p> : result?.data.length ?
    <div class="historic-grid">{result.data.map(row => <article class="panel historic-card" key={row.season}>
      <h2>Temporada {row.season}</h2>
      <p><strong>{row.matches_loaded}</strong> partidos finalizados guardados</p>
      {row.official_leader && <p>Primero en su grupo: <strong>{row.official_leader.team.name}</strong></p>}
      {row.leading_scorer && <p>Goleador: <strong>{row.leading_scorer.name}</strong> ({row.leading_scorer.goals})</p>}
      <small>{row.complete ? "Datos importados, cobertura según competición" : "Archivo parcial; no es un historial completo"}</small>
    </article>)}</div> : <div class="panel sport-landing"><h2>Archivo en preparación</h2><p>Los años anteriores se incorporarán progresivamente desde fuentes verificadas.</p></div>}
  </section>;
}
