import { useApi } from "./api";
import { BookmakerMark } from "./bookmaker-brands";

type Outcome = "home" | "draw" | "away";
type Market = { home: number; draw: number; away: number };
type Quote = {
  bookmaker: string | null;
  source: "live" | "prematch";
  captured_at: string | null;
  prices: Market;
  implied: Market;
  normalized: Market;
};
type Snapshot = { quotes: Quote[]; updated_at: string; stale: boolean } | null;
type OddsData = { live: Snapshot; prematch: Snapshot; match_status: string };
export type LiveOddsSummary = {
  fixture_id: number;
  prices: Market;
  implied: Market;
  captured_at: string | null;
  updated_at: string;
  source: string;
};
const LIVE = new Set(["1H", "HT", "2H", "ET", "BT", "P", "INT", "LIVE"]);
const OUTCOMES: {key:Outcome; label:string}[] = [
  {key:"home",label:"Local · 1"},
  {key:"draw",label:"Empate · X"},
  {key:"away",label:"Visitante · 2"},
];

/** Same-market, same-stake gross-return uplift relative to lowest quote.
 * This is NOT the implied probability or an expected investment return.
 */
export function payoutUplift(offer: number, lowest: number): number {
  if (!Number.isFinite(offer) || !Number.isFinite(lowest) || offer <= 1 || lowest <= 1)
    return 0;
  return Math.max(0, (offer / lowest - 1) * 100);
}
function PercentBar({value,max}:{value:number;max:number}) {
  const safe = Math.max(0, Math.min(100, max > 0 ? value/max*100 : 0));
  return <span class="odds-percent">
    <span class="odds-percent-track" aria-hidden="true"><span style={{width:`${safe}%`}} /></span>
    <strong>+{value.toFixed(1)}%</strong>
  </span>;
}
function OddsDisclaimer() {
  return <p class="odds-warning">
    Solo mayores de 18 años o la edad legal aplicable. Las cuotas y operadores dependen
    de la jurisdicción. Los porcentajes son comparaciones matemáticas, no predicciones
    ni garantías de ganancias. La apuesta puede implicar perder todo el dinero.
  </p>;
}
function BookmakerComparison({quotes,stale}: {quotes:Quote[];stale:boolean}) {
  // Only a named bookmaker from the provider can own a price.
  const named = quotes.filter(q => q.bookmaker && OUTCOMES.every(o =>
    Number.isFinite(q.prices?.[o.key]) && q.prices[o.key] > 1));
  // Do not compare samples that may represent different moments.
  const latest = Math.max(...named.map(q => q.captured_at ?
    new Date(q.captured_at).getTime() : 0).filter(Number.isFinite), 0);
  const comparable = named.filter(q => !latest || !q.captured_at ||
    Math.abs(new Date(q.captured_at).getTime() - latest) <= 15 * 60_000);
  const bestByName = new Map<string,Quote>();
  for (const quote of comparable) {
    const name = quote.bookmaker!.trim();
    if (!bestByName.has(name.toLowerCase())) bestByName.set(name.toLowerCase(), quote);
  }
  const offers = [...bestByName.values()];
  if (!offers.length) return <p class="coverage-notice">
    Sin cuotas 1X2 identificadas por casa para este partido. No asignamos
    porcentajes ni logos a operadores que la API no identifica.
  </p>;
  if (stale) return <div class="odds-bookmakers">
    <p class="coverage-notice">Últimas cuotas registradas: datos anteriores, no aptos
    para comparar ofertas actuales. Verificá directamente el mercado y la licencia local.</p>
    {offers.slice(0,8).map(q => <div class="odds-house" key={q.bookmaker!}>
      <BookmakerMark name={q.bookmaker!}/>
      <span class="updated">Cuotas históricas sin comparación vigente</span>
    </div>)}
  </div>;
  const lowest = Object.fromEntries(OUTCOMES.map(o => [
    o.key, Math.min(...offers.map(q => q.prices[o.key])),
  ])) as Record<Outcome,number>;
  const maxUplift = Math.max(0,...offers.flatMap(q =>
    OUTCOMES.map(o => payoutUplift(q.prices[o.key], lowest[o.key]))));
  return <div class="odds-bookmakers">
    <p class="updated">Cuota decimal · Barra: cuánto más paga cada casa por el
      mismo resultado y apuesta, frente a la cuota más baja registrada en esta captura.</p>
    {offers.slice(0,12).map(q => <div class="odds-house" key={q.bookmaker!}>
      <div class="odds-house-title">
        <BookmakerMark name={q.bookmaker!}/>
        <small>Fuente: API-Football · {q.captured_at
          ? new Date(q.captured_at).toLocaleString("es-AR") : "hora no disponible"}</small>
      </div>
      <div class="odds-choices">
        {OUTCOMES.map(o => {
          const price = q.prices[o.key];
          const gain = payoutUplift(price, lowest[o.key]);
          return <div key={o.key} class={gain > 0 && gain ===
            Math.max(...offers.map(candidate => payoutUplift(candidate.prices[o.key],lowest[o.key])))
            ? "odds-best-choice" : ""}>
            <small>{o.label} · cuota {price.toFixed(2)}</small>
            {offers.length > 1
              ? <PercentBar value={gain} max={maxUplift}/>
              : <span class="coverage-notice">Se necesita otra casa para comparar</span>}
          </div>;
        })}
      </div>
    </div>)}
    <p class="updated">El cálculo es (cuota de la casa ÷ cuota mínima − 1) × 100.
      Ejemplo: cuota 2,20 frente a 2,00 = +10% de pago bruto, antes de impuestos.
      No es la probabilidad de acertar ni el retorno esperado.</p>
  </div>;
}

