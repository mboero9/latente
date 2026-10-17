import { useEffect, useMemo, useRef, useState } from "preact/hooks";
import { useApi } from "./api";
import type { League, Match, Team } from "./types";

type BracketMatch = Match & { next_match_id?:number; qualified_team_id?:number };
type Stage = { name:string; order:number; matches:BracketMatch[]; tie_count?:number };
type Bracket = { stages:Stage[]; season:number; league:string };
type Tie = {key:string; teams:[Team,Team]; matches:BracketMatch[]};
type StageWithTies = Stage & {ties:Tie[]};

// Sixteen fixtures in the Round of 16 normally represent eight two-leg
// matchups. Group by the identity of BOTH teams, regardless of home advantage.
// Never group placeholders that have unknown or identical team IDs.
export function groupBracketTies(matches:BracketMatch[]):Tie[] {
  const groups=new Map<string,Tie>();
  for (const match of matches) {
    const home=match.home?.id, away=match.away?.id;
    const valid=home!=null && away!=null && home!==away;
    const key=valid ? [home,away].sort((a,b)=>a-b).join(":") : `fixture:${match.id}`;
    const existing=groups.get(key);
    if (existing) existing.matches.push(match);
    else groups.set(key,{key,teams:[match.home,match.away],matches:[match]});
  }
  return [...groups.values()];
}

const SLOT=178;
const CARD=156;
const PLAYED=new Set(["FT","AET","PEN","1H","HT","2H","ET","BT","P","INT","LIVE"]);
function legScore(match:BracketMatch,team:Team):string {
  if (!PLAYED.has(match.status)) return "—";
  const goals=match.home.id===team.id?match.home_goals:
    match.away.id===team.id?match.away_goals:null;
  return goals==null?"—":String(goals);
}
function shortDay(raw:string) {
  const day=raw.slice(0,10);
  const [y,m,d]=day.split("-");
  return y&&m&&d?`${Number(d)}/${Number(m)}`:day;
}
function MatchupCard({tie,top}:{tie:Tie;top:number}) {
  const legs=tie.matches;
  const multiple=legs.length>1;
  return <article class="knockout-tie" data-tie-key={tie.key}
    style={{top:`${top}px`}} aria-label={`Cruce ${tie.teams[0].name} contra ${tie.teams[1].name}`}>
    <div class="knockout-tie-head">
      <span>{multiple?"Ida y vuelta":"Partido único"}</span>
      {legs.length>2&&<span>{legs.length} encuentros</span>}
    </div>
    <div class="knockout-score-head">
      <span/>
      {legs.map((match,i)=><span key={match.id}
        title={`${shortDay(match.kickoff)} · ${match.status}`}>
        {multiple?(i===0?"Ida":i===1?"Vuelta":`P${i+1}`):"Resultado"}
      </span>)}
    </div>
    {tie.teams.map(team=><div class="knockout-team" key={team.id}>
      <span title={team.name}>{team.name}</span>
      <div class="knockout-leg-scores">
        {legs.map(match=><b key={match.id}>{legScore(match,team)}</b>)}
      </div>
    </div>)}
    <div class="knockout-tie-footer">
      {legs.map((match,i)=><a key={match.id}
        class="knockout-leg-link" data-match-id={match.id}
        href={`#/match/${match.id}`}
        title={`Ver ${tie.teams[0].name} – ${tie.teams[1].name} · ${match.status}`}>
        {multiple?(i===0?"Ida":i===1?"Vuelta":`P${i+1}`):"Ficha"}
        {" · "}{shortDay(match.kickoff)} ↗
      </a>)}
    </div>
  </article>;
}

