import { useState } from "preact/hooks";
import { useApi } from "./api";
import { TeamMark } from "./team-mark";

type Dataset = { kind: string; ref: string; updated_at: string; count: number; note: string };
type StandRow = { team_id: number | string; team: string; group: string | null;
  stage: string | null; rank: number | null; played: number | null;
  won: number | null; drawn?: number | null; lost: number | null;
  scored?: number | null; conceded?: number | null; points: number | null;
  logo?: string | null };
type Driver = { driver?: { name?: string }; team?: { name?: string }; position?: number; points?: number };

function Amount({value}:{value:number|null|undefined}) {
  return <>{value == null ? "—" : value}</>;
}

export function SportsStandings({sport}:{sport:string}) {
  const {result:catalog,loading} = useApi<Dataset[]>(`/api/sports/${sport}/datasets`, 300000);
  const options = (catalog?.data||[]).filter(d => ["standings","drivers","constructors"].includes(d.kind));
  const [selection,setSelection]=useState("");
  const [group,setGroup]=useState("all");
  const current = options.find(d=>d.kind+":"+d.ref===selection) || options[0];
  const {result,error} = useApi<(StandRow|Driver)[]>(
    current ? `/api/sports/${sport}/dataset?kind=${current.kind}&ref=${encodeURIComponent(current.ref)}` : null,360000);
  const rows=result?.data||[];
  const isRace=current?.kind==="drivers"||current?.kind==="constructors";
  const groups=[...new Set(rows.filter(r=>"team_id" in r).map(r=>(r as StandRow).group||"General"))].sort();
  const visible=rows.filter(r=>group==="all"||(!isRace && ("team_id" in r) && ((r as StandRow).group||"General")===group));
  return <section class="sport-standings-block">
    <h2 class="sport-section-title">Posiciones oficiales por liga y temporada</h2>
    {loading?<p>Cargando competiciones…</p>:!options.length?
      <p class="coverage-notice">Sin tabla oficial sincronizada todavía para esta disciplina.
      Las posiciones se importan desde API-Sports solo para ligas y temporadas verificadas.</p>:
      <>
        <label class="season-label">Liga / temporada
          <select value={current?.kind+":"+current?.ref||""} onChange={e=>{setSelection(e.currentTarget.value);setGroup("all");}}>
            {options.map(d=><option key={d.kind+":"+d.ref} value={d.kind+":"+d.ref}>
              {d.note?.startsWith("País:")?d.note.split(".")[0]+" · ":""}
              {d.ref.replace(":", " · ")} · {d.count} registros
            </option>)}
          </select>
        </label>
        {groups.length>1&&<label class="season-label">Grupo / conferencia
          <select value={groups.includes(group)?group:"all"} onChange={e=>setGroup(e.currentTarget.value)}>
            <option value="all">Todos los grupos</option>
            {groups.map(g=><option key={g} value={g}>{g}</option>)}
          </select>
        </label>}
        {error?<p class="coverage-notice">{error}</p>:rows.length?
          <div class="panel table-scroll" role="region" tabIndex={0} aria-label="Posiciones oficiales">
            <table><thead>
              <tr><th>#</th><th>Club / piloto</th><th>Grupo</th>
                {!isRace&&<><th>PJ</th><th>G</th><th>E</th><th>P</th><th>A favor</th><th>En contra</th><th>% G</th></>}
                <th>Puntos</th>
              </tr></thead><tbody>
              {visible.map((r,i)=>{
                const standings=r as StandRow, race=r as Driver;
                const name=isRace?(race.driver?.name||race.team?.name||"No informado"):standings.team;
                const logo=!isRace?standings.logo:null;
                const pct=(!isRace&&standings.played&&standings.won!=null)
                  ?(100*standings.won/standings.played).toFixed(1)+"%":"—";
                return <tr key={isRace?i:(standings.team_id+"-"+standings.group)}>
                  <td>{isRace?race.position??i+1:standings.rank??i+1}</td>
                  <th scope="row"><span class="sport-team-inline">
                    {!isRace&&<TeamMark name={name} logo={logo} teamId={standings.team_id} sport={sport}/>}
                    {name}</span></th>
                  <td>{isRace?(current.kind==="drivers"?"Pilotos":"Escuderías"):standings.group||"General"}</td>
                  {!isRace&&<><td><Amount value={standings.played}/></td>
                    <td><Amount value={standings.won}/></td>
                    <td><Amount value={standings.drawn}/></td>
                    <td><Amount value={standings.lost}/></td>
                    <td><Amount value={standings.scored}/></td>
                    <td><Amount value={standings.conceded}/></td>
                    <td>{pct}</td></>}
                  <td><Amount value={r.points}/></td>
                </tr>;
              })}
              </tbody></table>
          </div>:
          <p class="coverage-notice">La clasificación todavía no contiene registros de equipos.</p>}
        <p class="updated">Fuente: API-Sports · última actualización {new Date(current.updated_at).toLocaleString("es-AR")}.
          Los valores ausentes se muestran como —; no se reemplazan por estadísticas ficticias.</p>
      </>}
    <h2 class="sport-section-title">Estadísticas y líderes</h2>
    <p class="coverage-notice">Los goleadores o anotadores individuales se mostrarán solo cuando la API del deporte
      ofrezca datos de jugadores por liga y temporada. Las estadísticas colectivas no se atribuyen a jugadores.</p>
  </section>;
}
