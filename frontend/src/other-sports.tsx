import { useState } from "preact/hooks";
import { useApi } from "./api";
import type { League, Team } from "./types";
export const sports = [
  { slug: "nhl", name: "NHL · Hockey", emoji: "🏒" },
  { slug: "mlb", name: "MLB · Béisbol", emoji: "⚾" },
  { slug: "nba", name: "NBA", emoji: "🏀" },
  { slug: "basketball", name: "Básquet", emoji: "🏀" },
  { slug: "f1", name: "Fórmula 1", emoji: "🏎️" },
  { slug: "nfl", name: "NFL", emoji: "🏈" },
  { slug: "rugby", name: "Rugby", emoji: "🏉" },
] as const;
type SportStatus = { name: string; configured: boolean; note: string };
type Archive = { season: number; matches_loaded: number; official_leader: {team: Team;group: string}|null;leading_scorer:{name:string;goals:number;team:Team}|null;complete:boolean };
type OtherGame = {id:number|null;league:string;date:string|{start?:string};home:string;away:string;home_score:number|null;away_score:number|null;status:string};
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
  const yesterday = shift(-1), tomorrow = shift(1);
  const past = useApi<OtherGamesResponse>(sport ? `/api/sports/${sport.slug}/games?date=${yesterday}` : null, 120000);
  const today = useApi<OtherGamesResponse>(sport ? `/api/sports/${sport.slug}/games?date=${localToday}` : null, 60000);
  const future = useApi<OtherGamesResponse>(sport ? `/api/sports/${sport.slug}/games?date=${tomorrow}` : null, 120000);
  const selected = tab === "past" ? past : tab === "today" ? today : future;
  const state = selected.result?.data;
  const all = [...(past.result?.data.games || []), ...(today.result?.data.games || []), ...(future.result?.data.games || [])];
  const clubNames = Array.from(new Set(all.flatMap(game => [game.home, game.away]).filter(name => name && name !== "Local" && name !== "Visitante")));
  if (!sport) return <p>Deporte no disponible.</p>;
  return <section class="sport-landing">
    <div class="view-heading"><div><span class="eyebrow">LATENTE · DEPORTES</span>
      <h1>{sport.emoji} {sport.name}</h1>
      <p>Partidos, equipos y resultados recientes con información real del proveedor.</p></div></div>
    <div class="sports-tabs" role="group" aria-label="Elegir fecha de partidos">
      <button class={tab === "past" ? "active" : ""} onClick={() => setTab("past")}>Ayer</button>
      <button class={tab === "today" ? "active" : ""} onClick={() => setTab("today")}>Hoy</button>
      <button class={tab === "future" ? "active" : ""} onClick={() => setTab("future")}>Mañana</button>
    </div>
    {selected.loading ? <p>Cargando datos…</p> : selected.error ? <p>{selected.error} <button onClick={selected.retry}>Reintentar</button></p>
    : !state?.configured ? <article class="panel sport-intro"><h2>Integración pendiente</h2>
      <p>Verificando acceso Free. Los demás deportes usan la misma clave privada de la cuenta API-Sports, pero cada plan conserva su propia cuota y cobertura.</p>
    </article> : <>
      {state.message && <p class="coverage-notice">{state.message}</p>}
      <h2 class="sport-section-title">Partidos · {tab === "past" ? yesterday : tab === "today" ? localToday : tomorrow}</h2>
      {state.games.length ? <div class="sports-games">{state.games.map((game, idx) => <article class="panel sport-game" key={game.id ?? idx}>
        <small>{game.league || "Competición"}</small>
        <div class="sport-game-teams"><strong>{game.home}</strong><span>{game.home_score ?? "—"} : {game.away_score ?? "—"}</span><strong>{game.away}</strong></div>
        <small>{game.status || "Estado no informado"}</small>
      </article>)}</div> : <article class="panel sport-intro"><h2>No hay encuentros para esta fecha</h2>
        <p>Podés elegir ayer u otra fecha. La cobertura y las competiciones disponibles dependen del proveedor.</p>
      </article>}
      <h2 class="sport-section-title">Equipos encontrados ({clubNames.length})</h2>
      {clubNames.length ? <div class="sports-clubs">{clubNames.map(name => <span class="sports-club" key={name}>{name}</span>)}</div> :
      <p class="match-details-unavailable">Los equipos aparecerán cuando haya encuentros verificados.</p>}
      <p class="coverage-notice">Cobertura de prueba: ayer, hoy y mañana. Las estadísticas detalladas, planteles y tablas oficiales necesitan validar los endpoints específicos de cada disciplina.</p>
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
