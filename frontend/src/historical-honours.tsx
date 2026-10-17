import { useState } from "preact/hooks";
import { useApi } from "./api";
import { HistoricFlag } from "./historic-flags";
import { HistoricClubCrest } from "./historic-media";

/** Historical reference snapshots; NOT automatically updated APIs.
 * Clubs: UEFA five major competitions + confederation equivalent +
 * official world/intercontinental club titles. Include other official
 * inter-confederation cups where documented, exclude domestic/friendlies.
 * Count definitions differ by confederation: no universal world registry.
 */
type ClubTitle = {name:string;country:string;flag:string;confed:number;world:number;other?:number;detail:string;teamId?:number};
const CLUBS: ClubTitle[] = [
  {name:"Real Madrid",country:"España",flag:"🇪🇸",confed:23,world:9,
    detail:"15 Champions, 2 UEFA y 6 Supercopas UEFA; 9 títulos mundiales/intercontinentales.",teamId:541},
  {name:"Al Ahly",country:"Egipto",flag:"🇪🇬",confed:25,world:0,other:1,
    detail:"12 Champions CAF, 4 Recopas CAF, 1 Confederación CAF, 8 Supercopas CAF y 1 Afro-Asiática."},
  {name:"AC Milan",country:"Italia",flag:"🇮🇹",confed:14,world:4,
    detail:"7 Copas de Europa, 2 Recopas y 5 Supercopas UEFA; 4 mundiales/intercontinentales."},
  {name:"Boca Juniors",country:"Argentina",flag:"🇦🇷",confed:15,world:3,
    detail:"6 Libertadores y otras 9 copas CONMEBOL; 3 Intercontinentales."},
  {name:"Independiente",country:"Argentina",flag:"🇦🇷",confed:16,world:2,
    detail:"7 Libertadores y otras 9 copas regionales/intercontinentales; 2 Intercontinentales."},
  {name:"FC Barcelona",country:"España",flag:"🇪🇸",confed:14,world:3,
    detail:"5 Champions, 4 Recopas, 5 Supercopas UEFA y 3 Mundiales de Clubes.",teamId:529},
  {name:"Liverpool",country:"Inglaterra",flag:"🏴",confed:13,world:1,
    detail:"6 Champions, 3 UEFA y 4 Supercopas UEFA; 1 Mundial de Clubes.",teamId:40},
  {name:"Bayern Múnich",country:"Alemania",flag:"🇩🇪",confed:10,world:4,
    detail:"6 Champions, 1 UEFA, 1 Recopa y 2 Supercopas UEFA; 4 mundiales/intercontinentales.",teamId:157},
  {name:"Chelsea",country:"Inglaterra",flag:"🏴",confed:9,world:2,
    detail:"2 Champions, 2 Europa League, 1 Conference, 2 Recopas, 2 Supercopas UEFA; 2 Mundiales de Clubes."},
  {name:"Ajax",country:"Países Bajos",flag:"🇳🇱",confed:8,world:2,
    detail:"4 Copas de Europa, 1 UEFA, 1 Recopa y 2 Supercopas UEFA; 2 Intercontinentales."},
  {name:"Sevilla",country:"España",flag:"🇪🇸",confed:8,world:0,
    detail:"7 Europa League/Copas UEFA y 1 Supercopa UEFA."},
];
const sortedClubs=[...CLUBS].sort((a,b)=>
  (b.confed+b.world+(b.other||0))-(a.confed+a.world+(a.other||0))
  ||a.name.localeCompare(b.name,"es"));
