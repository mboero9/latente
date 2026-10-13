import { useState } from "preact/hooks";
import { useApi } from "./api";
import type { League } from "./types";

type ClubMetrics = {
  team_id: number; name: string; played: number; won: number; drawn: number;
  lost: number; scored: number; conceded: number;
  goals_for_per_game: number | null; goals_against_per_game: number | null;
  combined_goals_per_game: number | null; points_per_game_estimated: number | null;
  win_rate_pct: number; official_points: number | null;
  matches_complete_vs_standings: boolean;
};
type PlayerMetrics = { player_id: number; name: string; team_id: number;
  goals: number; appearances: number | null; goals_per_appearance: number | null; };
type Snapshot = { season: number; finished_matches_available: number;
  teams: ClubMetrics[]; players: PlayerMetrics[];
  official_standings_loaded: boolean; official_scorers_loaded: boolean;
  scope: string; };
const metric = (x: number | null) => x === null ? "—" : x.toFixed(2);

export function FootballAnalytics({ league }: { league: League }) {
  const [season, setSeason] = useState(league.season);
  const { result, loading, error, retry } = useApi<Snapshot>(
    `/api/leagues/${league.id}/analytics?season=${season}`, 120000);
  const metrics = result?.data;
  return <section class="football-analytics">
    <div class="view-heading"><div><span class="eyebrow">DATOS VERIFICADOS</span>
      <h1>{league.name} · Estadísticas</h1></div>
      <label class="season-label">Temporada
        <select value={season} onChange={e => setSeason(Number(e.currentTarget.value))}>
          {(league.loaded_seasons || [league.season]).map(y => <option value={y}>{y}</option>)}
        </select></label>
    </div>
    {error && <p>{error} <button onClick={retry}>Reintentar</button></p>}
    {loading ? <p>Cargando estadísticas…</p> : metrics ? <>
      <p class="coverage-notice">Datos calculados con {metrics.finished_matches_available} partidos
      terminados importados. No incluye encuentros no disponibles ni sustituye
      posiciones oficiales o promedios de descenso.</p>
      <article class="panel"><div class="panel-top"><h2>Rendimiento por equipo</h2><span>{season}</span></div>
        <div class="table-scroll"><table><thead><tr>
          <th>Equipo</th><th>PJ</th><th>G</th><th>E</th><th>P</th>
          <th>GF/PJ</th><th>GC/PJ</th><th>Goles totales/PJ</th><th>Puntos/PJ estimados</th>
        </tr></thead><tbody>
          {metrics.teams.map(team => <tr key={team.team_id}>
            <th scope="row">{team.name}</th><td>{team.played}</td><td>{team.won}</td>
            <td>{team.drawn}</td><td>{team.lost}</td>
            <td>{metric(team.goals_for_per_game)}</td>
            <td>{metric(team.goals_against_per_game)}</td>
            <td>{metric(team.combined_goals_per_game)}</td>
            <td>{metric(team.points_per_game_estimated)}</td>
          </tr>)}
        </tbody></table></div>
      </article>
      <article class="panel"><div class="panel-top"><h2>Goles por aparición</h2>
        <small>{metrics.official_scorers_loaded ? "Goleadores oficiales del proveedor" : "Goleadores aún sin datos oficiales"}</small>
      </div><div class="table-scroll"><table><thead><tr>
        <th>Jugador</th><th>Goles</th><th>Partidos</th><th>Goles/partido</th>
      </tr></thead><tbody>{metrics.players.map(player => <tr key={player.player_id + "-" + player.team_id}>
        <th scope="row">{player.name}</th><td>{player.goals}</td>
        <td>{player.appearances ?? "—"}</td><td>{metric(player.goals_per_appearance)}</td>
      </tr>)}</tbody></table></div></article>
      <p class="updated">{metrics.scope}</p>
    </> : null}
  </section>;
}
