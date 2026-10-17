import { useApi } from "./api";
import type { League } from "./types";

const OFFICIAL="https://www.ligaprofesional.ar/torneo-clausura-mercado-libre-2026/";
type Period={played:number|null;points:number|null;has_imported_games:boolean};
type Row={
  team_id:number;team:{id:number;name:string};
  rank:number;played:number;points:number;average:number;
  seasons:Record<string,Period>;missing_seasons:number[];
  verified:boolean;reference:{played:number;points:number}|null;
  difference:{played:number;points:number}|null;
};
type Averages={
  rows:Row[];matches_used:number;matches_by_season:Record<string,number>;
  reference_count:number;verified_count:number;
  provisional:boolean;note:string;
};

function seasonPoints(row:Row,year:number){
  const item=row.seasons[String(year)];
  return item?.has_imported_games?item.points:"—";
}

export function PromediosPage({league}:{league:League}) {
  const {result,loading,error,retry}=useApi<Averages>(
    "/api/leagues/128/promedios?season=2026",60000);
  const data=result?.data;
  return <section class="promedios-view">
    <div class="view-heading"><div>
      <span class="eyebrow">PRIMERA DIVISIÓN ARGENTINA</span>
      <h1>{league.name} · Promedios 2026</h1>
    </div></div>
    <article class="panel promedios-card">
      <h2>Tabla de descenso por promedio</h2>
      <p>Motor de Latente: puntos obtenidos durante 2024, 2025 y 2026
        divididos por los partidos válidos de Primera de cada club. Para
        2026 se computan las fases de zonas, no los playoffs.</p>
      <p class="coverage-notice" role="note">
        <strong>Cálculo parcial, no oficial.</strong> La cobertura de API-Football
        puede no incluir todos los partidos de 2024–2026, y los puntos de
        temporadas anteriores de los clubes ascendidos necesitan validación.
        Esta tabla <strong>no determina descensos</strong> ni aplica sanciones,
        desempates o correcciones de la AFA.</p>
      {loading?<p>Cargando partidos de PostgreSQL…</p>:
        error?<p class="coverage-notice">{error}
          <button type="button" onClick={retry}>Reintentar</button></p>:
        data?.rows.length?<div class="promedios-data">
          <p class="updated">Partidos de fases válidas importados:
            {" "}{data.matches_used} · 2024: {data.matches_by_season["2024"]||0}
            {" "}· 2025: {data.matches_by_season["2025"]||0}
            {" "}· 2026: {data.matches_by_season["2026"]||0}.
            {" "}{data.reference_count
              ? `${data.verified_count} clubes coinciden con la referencia LPF almacenada.`
              : "Validación con referencia LPF pendiente."}
          </p>
          <div class="table-scroll promedios-table" role="region" tabIndex={0}
            aria-label="Tabla provisional de promedios, deslizar horizontalmente para consultar temporadas">
            <table>
              <thead><tr>
                <th scope="col">#</th><th scope="col">Equipo</th>
                <th scope="col">2024</th><th scope="col">2025</th>
                <th scope="col">2026</th><th scope="col">PTS</th>
                <th scope="col">PJ</th><th scope="col">Promedio</th>
                <th scope="col">Validación</th>
              </tr></thead>
              <tbody>{data.rows.map(row=><tr key={row.team_id}>
                <td>{row.rank}</td><th scope="row" title={row.team.name}>{row.team.name}</th>
                {[2024,2025,2026].map(year=><td key={year}
                  title={row.seasons[String(year)]?.played
                    ? `${row.seasons[String(year)].played} partidos importados en ${year}`
                    : `Faltan datos verificados de ${year}`}>
                  {seasonPoints(row,year)}</td>)}
                <td>{row.points}</td><td>{row.played}</td>
                <td class="promedios-number">{row.average.toLocaleString("es-AR",
                  {minimumFractionDigits:3,maximumFractionDigits:3})}</td>
                <td><span class="promedios-validation">
                  {row.verified?"Coincide con LPF":row.reference
                    ?"Difiere de LPF":"Sin contrastar"}
                </span></td>
              </tr>)}</tbody>
            </table>
          </div>
          <p class="updated">«—» significa que Latente todavía no tiene
            resultados válidos importados de esa temporada. No significa
            cero puntos ni que ese club haya jugado en otra categoría.
            El ranking anterior usa únicamente los partidos disponibles y
            puede diferir del oficial.</p>
        </div>:
        <p class="coverage-notice">Todavía no hay suficientes partidos de
          las fases válidas importados para calcular promedios. No generamos
          posiciones ni denominadores ficticios.</p>}
      <a class="official-standings-link" href={OFFICIAL}
        target="_blank" rel="noopener noreferrer">
        Consultar promedios oficiales de la Liga Profesional ↗
      </a>
      <small>Referencia: Liga Profesional de Fútbol y reglamento 2026.
        API-Football aporta marcadores; Latente realiza su propio cálculo
        usando los datos persistidos en PostgreSQL.</small>
    </article>
  </section>;
}
