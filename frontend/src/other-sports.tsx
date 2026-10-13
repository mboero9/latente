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
export function SportPage({ slug }: { slug: string }) {
  const sport = sports.find(x => x.slug === slug);
  const { result, loading } = useApi<SportStatus[]>("/api/sports/status", 60_000);
  if (!sport) return <p>Deporte no disponible.</p>;
  const configured = result?.data.find(x => x.name === sport.slug)?.configured;
  return <section class="panel sport-landing">
    <span class="eyebrow">LATENTE · DEPORTES</span>
    <h1>{sport.emoji} {sport.name}</h1>
    <h2>{configured ? "Fuente configurada" : "Integración de datos pendiente"}</h2>
    <p>{loading ? "Comprobando conexión…" : configured
      ? "La credencial de este deporte está configurada en Railway. Todavía hay que validar la cobertura y sincronizar los resultados."
      : "Este deporte requiere su propio plan gratuito de API-Sports y una clave específica en Railway. La suscripción Pro de fútbol no habilita los demás deportes."}</p>
    <p>No mostramos resultados inventados. Los próximos pasos son integrar calendarios, marcadores y clasificaciones reales para cada disciplina.</p>
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
