/**
 * Guía a plataformas oficiales para Argentina. No es una grilla de TV por
 * fixture: API-Football no verifica el canal de cada encuentro. Nunca
 * afirmar que un partido se transmite en un enlace solo por su liga.
 */
import { useApi } from "./api";
import type { Match } from "./types";

type Service = {
  name: string;
  url: string;
  access: "Pago" | "Gratis según evento" | "Registro / TV paga";
  note: string;
};
const DISNEY: Service = {
  name: "Disney+ (ESPN)",
  url: "https://www.disneyplus.com/es-ar",
  access: "Pago",
  note: "Consultá la programación de ESPN; la disponibilidad depende del plan y el partido.",
};
const TNT: Service = {
  name: "TNT Sports (HBO Max)",
  url: "https://tntsports.com.ar/suscribite/",
  access: "Pago",
  note: "Pack Fútbol o acceso habilitado por operador. Revisá el encuentro en la agenda.",
};
const TYC: Service = {
  name: "TyC Sports Play",
  url: "https://www.tycsportsplay.com/",
  access: "Registro / TV paga",
  note: "Eventos abiertos y otros que requieren registro o vincular un cableoperador.",
};
const FIFA: Service = {
  name: "FIFA+ / DAZN",
  url: "https://www.fifa.com/es/dazn",
  access: "Gratis según evento",
  note: "FIFA+ ofrece ciertos encuentros gratuitos. Confirmá que este partido esté listado para Argentina.",
};

export function servicesForLeague(id: number): Service[] {
  switch (id) {
    case 128:
      return [TNT, DISNEY];
    case 130:
      return [TYC];
    case 129:
      return [TYC];
    case 140:
    case 39:
    case 2:
    case 3:
    case 13:
    case 11:
      return [DISNEY];
    case 1:
      return [TYC];
    default:
      return [];
  }
}

export function WatchView({ id }: { id: number }) {
  const { result, loading, error, retry } = useApi<Match>(`/api/fixtures/${id}`, 60_000);
  const match = result?.data;
  const services = match ? servicesForLeague(match.league_id) : [];
  return <section class="watch-view">
    <a class="back-link" href={`#/match/${id}`}>← Volver al partido</a>
    <div class="view-heading"><div>
      <span class="eyebrow">LATENTE.CFD · TRANSMISIONES LEGALES</span>
      <h1>📺 Dónde ver el partido</h1>
      {match && <p>{match.home.name} vs. {match.away.name} · {match.league.name}</p>}
    </div></div>
    {loading ? <article class="panel watch-panel">Cargando partido…</article>
      : error ? <article class="panel watch-panel">{error} <button onClick={retry}>Reintentar</button></article>
      : <>
        <article class="panel watch-panel">
          <h2>Plataformas oficiales para consultar</h2>
          <p>Estas son opciones de programación para espectadores en Argentina. <strong>No verificamos los derechos ni la disponibilidad de la transmisión específica de este partido.</strong> Podés abrir la agenda oficial y buscar el encuentro. El acceso cambia por país, competencia y plan.</p>
          {services.length > 0 ? <div class="watch-services">
            {services.map(s => <a class="watch-service" key={s.name}
              href={s.url} target="_blank" rel="noopener noreferrer"
              aria-label={`Consultar ${s.name} en otra pestaña`}>
              <strong>{s.name} ↗</strong>
              <span class="watch-access">{s.access}</span>
              <small>{s.note}</small>
            </a>)}
          </div> : <p>Por ahora no hay una plataforma asignada a esta liga en nuestra guía. Consultá las agendas oficiales que aparecen abajo.</p>}
        </article>
        <article class="panel watch-panel">
          <h2>Otras agendas legales</h2>
          <p>No son transmisiones confirmadas de este partido: son catálogos donde podés encontrar eventos disponibles y comprobar opciones gratuitas o de pago.</p>
          <div class="watch-services">
            {[FIFA, TYC, DISNEY].filter(s => !services.some(x => x.name === s.name))
              .map(s => <a class="watch-service" key={s.name}
                href={s.url} target="_blank" rel="noopener noreferrer">
                <strong>{s.name} ↗</strong>
                <span class="watch-access">{s.access}</span>
                <small>{s.note}</small>
              </a>)}
          </div>
        </article>
        <p class="updated">Latente no aloja, reproduce, retransmite ni enlaza emisiones no autorizadas. Los servicios externos son independientes y pueden exigir suscripción.</p>
      </>}
  </section>;
}
