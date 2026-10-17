import { useState } from "preact/hooks";

/** F1 photos are provided by OpenF1 as optional *source URLs* for recent
 * sessions. Never construct unknown or fake player portraits.
 * Constructor marks below are independently verified Commons file names
 * (not Formula One's protected corporate F1 logo).
 */
const VERIFIED_LOGOS: Record<string,string> = {
 "mercedes":"Mercedes-AMG Petronas F1 Team logo (2026).svg",
 "mclaren":"McLaren logo (2026).svg",
 "alpine":"BWT Alpine F1 Team Logo.png",
 "alpine f1 team":"BWT Alpine F1 Team Logo.png",
 "haas f1 team":"Haas F1 Team Logo.svg",
 "haas":"Haas F1 Team Logo.svg",
 "williams":"Williams F1 logo 2026.png",
 "williams racing":"Williams F1 logo 2026.png",
 "audi":"Audif1.com logo17 (cropped).svg",
 "cadillac":"Cadillac Formula 1 Team logo.png",
 "red bull racing":"Red Bull Racing-Logo.png",
 "red bull":"Red Bull Racing-Logo.png",
};
const TEAM_COLOURS:Record<string,string>={
 "ferrari":"#e80020","red bull":"#3671c6",
 "red bull racing":"#3671c6", "rb f1 team":"#4681d7",
 "racing bulls":"#4681d7", "mercedes":"#00a19c",
 "mclaren":"#f58020", "alpine":"#0090ff",
 "haas f1 team":"#666666","williams":"#005aff",
 "audi":"#f50537","cadillac":"#555555",
 "aston martin":"#00594f",
};
const COUNTRY_CODE:Record<string,string> = {
 "Argentina":"ar","Australia":"au","Austria":"at","Bélgica":"be",
 "Brasil":"br","Canadá":"ca","China":"cn","Colombia":"co",
 "Chequia":"cz","Dinamarca":"dk","Países Bajos":"nl",
 "Finlandia":"fi","Francia":"fr","Alemania":"de","India":"in",
 "Indonesia":"id","Irlanda":"ie","Italia":"it","Japón":"jp",
 "Malasia":"my","México":"mx","Mónaco":"mc","Nueva Zelanda":"nz",
 "Polonia":"pl","Portugal":"pt","Rusia":"ru",
 "Sudáfrica":"za","España":"es","Suecia":"se",
 "Suiza":"ch","Tailandia":"th","Venezuela":"ve",
 "Reino Unido":"gb","Estados Unidos":"us",
 "Uruguay":"uy","Egipto":"eg"
};

export function F1CountryFlag({name}:{name:string}) {
 const [bad,setBad]=useState(false);
 const code=COUNTRY_CODE[name];
 return code&&!bad?<img class="f1-flag" alt="" title={name}
  loading="lazy" width="25" height="18"
  src={`https://flagcdn.com/32x24/${code}.png`}
  onError={()=>setBad(true)}/>:
  <span class="f1-flag-fallback" aria-hidden="true">◻</span>;
}
export function F1Portrait({name,photo}:{name:string;photo?:string|null}) {
 const [bad,setBad]=useState(false);
 let safe=false;
 try { const parsed=new URL(photo||""); safe=parsed.protocol==="https:" &&
   ["media.formula1.com","www.formula1.com"].includes(parsed.hostname); }
 catch { /* empty portrait */ }
 const initials=name.trim().split(/\s+/).slice(0,2).map(v=>v[0]||"").join("").toUpperCase();
 return <span class="f1-driver-photo" title={photo&&!bad?"Retrato: "+name:"Retrato no disponible"}>
  {safe&&!bad?<img src={photo!} alt={`Retrato de ${name}`}
    loading="lazy" decoding="async" onError={()=>setBad(true)}/>:
    <span aria-hidden="true">{initials}</span>}
 </span>;
}
export function F1TeamLogo({name}:{name:string}) {
 const [bad,setBad]=useState(false);
 // Joins like McLaren / Mercedes are not a single constructor emblem.
 const key=name.toLowerCase().trim();
 const filename=VERIFIED_LOGOS[key];
 const initials=name.split(/\s+/).slice(0,2).map(s=>s[0]).join("").toUpperCase();
 const colour=TEAM_COLOURS[key]||"#5e86a5";
 const url=filename?
  `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(filename)}`:null;
 return <span class="f1-team-logo" title={name}>
  {url&&!bad?<img alt="" src={url} loading="lazy" decoding="async"
    referrerPolicy="no-referrer" onError={()=>setBad(true)}/>:
    <span class="f1-team-fallback" style={{borderColor:colour,color:colour}}
      aria-hidden="true">{initials||"F1"}</span>}
 </span>;
}