type Region="conmebol"|"uefa"|"caf"|"afc"|"concacaf";
type Nation = {name:string;flag:string;region:Region;world:number;continental:number;competition:string};
const NATIONS:Nation[] = [
  {name:"Argentina",flag:"🇦🇷",region:"conmebol",world:3,continental:16,competition:"Copa América"},
  {name:"Uruguay",flag:"🇺🇾",region:"conmebol",world:2,continental:15,competition:"Copa América"},
  {name:"Brasil",flag:"🇧🇷",region:"conmebol",world:5,continental:9,competition:"Copa América"},
  {name:"México",flag:"🇲🇽",region:"concacaf",world:0,continental:10,competition:"Copa Oro (1991–2025)"},
  {name:"Alemania",flag:"🇩🇪",region:"uefa",world:4,continental:3,competition:"Eurocopa"},
  {name:"Egipto",flag:"🇪🇬",region:"caf",world:0,continental:7,competition:"Copa Africana"},
  {name:"Estados Unidos",flag:"🇺🇸",region:"concacaf",world:0,continental:7,competition:"Copa Oro"},
  {name:"España",flag:"🇪🇸",region:"uefa",world:2,continental:4,competition:"Eurocopa"},
  {name:"Italia",flag:"🇮🇹",region:"uefa",world:4,continental:2,competition:"Eurocopa"},
  {name:"Camerún",flag:"🇨🇲",region:"caf",world:0,continental:5,competition:"Copa Africana"},
  {name:"Francia",flag:"🇫🇷",region:"uefa",world:2,continental:2,competition:"Eurocopa"},
  {name:"Ghana",flag:"🇬🇭",region:"caf",world:0,continental:4,competition:"Copa Africana"},
  {name:"Japón",flag:"🇯🇵",region:"afc",world:0,continental:4,competition:"Copa Asiática"},
  {name:"Arabia Saudita",flag:"🇸🇦",region:"afc",world:0,continental:3,competition:"Copa Asiática"},
  {name:"Nigeria",flag:"🇳🇬",region:"caf",world:0,continental:3,competition:"Copa Africana"},
  {name:"Costa de Marfil",flag:"🇨🇮",region:"caf",world:0,continental:3,competition:"Copa Africana"},
  {name:"Paraguay",flag:"🇵🇾",region:"conmebol",world:0,continental:2,competition:"Copa América"},
  {name:"Chile",flag:"🇨🇱",region:"conmebol",world:0,continental:2,competition:"Copa América"},
  {name:"Perú",flag:"🇵🇪",region:"conmebol",world:0,continental:2,competition:"Copa América"},
  {name:"Países Bajos",flag:"🇳🇱",region:"uefa",world:0,continental:1,competition:"Eurocopa"},
  {name:"Portugal",flag:"🇵🇹",region:"uefa",world:0,continental:1,competition:"Eurocopa"},
  {name:"Inglaterra",flag:"🏴",region:"uefa",world:1,continental:0,competition:"Eurocopa"},
];
const REGIONS:{id:Region|"all";label:string}[]=[
  {id:"all",label:"Todas"},
  {id:"conmebol",label:"Copa América"},
  {id:"uefa",label:"Eurocopa"},
  {id:"caf",label:"Copa Africana"},
  {id:"afc",label:"Copa Asiática"},
  {id:"concacaf",label:"Copa Oro"},
];
function ClubMark({club,logos}:{club:ClubTitle;logos:Record<string,number>}) {
  return <span class="historic-club-name">
    <HistoricClubCrest name={club.name} verifiedId={logos[club.name]}
      fallbackId={club.teamId}/>
    <span class="historic-club-text">{club.name}
      <small><HistoricFlag country={club.country} compact/>{club.country}</small>
    </span>
  </span>;
}
/** Independent full-width table so the homepage can stack its rankings. */
export function ClubHonours() {
  const {result: crestResult} = useApi<Record<string,number>>("/api/history/club-crests",0);
  const logos = crestResult?.data || {};
  return (
    <section class="historical-honours-section" id="copas-clubes">
      <div class="view-heading"><div><span class="eyebrow">PALMARÉS MUNDIAL · CLUBES</span>
        <h2>Clubes con más títulos internacionales</h2></div></div>
      <p class="coverage-notice">Corte histórico: octubre de 2026. Solo títulos internacionales oficiales de primer equipo masculino: copas de confederación, supercopas internacionales y títulos mundiales/intercontinentales. No incluye ligas ni copas nacionales, amistosos, ni Copa de Ferias/Copa Latina. No existe un único registro mundial con criterios totalmente uniformes; es una selección documentada, no una clasificación oficial de FIFA.</p>
      <div class="panel table-scroll" tabIndex={0} role="region" aria-label="Ranking internacional de clubes">
        <table><thead><tr><th>#</th><th>Club</th><th>Copas continentales</th><th>Mundiales / intercontinentales</th><th>Otras int.</th><th>Total</th></tr></thead>
          <tbody>{sortedClubs.map((club,i)=><tr key={club.name}>
            <td class="rank">{i+1}</td><th scope="row" title={club.detail}><ClubMark club={club} logos={logos}/></th>
            <td>{club.confed}</td><td>{club.world}</td><td>{club.other||"—"}</td>
            <td class="points"><strong>{club.confed+club.world+(club.other||0)}</strong></td>
          </tr>)}</tbody>
        </table>
      </div>
      <p class="updated">Para comprobar el desglose: <a href="https://es.uefa.com/uefachampionsleague/news/0254-0e97b2d74bea-89896c169762-1000--los-equipos-mas-laureados/" target="_blank" rel="noopener noreferrer">UEFA · Palmarés histórico ↗</a> · <a href="https://www.realmadrid.com/en-US/the-club/track-record/football" target="_blank" rel="noopener noreferrer">Real Madrid · palmarés oficial ↗</a> · <a href="https://www.sobrefutbol.com/torneos/equipos_mas_ganadores.htm" target="_blank" rel="noopener noreferrer">Comparación internacional ↗</a>. Algunos rankings alternativos añaden antiguas copas regionales y muestran cifras distintas.</p>
    </section>
  );
}

