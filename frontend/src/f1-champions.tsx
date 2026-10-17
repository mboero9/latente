import { useState } from "preact/hooks";
import { useApi } from "./api";
import { F1CountryFlag, F1TeamLogo } from "./f1-media";

type Champion = {year:number;name:string;nationality?:string|null;
  points:number;wins:number;team?:string|null};
type History = {available:boolean;through?:number;message?:string;
  drivers:Champion[];constructors:Champion[];provider?:string};
const DEMONYMS:Record<string,string>={
  "british":"Reino Unido","german":"Alemania","argentine":"Argentina",
  "australian":"Australia","austrian":"Austria","brazilian":"Brasil",
  "dutch":"Países Bajos","french":"Francia","finnish":"Finlandia",
  "italian":"Italia","spanish":"España","american":"Estados Unidos",
  "canadian":"Canadá","monegasque":"Mónaco","new zealander":"Nueva Zelanda",
  "swedish":"Suecia","belgian":"Bélgica","south african":"Sudáfrica",
  "swiss":"Suiza","mexican":"México","japanese":"Japón",
};
export function F1Champions() {
 const [type,setType]=useState<"drivers"|"constructors">("drivers");
 const [all,setAll]=useState(false);
 const {result,loading,error,retry}=useApi<History>("/api/f1/champions",86400000);
 const data=result?.data;
 const entries=type==="drivers"?data?.drivers||[]:data?.constructors||[];
 const visible=all?entries:entries.slice(0,15);
 return <section id="f1-historicos" class="f1-champions">
  <div class="view-heading">
   <div><span class="eyebrow">ARCHIVO · FÓRMULA 1</span>
    <h2>🏆 Campeones históricos de F1</h2>
    <p>Campeones mundiales oficiales al finalizar cada temporada. El líder de
    la temporada actual no se presenta como campeón.</p></div>
  </div>
  <div class="sports-tabs" role="group" aria-label="Tipo de campeonato histórico">
   <button class={type==="drivers"?"active":""} onClick={()=>{setType("drivers");setAll(false);}}>Pilotos</button>
   <button class={type==="constructors"?"active":""} onClick={()=>{setType("constructors");setAll(false);}}>Constructores</button>
  </div>
  {loading?<p class="coverage-notice">Cargando campeones verificados…</p>:
   error?<p class="coverage-notice">No se pudo consultar el archivo.
    <button onClick={retry}>Reintentar</button></p>:
   !data?.available?<p class="coverage-notice">
      {data?.message||"No hay archivo histórico verificado disponible."}
    </p>:<>
    <p class="updated">Temporadas finalizadas hasta {data.through}.
      Fuente: Jolpica/Ergast. Campeonato de constructores desde 1958.</p>
    <div class="panel table-scroll f1-champions-table"><table>
      <thead><tr><th>Año</th><th>{type==="drivers"?"Piloto campeón":"Escudería campeona"}</th>
       <th>País</th><th>Puntos</th><th>Victorias</th></tr></thead>
      <tbody>{visible.map(row=>{
       const country=DEMONYMS[row.nationality?.toLowerCase()||""]||row.nationality||"—";
       return <tr key={row.year}>
        <td class="f1-champ-year">{row.year}</td>
        <th scope="row"><span class="f1-identity">
         {type==="constructors"?<F1TeamLogo name={row.name}/>:null}
         <span>{row.name}{type==="drivers"&&row.team&&<small>{row.team}</small>}</span>
        </span></th>
        <td><span class="f1-nationality"><F1CountryFlag name={country}/>{country}</span></td>
        <td>{row.points}</td><td>{row.wins}</td>
       </tr>;
      })}</tbody>
    </table></div>
    {entries.length>15&&<button class="f1-more-champions" type="button"
      onClick={()=>setAll(!all)}>{all?"Mostrar los últimos 15":
      `Ver todos los campeones (${entries.length})`}</button>}
   </>}
  <p class="updated">Los logotipos actuales solo se muestran cuando existe una
   imagen verificada. Los equipos históricos pueden tener identidades de otra época.</p>
  <a class="official-standings-link" href="https://www.formula1.com/en/results.html"
    target="_blank" rel="noopener noreferrer">Archivo oficial de Fórmula 1 ↗</a>
 </section>;
}
