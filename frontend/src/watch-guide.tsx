import { useEffect, useState } from "preact/hooks";
import { useApi } from "./api";
import { BettingGuide } from "./betting-guide";

/** Guía editorial de derechos. No garantiza que un partido específico esté disponible.
 * Fuentes oficiales 2026, revisables al cambiar los acuerdos.
 */
type Channel = { name: string; url: string; coverage: string };
type Country = "AR"|"BR"|"US"|"CA"|"MX"|"ES"|"GB"|"AU"|"CL"|"CO"|"PE"|"UY"|"PY"|"EC"|"BO"|"VE"|"NZ"|"IT"|"DE"|"FR"|"DO";
type Category = string;
const countries: {code:Country; name:string}[] = [
  {code:"AR",name:"Argentina"},{code:"BR",name:"Brasil"},{code:"US",name:"Estados Unidos"},
  {code:"CA",name:"Canadá"},{code:"MX",name:"México"},{code:"ES",name:"España"},
  {code:"GB",name:"Reino Unido"},{code:"AU",name:"Australia"},
  {code:"CL",name:"Chile"},{code:"CO",name:"Colombia"},{code:"PE",name:"Perú"},{code:"UY",name:"Uruguay"},
  {code:"PY",name:"Paraguay"},{code:"EC",name:"Ecuador"},{code:"BO",name:"Bolivia"},{code:"VE",name:"Venezuela"},
  {code:"NZ",name:"Nueva Zelanda"},{code:"IT",name:"Italia"},{code:"DE",name:"Alemania"},
  {code:"FR",name:"Francia"},{code:"DO",name:"República Dominicana"},
];
const categories: {code:Category; name:string}[] = [
  {code:"argentina",name:"Fútbol argentino / Copa Argentina"},
  {code:"libertadores",name:"Libertadores / Sudamericana"},
  {code:"champions",name:"Champions League"},
  {code:"laliga",name:"LaLiga"},
  {code:"nba",name:"NBA"},
  {code:"nfl",name:"NFL"},
  {code:"nhl",name:"NHL"},
  {code:"mlb",name:"MLB"},
  {code:"f1",name:"Fórmula 1"},
  {code:"afl",name:"Fútbol australiano AFL"},
  {code:"rugby",name:"Rugby"},
  {code:"mls",name:"MLS / fútbol de Estados Unidos"},
  {code:"copa-america",name:"Copa América / Eliminatorias CONMEBOL"},
  {code:"mundial",name:"Copa Mundial FIFA y Eliminatorias"},
  {code:"sudamericana",name:"Copa Sudamericana / Recopa"},
  {code:"europa-league",name:"Europa League / Conference League"},
  {code:"premier-league",name:"Premier League"},
  {code:"serie-a",name:"Serie A de Italia"},
  {code:"bundesliga",name:"Bundesliga"},
  {code:"ligue1",name:"Ligue 1 / Copa Francia"},
  {code:"libertadores-fem",name:"Fútbol femenino internacional"},
  {code:"wnba",name:"WNBA"},
  {code:"basquet",name:"Básquet / Euroliga / FIBA / AmeriCup"},
  {code:"handball",name:"Handball / Mundial / EHF"},
  {code:"volleyball",name:"Vóley / VNL / Mundial / CEV"},
  {code:"cricket",name:"Cricket / ICC / ligas"},
  {code:"rugby-cups",name:"Rugby Championship / Mundial / Seis Naciones"},
  {code:"rugby-clubs",name:"Top 14 / URC / Super Rugby / Premiership"},
  {code:"f1-support",name:"Fórmula 2 / Fórmula 3 / categorías motor"},

];
const ch=(name:string,url:string,coverage:string):Channel=>({name,url,coverage});
const guide: Partial<Record<Country,Partial<Record<Category,Channel[]>>>> = {
  AR:{
    argentina:[ch("TyC Sports Play","https://play.tycsports.com/","Copa Argentina: acceso con cableoperador; verificar programación"),ch("ESPN Premium","https://www.espn.com.ar/","Partidos seleccionados de Liga Profesional; requiere pack fútbol")],
    libertadores:[ch("ESPN / Disney+ Premium","https://www.disneyplus.com/es-ar","Partidos de Libertadores y Sudamericana; disponibilidad según cruce")],
    champions:[ch("UEFA · socios de transmisión","https://www.uefa.com/uefachampionsleague/news/0253-0d82037aaedd-f371c464f919-1000--where-to-watch-the-uefa-champions-league/","ESPN y FOX Sports Argentina")],
    laliga:[ch("ESPN / Disney+","https://www.disneyplus.com/es-ar","Derechos de ESPN para encuentros seleccionados"),ch("DSPORTS / DGO","https://www.directvgo.com/","Cobertura de LaLiga según partido")],
    nba:[ch("NBA League Pass","https://www.nba.com/watch/league-pass-stream/","Cobertura por suscripción y restricciones territoriales")],
    nfl:[ch("NFL Game Pass en DAZN","https://www.dazn.com/","Partidos internacionales, sujeto a condiciones")],
    nhl:[ch("NHL · dónde ver por país","https://www.nhl.com/info/how-to-watch-and-stream-nhl-games","Consultar derechos argentinos; NHL.TV en DAZN no es universal")],
    mlb:[ch("MLB.TV","https://www.mlb.com/live-stream-games/","Verificar exclusividades y bloqueos por territorio")],
    f1:[ch("F1 TV","https://f1tv.formula1.com/","Disponibilidad y modalidad según territorio")],
    afl:[ch("Watch AFL","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Streaming oficial fuera de Australia")],
    rugby:[ch("RugbyPass TV","https://rugbypass.tv/","Solo torneos sin restricciones locales"),ch("ESPN / Disney+","https://www.disneyplus.com/es-ar","Torneos seleccionados; confirmar evento")],
  },
  BR:{
    champions:[ch("UEFA · Brasil","https://www.uefa.com/uefachampionsleague/news/0253-0d82037aaedd-f371c464f919-1000--where-to-watch-the-uefa-champions-league/","TNT Sports y SBT para Champions")],
    nfl:[ch("NFL Game Pass · DAZN","https://www.dazn.com/","Oferta internacional")],
    nba:[ch("NBA League Pass","https://www.nba.com/watch/league-pass-stream/","Verificar restricciones")],
    f1:[ch("F1 TV","https://f1tv.formula1.com/","Disponibilidad local")],
    afl:[ch("Watch AFL","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Exterior de Australia")],
  },
  US:{
    champions:[ch("Paramount+","https://www.paramountplus.com/","UEFA Champions League, según calendario"),ch("TUDN","https://www.tudn.com/","Cobertura en español")],
    nfl:[ch("NFL · Ways to Watch","https://www.nfl.com/ways-to-watch/","CBS, FOX, NBC, ESPN, Prime Video y otros; depende del partido")],
    nba:[ch("NBA · Where to Watch","https://www.nba.com/news/how-to-watch-games-2026-27-season","ESPN/ABC, NBC/Peacock y Prime Video según fecha")],
    nhl:[ch("NHL · guía de transmisión","https://www.nhl.com/info/how-to-watch-and-stream-nhl-games","ESPN/ABC, TNT, ESPN+; bloqueos regionales")],
    mlb:[ch("MLB.TV","https://www.mlb.com/live-stream-games/","Bloqueos locales y transmisiones exclusivas")],
    f1:[ch("Apple TV · F1","https://tv.apple.com/","Cobertura exclusiva F1 2026 en Estados Unidos")],
    afl:[ch("Watch AFL","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Disponible fuera de Australia")],
  },
  CA:{
    champions:[ch("DAZN","https://www.dazn.com/","Socio de Champions League en Canadá")],
    nhl:[ch("Sportsnet+","https://www.sportsnet.ca/","Partidos disponibles según derechos"),ch("Prime Video","https://www.primevideo.com/","Juegos seleccionados")],
    nfl:[ch("NFL Game Pass · DAZN","https://www.dazn.com/","Sujeto a territorio")],
    nba:[ch("NBA League Pass","https://www.nba.com/watch/league-pass-stream/","Sujeto a restricciones")],
    mlb:[ch("MLB.TV","https://www.mlb.com/live-stream-games/","Restricciones específicas de Canadá")],
    afl:[ch("Watch AFL","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Fuera de Australia")],
  },
  MX:{
    champions:[ch("UEFA · socios de México","https://www.uefa.com/uefachampionsleague/news/0253-0d82037aaedd-f371c464f919-1000--where-to-watch-the-uefa-champions-league/","HBO Max y FOX, según partido")],
    nfl:[ch("NFL Game Pass · DAZN","https://www.dazn.com/","Verificar disponibilidad territorial")],
    nba:[ch("NBA League Pass","https://www.nba.com/watch/league-pass-stream/","Verificar bloqueos")],
    mlb:[ch("MLB.TV","https://www.mlb.com/live-stream-games/","Verificar restricciones")],
    afl:[ch("Watch AFL","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Fuera de Australia")],
  },
  ES:{
    champions:[ch("Movistar Plus+","https://www.movistarplus.es/","Derechos Champions League, según paquete")],
    laliga:[ch("Movistar Plus+","https://www.movistarplus.es/","Cobertura LaLiga"),ch("DAZN","https://www.dazn.com/","Jornadas y encuentros contratados")],
    nba:[ch("NBA League Pass","https://www.nba.com/watch/league-pass-stream/","Streaming oficial")],
    nfl:[ch("NFL Game Pass · DAZN","https://www.dazn.com/","Cobertura internacional")],
    f1:[ch("F1 TV","https://f1tv.formula1.com/","Consultar modalidades disponibles en España")],
    afl:[ch("Watch AFL","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Exterior de Australia")],
  },
  GB:{
    champions:[ch("TNT Sports","https://www.tntsports.co.uk/","Socio Champions"),ch("Amazon Prime Video","https://www.primevideo.com/","Selección de partidos")],
    nfl:[ch("NFL Game Pass · DAZN","https://www.dazn.com/","Puede haber blackouts")],
    nba:[ch("NBA League Pass","https://www.nba.com/watch/league-pass-stream/","Verificar cobertura")],
    nhl:[ch("NHL · guía por país","https://www.nhl.com/info/how-to-watch-and-stream-nhl-games","NHL.TV vía DAZN en territorios elegibles")],
    f1:[ch("Sky Sports F1 / NOW","https://www.skysports.com/f1","Derechos F1 Reino Unido")],
    afl:[ch("Watch AFL","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Exterior de Australia")],
  },
  AU:{
    champions:[ch("Stan Sport","https://www.stan.com.au/sport","Socio Champions en Australia")],
    afl:[ch("Kayo Sports / Foxtel","https://kayosports.com.au/","Cobertura nacional de AFL"),ch("AFL · transmisiones oficiales","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Channel 7 y socios domésticos")],
    rugby:[ch("Stan Sport","https://www.stan.com.au/sport","Eventos contratados")],
    nba:[ch("NBA League Pass","https://www.nba.com/watch/league-pass-stream/","Verificar restricciones")],
    nfl:[ch("NFL Game Pass · DAZN","https://www.dazn.com/","Cobertura internacional")],
    f1:[ch("F1 TV","https://f1tv.formula1.com/","Verificar disponibilidad")],
  },
};

