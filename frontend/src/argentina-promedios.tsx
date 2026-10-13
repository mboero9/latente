import type { League } from "./types";

const OFFICIAL = "https://www.ligaprofesional.ar/torneo-clausura-mercado-libre-2026/";

export function PromediosPage({ league }: { league: League }) {
  return <section class="promedios-view">
    <div class="view-heading"><div>
      <span class="eyebrow">PRIMERA DIVISIÓN ARGENTINA</span>
      <h1>{league.name} · Promedios 2026</h1>
    </div></div>
    <article class="panel promedios-card">
      <h2>Tabla de descenso por promedio</h2>
      <p>La referencia oficial considera los puntos de 2024, 2025 y 2026,
        divididos por los partidos válidos jugados por cada club en esas temporadas.
        Los ascendidos participan con los años disputados en Primera.</p>
      <p><strong>Consultá el cálculo oficial actualizado.</strong> La tabla del
        Apertura o del Clausura por sí sola no permite reconstruir los promedios.
        Hasta contar con todas las fases y reglamentos, Latente no mostrará
        una proyección incompleta como si determinara el descenso.</p>
      <a class="official-standings-link" href={OFFICIAL} target="_blank" rel="noopener noreferrer">
        Ver promedios oficiales de la Liga Profesional ↗
      </a>
      <small>Fuente del descenso: Liga Profesional de Fútbol de AFA. La clasificación
        anual y la tabla de promedios son cálculos diferentes.</small>
    </article>
  </section>;
}
