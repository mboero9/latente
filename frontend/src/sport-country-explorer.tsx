import { useState } from "preact/hooks";

export type SportCompetition = {
  name:string; country:string; provider_id:number|null; seasons:number[];
  official_url:string|null; verified_source:"federation"|"api_sports_catalog";
  has_imported_data:boolean;
};
export type CountryGame = {
  league_id?:number|string|null; league:string; country?:string|null;
};

const COUNTRY_ALIASES:Record<string,string>={
  "argentina":"Argentina","argentinian":"Argentina",
  "world":"Internacional","international":"Internacional",
  "europe":"Europa","usa":"Estados Unidos","united states":"Estados Unidos",
  "spain":"España","brazil":"Brasil","brasil":"Brasil",
  "italy":"Italia","germany":"Alemania","france":"Francia",
  "poland":"Polonia","turkey":"Turquía","greece":"Grecia",
  "japan":"Japón","mexico":"México",
};
export function normalizedSportCountry(raw?:string|null) {
  const name=String(raw||"").trim();
  return COUNTRY_ALIASES[name.toLowerCase()]||name||"Sin país informado";
}
export function countryForGame(game:CountryGame,competitions:SportCompetition[]) {
  if (game.country) return normalizedSportCountry(game.country);
  const matching=competitions.filter(c=>c.provider_id!==null &&
    String(c.provider_id)===String(game.league_id));
  return matching.length===1?matching[0].country:"Sin país informado";
}
export function matchesCompetition(game:CountryGame,selection:string,competitions:SportCompetition[]) {
  if(selection==="all") return true;
  const c=competitions.find(x=>competitionKey(x)===selection);
  if(!c) return false;
  if(c.provider_id!==null) return String(game.league_id)===String(c.provider_id);
  return false; // federation-only entry without an actual provider fixture ID
}
export function competitionKey(c:SportCompetition) {
  return c.provider_id!==null?`id:${c.provider_id}`:`official:${c.country}:${c.name}`;
}

export function SportCountryExplorer({
  sport,country,onCountry,league,onLeague,competitions,loading,numberOfGames,
}:{
  sport:string;country:string;onCountry:(v:string)=>void;
  league:string;onLeague:(v:string)=>void;competitions:SportCompetition[];
  loading:boolean;numberOfGames:number;
}) {
  const [expanded,setExpanded]=useState(false);
  const countries=[...new Set(competitions.map(c=>c.country))].sort((a,b)=>
    a==="Argentina"?-1:b==="Argentina"?1:
    a==="Internacional"?-1:b==="Internacional"?1:
    a.localeCompare(b,"es"));
  const actual=country==="all"?competitions:competitions.filter(c=>c.country===country);
  const display=expanded?actual:actual.slice(0,24);
  const sportLabel=sport==="basketball"?"básquet FIBA":
    sport==="volleyball"?"vóley":"handball";
  return <section class="sport-country-explorer panel" aria-label={`Ligas de ${sportLabel} por país`}>
    <div class="sport-country-header">
      <div><span class="eyebrow">COMPETICIONES POR PAÍS</span>
        <h2>Ligas de {sportLabel}</h2>
        <p>Argentina primero. Elegí un país y una competición para filtrar
          los partidos reales que ya tiene Latente.</p>
      </div>
      <div class="sport-country-selectors">
        <label>País
          <select value={country} onChange={e=>{
            onCountry(e.currentTarget.value);onLeague("all");setExpanded(false);
          }}>
            <option value="all">Todos los países</option>
            {!countries.includes("Argentina")&&<option value="Argentina">Argentina</option>}
            {countries.map(name=><option key={name} value={name}>{name}</option>)}
          </select>
        </label>
        <label>Competición
          <select value={league==="all"||actual.some(c=>competitionKey(c)===league)?league:"all"}
            onChange={e=>onLeague(e.currentTarget.value)}>
            <option value="all">Todas las ligas del país</option>
            {actual.map(c=><option key={competitionKey(c)} value={competitionKey(c)}>
              {c.name}
            </option>)}
          </select>
        </label>
      </div>
    </div>
    {loading?<p class="updated">Cargando el catálogo de ligas…</p>:
      <p class="updated">{actual.length} competiciones identificadas · {numberOfGames} partidos
        importados para los filtros seleccionados. Una liga del catálogo no garantiza
        resultados automáticos ni tablas disponibles en el plan contratado.</p>}
    <div class="sport-competition-grid">
      {display.map(c=><article class="sport-competition-card" key={competitionKey(c)}>
        <div>
          <span class="sport-competition-country">{c.country}</span>
          <h3>{c.name}</h3>
          <small>{c.has_imported_data?"Datos importados":
            c.provider_id!==null?"En el catálogo API · resultados no confirmados":
              "Fuente federativa · sin feed confirmado"}</small>
        </div>
        {c.official_url?<a href={c.official_url} rel="noopener noreferrer"
          target="_blank" aria-label={`Fuente oficial de ${c.name}`}>
          Fuente oficial ↗
        </a>:<button type="button"
          onClick={()=>onLeague(competitionKey(c))} aria-label={`Ver partidos de ${c.name}`}>
          Ver datos ↗
        </button>}
      </article>)}
    </div>
    {actual.length>24&&<button class="sport-country-more" type="button"
      onClick={()=>setExpanded(!expanded)}>
      {expanded?"Mostrar menos":`Ver todas las ligas (${actual.length})`}
    </button>}
    {country==="Argentina"&&<p class="sport-country-note">
      Las fuentes nacionales corresponden a las federaciones y organizadores.
      Cuando la API no confirme cobertura, abrí la fuente oficial para consultar
      resultados y posiciones, sin atribuirle a Latente marcadores no recibidos.
    </p>}
  </section>;
}