/** National team filters and sorting belong only to this table. */
export function NationalHonours() {
  const [region,setRegion]=useState<Region|"all">("all");
  const [order,setOrder]=useState<"all"|"world">("all");
  const nations=[...NATIONS].filter(n=>region==="all"||n.region===region)
    .sort((a,b)=>order==="world" ? b.world-a.world || b.continental-a.continental :
      (b.world+b.continental)-(a.world+a.continental) || b.world-a.world);
  return (
    <section class="historical-honours-section" id="copas-selecciones">
      <div class="view-heading"><div><span class="eyebrow">PALMARÉS MUNDIAL · SELECCIONES</span>
        <h2>Selecciones con más Mundiales y copas continentales</h2></div></div>
      <p class="coverage-notice">Selecciones mayores masculinas. Total = Copas del Mundo FIFA + campeonato continental principal (Copa América, Eurocopa, AFCON, Copa Asiática o Copa Oro). Quedan fuera Confederaciones, Nations League, Finalissima, Juegos Olímpicos y torneos juveniles. Para CONCACAF la columna registra la Copa Oro moderna, sin campeonatos previos a 1991; no es una suma de todos los trofeos oficiales. España incluye su Mundial 2026.</p>
      <div class="sports-tabs historical-filter-tabs" role="group" aria-label="Filtrar selecciones por confederación">
        {REGIONS.map(item=><button key={item.id} class={region===item.id?"active":""}
          onClick={()=>setRegion(item.id)}>{item.label}</button>)}
      </div>
      <div class="sports-tabs historical-filter-tabs" role="group" aria-label="Ordenar ranking de selecciones">
        <button class={order==="all"?"active":""} onClick={()=>setOrder("all")}>Copas totales</button>
        <button class={order==="world"?"active":""} onClick={()=>setOrder("world")}>Más Mundiales</button>
      </div>
      <div class="panel table-scroll" tabIndex={0} role="region" aria-label="Títulos de selecciones">
        <table><thead><tr><th>#</th><th>Selección</th><th>Mundiales</th><th>Copas continentales</th><th>Competición</th><th>Total</th></tr></thead>
          <tbody>{nations.map((nation,i)=><tr key={nation.name}>
            <td class="rank">{i+1}</td>
            <th scope="row"><span class="historic-club-name"><HistoricFlag country={nation.name}/>{nation.name}</span></th>
            <td>{nation.world}</td><td>{nation.continental}</td><td>{nation.competition}</td>
            <td class="points"><strong>{nation.world+nation.continental}</strong></td>
          </tr>)}</tbody>
        </table>
      </div>
      <p class="updated">Fuentes: <a href="https://www.fifa.com/en/tournaments/mens/worldcup/articles/world-cup-champions-1982-2026-italy-argentina-germany-brazil-france-spain" target="_blank" rel="noopener noreferrer">FIFA · Mundiales hasta 2026 ↗</a> · <a href="https://copaamerica.com/es/novedades/titulos-argentina-campeon-copa-america" target="_blank" rel="noopener noreferrer">CONMEBOL · Copa América ↗</a> · <a href="https://es.uefa.com/uefaeuro/history/winners/" target="_blank" rel="noopener noreferrer">UEFA · Eurocopa ↗</a> · <a href="https://www.cafonline.com/afcon2025/news/totalenergies-caf-africa-cup-of-nations-afcon-finals-records/" target="_blank" rel="noopener noreferrer">CAF · Copa Africana ↗</a> · <a href="https://es.concacaf.com/competitions/gold-cup/news/jimenez-y-alvarez-guian-a-mexico-a-su-decimo-titulo-de-copa-oro" target="_blank" rel="noopener noreferrer">CONCACAF · Copa Oro ↗</a>.</p>
    </section>
  );
}

/** Retained as the dedicated complete archive page. */
export function HistoricalHonours() {
  return <><ClubHonours/><NationalHonours/></>;
}
