import { useState } from "preact/hooks";

/**
 * Published website favicons, used solely to identify the company.
 * They are NOT sponsored placements, standalone licensed brand assets
 * or evidence that the company is authorized in the viewer's province.
 */
type Brand = { label:string; domain:string; pattern:RegExp };
const BRANDS:Brand[] = [
  {label:"Betsson",domain:"www.betsson.bet.ar",pattern:/^betsson\b/i},
  {label:"Betano",domain:"www.betano.bet.ar",pattern:/^betano\b/i},
  {label:"bplay",domain:"caba.bplay.bet.ar",pattern:/^bplay\b/i},
  {label:"bet365",domain:"www.bet365.bet.ar",pattern:/^bet\s*365\b/i},
  {label:"BetWarrior",domain:"www.betwarrior.bet.ar",pattern:/^betwarrior\b/i},
  {label:"Sportsbet",domain:"sports.bet.ar",pattern:/^sports?bet\b/i},
  {label:"Stake",domain:"pba.stake.bet.ar",pattern:/^stake\b/i},
  {label:"Codere",domain:"www.codere.es",pattern:/^codere\b/i},
  {label:"Betfair",domain:"www.betfair.com",pattern:/^betfair\b/i},
  {label:"Winamax",domain:"www.winamax.fr",pattern:/^winamax\b/i},
  {label:"Betclic",domain:"www.betclic.fr",pattern:/^betclic\b/i},
  {label:"PMU",domain:"www.pmu.fr",pattern:/^pmu\b/i},
  {label:"Sportium",domain:"www.sportium.es",pattern:/^sportium\b/i},
  {label:"Unibet",domain:"www.unibet.fr",pattern:/^unibet\b/i},
  {label:"bwin",domain:"www.bwin.com",pattern:/^bwin\b/i},
  {label:"DraftKings",domain:"www.draftkings.com",pattern:/^draftkings\b/i},
  {label:"FanDuel",domain:"www.fanduel.com",pattern:/^fanduel\b/i},
];
export function bookmakerBrand(name:string) {
  return BRANDS.find(brand=>brand.pattern.test(name.trim()));
}
export function BookmakerMark({
  name, compact=false, showName=true,
}: {name:string;compact?:boolean;showName?:boolean}) {
  const brand=bookmakerBrand(name);
  const [failed,setFailed]=useState(false);
  const label=brand?.label || name;
  const fallback=label.replace(/[^\p{L}\p{N} ]/gu,"").split(/\s+/)
    .map(x=>x[0]).slice(0,2).join("").toUpperCase() || label.slice(0,2).toUpperCase();
  return <span class={compact?"bookmaker-brand bookmaker-brand-compact":"bookmaker-brand"}
    title={label} aria-label={label}>
    <span class="bookmaker-brand-mark">
      {brand&&!failed ? <img loading="lazy" decoding="async" alt=""
        width={compact?22:34} height={compact?22:34}
        src={`https://www.google.com/s2/favicons?domain=${encodeURIComponent(brand.domain)}&sz=128`}
        onError={()=>setFailed(true)}/>:
        <span class="bookmaker-brand-initials" aria-hidden="true">{fallback}</span>}
    </span>
    {showName && <strong>{label}</strong>}
  </span>;
}
