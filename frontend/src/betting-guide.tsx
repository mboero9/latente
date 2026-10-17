import { useEffect, useState } from "preact/hooks";
import { useApi } from "./api";
import { BookmakerMark } from "./bookmaker-brands";

type Entry={name:string;url:string;note:string;kind:"private"|"public"};
const AR_CABA:Entry[]=[
 {name:"Betano",url:"https://www.betano.bet.ar/",kind:"private",note:"Comprobar habilitación del dominio y oferta en la jurisdicción"},
 {name:"bplay",url:"https://caba.bplay.bet.ar/",kind:"private",note:"Dominio específico de CABA"},
 {name:"bet365",url:"https://www.bet365.bet.ar/",kind:"private",note:"Verificar habilitación actual para CABA"},
 {name:"Betsson",url:"https://www.betsson.bet.ar/",kind:"private",note:"Confirmar licencia y restricciones territoriales"},
 {name:"BetWarrior",url:"https://caba.betwarrior.bet.ar/",kind:"private",note:"Dominio específico de CABA"},
 {name:"Codere",url:"https://m.caba.codere.bet.ar/",kind:"private",note:"Dominio específico de CABA"},
];
const LICENSED: Record<string,Entry[]>={
 ES:[
  {name:"SELAE · La Quiniela",url:"https://www.loteriasyapuestas.es/es/jugar/quiniela",kind:"public",note:"Oferta estatal de quiniela (pozo), no cuota decimal 1X2"},
  {name:"bet365",url:"https://www.bet365.es/",kind:"private",note:"Verificar licencia vigente en el registro DGOJ"},
  {name:"Codere",url:"https://www.codere.es/",kind:"private",note:"Verificar mercado y licencia vigente en DGOJ"},
 ],
 FR:[
  {name:"FDJ · Parions Sport",url:"https://www.fdj.fr/",kind:"public",note:"Red estatal de apuestas deportivas presenciales; no equivale a cuotas online de cada casa"},
  {name:"Winamax",url:"https://www.winamax.fr/",kind:"private",note:"Operador listado por ANJ en apuestas deportivas online"},
  {name:"Betclic",url:"https://www.betclic.fr/",kind:"private",note:"Operador listado por ANJ en apuestas deportivas online"},
  {name:"bet365",url:"https://www.bet365.fr/",kind:"private",note:"Operador listado por ANJ en apuestas deportivas online"},
 ],
 GB:[
  {name:"bet365",url:"https://www.bet365.com/",kind:"private",note:"Verificar titular y licencia vigente en registro UKGC"},
  {name:"Betfair",url:"https://www.betfair.com/",kind:"private",note:"Verificar licencias y condiciones en UKGC"},
 ],
};
// Regulator/authority is NOT a bookmaker. Some jurisdictions have no state-run
// fixed-odds sportsbook, so never label a regulator as a paying house.
const AUTHORITIES:Record<string,{name:string;url:string;description:string}>={
 AR:{name:"ALEA · registros oficiales de Argentina",url:"https://www.alea.org.ar/juegosonlineautorizados",description:"La licencia depende de CABA o de cada provincia. El dominio .bet.ar no reemplaza esa comprobación."},
 BR:{name:"Secretaria de Prêmios e Apostas · Brasil",url:"https://www.gov.br/fazenda/pt-br/composicao/orgaos/secretaria-de-premios-e-apostas/medida-provisoria-ndeg-1-394-2026-entenda-as-novas-regras-para-as-apostas-de-quota-fixa",description:"Medida Provisoria 1.394/2026: restricciones a la oferta y publicidad de cuotas fijas."},
 ES:{name:"Dirección General de Ordenación del Juego",url:"https://www.ordenacionjuego.es/",description:"Registro español de operadores online autorizados."},
 FR:{name:"ANJ · operadores habilitados en Francia",url:"https://anj.fr/offre-de-jeu-et-marche/operateurs-agrees",description:"Lista pública y actualizable de sitios autorizados."},
 GB:{name:"UK Gambling Commission",url:"https://www.gamblingcommission.gov.uk/licensees-and-businesses/page/public-register",description:"Registro de licencias y titulares autorizados para Gran Bretaña."},
 US:{name:"Regulación por estado · National Council on Problem Gambling",url:"https://www.ncpgambling.org/",description:"Las apuestas deportivas dependen de cada estado; esta organización no es el regulador estatal."},
 CA:{name:"Alcohol and Gaming Commission of Ontario",url:"https://www.agco.ca/",description:"Ejemplo provincial: Ontario. Canadá no tiene una licencia única nacional para casas deportivas."},
 AU:{name:"Australian Communications and Media Authority",url:"https://www.acma.gov.au/",description:"Revisar restricciones nacionales y las regulaciones del estado o territorio."},
 NZ:{name:"Department of Internal Affairs · Gambling",url:"https://www.dia.govt.nz/Gambling",description:"Consultar productos legales y operadores autorizados."},
 IT:{name:"Agenzia delle Dogane e dei Monopoli",url:"https://www.adm.gov.it/",description:"Consultar operadores con concesión válida en Italia."},
 CO:{name:"Coljuegos · Colombia",url:"https://www.coljuegos.gov.co/",description:"Consultar listado oficial de operadores de apuestas autorizados."},
 PE:{name:"MINCETUR · Perú",url:"https://www.gob.pe/mincetur",description:"Consultar autorizaciones de apuestas a distancia."},
 MX:{name:"SEGOB · Juegos y Sorteos · México",url:"https://www.gob.mx/segob",description:"Permisos y restricciones nacionales y locales."},
 CL:{name:"Superintendencia de Casinos de Juego · Chile",url:"https://www.scj.gob.cl/",description:"Esta autoridad regula casinos, no equivale a una licencia para apuestas deportivas online."},
 UY:{name:"Dirección Nacional de Loterías y Quinielas · Uruguay",url:"https://www.gub.uy/ministerio-economia-finanzas/",description:"Consultar modalidades estatales y restricciones de apuestas privadas."},
 DE:{name:"Gemeinsame Glücksspielbehörde der Länder",url:"https://www.gluecksspiel-behoerde.de/",description:"Lista oficial de proveedores autorizados en Alemania."},
};
const COUNTRY_CHOICES=[
 ["AR","Argentina"],["BR","Brasil"],["US","Estados Unidos"],["CA","Canadá"],
 ["MX","México"],["ES","España"],["GB","Reino Unido"],["AU","Australia"],
 ["NZ","Nueva Zelanda"],["FR","Francia"],["IT","Italia"],["DE","Alemania"],
 ["CL","Chile"],["CO","Colombia"],["PE","Perú"],["UY","Uruguay"],
 ["PY","Paraguay"],["EC","Ecuador"],["BO","Bolivia"],["VE","Venezuela"],
 ["DO","República Dominicana"]
] as const;
function OperatorList({items,type}:{items:Entry[];type:"public"|"private"}) {
 const filtered=items.filter(item=>item.kind===type);
 return <section class="licensed-operators">
   <h3>{type==="private"?"Operadores privados · referencias sujetas a licencia":
     "Opciones estatales · modalidad distinta cuando corresponda"}</h3>
   {filtered.length?
     <div class="watch-links bookmaker-directory">{filtered.map(item=>
       <a key={item.name} href={item.url} target="_blank"
         rel="noopener noreferrer nofollow sponsored">
         {type==="private"?<BookmakerMark name={item.name}/>:
           <strong class="public-operator-mark">🏛️ {item.name}</strong>}
         <small>{item.note} · Confirmar permiso local antes de acceder.</small>
       </a>)}</div>:
     <p class="coverage-notice">{type==="private"
       ?"Todavía no tenemos dos operadores independientes con licencia verificada para esta jurisdicción. No incluimos sitios no confirmados."
       :"No se confirmó una casa estatal que publique cuotas deportivas comparables. El regulador público se presenta aparte: no es una casa de apuestas."}</p>}
 </section>;
}
export function BettingGuide({country}:{country:string}) {
 const [province,setProvince]=useState("CABA");
 const regulator=AUTHORITIES[country];
 const blocked=country==="BR";
 const offers=country==="AR"?(province==="CABA"?AR_CABA:[]):LICENSED[country] || [];
 return <section class="betting-guide" aria-label="Información legal sobre operadores por país">
   <h2>18+ · Regulación y operadores por país</h2>
   <p class="updated">Directorio informativo, separado de las cuotas y los marcadores.
      Una autoridad pública no es una casa de apuestas; tampoco todos los
      países cuentan con un operador estatal de cuotas fijas. Las licencias
      cambian por jurisdicción y deben revisarse en la fuente oficial.</p>
   {country==="AR"&&<label class="season-label">Jurisdicción argentina
       <select value={province} onChange={e=>setProvince(e.currentTarget.value)}>
         <option value="CABA">Ciudad de Buenos Aires</option>
         <option value="PBA">Provincia de Buenos Aires</option>
         <option value="otras">Otra provincia</option>
       </select>
     </label>}
   {regulator?<div class="watch-links"><a href={regulator.url} target="_blank"
       rel="noopener noreferrer"><strong>🏛️ {regulator.name} ↗</strong>
       <small>{regulator.description}</small></a></div>:
      <p class="coverage-notice">No tenemos un regulador y un mercado de casas
        verificables para este país. Consultá primero la normativa local; no
        mostramos operadores sin confirmar sus autorizaciones.</p>}
   {blocked?<p class="coverage-notice">Brasil: por la Medida Provisoria
      1.394/2026 no mostramos operadores comerciales, logos ni enlaces
      promocionales de apuestas de cuota fija para esta jurisdicción.</p>:
      <>
        <OperatorList items={offers} type="public"/>
        <OperatorList items={offers} type="private"/>
      </>}
   <p class="odds-warning">Solo mayores de 18 años o edad superior exigida.
     Apostar puede ocasionar pérdidas. No hay ganancias garantizadas.
     Ninguna casa mostrada patrocina este directorio salvo indicación expresa.</p>
 </section>;
}
export function BettingView() {
 const [country,setCountry]=useState<string>("AR");
 const [manual,setManual]=useState(false);
 const {result}=useApi<{country:string|null}>("/api/visitor/country",0);
 useEffect(()=>{
  const found=result?.data?.country;
  if(!manual&&found&&COUNTRY_CHOICES.some(([id])=>id===found))setCountry(found);
 },[result?.data?.country,manual]);
 return <section class="watch-guide panel">
  <div class="view-heading"><div><span class="eyebrow">LATENTE · MAYORES DE EDAD</span>
    <h1>18+ · Información legal de casas por país</h1></div></div>
  <label class="season-label">País
   <select value={country} onChange={e=>{setCountry(e.currentTarget.value);setManual(true);}}>
    {COUNTRY_CHOICES.map(([id,name])=><option key={id} value={id}>{name}</option>)}
   </select>
  </label>
  <BettingGuide country={country}/>
 </section>;
}
