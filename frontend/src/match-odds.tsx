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
function PercentBar({value}:{value:number}) {
  const safe=Math.max(0,Math.min(100,value));
  return <span class="odds-percent"><span class="odds-percent-track" aria-hidden="true">
    <span style={{width:`${safe}%`}}/></span><strong>{value.toFixed(1)}%</strong></span>;
}
function NamedBookmakerComparison({quotes}:{quotes:Quote[]}) {
  return <div class="odds-bookmakers">
    {(["Betano","bplay"] as const).map(name=>{
      const found=quotes.find(q=>q.bookmaker &&
        (name==="Betano"?/\bbetano\b/i:/\bbplay\b/i).test(q.bookmaker));
      return <div class="odds-house" key={name}>
        <strong>{name}</strong>
        {found?<div class="odds-choices">
          <div><small>Local · 1</small><PercentBar value={found.implied.home}/></div>
          <div><small>Empate · X</small><PercentBar value={found.implied.draw}/></div>
          <div><small>Visitante · 2</small><PercentBar value={found.implied.away}/></div>
        </div>:<span class="coverage-notice">Sin porcentaje verificado de esta casa para el partido.</span>}
      </div>;
    })}
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
      <span>1 <b>{entry.implied.home.toFixed(1)}%</b></span>
      <span>X <b>{entry.implied.draw.toFixed(1)}%</b></span>
      <span>2 <b>{entry.implied.away.toFixed(1)}%</b></span>
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
  const prematchQuotes=data?.prematch?.quotes||[];
  const namedOffers=prematchQuotes.filter(q=>q.bookmaker &&
    /\b(betano|bplay)\b/i.test(q.bookmaker));
  const liveAvailable=Boolean(liveMatch && data?.live?.quotes.length && !data?.live?.stale);
  return <article class="panel match-odds" aria-label="Información sobre cuotas de apuestas">
    <div class="match-odds-heading">
      <h2>Cuotas 1X2 · ¿cuánto paga cada resultado?</h2>
      <small>{liveMatch?"Partido en vivo":"Próximo partido"}</small>
    </div>
    <p class="updated">1: {home} · X: empate · 2: {away} · resultado del tiempo reglamentario.</p>
    {loading?<p>Consultando últimas capturas…</p>:error?
      <p class="coverage-notice">No se pudieron obtener las cuotas. <button onClick={retry}>Reintentar</button></p>:
      <>
        <p class="updated">
          Comparación de probabilidades implícitas (%) exclusivamente de Betano y bplay cuando el proveedor identifica esas casas.
          {data?.prematch?.updated_at&&` Última captura previa: ${new Date(data.prematch.updated_at).toLocaleString("es-AR")}.`}
          {liveMatch&&" El partido está en vivo: las capturas identificadas son previas al encuentro y NO son cuotas en vivo."}
        </p>
        <NamedBookmakerComparison quotes={namedOffers}/>
        {liveAvailable&&<p class="coverage-notice">API-Football también registra cuotas en vivo del mercado, pero no identifica la casa. No las atribuimos a Betano ni a bplay.</p>}
        {!namedOffers.length&&<p class="updated">No hay porcentajes confirmados por estas dos casas para este encuentro. Los enlaces externos permiten consultar sus ofertas actuales.</p>}
        <p class="updated">Cada barra representa 100 ÷ cuota decimal. El margen de la casa está incluido y no es un pronóstico.</p>
      </>}
    <ExternalOperators/>
    <OddsDisclaimer/>
  </article>;
}
