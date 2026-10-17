import { useState } from "preact/hooks";

/** Editorial identification of the competition or its governing body.
 * These are verified Wikimedia Commons file names; logos are trademarks,
 * not claims of sponsorship or commercial licensing. Generic sport categories
 * without a universal brand fall back to their familiar sport pictogram.
 * When the external asset is unavailable, the label remains accessible.
 */
const SPORT_LOGOS: Record<string,{file:string;kind:"shield"|"wide"|"tall";label:string}> = {
  nba: {file:"National Basketball Association logo 2017-present.svg",kind:"tall",label:"NBA"},
  f1: {file:"Formula One logo.svg",kind:"wide",label:"Fórmula 1"},
  nfl: {file:"NFL wordmark logo 2008.svg",kind:"shield",label:"NFL"},
  nhl: {file:"National Hockey League shield.svg",kind:"shield",label:"NHL"},
  mlb: {file:"Major League Baseball logo.svg",kind:"wide",label:"MLB"},
  wnba: {file:"WNBA logo.png",kind:"wide",label:"WNBA"},
  cricket: {file:"ICC logo (2026).svg",kind:"wide",label:"Consejo Internacional de Cricket"},
  basketball: {file:"FIBA logo.svg",kind:"shield",label:"Federación Internacional de Básquet"},
  handball: {file:"Internationalen Handballföderation.png",kind:"shield",label:"Federación Internacional de Handball"},
  volleyball: {file:"Fédération Internationale de Volleyball logo.svg",kind:"wide",label:"Federación Internacional de Vóley"},
};

export function SportNavLogo({slug,fallback}:{slug:string;fallback:string}) {
  const [failed,setFailed]=useState(false);
  const item=SPORT_LOGOS[slug];
  if(!item||failed) return <span class="sport-nav-pictogram" aria-hidden="true">{fallback}</span>;
  // Wikimedia Special:FilePath is an explicitly verified filename lookup.
  // No guessed CDN hashes; keep small logos lazy and source-hosted.
  const url=`https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(item.file)}`;
  return <img class={`sport-nav-logo sport-nav-logo--${item.kind}`}
    src={url} alt="" title={item.label} width="26" height="24"
    loading="lazy" decoding="async" referrerPolicy="no-referrer"
    onError={()=>setFailed(true)}/>;
}