// Acuerdos regionales: UEFA 2026/27 (ESPN en Sudamérica salvo Brasil),
// LaLiga 2026-2032 (ESPN y DSPORTS en nueve mercados hispanohablantes).
for (const code of ["CL","CO","PE","UY","PY","EC","BO","VE"] as Country[]) {
  guide[code] = {
    champions:[ch("ESPN / UEFA · operadores locales","https://www.uefa.com/uefachampionsleague/news/0253-0d82037aaedd-f371c464f919-1000--where-to-watch-the-uefa-champions-league/","ESPN en Sudamérica hispanohablante según evento")],
    laliga:[ch("ESPN / Disney+","https://www.disneyplus.com/","Derechos regionales de LaLiga"),ch("DSPORTS / DGO","https://www.directvgo.com/","Partidos según programación del país")],
    nfl:[ch("NFL Game Pass · DAZN","https://www.dazn.com/","Oferta internacional, verificar restricciones")],
    nba:[ch("NBA League Pass","https://www.nba.com/watch/league-pass-stream/","Disponibilidad territorial")],
    mlb:[ch("MLB.TV","https://www.mlb.com/live-stream-games/","Bloqueos por país y evento")],
    afl:[ch("Watch AFL","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Disponible fuera de Australia")],
  };
}
guide.NZ = {
  champions:[ch("DAZN","https://www.dazn.com/","Socio Champions League de Nueva Zelanda")],
  afl:[ch("Watch AFL","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Para público fuera de Australia")],
  nfl:[ch("NFL Game Pass · DAZN","https://www.dazn.com/","Según restricciones locales")],
};
guide.IT = {
  champions:[ch("Sky Sport / NOW","https://www.sky.it/","Champions League"),ch("Amazon Prime Video","https://www.primevideo.com/","Selección de partidos")],
  f1:[ch("Sky Sport F1 / NOW","https://www.sky.it/","Derechos F1 Italia confirmados por Formula 1")],
  nfl:[ch("NFL Game Pass · DAZN","https://www.dazn.com/","Cobertura internacional")],
};
guide.DE = {
  champions:[ch("UEFA · operadores Alemania","https://www.uefa.com/uefachampionsleague/news/0253-0d82037aaedd-f371c464f919-1000--where-to-watch-the-uefa-champions-league/","Revisar transmisiones por jornada")],
  nfl:[ch("NFL Game Pass · DAZN","https://www.dazn.com/","Cobertura internacional")],
  afl:[ch("Watch AFL","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Exterior de Australia")],
};
guide.FR = {
  champions:[ch("UEFA · operadores Francia","https://www.uefa.com/uefachampionsleague/news/0253-0d82037aaedd-f371c464f919-1000--where-to-watch-the-uefa-champions-league/","Revisar titulares de derechos")],
  nfl:[ch("NFL Game Pass · DAZN","https://www.dazn.com/","Cobertura internacional")],
  afl:[ch("Watch AFL","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Exterior de Australia")],
};
guide.DO = {
  champions:[ch("UEFA · República Dominicana","https://www.uefa.com/uefachampionsleague/news/0253-0d82037aaedd-f371c464f919-1000--where-to-watch-the-uefa-champions-league/","Televideo, ESPN, CPSL y S&T según evento")],
  nba:[ch("NBA League Pass","https://www.nba.com/watch/league-pass-stream/","Suscripción y cobertura según territorio")],
  nfl:[ch("NFL Game Pass · DAZN","https://www.dazn.com/","Consultar disponibilidad local")],
};

