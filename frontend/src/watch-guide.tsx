import { useState } from "preact/hooks";

/** Guía editorial de derechos. No garantiza que un partido específico esté disponible.
 * Fuentes oficiales 2026, revisables al cambiar los acuerdos.
 */
type Channel = { name: string; url: string; coverage: string };
type Country = "AR"|"BR"|"US"|"CA"|"MX"|"ES"|"GB"|"AU";
type Category = "argentina"|"libertadores"|"champions"|"laliga"|"nba"|"nfl"|"nhl"|"mlb"|"f1"|"afl"|"rugby";
const countries: {code:Country; name:string}[] = [
  {code:"AR",name:"Argentina"},{code:"BR",name:"Brasil"},{code:"US",name:"Estados Unidos"},
  {code:"CA",name:"Canadá"},{code:"MX",name:"México"},{code:"ES",name:"España"},
  {code:"GB",name:"Reino Unido"},{code:"AU",name:"Australia"},
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

export function WatchGuide({ initialSport, initialCountry = "AR" }: { initialSport?: string; initialCountry?: Country }) {
  const [country,setCountry] = useState<Country>(initialCountry);
  const [category,setCategory] = useState<Category>(
    (categories.some(c=>c.code===initialSport) ? initialSport : "argentina") as Category
  );
  const current = guide[country]?.[category] || [];
  return <section class="watch-guide panel">
    <h2>📺 Dónde ver los deportes</h2>
    <p class="updated">Guía por país y competición. No confirma la transmisión de un partido concreto; los derechos pueden cambiar dentro de la temporada y existir bloqueos.</p>
    <div class="watch-selectors">
      <label>País<select value={country} onChange={e=>setCountry(e.currentTarget.value as Country)}>
        {countries.map(c=><option value={c.code}>{c.name}</option>)}
      </select></label>
      <label>Deporte / torneo<select value={category} onChange={e=>setCategory(e.currentTarget.value as Category)}>
        {categories.map(c=><option value={c.code}>{c.name}</option>)}
      </select></label>
    </div>
    {current.length ? <div class="watch-links">{current.map(c=><a href={c.url} target="_blank" rel="noopener noreferrer" key={c.name}>
      <strong>{c.name} <span aria-hidden="true">↗</span></strong><small>{c.coverage}</small>
    </a>)}</div> : <p class="coverage-notice">Todavía no hay una fuente oficial verificada para esa combinación. No asignamos DAZN, TyC o Disney+ automáticamente a cada partido.</p>}
    <p class="updated">Fuentes: UEFA, AFA/TyC Sports, ESPN, LaLiga, NFL, NBA, NHL, MLB, Formula 1 y AFL. Los enlaces abren plataformas o guías legales; Latente no retransmite señales.</p>
  </section>;
}
