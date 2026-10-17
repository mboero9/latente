import { useState } from "preact/hooks";
import { useApi } from "./api";
import type { League } from "./types";

const NAMES:Record<string,string> = {
  "primera nacional":"nacional",
  "primera b nacional":"nacional",
  "primera b metropolitana":"b",
  "prim b metro":"b",
  "primera b":"b",
  "primera division b":"b",
  "primera c":"c",
  "prim c":"c",
  "primera division c":"c",
  "primera d":"d",
  "prim d":"d",
  "primera division d":"d",
};
function simpleName(value:string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase()
    .replace(/[^a-z0-9]+/g," ").trim();
}
export function lowerLeagueCode(league:League):string|null {
  if(simpleName(league.country)!=="argentina") return null;
  return NAMES[simpleName(league.name)]||null;
}
type Club={id:number;name:string;code?:string|null};
type AveragedRow={
  team_id:number;team:Club;rank:number;played:number;points:number;
  average:number;won:number;drawn:number;lost:number;
};
type Group={name:string;rows:AveragedRow[]};
type Averages={
  category:string;season:number;groups:Group[];
  historic_only:boolean;matches_available:boolean;
  official_url:string;rule:string;note:string;
};
function threeDigits(n:number) {
  return n.toLocaleString("es-AR",{minimumFractionDigits:3,maximumFractionDigits:3});
}

export function LowerLeaguePromedios({league}:{league:League}) {
  const category=lowerLeagueCode(league);
  const archival=category==="d";
  const [season,setSeason]=useState(archival?2023:league.season);
  const years=archival?
    [...new Set([2023,...(league.loaded_seasons||[]).filter(y=>y<=2023)])].sort((a,b)=>b-a):
    [...new Set([league.season,...(league.loaded_seasons||[])])].sort((a,b)=>b-a);
  const {result,loading,error,retry}=useApi<Averages>(
    category ? `/api/leagues/${league.id}/points-average?season=${season}`:null,60000,
  );
  const data=result?.data;
  return <section class="promedios-view ascenso-averages-view">
    <div class="view-heading">
      <div><span class="eyebrow">FÚTBOL ARGENTINO · ASCENSO</span>
        <h1>{league.name} · Promedios de puntos</h1></div>
      <label class="season-label">Temporada
        <select value={season} onChange={e=>setSeason(Number(e.currentTarget.value))}>
          {years.map(y=><option value={y} key={y}>{y}</option>)}
        </select>
      </label>
    </div>
    <article class="panel promedios-card">
      <h2>{archival?"Archivo histórico · Primera D":"Promedio de puntos por partido · "+season}</h2>
      <p>La columna <strong>PTS/PJ</strong> muestra los puntos de la tabla
        publicados para cada equipo, divididos por sus partidos jugados.
        Los grupos o zonas se presentan por separado.</p>
      <p class="coverage-notice" role="note">
        <strong>No es una tabla oficial de descenso.</strong> Los reglamentos AFA
        de estas divisiones utilizan las posiciones y sistemas de la temporada,
        no los promedios históricos de la Liga Profesional. No calculamos
        sanciones, desempates ni descensos.</p>
      {archival&&<p class="coverage-notice">
        <strong>Primera D: categoría histórica.</strong> Se fusionó con Primera C
        a partir de 2024, por lo que no existe una tabla de promedios 2026.
        Aquí se muestran únicamente temporadas antiguas que estén disponibles.
      </p>}
      {data?.rule&&<p>{data.rule}</p>}
      {loading?<p>Cargando tabla registrada…</p>:
        error?<p class="coverage-notice">{error}
          <button type="button" onClick={retry}>Reintentar</button></p>:
        data?.groups?.length?data.groups.map(group=><div class="ascenso-average-group" key={group.name}>
          <h3>{group.name}</h3>
          <div class="table-scroll promedios-table" role="region" tabIndex={0}
            aria-label={`Promedios de puntos ${league.name}, ${group.name}, ${season}; desplazamiento horizontal`}>
            <table>
              <thead><tr>
                <th scope="col">#</th><th scope="col">Equipo</th>
                <th scope="col">PTS</th><th scope="col">PJ</th>
                <th scope="col">PTS/PJ</th>
                <th scope="col">G</th><th scope="col">E</th><th scope="col">P</th>
              </tr></thead>
              <tbody>{group.rows.map(row=><tr key={row.team_id}>
                <td>{row.rank}</td>
                <th scope="row" class="club-cell">
                  <a href={`#/team/${row.team_id}`}>{row.team.name}</a>
                </th>
                <td>{row.points}</td><td>{row.played}</td>
                <td class="promedios-number">{threeDigits(row.average)}</td>
                <td>{row.won}</td><td>{row.drawn}</td><td>{row.lost}</td>
              </tr>)}</tbody>
            </table>
          </div>
        </div>):
        <p class="coverage-notice">No hay una tabla de posiciones importada
          y verificada para {season}. No calculamos puntos o coeficientes
          sobre temporadas faltantes ni los reemplazamos por ceros.</p>}
      <p class="updated">Indicador estadístico informativo con datos persistidos
        en PostgreSQL. Los cambios de reglamento, deducciones y desempates
        los determina exclusivamente la AFA.</p>
      {data?.official_url&&<a class="official-standings-link"
        href={data.official_url} target="_blank" rel="noopener noreferrer">
        Consultar reglamento o archivo AFA ↗
      </a>}
      <a class="official-standings-link" href={`#/table/${league.id}`}>
        Ver tabla de posiciones de la categoría ↗</a>
    </article>
  </section>;
}
