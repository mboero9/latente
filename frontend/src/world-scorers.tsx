/** Historical reference snapshot, NOT an automatically updated 2026 career count.
 * IFFHS worldwide top-level official goals, through 31 March 2023:
 * https://www.iffhs.com/posts/2670
 */
type HistoricScorer = {name:string;country:string;flag:string;goals:number;club:string;teamId?:number};
const rows: HistoricScorer[] = [
  { name: "Cristiano Ronaldo", country: "Portugal", flag: "🇵🇹", goals: 834, club: "Al Nassr (2023)", teamId: 2939 },
  { name: "Lionel Messi", country: "Argentina", flag: "🇦🇷", goals: 803, club: "Inter Miami CF (actual, 2026)", teamId: 9568 },
  { name: "Pelé", country: "Brasil", flag: "🇧🇷", goals: 762, club: "Santos (histórico)", teamId: 128 },
  { name: "Romário", country: "Brasil", flag: "🇧🇷", goals: 755, club: "Vasco da Gama (histórico)" },
  { name: "Ferenc Puskás", country: "Hungría / España", flag: "🇭🇺", goals: 724, club: "Real Madrid (histórico)", teamId: 541 },
  { name: "Josef Bican", country: "Austria / Checoslovaquia", flag: "🇦🇹", goals: 722, club: "Slavia Praga (histórico)" },
  { name: "Jimmy Jones", country: "Irlanda del Norte", flag: "🇬🇧", goals: 648, club: "Glenavon (histórico)" },
  { name: "Gerd Müller", country: "Alemania", flag: "🇩🇪", goals: 634, club: "Bayern Múnich (histórico)", teamId: 157 },
  { name: "Joe Bambrick", country: "Irlanda del Norte", flag: "🇬🇧", goals: 629, club: "Linfield (histórico)" },
  { name: "Abe Lenstra", country: "Países Bajos", flag: "🇳🇱", goals: 624, club: "SC Heerenveen (histórico)" },
  { name: "Eusébio", country: "Portugal", flag: "🇵🇹", goals: 619, club: "Benfica (histórico)", teamId: 211 },
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
    <p class="updated">Registro histórico IFFHS · corte: marzo de 2023. No son los totales actuales.</p>
    {rows.slice(0,2).map((p,i)=><div class="world-scorer-line" key={p.name}>
      <span>{i+1}.</span><ReferenceBadge teamId={p.teamId} flag={p.flag} country={p.country} currentClub={p.name === "Lionel Messi"} />
      <strong>{p.name}</strong><span class="world-scorer-count">{p.goals}</span>
    </div>)}
    <a class="world-scorer-link" href="#/world-scorers">Ver tabla histórica completa →</a>
  </section>;
}
export function WorldScorersPage() {
  return <section class="world-scorers-page">
    <div class="view-heading"><div><span class="eyebrow">ARCHIVO DEPORTIVO · IFFHS</span><h1>Goleadores históricos del mundo</h1></div></div>
    <p class="coverage-notice">Ranking documental IFFHS con corte al <strong>31 de marzo de 2023</strong>. No es un ranking actualizado a 2026: Cristiano Ronaldo, Lionel Messi y otros jugadores sumaron goles desde entonces. Los goles corresponden a ese corte histórico, pero el club mostrado de Messi es el actual (Inter Miami CF, 2026), no el que tenía en marzo de 2023. En los demás casos, los clubes son referencias de época. Cuando no hay escudo verificado, se muestra la bandera del país. El cómputo oficial varía según el criterio de competiciones incluidas.</p>
    <div class="panel table-scroll">
      <table class="scorers-table"><thead><tr><th>#</th><th>Jugador</th><th>País</th><th>Club mostrado</th><th>Goles al corte</th></tr></thead>
      <tbody>{rows.map((p,i)=><tr key={p.name}>
        <td>{i+1}</td>
        <th scope="row"><span class="world-scorer-shield" title={p.country}>{p.flag}</span> {p.name}</th>
        <td>{p.country}</td><td>{p.club}</td><td><strong>{p.goals.toLocaleString("es-AR")}</strong></td>
      </tr>)}</tbody></table>
    </div>
    <p class="updated">Datos históricos: <a href="https://www.iffhs.com/posts/2670" target="_blank" rel="noopener noreferrer">IFFHS – All-time goal-scorers, abril de 2023 ↗</a>. El ranking se actualizará cuando se integre una fuente de totales de carrera verificables y vigente.</p>
  </section>;
}
