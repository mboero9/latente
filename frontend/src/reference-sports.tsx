import { useState } from "preact/hooks";
import type { ComponentChildren } from "preact";
import { useApi } from "./api";
import { ScoreboardPanel } from "./scoreboards";
import { TeamMark } from "./team-mark";
import { F1CountryFlag, F1Portrait, F1TeamLogo } from "./f1-media";
import { F1Champions } from "./f1-champions";

type F1 = { available:boolean; message?:string; season:number; round?:string;
  drivers:{rank:number;name:string;nationality?:string|null;team:string;family_name?:string|null;photo?:string|null;team_colour?:string|null;team_nationalities?:(string|null)[];points:number;wins:number}[];
  constructors:{rank:number;name:string;nationality?:string|null;points:number;wins:number}[];
  upcoming?:{name:string;date:string;circuit:string}|null;
  last_race?:{name:string;date:string;circuit:string;
    podium:{position:number;name:string;team:string;nationality?:string|null;team_nationality?:string|null}[];
    results:{position:number;driver:string;team:string;nationality?:string|null;team_nationality?:string|null;time?:string}[]};
  updated_at?:string; stale?:boolean };
type NBA = { available:boolean; message?:string; season:number; rows:{
  id:string;name:string;logo?:string|null;group:string;wins:number|null;losses:number|null;
  win_pct:number|null;rank:number|null;games_back:number|null}[];
  note?:string;updated_at?:string;stale?:boolean };
type Cricket = { available:boolean; message?:string;needs_key:boolean;
  competition:string;provider:string;rows:{
  id:string;name:string;group:string;wins:number|null;losses:number|null;
  win_pct:number|null;rank:number|null;}[];
  matches:{id:string;name:string;date:string;status:string;
  teams:string[];score:{r?:number;w?:number;o?:number;inning?:string}[];
  match_type?:string}[];updated_at?:string;stale?:boolean };
type Historic = {rows:{team:string;team_id:number;pj:number;pg:number;pe:number;pp:number;
  gf:number;gc:number;difference:number;points_3v:number;win_pct:number}[];
  seasons:number[];matches:number;partial:boolean;note:string};

const seasons = Array.from({length:12}, (_,i)=>new Date().getFullYear()-i);
function Status({ stamp, stale }: {stamp?:string;stale?:boolean}) {
  return <p class="updated">{stamp ? `Consulta: ${new Date(stamp).toLocaleString("es-AR")}` : "Datos pendientes"}
    
  </p>;
}
function Notice({children}:{children:ComponentChildren}) {
  return <p class="coverage-notice">{children}</p>;
}
function Source({href,children}:{href:string;children:ComponentChildren}) {
  return <a class="official-standings-link" href={href} target="_blank" rel="noopener noreferrer">{children} ↗</a>;
}

