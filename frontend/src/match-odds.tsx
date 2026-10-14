import { useApi } from "./api";

type Quote = {
  bookmaker: string | null;
  source: "live" | "prematch";
  captured_at: string | null;
  prices: { home: number; draw: number; away: number };
  implied: { home: number; draw: number; away: number };
  normalized: { home: number; draw: number; away: number };
};
type Snapshot = { quotes: Quote[]; updated_at: string; stale: boolean } | null;
type OddsData = { live: Snapshot; prematch: Snapshot; match_status: string };
const LIVE = new Set(["1H", "HT", "2H", "ET", "BT", "P", "INT", "LIVE"]);

export function MatchOdds({ id, status, home, away }: { id: number; status: string; home: string; away: string }) {
  const liveMatch = LIVE.has(status);
  const relevant = liveMatch || ["NS", "TBD"].includes(status);
  const { result, loading, error } = useApi<OddsData>(
    relevant ? `/api/fixtures/${id}/odds` : null, 60000
  );
  if (!relevant) return null;
  const data = result?.data;
  const snapshot = (liveMatch && data?.live?.quotes.length ? data.live : data?.prematch);
  const livePrices = liveMatch && snapshot === data?.live;
  const quotes = [...(snapshot?.quotes || [])].sort((a,b) => {
    const p = (name: string | null) => /betano|bplay|bet365|bwin|pinnacle/i.test(name || "") ? 0 : 1;
    return p(a.bookmaker) - p(b.bookmaker);
  }).slice(0, 7);
  return <article class="panel match-odds" aria-label="Cuotas informativas de apuestas">
    <h2>Cuotas y probabilidades implícitas</h2>
    <p class="updated">Mercado 1X2 · victoria local / empate / victoria visitante, en tiempo reglamentario.</p>
    {loading ? <p>Consultando cuotas guardadas…</p> :
      error ? <p class="match-details-unavailable">No se pudo obtener la comparación.</p> :
      quotes.length ? <>
        <p class="updated">
          {livePrices ? "Cuotas de mercado en vivo (sin casa identificada)" : "Cuotas previas al partido por casa cuando el proveedor las identifica"}
          {" · "}Captura: {snapshot?.updated_at ? new Date(snapshot.updated_at).toLocaleString("es-AR") : "sin fecha"}
          {snapshot?.stale ? " · Datos desactualizados, no usar como cotización vigente" : ""}
        </p>
        <div class="odds-scroll"><table class="odds-table">
          <thead><tr><th>Fuente / Casa</th><th>{home}</th><th>Empate</th><th>{away}</th></tr></thead>
          <tbody>{quotes.map((q,i)=><tr key={q.bookmaker || i}>
            <th>{q.bookmaker || "Mercado API-Football (casa no informada)"}</th>
            {(["home","draw","away"] as const).map(k=><td key={k}>
              <strong>{q.prices[k].toFixed(2)}</strong>
              <small>{q.implied[k].toFixed(1)}% imp.</small>
            </td>)}
          </tr>)}</tbody>
        </table></div>
        <p class="updated">El porcentaje es 100 ÷ cuota decimal: **incluye el margen de la casa y no predice el resultado**. Los precios pueden cambiar o suspenderse en segundos.</p>
      </> : <p class="match-details-unavailable">No hay cuotas reales verificadas para este encuentro. El proveedor puede no cubrirlo o no haber enviado cotizaciones aún.</p>}
    <div class="odds-external">
      <span>Consultar operadores externos (no necesariamente ofrecen estas cuotas):</span>
      <a href="https://www.betano.bet.ar/" target="_blank" rel="noopener noreferrer nofollow sponsored">Betano <span aria-hidden="true">↗</span></a>
      <a href="https://www.bplay.bet.ar/deportes/" target="_blank" rel="noopener noreferrer nofollow sponsored">bplay <span aria-hidden="true">↗</span></a>
    </div>
    <p class="odds-warning">Solo mayores de 18 años, donde esté permitido legalmente. Consultá las condiciones y disponibilidad por provincia. El juego compulsivo es perjudicial para vos y tu familia. Latente no acepta apuestas.</p>
  </article>;
}
