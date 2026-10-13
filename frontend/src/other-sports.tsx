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
  const day = new Date().toLocaleDateString("en-CA", { timeZone: "America/Argentina/Buenos_Aires" });
  const { result, loading, error, retry } = useApi<OtherGamesResponse>(
    sport ? `/api/sports/${sport.slug}/games?date=${day}` : null, 60000
  );
  const state = result?.data;
  if (!sport) return <p>Deporte no disponible.</p>;
  return <section class="sport-landing">
    <div class="view-heading"><div><span class="eyebrow">LATENTE · DEPORTES</span>
      <h1>{sport.emoji} {sport.name}</h1>
      <p>Resultados y calendario · {day}</p></div></div>
    {loading ? <p>Cargando partidos…</p> : error ? <p>{error} <button onClick={retry}>Reintentar</button></p>
    : !state?.configured ? <article class="panel sport-intro"><h2>Plan Free pendiente de configurar</h2>
      <p>Este deporte requiere una suscripción gratuita independiente de API-Sports y una clave privada cargada en Railway. API-Football Pro solo habilita fútbol.</p>
      <p>No mostramos resultados inventados.</p>
    </article> : <>
      {state.message && <p class="coverage-notice">{state.message}</p>}
      {state.games.length ? <div class="sports-games">{state.games.map((game,idx)=><article class="panel sport-game" key={game.id ?? idx}>
        <small>{game.league || "Competición"}</small>
        <div class="sport-game-teams"><strong>{game.home}</strong><span>{game.home_score ?? "—"} : {game.away_score ?? "—"}</span><strong>{game.away}</strong></div>
        <small>{game.status}</small>
      </article>)}</div> : <article class="panel sport-intro"><h2>Sin encuentros disponibles</h2>
        <p>Puede no haber partidos hoy o la cobertura de este plan ser limitada.</p>
      </article>}
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
