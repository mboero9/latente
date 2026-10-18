import { useState } from "preact/hooks";

const providers: Record<string,string> = {
  football: "football",
  nhl: "hockey", mlb: "baseball", nfl: "american-football",
  nba: "basketball", wnba: "basketball",
  basketball: "basketball", handball: "handball",
  volleyball: "volleyball", rugby: "rugby",
};
const allowed = new Set([
  "media.api-sports.io", "api.urba.org.ar", "a.espncdn.com", "a1.espncdn.com",
  "a2.espncdn.com", "cdn.espn.com", "cdn.nba.com",
  "upload.wikimedia.org", "static.flashscore.com",
  "www.thesportsdb.com", "r2.thesportsdb.com", "thesportsdb.com",
]);

// The official URBA 2026 Top 14 file names are independently listed by
// backend/app/rugby_clubs.py. This name lookup also covers tables whose provider
// omits a logo or returns an unrelated numerical team_id.
// Keep exact names (including known short forms), never fuzzy guesses.
const URBA_CRESTS: Record<string,string> = {
  "hindu":"hindu", "los tilos":"lostilos",
  "la plata rugby club":"laplata", "la plata rc":"laplata",
  "sic":"sic", "san isidro club":"sic",
  "belgrano ac":"belgrano", "belgrano athletic":"belgrano",
  "belgrano athletic club":"belgrano",
  "casi":"casi", "club atletico san isidro":"casi",
  "cuba":"cuba", "club universitario de buenos aires":"cuba",
  "newman":"newman", "newman rc":"newman",
  "alumni":"alumni", "alumni rc":"alumni",
  "los matreros":"losmatreros", "los matreros rc":"losmatreros",
  "b a c r c":"bacrc", "bacrc":"bacrc",
  "buenos aires cricket rugby club":"bacrc",
  "buenos aires cricket and rugby club":"bacrc",
  "regatas bella vista":"regatasbellavista", "club regatas bella vista":"regatasbellavista",
  "champagnat":"champagnat", "club champagnat":"champagnat",
  "club atletico del rosario":"rosario", "atletico del rosario":"rosario",
  "atletico rosario":"rosario",
};
function urbaLogo(name:string):string|undefined {
  const normalized=name.normalize("NFD").replace(/[\u0300-\u036f]/g,"")
    .toLowerCase().replace(/[^a-z0-9]+/g," ").trim();
  const file=URBA_CRESTS[normalized];
  return file ? `https://api.urba.org.ar/img/clubs/${file}.png` : undefined;
}

/** Use an official logo when available; initials are only the final fallback. */
export function TeamMark({name,logo,sport,teamId}:{
  name:string; logo?:string|null; sport?:string;
  teamId?:number|string|null;
}) {
  const [bad,setBad]=useState(false);
  // Prefer the verified URBA club crest to opaque provider URLs/IDs.
  let url: string|undefined = sport==="rugby" ? urbaLogo(name) : undefined;
  if (!url && logo) {
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