export function ReferenceSportPage({slug}:{slug:string}) {
  const [season,setSeason]=useState(slug === "nba" ? new Date().getFullYear()-1 : new Date().getFullYear());
  const [competition,setCompetition]=useState("ipl");
  const [f1Tab,setF1Tab]=useState<"drivers"|"constructors"|"results">("drivers");
  const [nbaSort,setNbaSort]=useState<"wins"|"pct">("wins");
  const isF1=slug==="f1", isNba=slug==="nba", isCricket=slug==="cricket";
  const isUS=["nhl","mlb","nfl","wnba"].includes(slug);
  const query = isCricket ? `?competition=${competition}` : `?season=${season}`;
  const {result,loading,error,retry} = useApi<F1 | NBA | Cricket>(
    isF1||isNba||isCricket||isUS ? `/api/reference/${slug}${query}` : null, 3600000);
  const data=result?.data;
  const heading=isF1?"Fórmula 1":isNba?"NBA":isCricket?"Cricket":({nhl:"NHL · Hockey",mlb:"MLB · Béisbol",nfl:"NFL",wnba:"WNBA"} as Record<string,string>)[slug]||"Deportes";
  return <section class="sport-landing">
    <div class="view-heading"><div><span class="eyebrow">LATENTE · DEPORTES</span>
      <h1>{isF1?"🏎️":isNba?"🏀":isCricket?"🏏":slug==="nhl"?"🏒":slug==="mlb"?"⚾":slug==="wnba"?"🏀":"🏈"} {heading}</h1>
      <p>{isF1?"Resultados por Gran Premio y tablas de pilotos y equipos":
        isNba?"Posiciones, conferencias y temporadas anteriores":
        isUS?"Clasificaciones de temporada, récords y archivo histórico":
        "Cricket internacional, IPL, ICC y resultados verificados"}</p>
    </div></div>
    {isCricket ? <label class="season-label">Competición
      <select value={competition} onChange={e=>setCompetition(e.currentTarget.value)}>
        <option value="ipl">Indian Premier League (IPL)</option>
        <option value="icc.t20">ICC T20</option>
        <option value="icc.world-cup">Copa Mundial ICC</option>
      </select></label>
    : <label class="season-label">Temporada
      <select value={season} onChange={e=>setSeason(Number(e.currentTarget.value))}>
        {isF1 ? Array.from({length:8},(_,i)=>new Date().getFullYear()-i)
          .map(year=><option value={year} key={year}>{year}</option>) :
          seasons.map(year=><option value={year} key={year}>{year}–{String(year+1).slice(-2)}</option>)}
      </select></label>}
    {loading ? <p>Cargando tablas y estadísticas…</p> : error ?
      <Notice>La API no responde: {error} <button onClick={retry}>Reintentar</button></Notice> :
      !data?.available ? <Notice>{data?.message || "No hay posiciones verificadas disponibles para esta selección."}</Notice> : null}
    {isF1 && data?.available && <F1Content data={data as F1} tab={f1Tab} setTab={setF1Tab}/>}
    {isF1 && <F1Champions/>}
    {(isNba||isUS) && data?.available && <NBAContent data={data as NBA} sort={nbaSort} setSort={setNbaSort}/>}
    {isNba && <div class="panel sport-intro"><h2>Archivo NBA</h2>
      <p>Seleccioná una temporada anterior para comparar posiciones, victorias y porcentaje de triunfos.
        Las tablas corresponden a la temporada regular; no son una suma histórica de todas las décadas.</p>
      <Source href="https://www.nba.com/standings">Posiciones oficiales NBA</Source>
      <Source href="https://www.nba.com/history">Archivo oficial NBA</Source>
    </div>}
    {(isNba||isUS) && <ScoreboardPanel sport={slug} />}
    {isUS && <p class="coverage-notice">Clasificación de temporada regular obtenida de ESPN. Los resultados se actualizan con caché y pueden no incluir temporadas sin cobertura.</p>}
    {isCricket && <CricketContent data={data as Cricket | undefined}/>}
    {!isCricket && data?.available && <Status stamp={data.updated_at} stale={data.stale}/>}
  </section>;
}


/* Nacionalidades provistas por Jolpica/Ergast; nunca se infieren del nombre del equipo. */
const F1_COUNTRIES:Record<string,[string,string]> = {
  argentine:["🇦🇷","Argentina"], argentinian:["🇦🇷","Argentina"],
  american:["🇺🇸","Estados Unidos"], australian:["🇦🇺","Australia"],
  austrian:["🇦🇹","Austria"], belgian:["🇧🇪","Bélgica"],
  brazilian:["🇧🇷","Brasil"], british:["🇬🇧","Reino Unido"],
  canadian:["🇨🇦","Canadá"], chinese:["🇨🇳","China"],
  colombian:["🇨🇴","Colombia"], czech:["🇨🇿","Chequia"],
  danish:["🇩🇰","Dinamarca"], dutch:["🇳🇱","Países Bajos"],
  finnish:["🇫🇮","Finlandia"], french:["🇫🇷","Francia"],
  german:["🇩🇪","Alemania"], indian:["🇮🇳","India"],
  indonesian:["🇮🇩","Indonesia"], irish:["🇮🇪","Irlanda"],
  italian:["🇮🇹","Italia"], japanese:["🇯🇵","Japón"],
  malaysian:["🇲🇾","Malasia"], mexican:["🇲🇽","México"],
  monegasque:["🇲🇨","Mónaco"], "new zealander":["🇳🇿","Nueva Zelanda"],
  polish:["🇵🇱","Polonia"], portuguese:["🇵🇹","Portugal"],
  russian:["🇷🇺","Rusia"], "south african":["🇿🇦","Sudáfrica"],
  spanish:["🇪🇸","España"], swedish:["🇸🇪","Suecia"],
  swiss:["🇨🇭","Suiza"], thai:["🇹🇭","Tailandia"],
  venezuelan:["🇻🇪","Venezuela"],
};
function F1Nationality({value}:{value?:string|null}) {
  const raw=value?.trim();
  const known=raw ? F1_COUNTRIES[raw.toLowerCase()] : undefined;
  return <span class="f1-nationality" title={raw||"Nacionalidad no informada"}>
    {known ? <><F1CountryFlag name={known[1]}/>{known[1]}</> : raw||"—"}
  </span>;
}
function F1TeamNationalities({values}:{values?:(string|null)[]}) {
  return <span class="f1-nationality-list">{values?.length
    ? values.map((value,i)=><F1Nationality key={i} value={value}/>)
    : <F1Nationality/>}</span>;
}