export function CupBracket({league}:{league:League}) {
  const [season,setSeason]=useState(league.season);
  const {result,loading,error,retry}=useApi<Bracket>(
    `/api/leagues/${league.id}/bracket?season=${season}`,120000,
  );
  const stages=result?.data?.stages||[];
  const rounds=useMemo<StageWithTies[]>(
    ()=>stages.map(stage=>({...stage,ties:groupBracketTies(stage.matches)})),
    [result?.data],
  );
  const maxTies=Math.max(1,...rounds.map(stage=>stage.ties.length));
  const graph=useRef<HTMLDivElement>(null);
  const [paths,setPaths]=useState<string[]>([]);
  const [connected,setConnected]=useState(0);

  useEffect(()=>{
    const recalc=()=>{
      const root=graph.current;
      if (!root) return;
      const bounds=root.getBoundingClientRect();
      const drawn:string[]=[];
      const seen=new Set<string>();
      for (const stage of rounds) for (const tie of stage.ties) {
        for (const match of tie.matches) {
          if (!match.next_match_id) continue;
          const from=root.querySelector<HTMLElement>(`[data-match-id="${match.id}"]`)
            ?.closest<HTMLElement>(".knockout-tie");
          const to=root.querySelector<HTMLElement>(`[data-match-id="${match.next_match_id}"]`)
            ?.closest<HTMLElement>(".knockout-tie");
          if (!from||!to||from===to) continue;
          const key=`${stage.order}:${tie.key}:${match.next_match_id}`;
          if (seen.has(key)) continue;
          seen.add(key);
          const a=from.getBoundingClientRect(),b=to.getBoundingClientRect();
          const x1=a.right-bounds.left,y1=a.top+a.height/2-bounds.top;
          const x2=b.left-bounds.left,y2=b.top+b.height/2-bounds.top;
          if (x2<=x1) continue;
          const middle=x1+(x2-x1)/2;
          drawn.push(`M ${x1} ${y1} H ${middle} V ${y2} H ${x2}`);
        }
      }
      setPaths(previous=>previous.join("|")===drawn.join("|")?previous:drawn);
      setConnected(previous=>previous===drawn.length?previous:drawn.length);
    };
    const frame=requestAnimationFrame(recalc);
    const observer=typeof ResizeObserver!=="undefined"?new ResizeObserver(recalc):null;
    if (graph.current) observer?.observe(graph.current);
    window.addEventListener("resize",recalc);
    return ()=>{cancelAnimationFrame(frame);observer?.disconnect();window.removeEventListener("resize",recalc);};
  },[result?.data,season]);

  return <section class="cup-bracket">
    <div class="view-heading"><div><span class="eyebrow">CUADRO ELIMINATORIO</span>
      <h1>{league.name} · Playoffs</h1></div>
      <label class="season-label">Temporada
        <select value={season} onChange={e=>setSeason(Number(e.currentTarget.value))}>
          {[...new Set([league.season,...(league.loaded_seasons||[])])].sort((a,b)=>b-a)
            .map(y=><option value={y}>{y}</option>)}
        </select>
      </label>
    </div>
    <nav class="subnav" aria-label="Vistas de la copa">
      <a class="active" href={`#/bracket/${league.id}`}>Llave de playoffs</a>
      <a href={`#/fixtures/${league.id}`}>Todos los partidos</a>
    </nav>
    <p class="updated">Llaves verificadas con los equipos y partidos importados.
      En series de ida y vuelta, ambos resultados se muestran en un mismo cruce;
      las líneas unen únicamente equipos identificados en la fase siguiente.</p>
    {loading?<p>Cargando cuadro de copa…</p>:
      error?<p>{error} <button onClick={retry}>Reintentar</button></p>:
      rounds.length ? <>
        <div class="knockout-scroll" role="region" tabIndex={0}
          aria-label="Cuadro de rondas eliminatorias. Desplazamiento horizontal disponible.">
          <div class="knockout-columns" ref={graph}>
            <svg class="knockout-links" aria-hidden="true">
              {paths.map((path,i)=><path key={`${i}:${path}`} d={path}/>)}
            </svg>
            {rounds.map(stage=><div class="knockout-round" key={stage.order}>
              <h2>{stage.name}{stage.order===5?" 🏆":""}</h2>
              <span class="updated">{stage.ties.length} cruces · {stage.matches.length} partidos verificados</span>
              <div class="knockout-round-body" style={{height:`${maxTies*SLOT}px`}}>
                {stage.ties.map((tie,index)=>{
                  const ratio=maxTies/stage.ties.length;
                  const top=Math.max(0,(index+.5)*ratio*SLOT-CARD/2);
                  return <MatchupCard key={tie.key} tie={tie} top={top}/>;
                })}
              </div>
            </div>)}
          </div>
        </div>
        <p class="coverage-notice">
          {connected
            ? `${connected} conexiones confirmadas entre cruces. `
            : "Todavía no hay conexiones verificadas entre las fases importadas. "}
          Si faltan fases, rivales o una clasificación confirmada en la fuente,
          se conserva el espacio sin trazar una conexión ficticia. Tocá «Ida»,
          «Vuelta» o «Ficha» para abrir el marcador original.</p>
      </>:<div class="panel sport-intro"><h2>Llave pendiente de sincronización</h2>
        <p>Esta edición todavía no dispone de rondas eliminatorias identificables en las fechas importadas.</p>
      </div>}
  </section>;
}
