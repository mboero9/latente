/** Curated career snapshot: active leaders updated 12 October 2026.
 * All other retired players retain the IFFHS March 2023 historical cutoff.
 * Career goals include competitive senior clubs and senior international matches;
 * excludes club friendlies, youth matches, and shootout penalties.
 */
import { HistoricalHonours } from "./historical-honours";
type HistoricScorer = {name:string;country:string;flag:string;goals:number;club:string;teamId?:number;asOf:string;source?:string};
const rows: HistoricScorer[] = [
  { name: "Cristiano Ronaldo", country: "Portugal", flag: "🇵🇹", goals: 981, club: "Al Nassr (2026)", teamId: 2939, asOf: "12/10/2026", source: "https://messivsronaldo17.com/" },
  { name: "Lionel Messi", country: "Argentina", flag: "🇦🇷", goals: 934, club: "Inter Miami CF (actual, 2026)", teamId: 9568, asOf: "12/10/2026", source: "https://latendencia.cl/cuantos-goles-tiene-messi-en-su-carrera-y-en-mundiales/" },
  { name: "Pelé", country: "Brasil", flag: "🇧🇷", goals: 762, club: "Santos (histórico)", teamId: 128, asOf: "31/03/2023" },
  { name: "Romário", country: "Brasil", flag: "🇧🇷", goals: 755, club: "Vasco da Gama (histórico)", asOf: "31/03/2023" },
  { name: "Ferenc Puskás", country: "Hungría / España", flag: "🇭🇺", goals: 724, club: "Real Madrid (histórico)", teamId: 541, asOf: "31/03/2023" },
  { name: "Josef Bican", country: "Austria / Checoslovaquia", flag: "🇦🇹", goals: 722, club: "Slavia Praga (histórico)", asOf: "31/03/2023" },
  { name: "Jimmy Jones", country: "Irlanda del Norte", flag: "🇬🇧", goals: 648, club: "Glenavon (histórico)", asOf: "31/03/2023" },
  { name: "Gerd Müller", country: "Alemania", flag: "🇩🇪", goals: 634, club: "Bayern Múnich (histórico)", teamId: 157, asOf: "31/03/2023" },
  { name: "Joe Bambrick", country: "Irlanda del Norte", flag: "🇬🇧", goals: 629, club: "Linfield (histórico)", asOf: "31/03/2023" },
  { name: "Abe Lenstra", country: "Países Bajos", flag: "🇳🇱", goals: 624, club: "SC Heerenveen (histórico)", asOf: "31/03/2023" },
  { name: "Eusébio", country: "Portugal", flag: "🇵🇹", goals: 619, club: "Benfica (histórico)", teamId: 211, asOf: "31/03/2023" },
];
function ReferenceBadge({ teamId, flag, country, currentClub }: { teamId?: number; flag: string; country: string; currentClub?: boolean }) {
  return <span class="world-scorer-shield" title={teamId ? (currentClub ? "Club actual (2026)" : "Club de referencia histórico") : country}>
    {teamId ? <img src={`https://media.api-sports.io/football/teams/${teamId}.png`} alt="" loading="lazy"
      onError={e => { e.currentTarget.style.display="none"; e.currentTarget.parentElement?.setAttribute("title",country); }} /> : null}
    <span class={teamId ? "badge-fallback" : ""}>{flag}</span>
  </span>;
}
export function WorldScorersTeaser() {
  return <section class="panel world-scorers-teaser">
    <span class="eyebrow">ARCHIVO DEL FÚTBOL</span>
    <h2>Goleadores históricos del mundo</h2>
    <p class="updated">Cristiano Ronaldo y Messi: actualizado al 12/10/2026. Otros registros: archivo IFFHS.</p>
    {rows.slice(0,2).map((p,i)=><div class="world-scorer-line" key={p.name}>
      <span>{i+1}.</span><ReferenceBadge teamId={p.teamId} flag={p.flag} country={p.country} currentClub={p.name === "Lionel Messi" || p.name === "Cristiano Ronaldo"} />
      <strong>{p.name}</strong><span class="world-scorer-count">{p.goals}</span>
    </div>)}
    <a class="world-scorer-link" href="#/world-scorers">Ver goleadores y copas internacionales →</a>
  </section>;
}
/** Complete scorers table, also displayed as its own block on the homepage. */
export function WorldScorersSection() {
  return <section class="world-scorers-section" id="goleadores-historicos">

    <div class="view-heading"><div><span class="eyebrow">ARCHIVO DEPORTIVO · GOLES Y COPAS</span><h1>Goleadores históricos del mundo</h1></div></div>
    <p class="coverage-notice">Goles oficiales de carrera, clubes y selección mayor. Cristiano Ronaldo y Lionel Messi tienen corte al <strong>12 de octubre de 2026</strong>; para los demás jugadores retirados se conserva el registro IFFHS histórico del 31 de marzo de 2023. Las cifras son una fotografía fechada, no un marcador en vivo, y pueden variar por el criterio estadístico. Clubes mostrados: los actuales de Messi y Ronaldo; los de los demás jugadores son de referencia histórica.</p>
    <div class="panel table-scroll">
      <table class="scorers-table"><thead><tr><th>#</th><th>Jugador</th><th>País</th><th>Club mostrado</th><th>Goles oficiales</th><th>Actualizado</th></tr></thead>
      <tbody>{rows.map((p,i)=><tr key={p.name}>
        <td>{i+1}</td>
        <th scope="row"><span class="world-scorer-shield" title={p.country}>{p.flag}</span> {p.name}</th>
        <td>{p.country}</td><td>{p.club}</td><td><strong>{p.goals.toLocaleString("es-AR")}</strong></td><td>{p.asOf}</td>
      </tr>)}</tbody></table>
    </div>
    <p class="updated">Fuentes: <a href="https://messivsronaldo17.com/" target="_blank" rel="noopener noreferrer">recuento de Cristiano y Messi, 12/10/2026 ↗</a> · <a href="https://www.iffhs.com/posts/2670" target="_blank" rel="noopener noreferrer">IFFHS, históricos retirados ↗</a>. Se actualizarán los jugadores activos cuando se verifiquen nuevos goles.</p>
  </section>;
}

/** Dedicated history route keeps all three tables as individual sections. */
export function WorldScorersPage() {
  return <div class="world-scorers-page">
    <WorldScorersSection/>
    <HistoricalHonours/>
  </div>;
}