function F1Content({data,tab,setTab}:{data:F1;tab:"drivers"|"constructors"|"results";setTab:(value:"drivers"|"constructors"|"results")=>void}) {
  return <>
    {data.upcoming && <article class="panel sport-intro"><span class="eyebrow">PRÓXIMO GRAN PREMIO</span>
      <h2>{data.upcoming.name} · {data.upcoming.date}</h2><p>{data.upcoming.circuit}</p></article>}
    {data.last_race && <article class="panel sport-intro">
      <span class="eyebrow">ÚLTIMO GRAN PREMIO FINALIZADO</span>
      <h2>{data.last_race.name} · {data.last_race.date}</h2>
      <p>{data.last_race.circuit}</p>
      <div class="sports-clubs">{data.last_race.podium.map(p=><span class="sports-club" key={p.position}>
        {p.position===1?"🏆 ":""}<F1Portrait name={p.name} photo={data.drivers.find(d=>d.name===p.name)?.photo}/>{p.position}º {p.name} <F1Nationality value={p.nationality}/> · <F1TeamLogo name={p.team}/>{p.team} <F1Nationality value={p.team_nationality}/></span>)}</div>
    </article>}
    <div class="sports-tabs" role="group" aria-label="Clasificación F1">
      <button class={tab==="drivers"?"active":""} onClick={()=>setTab("drivers")}>Pilotos</button>
      <button class={tab==="constructors"?"active":""} onClick={()=>setTab("constructors")}>Constructores</button>
      <button class={tab==="results"?"active":""} onClick={()=>setTab("results")}>Última carrera</button>
    </div>
    <h2 class="sport-section-title">{tab==="drivers"?"Campeonato de pilotos":tab==="constructors"?"Copa de constructores":"Resultado del último GP"} · {data.season}</h2>
    <p class="f1-mobile-scroll-hint">← Deslizá la tabla para ver escuderías, puntos y victorias →</p>
    <div class="panel table-scroll f1-standings-scroll" role="region" tabIndex={0}
      aria-label="Clasificación de Fórmula 1. Desplazamiento horizontal disponible.">
      <table class={`f1-standings-table f1-standings-table--${tab}`}>
      <thead><tr>
        <th>#</th><th>{tab==="constructors"?"Escudería":"Piloto"}</th>
        {tab!=="constructors"&&<th>Nacionalidad piloto</th>}
        {tab!=="constructors"&&<th>Escudería</th>}
        <th>{tab==="constructors"?"Nacionalidad escudería":"País escudería"}</th>
        {tab==="results"?<th>Tiempo/Estado</th>:<><th>{tab==="constructors"?"Victorias":"Puntos"}</th><th>{tab==="constructors"?"Puntos":"Victorias"}</th></>}
      </tr></thead>
      <tbody>
        {tab==="drivers"&&data.drivers.map(d=><tr key={d.rank}>
          <td>{d.rank}</td><th scope="row"><span class="f1-identity"><F1Portrait name={d.name} photo={d.photo}/><span>{d.name}</span></span></th>
          <td><F1Nationality value={d.nationality}/></td>
          <td><span class="f1-identity"><F1TeamLogo name={d.team}/>{d.team}</span></td>
          <td><F1TeamNationalities values={d.team_nationalities}/></td>
          <td>{d.points}</td><td>{d.wins}</td>
        </tr>)}
        {tab==="constructors"&&data.constructors.map(t=><tr key={t.rank}>
          <td>{t.rank}</td><th scope="row"><span class="f1-identity"><F1TeamLogo name={t.name}/>{t.name}</span></th>
          <td><F1Nationality value={t.nationality}/></td><td>{t.wins}</td><td>{t.points}</td>
        </tr>)}
        {tab==="results"&&data.last_race?.results.map(d=><tr key={d.position}>
          <td>{d.position}</td><th scope="row"><span class="f1-identity"><F1Portrait name={d.driver} photo={data.drivers.find(p=>p.name===d.driver)?.photo}/>{d.driver}</span></th>
          <td><F1Nationality value={d.nationality}/></td><td><span class="f1-identity"><F1TeamLogo name={d.team}/>{d.team}</span></td>
          <td><F1Nationality value={d.team_nationality}/></td><td>{d.time||"—"}</td>
        </tr>)}
      </tbody>
    </table></div>
    <Notice>Campeonato en curso: el líder de puntos no es necesariamente el campeón mundial. Fuente Jolpica/Ergast, actualizada periódicamente.</Notice>
    <Source href="https://www.formula1.com/en/results.html">Resultados oficiales F1</Source>
  </>;
}

