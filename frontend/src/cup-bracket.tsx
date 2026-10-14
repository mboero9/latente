import { useState } from "preact/hooks";
import { useApi } from "./api";
import type { League, Match } from "./types";

type Stage = { name: string; order: number; matches: Match[] };
type Bracket = { stages: Stage[]; season: number; league: string };
export function CupBracket({ league }: { league: League }) {
  const [season, setSeason] = useState(league.season);
  const { result, loading, error, retry } = useApi<Bracket>(
    `/api/leagues/${league.id}/bracket?season=${season}`, 120000,
  );
  const stages = result?.data.stages || [];
  return <section class="cup-bracket">
    <div class="view-heading"><div><span class="eyebrow">CUADRO ELIMINATORIO</span>
      <h1>{league.name} · Copa</h1></div>
      <label class="season-label">Temporada
        <select value={season} onChange={e => setSeason(Number(e.currentTarget.value))}>
          {[...new Set([league.season, ...(league.loaded_seasons || [])])].sort((a,b)=>b-a).map(y=><option value={y}>{y}</option>)}
        </select>
      </label>
    </div>
    <p class="updated">Desde 32avos hasta la final, cuando estén disponibles en el proveedor. Las fases sin importar no se inventan y no se trazan conexiones no verificadas.</p>
    {loading ? <p>Cargando cuadro de copa…</p> : error ? <p>{error} <button onClick={retry}>Reintentar</button></p> :
    stages.length ? <>
      <div class="knockout-scroll" role="region" tabIndex={0} aria-label="Rondas eliminatorias">
        <div class="knockout-columns">
          {stages.map(stage => <div class="knockout-round" key={stage.order}>
            <h2>{stage.name}</h2>
            <span class="updated">{stage.matches.length} encuentros verificados</span>
            {stage.matches.map(match => <a class="knockout-match" href={`#/match/${match.id}`} key={match.id}>
              <div class="knockout-team"><span>{match.home.name}</span><b>{match.home_goals ?? "—"}</b></div>
              <div class="knockout-team"><span>{match.away.name}</span><b>{match.away_goals ?? "—"}</b></div>
              <small>{match.status === "NS" ? "Por disputar" : match.status} · {new Date(match.kickoff).toLocaleDateString("es-AR")}</small>
            </a>)}
          </div>)}
        </div>
      </div>
      <p class="coverage-notice">Las columnas siguen el orden del torneo, pero no indican cruces enlazados hasta que el origen y destino de cada equipo estén verificados. En partidos de ida y vuelta, abrí la ficha para ver cada resultado.</p>
    </> : <div class="panel sport-intro"><h2>Llave pendiente de sincronización</h2><p>Esta edición todavía no dispone de rondas eliminatorias identificables en las fechas importadas.</p></div>}
  </section>;
}
