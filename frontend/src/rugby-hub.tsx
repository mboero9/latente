import { useState } from "preact/hooks";
import { useApi } from "./api";

type Match = {
  id: string; date: string; home: string; away: string;
  home_score: number | null; away_score: number | null;
  status: string; completed: boolean;
};
type Position = {
  team: string; team_id?: number; rank: number | null; group: string;
  played: number | null; won: number | null; drawn: number | null;
  lost: number | null; points: number | null;
  for: number | null; against: number | null;
};
type Competition = {
  slug: string; name: string; league_id?: number | null;
  league_name?: string | null; country?: string | null; seasons?: number[];
};
type RugbyData = {
  available: boolean; configured: boolean; provider: string;
  league_name: string; season: number; seasons: number[];
  games: Match[]; official: Position[];
  updated_at?: string; message?: string | null;
};

export function RugbyHub() {
  const [competition, setCompetition] = useState("urba");
  const [year, setYear] = useState<number | null>(null);
  const [tab, setTab] = useState<"past" | "future">("past");

  const {result: catalog, loading: catalogLoading, error: catalogError} =
    useApi<Competition[]>("/api/rugby/catalog", 3600000);
  const options = catalog?.data || [];
  const current = options.find(item => item.slug === competition);
  const params = year != null ? "?season=" + year : "";
  const {result, loading, error, retry} = useApi<RugbyData>(
    "/api/rugby/" + competition + params, 300000);
  const data = result?.data;
  const games = (data?.games || []).filter(match => tab === "past" ? match.completed : !match.completed)
    .sort((a,b) => tab === "past" ? b.date.localeCompare(a.date) : a.date.localeCompare(b.date));
  const seasons = current?.seasons?.length ? current.seasons : data?.seasons || [];
  const updated = data?.updated_at ? new Date(data.updated_at).toLocaleString("es-AR") : null;

  return <section class="sport-landing">
    <div class="view-heading"><div>
      <span class="eyebrow">LATENTE · API-RUGBY</span>
      <h1>🏉 Rugby · Torneos y selecciones</h1>
      <p>Los Pumas, clubes argentinos y grandes competiciones del mundo. Partidos, resultados y posiciones confirmadas.</p>
    </div></div>
    <div class="grid rugby-filters">
      <label class="season-label">Competición
        <select value={competition} onChange={e => {
          setCompetition(e.currentTarget.value);
          setYear(null);
        }}>
          {(options.length ? options : [
            {slug:"urba",name:"URBA · Top 12 (Argentina)"},
            {slug:"championship",name:"Rugby Championship · Los Pumas"},
            {slug:"six-nations",name:"Seis Naciones"},
            {slug:"super-rugby",name:"Super Rugby"},
            {slug:"premiership",name:"Premiership Rugby"},
            {slug:"top-14",name:"Top 14 · Francia"},
            {slug:"urc",name:"United Rugby Championship"},
            {slug:"champions",name:"European Rugby Champions Cup"},
            {slug:"test-matches",name:"Amistosos internacionales"},
            {slug:"world-cup",name:"Mundial de Rugby"}
          ]).map(item => <option key={item.slug} value={item.slug}>
            {item.name}{item.league_id === null ? " · sin cobertura confirmada" : ""}
          </option>)}
        </select>
      </label>
      <label class="season-label">Temporada
        <select value={year ?? data?.season ?? ""} disabled={!seasons.length}
          onChange={e=>setYear(Number(e.currentTarget.value))}>
          {!seasons.length && <option value="">Pendiente de catálogo</option>}
          {seasons.map(y=><option value={y} key={y}>{y}</option>)}
        </select>
      </label>
    </div>
    {catalogLoading && <p class="updated">Cargando catálogo de ligas…</p>}
    {catalogError && <p class="coverage-notice">Catálogo temporalmente no disponible: {catalogError}</p>}
    {loading ? <p>Cargando partidos y clasificaciones…</p> : error ?
      <p class="coverage-notice">{error} <button onClick={retry}>Reintentar</button></p> :
      !data?.available ? <p class="coverage-notice">
        {data?.message || "No hay datos disponibles para esta edición."}
        {!data?.configured && " La clave de API-Rugby debe estar habilitada en la cuenta."}
      </p> : null}
    <h2 class="sport-section-title">Posiciones oficiales · {data?.league_name || current?.name || "Rugby"}</h2>
    {data?.official?.length ? <div class="panel table-scroll">
      <table><thead><tr>
        <th>#</th><th>Equipo</th><th>Grupo</th><th>PJ</th><th>G</th><th>E</th><th>P</th><th>Pts</th>
      </tr></thead><tbody>{data.official.map((r,i)=><tr key={(r.team_id || r.team) + r.group}>
        <td>{r.rank ?? i+1}</td><th scope="row">{r.team}</th><td>{r.group || "—"}</td>
        <td>{r.played ?? "—"}</td><td>{r.won ?? "—"}</td><td>{r.drawn ?? "—"}</td>
        <td>{r.lost ?? "—"}</td><td>{r.points ?? "—"}</td>
      </tr>)}</tbody></table>
    </div> : <p class="coverage-notice">
      No hay posiciones oficiales verificadas para esta temporada. No se calculan puntos bonus ni desempates a partir de marcadores.
    </p>}

    <h2 class="sport-section-title">Resultados y próximos partidos</h2>
    <div class="sports-tabs" role="group">
      <button class={tab === "past" ? "active" : ""} onClick={()=>setTab("past")}>Resultados</button>
      <button class={tab === "future" ? "active" : ""} onClick={()=>setTab("future")}>Programados</button>
    </div>
    {games.length ? <div class="sports-games">{games.slice(0,70).map(m=><article class="panel sport-game" key={m.id}>
      <small class="sport-game-league">{m.date ? new Date(m.date).toLocaleDateString("es-AR") : "—"} · {m.status}</small>
      <div class="sport-game-teams"><strong class="sport-team">{m.home}</strong>
        <span>{m.home_score ?? "—"} : {m.away_score ?? "—"}</span>
        <strong class="sport-team sport-team-away">{m.away}</strong></div>
    </article>)}</div> : <p class="coverage-notice">
      No hay partidos {tab === "past" ? "finalizados" : "programados"} disponibles en la edición seleccionada.
    </p>}
    <p class="updated">Fuente: API-Rugby de API-Sports · importación y caché en PostgreSQL.
      {updated ? " Última importación: " + updated : " Importación pendiente."}
      Los datos se actualizan según la cobertura real y la cuota del proveedor.
    </p>
  </section>;
}
