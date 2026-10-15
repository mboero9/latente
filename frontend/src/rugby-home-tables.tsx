import { useEffect, useState } from "preact/hooks";
import { useApi } from "./api";
import { TeamMark } from "./team-mark";

type Competition = {slug:string;name:string;region?:string|null;seasons?:number[]};
type Position = {team:string;team_id?:number|null;logo?:string|null;rank?:number|null;
  played?:number|null;won?:number|null;lost?:number|null;points?:number|null};
type RugbyData = {official:Position[];provider:string;season:number;updated_at?:string|null};

const COUNTRIES:Record<string,{label:string;slug:string}>={
  AR:{label:"Argentina · URBA Top 12",slug:"urba"},
  FR:{label:"Francia · Top 14",slug:"top-14"},
  ZA:{label:"Sudáfrica · Currie Cup",slug:"currie-cup"},
  NZ:{label:"Nueva Zelanda · NPC",slug:"npc-nz"},
  GB:{label:"Inglaterra · Premiership",slug:"premiership"},
  IE:{label:"Irlanda · URC",slug:"urc"},
  IT:{label:"Italia · Top10",slug:"top10-italia"},
  US:{label:"Estados Unidos · Major League Rugby",slug:"mlr"},
  AU:{label:"Australia · Super Rugby",slug:"super-rugby"},
  ES:{label:"Europa · Rugby Europe",slug:"europe-championship"},
  PT:{label:"Europa · Rugby Europe",slug:"europe-championship"},
};
function preferredCountry() {
  // Browser locale/timezone is a preference, NOT a verified geolocation.
  // Do not request device location or send visitor IP to outside services.
  try {
    const locale=navigator.language.split("-")[1]?.toUpperCase();
    if (locale && COUNTRIES[locale]) return locale;
    const tz=Intl.DateTimeFormat().resolvedOptions().timeZone || "";
    if (/Buenos_Aires|Argentina\//.test(tz)) return "AR";
    if (/Johannesburg/.test(tz)) return "ZA";
    if (/Auckland/.test(tz)) return "NZ";
    if (/Paris/.test(tz)) return "FR";
    if (/London/.test(tz)) return "GB";
  } catch { /* unknown browser preferences */ }
  return "AR";
}
function MiniRugbyTable({slug,title}:{slug:string;title:string}) {
  const {result,loading}=useApi<RugbyData>(`/api/rugby/${slug}`, 300000);
  const rows=result?.data?.official || [];
  return <section class="panel rugby-home-card">
    <h3>🏉 {title}</h3>
    {loading?<p class="updated">Consultando clasificación…</p>:
      rows.length?<div class="table-scroll" role="region" aria-label={title} tabIndex={0}>
        <table><thead><tr><th>#</th><th>Club</th><th>PJ</th><th>Pts</th></tr></thead><tbody>
          {rows.map((row,i)=><tr key={row.team}>
            <td>{row.rank??i+1}</td><th scope="row"><span class="sport-team-inline">
              <TeamMark name={row.team} logo={row.logo} sport="rugby" teamId={row.team_id}/>{row.team}
            </span></th><td>{row.played??"—"}</td><td>{row.points??"—"}</td>
          </tr>)}
        </tbody></table></div>:
        <p class="updated">Todavía no hay tabla oficial verificada de esta competición.</p>}
    <a href={`#/sport/rugby`}>Ver rugby y competiciones →</a>
    {rows.length>0&&<p class="updated">Fuente: {result?.data?.provider}. Temporada {result?.data?.season}.</p>}
  </section>;
}
export function RugbyHomeTables() {
  const [country,setCountry]=useState(preferredCountry);
  const [local,setLocal]=useState(false);
  const {result:regionResult}=useApi<{country:string|null;source:string}>("/api/visitor/country",0);
  useEffect(()=>{
    const code=regionResult?.data?.country;
    if (!local && code && COUNTRIES[code]) setCountry(code);
  },[regionResult?.data?.country,local]);
  const options=Object.entries(COUNTRIES);
  const countryInfo=COUNTRIES[country]||COUNTRIES.AR;
  const outside=countryInfo.slug!=="urba";
  return <section class="rugby-home-block" aria-label="Rugby: Argentina y país del visitante">
    <div class="view-heading"><div><span class="eyebrow">RUGBY · POSICIONES</span>
      <h2>Argentina y ligas del mundo</h2></div></div>
    <MiniRugbyTable slug="urba" title="Argentina · URBA Top 12"/>
    <label class="season-label">Tabla de otro país
      <select value={country} onChange={e=>{setCountry(e.currentTarget.value);setLocal(true);}}>
        {options.map(([code,option])=><option value={code} key={code}>{option.label}</option>)}
      </select>
    </label>
    {outside&&<MiniRugbyTable slug={countryInfo.slug} title={countryInfo.label}/>}
    <p class="updated">{local?"País elegido manualmente.":"País sugerido por Cloudflare cuando está disponible; si no, por idioma o zona horaria. La selección puede cambiarse."} Podés elegir otra competición desde el menú.</p>
  </section>;
}