function NBAContent({data,sort,setSort}:{data:NBA;sort:"wins"|"pct";setSort:(sort:"wins"|"pct")=>void}) {
  const groups = ["Eastern Conference","Western Conference"];
  const grouped = data.rows.filter(row=>row.name);
  const rank=(rows:NBA["rows"])=>[...rows].sort((a,b)=>(sort==="wins"?
    Number(b.wins??-1)-Number(a.wins??-1):Number(b.win_pct??-1)-Number(a.win_pct??-1))||a.name.localeCompare(b.name));
  const groupsFound=[...new Set(grouped.map(row=>row.group||"NBA"))];
  const display=groupsFound.length>1?groupsFound:groups;
  return <>
    <div class="sports-tabs" role="group"><button class={sort==="wins"?"active":""} onClick={()=>setSort("wins")}>Por victorias</button>
      <button class={sort==="pct"?"active":""} onClick={()=>setSort("pct")}>Por porcentaje</button></div>
    {((groupsFound.length>1?display:["NBA"]).map(group=>{
      const rows=group==="NBA"?grouped:grouped.filter(row=>row.group===group);
      return <div key={group}><h2 class="sport-section-title">{group}</h2>
        {rows.length?<div class="panel table-scroll"><table><thead><tr><th>#</th><th>Equipo</th><th>G</th><th>P</th><th>%V</th><th>Dif.</th></tr></thead>
        <tbody>{rank(rows).map((team,i)=><tr key={team.id||team.name}><td>{i+1}</td><th scope="row"><span class="sport-team-inline"><TeamMark name={team.name} logo={team.logo} />{team.name}</span></th>
          <td>{team.wins??"—"}</td><td>{team.losses??"—"}</td>
          <td>{team.win_pct==null?"—":(Number(team.win_pct)*100).toFixed(1)+"%"}</td>
          <td>{team.games_back??"—"}</td></tr>)}</tbody></table></div>:
          <Notice>No hay registros de esta conferencia en esta temporada.</Notice>}
      </div>;
    }))}
    <Notice>{data.note} Los datos dependen de la cobertura histórica de ESPN; si falta una temporada, no se reconstruye con estimaciones.</Notice>
  </>;
}
const TOP_CRICKET_T20_OCT2026 = [
  ["Inglaterra",41,11021,269],["India",70,18802,269],["Australia",38,9868,260],
  ["Nueva Zelanda",50,12348,247],["Sudáfrica",53,12881,243],
  ["Pakistán",62,14883,240],["West Indies",59,13836,235],
  ["Bangladesh",55,12220,222],["Sri Lanka",52,11489,221],
  ["Afganistán",41,8925,218],
] as const;
function CricketContent({data}:{data?:Cricket}) {
  return <>
    <h2 class="sport-section-title">Ranking mundial ICC · T20 masculino</h2>
    <p class="updated">Corte histórico verificado: 13 de octubre de 2026. Ranking de selecciones, no tabla de la IPL ni clasificación en vivo.</p>
    <div class="panel table-scroll"><table><thead><tr><th>#</th><th>Selección</th><th>Partidos</th><th>Puntos</th><th>Rating</th></tr></thead>
      <tbody>{TOP_CRICKET_T20_OCT2026.map(([name,played,points,rating],i)=><tr key={name}>
        <td>{i+1}</td><th scope="row">{name}</th><td>{played}</td><td>{points}</td><td>{rating}</td></tr>)}</tbody>
    </table></div>
    <Source href="https://www.icc-cricket.com/rankings">Ranking ICC actualizado</Source>
    <h2 class="sport-section-title">Tabla de posiciones por competición</h2>
    {data?.rows?.length ? <div class="panel table-scroll"><table>
      <thead><tr><th>#</th><th>Equipo</th><th>Grupo</th><th>G</th><th>P</th><th>%V</th></tr></thead><tbody>
      {data.rows.map((team,i)=><tr key={team.id||i}><td>{team.rank??i+1}</td><th scope="row"><span class="sport-team-inline"><TeamMark name={team.name} logo={("logo" in team && typeof team.logo === "string") ? team.logo : undefined}/>{team.name}</span></th>
        <td>{team.group}</td><td>{team.wins??"—"}</td><td>{team.losses??"—"}</td>
        <td>{team.win_pct??"—"}</td></tr>)}</tbody></table></div> :
      <Notice>El proveedor todavía no entregó una clasificación fiable para esta competición. No se asignan posiciones ficticias.</Notice>}
    <h2 class="sport-section-title">Resultados y estadísticas</h2>
    {data?.matches?.length ? <div class="sports-games">{data.matches.map(m=><article class="panel sport-game" key={m.id}>
      <strong>{m.name}</strong><small>{m.date} · {m.match_type?.toUpperCase()} · {m.status}</small>
      {(m.score||[]).map((s,i)=><p key={i}>{s.inning}: {s.r??"—"}/{s.w??"—"} ({s.o??"—"} overs)</p>)}
    </article>)}</div> : <Notice>Los marcadores de cricket requieren una clave activa de CricketData. Una vez configurada, se consultarán con caché del servidor.</Notice>}
    <div class="panel sport-intro"><h2>Selecciones y torneos internacionales</h2>
      <p>India, Australia, Inglaterra, Sudáfrica, Nueva Zelanda, Pakistán, Sri Lanka, Bangladesh, Afganistán y West Indies.
      Consultá los rankings separados para Test, ODI y T20: no existe una única tabla comparable de todas las modalidades.</p>
      <Source href="https://www.icc-cricket.com/rankings">Ranking mundial ICC</Source>
      <Source href="https://www.iplt20.com/points-table">Tabla oficial IPL</Source>
    </div>
    {data?.available && <Status stamp={data.updated_at} stale={data.stale}/>}
  </>;
}

