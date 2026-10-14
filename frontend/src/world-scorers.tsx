/** Historical reference snapshot, NOT an automatically updated 2026 career count.
 * IFFHS worldwide top-level official goals, through 31 March 2023:
 * https://www.iffhs.com/posts/2670
 */
const rows = [
  { name: "Cristiano Ronaldo", country: "Portugal", flag: "🇵🇹", goals: 834, club: "Al Nassr (2023)" },
  { name: "Lionel Messi", country: "Argentina", flag: "🇦🇷", goals: 803, club: "Paris Saint-Germain (2023)" },
  { name: "Pelé", country: "Brasil", flag: "🇧🇷", goals: 762, club: "Santos (histórico)" },
  { name: "Romário", country: "Brasil", flag: "🇧🇷", goals: 755, club: "Vasco da Gama (histórico)" },
  { name: "Ferenc Puskás", country: "Hungría / España", flag: "🇭🇺", goals: 724, club: "Real Madrid (histórico)" },
  { name: "Josef Bican", country: "Austria / Checoslovaquia", flag: "🇦🇹", goals: 722, club: "Slavia Praga (histórico)" },
  { name: "Jimmy Jones", country: "Irlanda del Norte", flag: "🇬🇧", goals: 648, club: "Glenavon (histórico)" },
  { name: "Gerd Müller", country: "Alemania", flag: "🇩🇪", goals: 634, club: "Bayern Múnich (histórico)" },
  { name: "Joe Bambrick", country: "Irlanda del Norte", flag: "🇬🇧", goals: 629, club: "Linfield (histórico)" },
  { name: "Abe Lenstra", country: "Países Bajos", flag: "🇳🇱", goals: 624, club: "SC Heerenveen (histórico)" },
  { name: "Eusébio", country: "Portugal", flag: "🇵🇹", goals: 619, club: "Benfica (histórico)" },
];
export function WorldScorersTeaser() {
  return <section class="panel world-scorers-teaser">
    <span class="eyebrow">ARCHIVO DEL FÚTBOL</span>
    <h2>Goleadores históricos del mundo</h2>
    <p class="updated">Registro histórico IFFHS · corte: marzo de 2023. No son los totales actuales.</p>
    {rows.slice(0,2).map((p,i)=><div class="world-scorer-line" key={p.name}>
      <span>{i+1}.</span><span class="world-scorer-shield" title={p.country}>{p.flag}</span>
      <strong>{p.name}</strong><span class="world-scorer-count">{p.goals}</span>
    </div>)}
    <a class="world-scorer-link" href="#/world-scorers">Ver tabla histórica completa →</a>
  </section>;
}
export function WorldScorersPage() {
  return <section class="world-scorers-page">
    <div class="view-heading"><div><span class="eyebrow">ARCHIVO DEPORTIVO · IFFHS</span><h1>Goleadores históricos del mundo</h1></div></div>
    <p class="coverage-notice">Ranking documental IFFHS con corte al <strong>31 de marzo de 2023</strong>. No es un ranking actualizado a 2026: Cristiano Ronaldo, Lionel Messi y otros jugadores sumaron goles desde entonces. Los emblemas junto a los jugadores identifican su selección; no son escudos de clubes. El cómputo oficial varía según el criterio de competiciones incluidas.</p>
    <div class="panel table-scroll">
      <table class="scorers-table"><thead><tr><th>#</th><th>Jugador</th><th>País</th><th>Club de referencia</th><th>Goles al corte</th></tr></thead>
      <tbody>{rows.map((p,i)=><tr key={p.name}>
        <td>{i+1}</td>
        <th scope="row"><span class="world-scorer-shield" title={p.country}>{p.flag}</span> {p.name}</th>
        <td>{p.country}</td><td>{p.club}</td><td><strong>{p.goals.toLocaleString("es-AR")}</strong></td>
      </tr>)}</tbody></table>
    </div>
    <p class="updated">Datos históricos: <a href="https://www.iffhs.com/posts/2670" target="_blank" rel="noopener noreferrer">IFFHS – All-time goal-scorers, abril de 2023 ↗</a>. El ranking se actualizará cuando se integre una fuente de totales de carrera verificables y vigente.</p>
  </section>;
}
