import { useState } from "preact/hooks";
import { useApi } from "./api";
import { TeamMark } from "./team-mark";

type Game = {
  id: string; league: string; date: string;
  home: string; away: string; home_logo?:string|null; away_logo?:string|null; home_score:number|null; away_score:number|null;
  status: string; completed:boolean; state:string
};
export type Scoreboard = { available:boolean; games?:Game[];
  from?:string;to?:string;updated_at?:string;message?:string;provider?:string;stale?:boolean };
function dayInArgentina(iso:string):string {
  if (!iso) return "";
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso.slice(0,10) :
    new Intl.DateTimeFormat("en-CA",{timeZone:"America/Argentina/Buenos_Aires",year:"numeric",month:"2-digit",day:"2-digit"}).format(date);
}
export function ScoreboardPanel({sport}:{sport:string}) {
  const [tab,setTab] = useState<"past"|"today"|"future">("past");
  const {result,loading,error,retry} = useApi<Scoreboard>(
    `/api/scoreboard/${sport}`, 120000);
  const data = result?.data, today = dayInArgentina(new Date().toISOString());
  const games = (data?.games||[]).filter(g=>{
    const d=dayInArgentina(g.date);
    return tab==="past" ? d<today : tab==="today" ? d===today : d>today;
  }).sort((a,b)=>tab==="past" ? b.date.localeCompare(a.date) : a.date.localeCompare(b.date));
  return <section class="sport-standings-block">
    <h2 class="sport-section-title">Partidos y resultados · ESPN</h2>
    <div class="sports-tabs" role="group" aria-label="Período de resultados">
      <button class={tab==="past"?"active":""} onClick={()=>setTab("past")}>Resultados</button>
      <button class={tab==="today"?"active":""} onClick={()=>setTab("today")}>Hoy</button>
      <button class={tab==="future"?"active":""} onClick={()=>setTab("future")}>Próximos</button>
    </div>
    {loading?<p>Cargando resultados…</p>:error?<p class="coverage-notice">{error} <button onClick={retry}>Reintentar</button></p>:
      games.length?<div class="sports-games">{games.slice(0,35).map(g=><article class="panel sport-game" key={g.id}>
        <small class="sport-game-league">{dayInArgentina(g.date)} · {g.status||"Programado"}</small>
        <div class="sport-game-teams">
          <strong class="sport-team"><TeamMark name={g.home} logo={g.home_logo}/>{g.home}</strong>
          <span>{g.home_score ?? "—"} : {g.away_score ?? "—"}</span>
          <strong class="sport-team sport-team-away"><TeamMark name={g.away} logo={g.away_logo}/>{g.away}</strong>
        </div>
      </article>)}</div>:
      <p class="coverage-notice">{data?.message||"No hay partidos verificados para este período."} Probá otra pestaña.</p>}
    {data?.updated_at&&<p class="updated">Última consulta: {new Date(data.updated_at).toLocaleString("es-AR")}{data.stale?" · Última copia disponible":""}. La cobertura depende de ESPN.</p>}
  </section>;
}
