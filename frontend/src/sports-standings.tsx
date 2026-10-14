import { useState } from "preact/hooks";
import { useApi } from "./api";

type Dataset = { kind: string; ref: string; updated_at: string; count: number; note: string };
type StandRow = { team_id: number | string; team: string; group: string | null;
  stage: string | null; rank: number | null; played: number | null;
  won: number | null; lost: number | null; points: number | null };
type Driver = { driver?: { name?: string }; team?: { name?: string }; position?: number; points?: number };
export function SportsStandings({ sport }: { sport: string }) {
  const { result: catalog, loading } = useApi<Dataset[]>(
    `/api/sports/${sport}/datasets`, 300000);
  const options = (catalog?.data || []).filter(d =>
    d.kind === "standings" || d.kind === "drivers" || d.kind === "constructors");
  const [selected, setSelected] = useState("");
  const current = options.find(d => d.ref === selected) || options[0];
  const { result, error } = useApi<(StandRow | Driver)[]>(
    current ? `/api/sports/${sport}/dataset?kind=${current.kind}&ref=${encodeURIComponent(current.ref)}` : null,
    360000);
  return <section class="sport-standings-block">
    <h2 class="sport-section-title">Posiciones oficiales y temporadas</h2>
    {loading ? <p>Cargando competiciones…</p> : !options.length ?
      <p class="coverage-notice">Todavía no hay posiciones oficiales sincronizadas
      para esta disciplina. Necesitamos confirmar los identificadores de liga,
      temporada y cobertura de su plan antes de publicar clasificaciones.</p>
      : <>
        <label class="season-label">Competición / temporada
          <select value={current?.ref || ""} onChange={e=>setSelected(e.currentTarget.value)}>
            {options.map(d => <option key={d.kind + d.ref} value={d.ref}>
              {d.note?.startsWith("País:") ? d.note.split(".")[0] + " · " : ""}{d.ref.replace(":", " · temporada ")} · {d.count} registros
            </option>)}
          </select>
        </label>
        {error ? <p>{error}</p> : result && <div class="panel table-scroll">
          <table><thead><tr>
            <th>#</th><th>Equipo / piloto</th><th>Grupo</th><th>PJ</th><th>G</th><th>P</th><th>Puntos</th>
          </tr></thead><tbody>{result.data.map((r, i) => {
            const isDriver = current?.kind === "drivers" || current?.kind === "constructors";
            const name = isDriver ? ((r as Driver).team?.name || (r as Driver).driver?.name || "Sin nombre informado") : (r as StandRow).team;
            return <tr key={i}><td>{isDriver ? (r as Driver).position ?? "—" : (r as StandRow).rank ?? "—"}</td>
              <th scope="row">{name}</th>
              <td>{isDriver ? (current?.kind === "constructors" ? "Constructores" : "Pilotos") : (r as StandRow).group || "—"}</td>
              <td>{isDriver ? "—" : (r as StandRow).played ?? "—"}</td>
              <td>{isDriver ? "—" : (r as StandRow).won ?? "—"}</td>
              <td>{isDriver ? "—" : (r as StandRow).lost ?? "—"}</td>
              <td>{r.points ?? "—"}</td>
            </tr>;
          })}</tbody></table>
        </div>}
        <p class="updated">Fuente API-Sports · actualizado {current.updated_at}.
        La clasificación es la que informa el proveedor para la competencia seleccionada.</p>
      </>}
    <h2 class="sport-section-title">Líderes y estadísticas históricas</h2>
    <p class="coverage-notice">Los anotadores individuales y los campeones históricos
    solo se publicarán cuando existan datos por jugador y temporada verificados
    para esta competición. No se extrapolan desde los marcadores de equipos.</p>
  </section>;
}