// Official global schedules and rights directories, never a claim that a
// specific event is broadcast by an unverified platform in a given country.
const directories: Partial<Record<Category,Channel[]>> = {
  mls:[ch("MLS Season Pass / Apple TV","https://tv.apple.com/","Revisar los derechos de MLS en tu territorio")],
  mundial:[ch("FIFA+ · partidos y derechos","https://www.plus.fifa.com/","Agenda y disponibilidad de eventos FIFA por territorio")],
  "copa-america":[ch("CONMEBOL · Copa América","https://copaamerica.com/","Programación y titulares de derechos por edición")],
  sudamericana:[ch("CONMEBOL · Sudamericana","https://www.conmebol.com/","Información oficial de la competición; no identifica canal por partido")],
  "europa-league":[ch("UEFA · socios de transmisión","https://www.uefa.com/uefaeuropaleague/","Comprobar broadcaster del torneo y país")],
  "premier-league":[ch("Premier League · Broadcasters","https://www.premierleague.com/en/broadcasters","Listado oficial por región")],
  "serie-a":[ch("Lega Serie A","https://www.legaseriea.it/","Consulta de programación y derechos locales")],
  bundesliga:[ch("Bundesliga · Where to watch","https://www.bundesliga.com/","Consultar socios locales por país")],
  ligue1:[ch("Ligue 1","https://ligue1.com/","Agenda y cobertura oficial")],
  "libertadores-fem":[ch("CONMEBOL","https://www.conmebol.com/","Cobertura de torneos femeninos según edición")],
  wnba:[ch("WNBA · Watch","https://www.wnba.com/","Agenda de transmisiones y League Pass")],
  basquet:[ch("FIBA · Courtside 1891","https://www.courtside1891.basketball/","Competiciones FIBA según derechos"),ch("EuroLeague TV","https://tv.euroleague.net/","Partidos de Euroliga con restricciones territoriales")],
  handball:[ch("EHF TV","https://www.ehftv.com/","Partidos EHF según derechos regionales"),ch("IHF · Handball","https://www.ihf.info/","Información oficial de Mundiales")],
  volleyball:[ch("VBTV · Volleyball World","https://subscribe.volleyballworld.com/","VNL y competiciones según disponibilidad"),ch("CEV","https://www.cev.eu/","Información oficial de competencias europeas")],
  cricket:[ch("ICC · Cricket","https://www.icc-cricket.com/","Información de broadcaster oficial por torneo")],
  "rugby-cups":[ch("RugbyPass TV","https://rugbypass.tv/","Solo eventos habilitados para tu país"),ch("World Rugby","https://www.world.rugby/","Programación y titulares de derechos")],
  "rugby-clubs":[ch("RugbyPass TV","https://rugbypass.tv/","Consultar Top 14, URC y Super Rugby según territorio"),ch("World Rugby","https://www.world.rugby/","Fuentes oficiales de competiciones")],
};
directories.argentina=guide.AR?.argentina;
directories.champions=[ch("UEFA · dónde ver","https://www.uefa.com/uefachampionsleague/news/0253-0d82037aaedd-f371c464f919-1000--where-to-watch-the-uefa-champions-league/","Revisar derechos por país")];
directories.libertadores=[ch("CONMEBOL","https://www.conmebol.com/","Consultar derechos oficiales del evento")];
directories.laliga=[ch("LaLiga","https://www.laliga.com/","Revisar transmisiones en tu país")];
directories.nba=[ch("NBA League Pass","https://www.nba.com/watch/league-pass-stream/","Disponibilidad por territorio")];
directories.nfl=[ch("NFL · Ways to Watch","https://www.nfl.com/ways-to-watch/","Transmisiones según país")];
directories.nhl=[ch("NHL · How to Watch","https://www.nhl.com/info/how-to-watch-and-stream-nhl-games","Derechos por región")];
directories.mlb=[ch("MLB.TV","https://www.mlb.com/live-stream-games/","Blackouts según mercado")];
directories.f1=[ch("Formula 1 · Where to Watch","https://www.formula1.com/en/toolbar/broadcast-information.html","Derechos por país")];
directories.rugby=directories["rugby-cups"];
directories.afl=[ch("AFL · Broadcast Guide","https://www.afl.com.au/matches/broadcast-guide/watch-afl","Programación local e internacional")];

