import { BookmakerMark } from "./bookmaker-brands";
import type { BettingAudience } from "./betting-audience";

const CABA = ["Betsson","Betano","bplay"] as const;
const PBA = ["Sportsbet","Stake"] as const;

/** A compact, context-only strip under live match details.
 * Logos are NEVER paired with unassigned API odds or described as sponsors.
 * Rendered only after visitor expressly chooses an adult/jurisdiction
 * preference on the dedicated 18+ information page. No outbound betting links.
 */
export function LiveBookmakers({audience,geoCountry}:{
  audience:BettingAudience|null;geoCountry:string|null|undefined;
}) {
  if (geoCountry !== "AR" || !audience?.adult || audience.country !== "AR")
    return null;
  const brands=audience.province==="CABA"?CABA:PBA;
  return <div class="live-bookmakers" aria-label="Referencias de operadores 18 años o más">
    <span class="live-bookmakers-intro">18+ · Referencias {audience.province}</span>
    <span class="live-bookmakers-brands">
      {brands.map(name=><span class="live-bookmakers-brand" key={name}>
        <BookmakerMark name={name} compact/>
      </span>)}
    </span>
    <a href="#/bet">Consultar licencias ↗</a>
    <small>No patrocinado · Sin cuotas atribuidas</small>
  </div>;
}
