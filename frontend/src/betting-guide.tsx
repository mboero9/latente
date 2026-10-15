import { useEffect, useState } from "preact/hooks";
import { useApi } from "./api";
type Operator={name:string;url:string;scope:string};
const AR_OPERATORS:Operator[]=[
 {name:"Betano",url:"https://www.betano.bet.ar/",scope:"Confirmar autorización para la provincia"},
 {name:"bplay",url:"https://caba.bplay.bet.ar/",scope:"Dominio de CABA; otras provincias usan dominios propios"},
 {name:"Bet365",url:"https://www.bet365.bet.ar/",scope:"Verificar jurisdicción habilitada"},
 {name:"Betsson",url:"https://www.betsson.bet.ar/",scope:"Verificar jurisdicción habilitada"},
 {name:"BetWarrior",url:"https://caba.betwarrior.bet.ar/",scope:"Dominio de CABA"},
 {name:"Codere",url:"https://m.caba.codere.bet.ar/",scope:"Dominio de CABA"},
];
const REGULATORS:Record<string,{name:string;url:string;description:string}>={
 AR:{name:"ALEA · operadores de juego online en Argentina",url:"https://www.alea.org.ar/juegosonlineautorizados",description:"Las licencias son provinciales. Seleccioná la provincia en el listado oficial."},
 GB:{name:"UK Gambling Commission · registro público",url:"https://www.gamblingcommission.gov.uk/licensees-and-businesses/page/public-register",description:"Buscá los operadores con licencia para Gran Bretaña."},
 ES:{name:"DGOJ · juego seguro",url:"https://www.ordenacionjuego.es/",description:"Consultar operadores autorizados en España."},
 FR:{name:"ANJ · Autorité nationale des jeux",url:"https://anj.fr/",description:"Consultar la lista de operadores y mercados habilitados en Francia."},
 IT:{name:"ADM · Agenzia delle Dogane e dei Monopoli",url:"https://www.adm.gov.it/",description:"Consultar concesionarios autorizados en Italia."},
 US:{name:"Regulación por estado · NCPG",url:"https://www.ncpgambling.org/",description:"En EE. UU. las apuestas deportivas dependen de cada estado. Consultar al regulador estatal."},
 AU:{name:"ACMA · Australian Communications and Media Authority",url:"https://www.acma.gov.au/",description:"Comprobar operadores legales y normas del territorio."},
 NZ:{name:"Department of Internal Affairs · Gambling",url:"https://www.dia.govt.nz/Gambling",description:"Consultar normativa vigente y operadores autorizados."},
};
export function BettingGuide({country}:{country:string}) {
 const [province,setProvince]=useState("CABA");
 const regulator=REGULATORS[country];
 return <section class="betting-guide" aria-label="Dónde apostar legalmente">
   <h2>18+ · Dónde apostar legalmente</h2>
   <p class="updated">Directorio informativo por país, separado de las transmisiones. Latente no recibe apuestas ni garantiza la disponibilidad de mercados, cuotas o bonos.</p>
   {country==="AR"&&<>
     <label class="season-label">Jurisdicción argentina
       <select value={province} onChange={e=>setProvince(e.currentTarget.value)}>
         <option value="CABA">Ciudad de Buenos Aires</option>
         <option value="PBA">Provincia de Buenos Aires</option>
         <option value="otras">Otra provincia</option>
       </select>
     </label>
     {province==="CABA"?
      <div class="watch-links">{AR_OPERATORS.map(o=><a key={o.name} href={o.url}
        target="_blank" rel="noopener noreferrer nofollow sponsored">
        <strong>{o.name} ↗</strong><small>{o.scope}. Revisar licencia y condiciones antes de registrarse.</small>
      </a>)}</div>:
      <p class="coverage-notice">Para {province==="PBA"?"Provincia de Buenos Aires":"esta provincia"} consultá primero los dominios y operadores habilitados en el registro oficial. No se aplica automáticamente una licencia de CABA a otra provincia.</p>}
   </>}
   {regulator?<div class="watch-links"><a href={regulator.url} target="_blank" rel="noopener noreferrer">
     <strong>{regulator.name} ↗</strong><small>{regulator.description}</small>
   </a></div>:<p class="coverage-notice">Todavía no contamos con una lista de operadores comprobados para este país. Consultá el regulador de juego local antes de utilizar una casa de apuestas.</p>}
   <p class="odds-warning">Solo para mayores de 18 años o la edad legal superior de tu jurisdicción. Apostar implica riesgo de perder dinero. No hay ganancias garantizadas. No apuestes para recuperar pérdidas.</p>
 </section>;
}

const COUNTRY_CHOICES=[
 ["AR","Argentina"],["BR","Brasil"],["US","Estados Unidos"],["CA","Canadá"],
 ["MX","México"],["ES","España"],["GB","Reino Unido"],["AU","Australia"],
 ["NZ","Nueva Zelanda"],["FR","Francia"],["IT","Italia"],["DE","Alemania"],
 ["CL","Chile"],["CO","Colombia"],["PE","Perú"],["UY","Uruguay"],
 ["PY","Paraguay"],["EC","Ecuador"],["BO","Bolivia"],["VE","Venezuela"],
 ["DO","República Dominicana"]
] as const;
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
   <h1>18+ · Dónde apostar por país</h1></div></div>
  <label class="season-label">País
   <select value={country} onChange={e=>{setCountry(e.currentTarget.value);setManual(true);}}>
    {COUNTRY_CHOICES.map(([id,name])=><option key={id} value={id}>{name}</option>)}
   </select>
  </label>
  <BettingGuide country={country}/>
 </section>;
}
