import { useApi } from "./api";

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

function OddsDisclaimer() {
  return <p class="odds-warning">
    Solo mayores de 18 años y en jurisdicciones donde esté permitido.
    El juego compulsivo es perjudicial para vos y tu familia. Latente no recibe apuestas.
    Las probabilidades implícitas incluyen margen y no representan predicciones.
  </p>;
}
function ExternalOperators() {
  return <div class="odds-external">
    <span>Consultar plataformas externas · cuotas propias, no necesariamente iguales a estas:</span>
    <a href="https://www.betano.bet.ar/" target="_blank" rel="noopener noreferrer nofollow sponsored">
      Betano <span aria-hidden="true">↗</span>
    </a>
    <a href="https://www.bplay.bet.ar/deportes/" target="_blank" rel="noopener noreferrer nofollow sponsored">
      bplay <span aria-hidden="true">↗</span>
    </a>
    <small>Disponibilidad según la provincia y verificación geográfica del operador.</small>
  </div>;
}
function OutcomeCell({price, implied}:{price:number; implied:number}) {
  return <div class="odds-value">
    <strong>{price.toFixed(2)}x</strong>
    <small>{implied.toFixed(1)}% impl.</small>
  </div>;
}

export function LiveOddsMini({fixtureId,home,away,entry}:{
  fixtureId:number; home:string; away:string; entry?:LiveOddsSummary;
}) {
  if (!entry) return <a class="live-odds-teaser" href={`#/match/${fixtureId}`}>
    Ver cuotas y probabilidades · datos sujetos a cobertura ↗
  </a>;
  return <div class="live-odds-mini">
    <span class="live-odds-label">Mercado en vivo · API-Football (casa no identificada) · Capturado {new Date(entry.updated_at).toLocaleTimeString("es-AR",{hour:"2-digit",minute:"2-digit"})} · 18+</span>
    <a href={`#/match/${fixtureId}`} aria-label={`Ver cuotas de ${home} contra ${away}`}>
      <span>1 <b>{entry.prices.home.toFixed(2)}</b> <small>{entry.implied.home.toFixed(1)}%</small></span>
      <span>X <b>{entry.prices.draw.toFixed(2)}</b> <small>{entry.implied.draw.toFixed(1)}%</small></span>
      <span>2 <b>{entry.prices.away.toFixed(2)}</b> <small>{entry.implied.away.toFixed(1)}%</small></span>
      <span class="odds-more">Detalle ↗</span>
    </a>
  </div>;
}

export function MatchOdds({id,status,home,away}:{
  id:number;status:string;home:string;away:string;
}) {
  const liveMatch = LIVE.has(status);
  const relevant = liveMatch || ["NS","TBD"].includes(status);
  const {result,loading,error,retry} = useApi<OddsData>(
    relevant ? `/api/fixtures/${id}/odds` : null, 60000
  );
  if (!relevant) return null;
  const data = result?.data;
  const liveQuotes = data?.live?.quotes || [];
  const prematchQuotes = data?.prematch?.quotes || [];
  const isLiveQuote = liveMatch && liveQuotes.length > 0 && !data?.live?.stale;
  const isPrematch = !isLiveQuote && prematchQuotes.length > 0;
  const snapshot = isLiveQuote ? data?.live : isPrematch ? data?.prematch : null;
  const quotes = [...(snapshot?.quotes || [])].sort((a,b)=>{
    const priority=(name:string|null)=>/betano|bplay|bet365|bwin|pinnacle|betfair/i.test(name||"")?0:1;
    return priority(a.bookmaker)-priority(b.bookmaker);
  }).slice(0,12);

  return <article class="panel match-odds" aria-label="Información sobre cuotas de apuestas">
    <div class="match-odds-heading">
      <h2>Cuotas 1X2 · ¿cuánto paga cada resultado?</h2>
      <small>{liveMatch?"Partido en vivo":"Próximo partido"}</small>
    </div>
    <p class="updated">1: {home} · X: empate · 2: {away} · resultado del tiempo reglamentario.</p>
    {loading?<p>Consultando las últimas cuotas guardadas…</p>:error?
      <p class="match-details-unavailable">No se pudo consultar la comparación. <button onClick={retry}>Reintentar</button></p>:
      quotes.length?<section>
        <p class="updated">
          {isLiveQuote ? "Mercado en vivo de API-Football: sin casa individual identificada."
            : liveMatch ? "Cuotas ANTERIORES al inicio del partido, no vigentes para apostar en vivo."
            : "Cuotas previas al inicio del partido, diferenciadas por casa cuando el proveedor informa su nombre."}
          {" · "}Último registro: {snapshot?.updated_at ? new Date(snapshot.updated_at).toLocaleString("es-AR") : "no informado"}.
          {snapshot?.stale?" Copia histórica/desactualizada: no considerar precio vigente.":""}
        </p>
        <div class="odds-scroll" role="region" tabIndex={0} aria-label="Tabla comparativa de cuotas y probabilidades">
          <table class="odds-table">
            <thead><tr>
              <th scope="col">Casa / Fuente</th>
              <th scope="col">{home} · 1</th>
              <th scope="col">Empate · X</th>
              <th scope="col">{away} · 2</th>
            </tr></thead>
            <tbody>{quotes.map((q,i)=><tr key={q.bookmaker||i}>
              <th scope="row">{q.bookmaker||"API-Football · mercado sin casa identificada"}</th>
              {(["home","draw","away"] as const).map(side=><td key={side}>
                <OutcomeCell price={q.prices[side]} implied={q.implied[side]}/>
              </td>)}
            </tr>)}</tbody>
          </table>
        </div>
        <p class="updated">Ejemplo: cuota 2,50 = 40% implícito (100 ÷ 2,50). La suma puede superar el 100% por el margen de la casa.</p>
      </section>:<p class="match-details-unavailable">
        No hay cuotas verificadas para este partido. API-Football puede no cubrir el mercado o no haber publicado datos.
      </p>}
    <ExternalOperators/>
    <OddsDisclaimer/>
  </article>;
}
