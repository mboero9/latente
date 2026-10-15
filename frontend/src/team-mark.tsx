import { useState } from "preact/hooks";

const providers: Record<string,string> = {
  nhl: "hockey", mlb: "baseball", nfl: "american-football",
  nba: "basketball", wnba: "basketball",
  basketball: "basketball", handball: "handball",
  volleyball: "volleyball", rugby: "rugby",
};
const allowed = new Set([
  "media.api-sports.io", "a.espncdn.com", "a1.espncdn.com",
  "a2.espncdn.com", "cdn.espn.com", "cdn.nba.com",
  "upload.wikimedia.org", "static.flashscore.com",
  "www.thesportsdb.com", "r2.thesportsdb.com", "thesportsdb.com",
]);

/** Real provider image when available; initial crest is only a placeholder. */
export function TeamMark({name,logo,sport,teamId}:{
  name:string; logo?:string|null; sport?:string;
  teamId?:number|string|null;
}) {
  const [bad,setBad]=useState(false);
  let url: string|undefined;
  if (logo) {
    try {
      const parsed = new URL(logo);
      if (parsed.protocol === "https:" && allowed.has(parsed.hostname)) url=logo;
    } catch { /* malformed provider image */ }
  }
  // API-Sports documents stable numeric team IDs and hosted team image URLs.
  // These may still return 404; never show a broken-image symbol.
  if (!url && sport && providers[sport] && teamId != null && /^\d+$/.test(String(teamId)))
    url=`https://media.api-sports.io/${providers[sport]}/teams/${teamId}.png`;
  const initials=name.trim().split(/\s+/).slice(0,2).map(w=>w[0]?.toUpperCase()||"").join("") || "?";
  return <span class="team-mark" title={url&&!bad?name:`Identificador de ${name}; escudo no disponible`}>
    {url&&!bad?<img src={url} alt="" loading="lazy" referrerPolicy="no-referrer"
      onError={()=>setBad(true)}/>:<span class="team-mark-placeholder" aria-hidden="true">{initials}</span>}
  </span>;
}
