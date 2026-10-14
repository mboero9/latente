import { useState } from "preact/hooks";
import { useApi } from "./api";

type Match = {id:string;date:string;home:string;away:string;
  home_score:number|null;away_score:number|null;status:string;completed:boolean};
type Row = {name?:string;team?:string;group?:string;rank?:number;
  pj?:number;g?:number;e?:number;p?:number;for?:number;against?:number;
  wins?:number;losses?:number};
type Rugby = {available:boolean;league_name:string;season:number;games:Match[];
  official:Row[];statistics:Row[];updated_at?:string;message?:string;stale?:boolean};
const competitions = [
  ["urba","URBA Top 14 · Argentina"],["championship","Rugby Championship · Los Pumas"],
  ["six-nations","Seis Naciones"],["super-rugby","Super Rugby Pacific"],
  ["premiership","Premiership Rugby"],["top-14","Top 14 · Francia"],
  ["urc","United Rugby Championship"],["champions","Champions Cup"],
  ["test-matches","Tests internacionales"],["world-cup","Mundial de Rugby"]
];
const current = new Date().getFullYear();
export function RugbyHub() {
  const [competition,setCompetition] = useState("urba");
  const [season,setSeason] = useState(current);
  const [tab,setTab] = useState<"past"|"future">("past");
  const {result,loading,error,retry} = useApi<Rugby>(
    `/api/rugby/${competition}?season=${season}`, 1800000);
  const data = result?.data;
  const games = (data?.games||[]).filter(match=>tab==="past"?match.completed:!match.completed)
    .sort((a,b)=>tab==="past"?b.date.localeCompare(a.date):a.date.localeCompare(b.date));
  return <section class="sport-landing">
    <div class="view-heading"><div>
      <span class="eyebrow">LATENTE · RUGBY</span><h1>🏉 Rugby · Torneos y selecciones</h1>
      <p>Los Pumas, URBA, Rugby Championship, Six Nations y las principales ligas del mundo.</p>
    </div></div>
    <div class="grid rugby-filters">
      <label class="season-label">Competición
        <select value={competition} onChange={e=>setCompetition(e.currentTarget.value)}>
          {competitions.map(([id,name])=><option key={id} value={id}>{name}</option>)}
        </select>
      </label>
      <label class="season-label">Temporada
        <select value={season} onChange={e=>setSeason(Number(e.currentTarget.value))}>
          {Array.from({length:7},(_,i)=>current+1-i).map(y=><option key={y} value={y}>{y}</option>)}
        </select>
      </label>
    </div>
    {loading?<p>Cargando datos de rugby…</p>:error?
      <p class="coverage-notice">{error} <button onClick={retry}>Reintentar</button></p>:
      !data?.available?<p class="coverage-notice">{data?.message||"No hay datos verificados para esta temporada."} La disponibilidad depende del proveedor.</p>:null}
    <h2 class="sport-section-title">Posiciones y estadísticas · {data?.league_name||"Rugby"}</h2>
    {data?.official?.length ? <div class="panel table-scroll">
      <table><thead><tr><th>#</th><th>Equipo</th><th>Grupo</th><th>G</th><th>P</th></tr></thead>
      <tbody>{data.official.map((r,i)=><tr key={r.name||i}>
        <td>{r.rank??i+1}</td><th scope="row">{r.name}</th>
        <td>{r.group||"—"}</td><td>{r.wins??"—"}</td><td>{r.losses??"—"}</td>
      </tr>)}</tbody></table>
    </div> : data?.statistics?.length ? <>
      <p class="coverage-notice">Estadísticas parciales calculadas desde los partidos finalizados que devolvió ESPN. NO es la tabla oficial: los puntos bonus y desempates varían por torneo.</p>
      <div class="panel table-scroll"><table>
        <thead><tr><th>#</th><th>Equipo</th><th>PJ</th><th>G</th><th>E</th><th>P</th><th>PF</th><th>PC</th></tr></thead>
        <tbody>{data.statistics.map((r,i)=><tr key={r.team||i}>
          <td>{i+1}</td><th scope="row">{r.team}</th><td>{r.pj}</td><td>{r.g}</td><td>{r.e}</td>
          <td>{r.p}</td><td>{r.for}</td><td>{r.against}</td></tr>)}</tbody>
      </table></div>
    </> : <p class="coverage-notice">Todavía no hay una tabla de posiciones verificable para esta edición.</p>}
    <h2 class="sport-section-title">Resultados y próximos partidos</h2>
    <div class="sports-tabs" role="group">
      <button class={tab==="past"?"active":""} onClick={()=>setTab("past")}>Resultados</button>
      <button class={tab==="future"?"active":""} onClick={()=>setTab("future")}>Programados</button>
    </div>
    {games.length ? <div class="sports-games">{games.slice(0,50).map(m=><article class="panel sport-game" key={m.id}>
      <small class="sport-game-league">{m.date?new Date(m.date).toLocaleDateString("es-AR"):"—"} · {m.status}</small>
      <div class="sport-game-teams"><strong class="sport-team">{m.home}</strong>
        <span>{m.home_score??"—"} : {m.away_score??"—"}</span>
        <strong class="sport-team sport-team-away">{m.away}</strong></div>
    </article>)}</div> : <p class="coverage-notice">No hay partidos {tab==="past"?"finalizados":"programados"} disponibles para la temporada seleccionada.</p>}
    <p class="updated">Fuente: ESPN Rugby (caché servidor). {data?.updated_at? "Consultado " + new Date(data.updated_at).toLocaleString("es-AR"):""}
    {data?.stale&&" · Datos anteriores; ESPN temporalmente no disponible"}</p>
  </section>;
}