export function ArgentinaAlltime() {
  const {result,loading,error}=useApi<Historic>("/api/leagues/128/alltime",300000);
  const [sort,setSort]=useState<"points_3v"|"pj"|"pg"|"win_pct">("points_3v");
  const data=result?.data;
  const rows=[...(data?.rows||[])].sort((a,b)=>b[sort]-a[sort]||b.points_3v-a.points_3v);
  return <section class="history-section">
    <div class="view-heading"><div><span class="eyebrow">PRIMERA DIVISIÓN ARGENTINA</span>
      <h1>Tabla histórica</h1><p>Todos los partidos finalizados disponibles en el archivo local de Latente.</p></div></div>
    {loading?<p>Cargando archivo…</p>:error?<Notice>{error}</Notice>:<>
      <Notice>{data?.note}</Notice>
      <p class="updated">Temporadas cargadas: {data?.seasons.join(", ")||"ninguna"} · Partidos: {data?.matches||0}</p>
      <div class="sports-tabs"><button class={sort==="points_3v"?"active":""} onClick={()=>setSort("points_3v")}>Puntos</button>
        <button class={sort==="pj"?"active":""} onClick={()=>setSort("pj")}>Partidos</button>
        <button class={sort==="pg"?"active":""} onClick={()=>setSort("pg")}>Victorias</button>
        <button class={sort==="win_pct"?"active":""} onClick={()=>setSort("win_pct")}>% victorias</button></div>
      <div class="panel table-scroll"><table><thead><tr><th>#</th><th>Equipo</th><th>Pts3V</th>
        <th>PJ</th><th>PG</th><th>PE</th><th>PP</th><th>GF</th><th>GC</th><th>DG</th><th>%PG</th></tr></thead>
        <tbody>{rows.map((r,i)=><tr key={r.team_id}><td>{i+1}</td><th scope="row">{r.team}</th>
          <td>{r.points_3v}</td><td>{r.pj}</td><td>{r.pg}</td><td>{r.pe}</td><td>{r.pp}</td>
          <td>{r.gf}</td><td>{r.gc}</td><td>{r.difference}</td><td>{r.win_pct}%</td></tr>)}</tbody></table></div>
      <p>Para la tabla histórica completa de Primera División, que incluye las épocas anteriores a los datos importados,
        consultá el archivo externo. No se deben comparar esos totales con esta tabla parcial.</p>
      <Source href="https://www.promiedos.com.ar/tablahistorica">Tabla histórica completa de referencia</Source>
    </>}
  </section>;
}