export function WatchGuide({ initialSport, initialCountry = "AR" }: { initialSport?: string; initialCountry?: Country }) {
  const [country,setCountry] = useState<Country>(initialCountry);
  const [category,setCategory] = useState<Category>(
    (categories.some(c=>c.code===initialSport) ? initialSport : "argentina") as Category
  );
  const [autoCountry,setAutoCountry]=useState(true);
  const {result:region}=useApi<{country:string|null}>("/api/visitor/country",0);
  useEffect(()=>{
    const code=region?.data?.country;
    if(autoCountry&&code&&countries.some(c=>c.code===code)) setCountry(code as Country);
  },[region?.data?.country,autoCountry]);
  const current = guide[country]?.[category] || [];
  const general = (directories[category]||[]).filter(s=>!current.some(x=>x.url===s.url));
  const displayed = [...current,...general];
  return <section class="watch-guide panel">
    <h2>📺 Dónde ver los deportes</h2>
    <p class="updated">Guía por país y competición. No confirma la transmisión de un partido concreto; los derechos pueden cambiar dentro de la temporada y existir bloqueos.</p>
    <div class="watch-selectors">
      <label>País<select value={country} onChange={e=>{setCountry(e.currentTarget.value as Country);setAutoCountry(false);}}>
        {countries.map(c=><option value={c.code}>{c.name}</option>)}
      </select></label>
      <label>Deporte / torneo<select value={category} onChange={e=>setCategory(e.currentTarget.value as Category)}>
        {categories.map(c=><option value={c.code}>{c.name}</option>)}
      </select></label>
    </div>
    {displayed.length ? <div class="watch-links">{displayed.map(c=><a href={c.url} target="_blank" rel="noopener noreferrer" key={c.name}>
      <strong>{c.name} <span aria-hidden="true">↗</span></strong><small>{c.coverage}</small>
    </a>)}</div> : <p class="coverage-notice">Todavía no hay una fuente oficial verificada para esa combinación. No asignamos DAZN, TyC o Disney+ automáticamente a cada partido.</p>}
    <p class="updated">Los enlaces incluyen guías oficiales generales cuando no se conocen derechos específicos para el país seleccionado. La plataforma real, el plan y el territorio deben confirmarse antes de cada evento.</p>
    <BettingGuide country={country} />
  </section>;
}
