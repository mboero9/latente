import { TeamMark } from "./team-mark";
import type { Match } from "./types";

export type LiveTeamForm = {
 fixture_id:number;home:string[];away:string[];sample_type:string;
};
const LABEL:{[key:string]:string}={W:"Victoria",D:"Empate",L:"Derrota"};
const LOCAL:{[key:string]:string}={W:"V",D:"E",L:"D"};

function ClubForm({name,teamId,form}:{
 name:string;teamId:number;form:string[];
}) {
 return <div class="live-form-team">
   <a class="live-form-club" href={`#/team/${teamId}`} title={name}>
     <TeamMark name={name} sport="football" teamId={teamId}/>
     <strong>{name}</strong>
   </a>
   <div class="live-form-results" role="list" aria-label={`Últimos resultados de ${name}`}>
     {form.length?form.map((result,i)=>
       <span role="listitem" key={i} class={`live-form-cell live-form-${result}`}
         title={LABEL[result]||"Resultado"}>{LOCAL[result]||"—"}</span>
     ):<span class="live-form-empty">Sin resultados confirmados</span>}
   </div>
 </div>;
}

export function LiveRecentForm({match,entry}:{
 match:Match;entry?:LiveTeamForm;
}) {
 if(!entry || !(entry.home?.length||entry.away?.length)) return null;
 return <aside class="live-form-panel"
   aria-label={`Rachas recientes de ${match.home.name} y ${match.away.name}`}>
   <div class="live-form-heading">
      <strong>Últimos partidos</strong>
      <span>Resultados verificados · hasta 5 por equipo</span>
   </div>
   <div class="live-form-grid">
     <ClubForm name={match.home.name} teamId={match.home.id}
       form={entry.home||[]}/>
     <ClubForm name={match.away.name} teamId={match.away.id}
       form={entry.away||[]}/>
   </div>
   <small>V victoria · E empate · D derrota. No es un pronóstico.</small>
 </aside>;
}
