import { useState } from "preact/hooks";
import { useApi } from "./api";
import { SportsStandings } from "./sports-standings";
import { WatchGuide } from "./watch-guide";
import { RugbyCompetitions } from "./rugby-competitions";
import { ReferenceSportPage } from "./reference-sports";
import { RugbyHub } from "./rugby-hub";
import { TeamMark } from "./team-mark";
import { SportCountryExplorer, countryForGame, matchesCompetition,
  normalizedSportCountry, type SportCompetition } from "./sport-country-explorer";
import type { League, Team } from "./types";
export const sports = [
  { slug: "nhl", name: "NHL · Hockey", emoji: "🏒" },
  { slug: "mlb", name: "MLB · Béisbol", emoji: "⚾" },
  { slug: "nba", name: "NBA", emoji: "🏀" },
  { slug: "wnba", name: "WNBA", emoji: "🏀" },
  { slug: "basketball", name: "Liga Argentina", emoji: "🏀" },
  { slug: "handball", name: "Handball", emoji: "🤾" },
  { slug: "volleyball", name: "Vóley", emoji: "🏐" },
  { slug: "f1", name: "Fórmula 1", emoji: "🏎️" },
  { slug: "nfl", name: "NFL", emoji: "🏈" },
  { slug: "rugby", name: "Rugby", emoji: "🏉" },
  { slug: "cricket", name: "Cricket", emoji: "🏏" },
] as const;
/** Consultas oficiales: no se conoce la señal del partido individual. */
type SportStatus = { name: string; configured: boolean; note: string };
type Archive = { season: number; matches_loaded: number; official_leader: {team: Team;group: string}|null;leading_scorer:{name:string;goals:number;team:Team}|null;complete:boolean };
type OtherGame = {id:number|null;league_id?:number|string|null;country?:string|null;home_id?:number|null;away_id?:number|null;league:string;date:string|{start?:string};home:string;away:string;home_logo?:string|null;away_logo?:string|null;league_logo?:string|null;home_score:number|null;away_score:number|null;status:string};
type OtherGamesResponse = {configured:boolean;games:OtherGame[];message:string|null};
export function SportPage({ slug }: { slug: string }) {
  const sport = sports.find(x => x.slug === slug);
  const [tab, setTab] = useState<"past" | "today" | "future">("today");
  const multiCountry = ["basketball", "volleyball", "handball"].includes(slug);
  const [country, setCountry] = useState("Argentina");
  const [competition, setCompetition] = useState("all");
  const {result:leagueCatalog,loading:catalogLoading} = useApi<SportCompetition[]>(
    multiCountry ? `/api/sports/${slug}/competitions` : null, 300000);
  const competitions=leagueCatalog?.data||[];
  const localToday = new Date().toLocaleDateString("en-CA", { timeZone: "America/Argentina/Buenos_Aires" });
  const shift = (days: number) => {
    const date = new Date(localToday + "T12:00:00Z");
    date.setUTCDate(date.getUTCDate() + days);
    return date.toISOString().slice(0, 10);
  };
  const {result, loading, error, retry} = useApi<{
    matches: OtherGame[]; dates_checked: string[]; snapshot_count: number;
    period: {from:string;to:string};
  }>(sport && !["f1", "nba", "cricket", "mlb", "nhl", "nfl", "wnba"].includes(slug) ? `/api/sports/${sport.slug}/overview` : null, 120000);
  const all = result?.data.matches || [];
  // Only imported fixtures, scoped to the explicitly chosen country/league.
  // A federation link alone never becomes a fake schedule or league table.
  const filtered = all.filter(game =>
    (!multiCountry || country==="all" ||
      countryForGame(game,competitions)===normalizedSportCountry(country)) &&
    (!multiCountry || matchesCompetition(game,competition,competitions)));
  const dateOf = (game: OtherGame) =>
    typeof game.date === "string"
      ? game.date.slice(0,10)
      : game.date?.start?.slice(0,10) || "";
  const visible = filtered.filter(game => {
    const day = dateOf(game);
    if (tab === "past") return day < localToday;
    if (tab === "future") return day > localToday;
    return day === localToday;
  }).sort((a,b) => tab === "past"
    ? dateOf(b).localeCompare(dateOf(a))
    : dateOf(a).localeCompare(dateOf(b)));
  const clubs = new Map<string, string | null>();
  for (const game of filtered) {
    if (game.home && game.home !== "Local") clubs.set(game.home, game.home_logo || clubs.get(game.home) || null);
    if (game.away && game.away !== "Visitante") clubs.set(game.away, game.away_logo || clubs.get(game.away) || null);
  }
  // Estadísticas derivadas exclusivamente de resultados finales reales
  // presentes en la ventana de ayer/hoy/mañana. No son tablas oficiales.
  const results = filtered.filter(game =>
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
  if (slug === "rugby") return <RugbyHub />;
  if (["f1", "nba", "wnba", "mlb", "nhl", "nfl", "cricket"].includes(slug)) return <ReferenceSportPage slug={slug} />;
  return <section class="sport-landing">
    <div class="view-heading"><div><span class="eyebrow">LATENTE · DEPORTES</span>
      <h1>{slug==="basketball"
        ? <><img class="sport-competition-mark" src="/lab-mark.svg" width="42" height="42"
            alt="" aria-hidden="true" />{sport.name}</>
        : <>{sport.emoji} {sport.name}</>}</h1>
      <p>{slug==="basketball"
        ? "Liga Argentina de Básquetbol (LAB). Partidos y equipos con datos verificados; también podés consultar otras ligas desde los filtros."
        : "Partidos, equipos y resultados recientes con información real del proveedor."}</p></div></div>
    {multiCountry && <SportCountryExplorer sport={slug} country={country}
      onCountry={setCountry} league={competition} onLeague={setCompetition}
      competitions={competitions} loading={catalogLoading} numberOfGames={filtered.length}/>}
    <div class="sports-tabs" role="group" aria-label="Elegir fecha de partidos">
      <button class={tab === "past" ? "active" : ""} onClick={() => setTab("past")}>Resultados</button>
      <button class={tab === "today" ? "active" : ""} onClick={() => setTab("today")}>Hoy</button>
      <button class={tab === "future" ? "active" : ""} onClick={() => setTab("future")}>Próximos</button>
    </div>
    {loading ? <p>Cargando partidos del archivo…</p> : error ? <p>{error} <button onClick={retry}>Reintentar</button></p>
    : <>
      <p class="updated">Partidos reales disponibles para la selección: {filtered.length} · fechas consultadas: {result?.data.dates_checked.length ?? 0}. La importación gratuita se completa progresivamente.</p>
      <h2 class="sport-section-title">{tab === "past" ? "Últimos resultados" : tab === "today" ? "Partidos de hoy" : "Próximos encuentros"}</h2>
      {visible.length ? <div class="sports-games">{visible.map((game, idx) => <article class="panel sport-game" key={game.id ?? idx}>
        <small class="sport-game-league">{game.league_logo && <img src={game.league_logo} alt="" loading="lazy" onError={e => {e.currentTarget.style.display = "none";}}/>}{game.league || "Competición"}</small>
        <div class="sport-game-teams">
          <strong class="sport-team"><TeamMark name={game.home} logo={game.home_logo} sport={slug} teamId={game.home_id}/>{game.home}</strong>
          <span>{game.home_score ?? "—"} : {game.away_score ?? "—"}</span>
          <strong class="sport-team sport-team-away"><TeamMark name={game.away} logo={game.away_logo} sport={slug} teamId={game.away_id}/>{game.away}</strong>
        </div>
        <small>{game.status || "Estado no informado"}</small>

      </article>)}</div> : <article class="panel sport-intro"><h2>No hay encuentros para esta fecha</h2>
        <p>Probá Resultados o Próximos. El proveedor puede no cubrir esta competencia o temporada en el plan gratuito.</p>
      </article>}
      <>
      <h2 class="sport-section-title">Equipos encontrados ({clubs.size})</h2>
      {clubs.size ? <div class="sports-clubs">{Array.from(clubs.entries()).map(([name, logo]) => <span class="sports-club" key={name}><TeamMark name={name} logo={logo} />{name}</span>)}</div> :
      <p class="match-details-unavailable">Los equipos aparecerán cuando haya encuentros verificados.</p>}
      <h2 class="sport-section-title">Rendimiento reciente · datos parciales</h2>
      <p class="updated">Ranking calculado solo con resultados finales verificados de los días consultados; no representa las posiciones de la temporada ni los récords históricos.</p>
      {ranking.length ? <div class="panel sport-record-table" role="table" aria-label="Victorias en la ventana disponible">
        <div class="sport-record-row sport-record-heading" role="row"><span>Equipo</span><span>PJ</span><span>G</span><span>A favor</span></div>
        {ranking.map(([name, data]) => <div class="sport-record-row" role="row" key={name}>
          <strong class="sport-team-inline"><TeamMark name={name} logo={clubs.get(name)}/>{name}</strong><span>{data.played}</span><span>{data.wins}</span><span>{data.scored}</span>
        </div>)}
      </div> : <p class="match-details-unavailable">No hay suficientes resultados finales en la ventana para calcular estadísticas fiables.</p>}
      </>
      {slug === "rugby" && <RugbyCompetitions />}
      <SportsStandings sport={sport.slug} country={multiCountry?country:"all"}
        leagueSelection={multiCountry?competition:"all"}
        competitions={multiCountry?competitions:[]}/>
      <WatchGuide initialSport={slug} />
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
