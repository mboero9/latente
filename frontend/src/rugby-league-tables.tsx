import { useState } from "preact/hooks";
import { useApi } from "./api";
import { TeamMark } from "./team-mark";

type Comp={slug:string;name:string;region?:string|null;seasons?:number[];source_coverage?:boolean};
type Position={team:string;team_id?:string|number|null;logo?:string|null;
 rank:number|null;played:number|null;won:number|null;drawn:number|null;
 lost:number|null;points:number|null;bonus?:number|null;difference?:number|null};
type Standing={official:Position[];league_name:string;season:number;provider:string;updated_at?:string|null};

const FEATURED=["urba","super-rugby-americas","interior-a","interior-b",
 "urba-primera-a","urba-primera-b","urba-primera-c",
 "litoral-top10","cordoba-top10","championship","top-14",
 "premiership","urc","six-nations","super-rugby",
 "npc-nz","currie-cup","mlr","challenge-cup",
 "pro-d2","europe-championship","champions"];
const OMIT=/jap(o|a)n|uruguay|chile/i;

function LeagueTable({comp}:{comp:Comp}) {
 const {result,loading,error}=useApi<Standing>(`/api/rugby/${encodeURIComponent(comp.slug)}`,600000);
 const data=result?.data;
 const rows=data?.official||[];
 return <article class="rugby-league-card panel" id={`rugby-table-${comp.slug}`}>
   <div class="rugby-league-card-heading">
     <h3>{comp.name}</h3>
     <span class="updated">{comp.region||""}</span>
   </div>
   {loading?<p class="updated">Cargando posiciones…</p>:
    error?<p class="coverage-notice">No se pudieron obtener los datos de esta liga.</p>:
    rows.length?<div class="table-scroll" role="region" aria-label={`Posiciones de ${comp.name}`} tabIndex={0}>
      <table><thead><tr>
       <th>#</th><th>Equipo</th><th>PJ</th><th>G</th><th>E</th><th>P</th><th>Bonus</th><th>Pts</th>
      </tr></thead><tbody>
      {rows.map((r,i)=><tr key={String(r.team_id||r.team)}>
       <td>{r.rank??i+1}</td>
       <th scope="row"><span class="sport-team-inline"><TeamMark name={r.team} logo={r.logo} sport="rugby" teamId={r.team_id}/>{r.team}</span></th>
       <td>{r.played??"—"}</td><td>{r.won??"—"}</td><td>{r.drawn??"—"}</td><td>{r.lost??"—"}</td>
       <td>{r.bonus??"—"}</td><td><strong>{r.points??"—"}</strong></td>
      </tr>)}
      </tbody></table></div>:
     <p class="coverage-notice">Tabla oficial pendiente de sincronización. No se calculan posiciones ni puntos bonus a partir de resultados parciales.</p>}
   {rows.length>0&&<p class="updated">Temporada {data?.season} · Fuente: {data?.provider}{data?.updated_at?` · ${new Date(data.updated_at).toLocaleString("es-AR")}`:""}</p>}
 </article>;
}

/** A dedicated card per competition. Load in bounded groups to avoid triggering
 * dozens of GET requests at once when visitors open the Rugby section.
 */
export function RugbyLeagueTables({competitions}:{competitions:Comp[]}) {
 const [expanded,setExpanded]=useState(false);
 const [filter,setFilter]=useState("");
 const entries=competitions.filter(c=>!OMIT.test((c.region||"")+" "+c.name))
  .sort((a,b)=>{
    const ai=FEATURED.indexOf(a.slug),bi=FEATURED.indexOf(b.slug);
    return (ai<0?999:ai)-(bi<0?999:bi)||a.name.localeCompare(b.name,"es");
  });
 const matching=entries.filter(c=>`${c.name} ${c.region||""}`.toLocaleLowerCase("es")
  .includes(filter.toLocaleLowerCase("es")));
 const visible=expanded||filter?matching:matching.slice(0,6);
 return <section class="rugby-all-league-tables">
   <div class="view-heading"><div>
     <span class="eyebrow">CLASIFICACIONES · RUGBY</span>
     <h2>Tablas de posiciones por competición</h2>
   </div></div>
   <p class="updated">Cada liga tiene su propia tabla y muestra exclusivamente datos oficiales sincronizados. Las competiciones sin clasificación se identifican como pendientes.</p>
   <label class="season-label">Buscar liga o región
    <input type="search" value={filter} placeholder="Argentina, Sudáfrica, Nueva Zelanda, Francia…"
      onInput={e=>setFilter(e.currentTarget.value)}/>
   </label>
   <div class="rugby-league-card-grid">
     {visible.map(c=><LeagueTable key={c.slug} comp={c}/>)}
   </div>
   {!filter&&matching.length>6&&<button class="sport-more-leagues" onClick={()=>setExpanded(!expanded)}>
    {expanded?"Mostrar menos ligas":`Ver todas las ligas (${matching.length})`}
   </button>}
   {!matching.length&&<p class="coverage-notice">No encontramos ligas para esa búsqueda.</p>}
 </section>;
}
