import { useApi } from "./api";
import type { Match } from "./types";
type Feed = { recent: Match[]; upcoming: Match[] };
function GameList({ matches, upcoming }: { matches: Match[]; upcoming: boolean }) {
  return matches.length ? <div class="league-recent-games">
    {matches.map(m => <a href={`#/match/${m.id}`} class="league-recent-game" key={m.id}>
      <span class="league-recent-date">{new Date(m.kickoff).toLocaleDateString("es-AR", {day: "2-digit", month: "2-digit"})}</span>
      <span class="league-recent-team">{m.home.name}</span>
      <strong>{m.home_goals ?? "–"} : {m.away_goals ?? "–"}</strong>
      <span class="league-recent-team">{m.away.name}</span>
      <span class="league-recent-detail">{upcoming ? "Programado" : m.status}</span>
    </a>)}
  </div> : <p class="updated">Todavía no hay encuentros de esta sección importados para la temporada.</p>;
}
export function LeagueRecent({ id, season }: { id: number; season: number }) {
  const {result, loading, error} = useApi<Feed>(`/api/leagues/${id}/recent?season=${season}`, 120000);
  return <section class="league-recent-section">
    <h2>Últimos resultados y próximos partidos</h2>
    <p class="updated">Solo resultados reales sincronizados; no inventamos encuentros ni marcadores.</p>
    {loading ? <p>Cargando últimos partidos…</p> : error ? <p>No se pudo consultar el calendario.</p> : <>
      <h3>Últimos 12 partidos terminados</h3>
      <GameList matches={result?.data.recent || []} upcoming={false}/>
      <h3>Próximos 12 encuentros programados</h3>
      <GameList matches={result?.data.upcoming || []} upcoming={true}/>
    </>}
  </section>;
}
