import { useState } from "preact/hooks";
import { TeamMark } from "./team-mark";

/** Profile photos use only verified API-Football player IDs.
 * Historic players outside the active coverage display honest initials.
 */
export function HistoricPlayerPortrait({name,playerId}:{
  name:string; playerId?:number;
}) {
  const [error,setError]=useState(false);
  const initials=name.split(/\s+/).slice(0,2).map(part=>part[0] || "")
    .join("").toUpperCase();
  return <span class="historic-player-portrait" title={name}>
    {playerId && !error ?
      <img alt={`Foto de ${name}`} width="34" height="34" loading="lazy"
        decoding="async" referrerPolicy="no-referrer"
        src={`https://media.api-sports.io/football/players/${playerId}.png`}
        onError={()=>setError(true)}/>:
      <span aria-hidden="true">{initials}</span>}
  </span>;
}

export function HistoricClubCrest({name,verifiedId,fallbackId}:{
  name:string; verifiedId?:number; fallbackId?:number;
}) {
  return <span class="historic-club-crest">
    <TeamMark name={name} sport="football" teamId={verifiedId || fallbackId}/>
  </span>;
}
