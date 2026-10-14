import { useApi } from "./api";

type AnnualRow = {
  team_id: number;
  team: { id: number; name: string };
  rank: number; played: number; won: number; drawn: number; lost: number;
  goals_for: number; goals_against: number; difference: number; points: number;
};
export function ArgentinaAnnual() {
  const { result, loading, error, retry } = useApi<AnnualRow[]>("/api/leagues/128/annual?season=2026", 60000);
  return <section>
    <div class="view-heading"><div><span class="eyebrow">FÚTBOL ARGENTINO</span>
      <h1>Tabla anual 2026</h1></div></div>
    <p class="coverage-notice"><strong>Clasificación parcial no oficial.</strong> Incluye únicamente los partidos de Primera División finalizados e importados en Latente. No contempla sanciones, deducciones ni todos los reglamentos del descenso. Partidos utilizados: {result?.meta.matches_used ?? "—"}.</p>
    {loading ? <p>Cargando partidos…</p> : error ? <p>{error} <button onClick={retry}>Reintentar</button></p>
    : !result?.data.length ? <p>No hay resultados suficientes para calcular una tabla anual.</p> :
    <div class="panel table-scroll"><table><thead><tr>
      <th>#</th><th>Equipo</th><th>PJ</th><th>G</th><th>E</th><th>P</th><th>DG</th><th>Pts.</th>
    </tr></thead><tbody>{result.data.map(row=><tr key={row.team_id}>
      <td>{row.rank}</td><th scope="row">{row.team.name}</th><td>{row.played}</td>
      <td>{row.won}</td><td>{row.drawn}</td><td>{row.lost}</td>
      <td>{row.difference}</td><td>{row.points}</td>
    </tr>)}</tbody></table></div>}
  </section>;
}