export function LiveOddsMini({fixtureId,home,away,entry,visible}: {
  fixtureId:number;home:string;away:string;entry?:LiveOddsSummary;
  visible?:boolean;
}) {
  // Only show 1X2 references to adults in an eligible jurisdiction.
  // Market-implied percentages are not forecasts; remove overround before
  // sizing the bar so its three segments always total 100.
  if (!visible || !entry) return null;
  const values=[entry.implied?.home,entry.implied?.draw,entry.implied?.away];
  if (!values.every(n=>typeof n==="number"&&Number.isFinite(n)&&n>0))
    return null;
  const total=values.reduce((a,b)=>a+b,0);
  if(total<=0) return null;
  const normalized=values.map(n=>n/total*100);
  return <div class="live-odds-mini live-odds-preview">
    <div class="live-odds-preview-title">
      <strong>Referencia 1X2 · mercado en vivo</strong>
      <a href={`#/match/${fixtureId}`} aria-label={`Ver datos de cuotas de ${home} contra ${away}`}>
        Detalle ↗
      </a>
    </div>
    <div class="live-odds-preview-bars" role="img"
      aria-label={`Porcentajes implícitos sin margen: local ${normalized[0].toFixed(0)}%, empate ${normalized[1].toFixed(0)}%, visitante ${normalized[2].toFixed(0)}%`}>
      {normalized.map((value,i)=><span key={i} style={{width:`${value}%`}}>
        {value>=11?`${value.toFixed(0)}%`:""}
      </span>)}
    </div>
    <div class="live-odds-preview-legend">
      <span>1 · {home}</span><span>X · Empate</span><span>2 · {away}</span>
    </div>
    <small>Probabilidades implícitas normalizadas de cuotas API-Football, sin casa
      identificada · 18+. No es un pronóstico ni garantiza resultados. Sin oferta ni cuota de casa concreta: sin casa identificada.</small>
  </div>;
}
export function MatchOdds({id,status,home,away}: {
  id:number;status:string;home:string;away:string;
}) {
  const liveMatch=LIVE.has(status);
  const relevant=liveMatch || ["NS","TBD"].includes(status);
  const {result,loading,error,retry}=useApi<OddsData>(
    relevant ? `/api/fixtures/${id}/odds` : null,60000);
  const {result:visitor}=useApi<{country:string|null}>(
    relevant ? "/api/visitor/country" : null,3600000);
  if (!relevant) return null;
  const regionBlocked = visitor?.data?.country === "BR";
  const data=result?.data;
  const prematch=data?.prematch;
  const liveAvailable=Boolean(liveMatch && data?.live?.quotes.length && !data?.live?.stale);
  return <article class="panel match-odds" aria-label="Información sobre cuotas de apuestas">
    <div class="match-odds-heading">
      <h2>Cuotas 1X2 · Comparación entre casas</h2>
      <small>{liveMatch?"Partido en vivo":"Próximo partido"}</small>
    </div>
    {regionBlocked ? <p class="coverage-notice">
      Comparación y referencias comerciales no disponibles en Brasil debido
      a las restricciones locales de apuestas deportivas vigentes.
    </p> : <>
      <p class="updated">1: {home} · X: empate · 2: {away}. Solo tiempo reglamentario.</p>
      {loading ? <p>Consultando últimas capturas…</p> : error ?
        <p class="coverage-notice">No se pudieron obtener las cuotas.
          <button onClick={retry}>Reintentar</button></p> : <>
          {liveMatch && <p class="updated">Estas son cuotas previas al partido,
            no precios ofrecidos en vivo. Nunca se atribuyen las cuotas en vivo sin
            casa identificada a Betano, bplay u otro operador.</p>}
          <BookmakerComparison quotes={prematch?.quotes || []} stale={prematch?.stale ?? true}/>
          {liveAvailable && <p class="coverage-notice">API-Football ofrece porcentajes
            implícitos para el mercado en vivo, pero no identifica qué casa los publica.</p>}
        </>}
      <a class="odds-directory" href="#/bet">Ver información legal por país y organismos reguladores ↗</a>
    </>}
    <OddsDisclaimer/>
  </article>;
}
