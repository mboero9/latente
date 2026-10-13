import { useState } from "preact/hooks";
import { useApi } from "./api";

type MatchEvent = {
  minute: number | null;
  extra: number | null;
  team_id: number;
  player: string;
  assist: string | null;
  type: string;
  detail: string;
  comments: string | null;
};
type Player = {
  id: number;
  name: string;
  number: number | null;
  position: string | null;
  grid: string | null;
};
type Lineup = {
  team_id: number;
  formation: string | null;
  coach: string | null;
  start: Player[];
  bench: Player[];
};
type RatedPlayer = {
  id: number;
  name: string;
  team_id: number | null;
  rating: number;
};
type Detail = {
  events: MatchEvent[];
  lineups: Lineup[];
  best_rated_player: RatedPlayer | null;
};
type MatchNames = { home: { id: number; name: string }; away: { id: number; name: string } };

function Pitch({ lineup, name }: { lineup: Lineup; name: string }) {
  const [showBench, setShowBench] = useState(false);
  const validGrid = (v: string | null) => {
    const matched = v?.match(/^([1-5]):([1-6])$/);
    return matched ? { row: Number(matched[1]), col: Number(matched[2]) } : null;
  };
  const lines = new Map<number, Player[]>();
  for (const player of lineup.start) {
    const position = validGrid(player.grid);
    if (position) lines.set(position.row, [...(lines.get(position.row) || []), player]);
  }
  const hasPositions = lines.size > 0;
  return (
    <div class="tactics-side">
      <div class="tactics-team">
        <strong>{name}</strong>
        <span>{lineup.formation || "Esquema sin informar"}</span>
      </div>
      {hasPositions ? (
        <div class="tactics-pitch" aria-label={`Ubicaciones de ${name}`}>
          <span class="pitch-half" aria-hidden="true" />
          <span class="pitch-circle" aria-hidden="true" />
          {lineup.start.map((player) => {
            const position = validGrid(player.grid);
            if (!position) return null;
            const mates = (lines.get(position.row) || []).length;
            const order = (lines.get(position.row) || []).findIndex((p) => p.id === player.id);
            const x = ((order + 1) / (mates + 1)) * 100;
            const y = 9 + ((position.row - 1) / 4) * 80;
            return <div class="pitch-player" key={player.id} style={{ left: `${x}%`, top: `${y}%` }}>
              <b>{player.number ?? "•"}</b><small>{player.name}</small>
            </div>;
          })}
        </div>
      ) : <p class="match-details-unavailable">No hay posiciones en cancha informadas.</p>}
      <div class="match-squad">
        <strong>Once inicial</strong>
        {lineup.start.length ? lineup.start.map(p => (
          <div key={p.id} class="squad-player"><span>{p.number ?? "—"}</span>{p.name}<small>{p.position || ""}</small></div>
        )) : <p>Once inicial todavía no disponible.</p>}
        {lineup.coach && <p>DT: {lineup.coach}</p>}
        {lineup.bench.length > 0 && <button class="lineup-toggle" onClick={() => setShowBench(!showBench)}>
          {showBench ? "Ocultar suplentes" : `Ver suplentes (${lineup.bench.length})`}
        </button>}
        {showBench && lineup.bench.map(p => <div key={p.id} class="squad-player"><span>{p.number ?? "—"}</span>{p.name}</div>)}
      </div>
    </div>
  );
}
function description(e: MatchEvent) {
  const type = e.type.toLowerCase(), detail = e.detail.toLowerCase();
  if (type === "goal") return { icon: "⚽", label: detail.includes("own goal") ? "Gol en contra" : detail.includes("penalty") ? "Gol de penal" : "Gol" };
  if (type === "card") return { icon: detail.includes("red") || detail.includes("second yellow") ? "🟥" : "🟨", label: "Tarjeta" };
  if (type === "subst") return { icon: "⇄", label: "Cambio" };
  if (type === "var") return { icon: "VAR", label: "VAR" };
  return { icon: "•", label: e.type || "Incidencia" };
}

export function MatchExtras({ id, teams }: { id: number; teams: MatchNames }) {
  const { result, loading, error, retry } = useApi<Detail>(`/api/fixtures/${id}/details`, 30_000);
  const data = result?.data;
  const events = [...(data?.events || [])].sort((a,b) => (a.minute ?? 0) - (b.minute ?? 0));
  const lineup = data?.lineups || [];
  const best = data?.best_rated_player;
  return (
    <section class="match-extras" aria-label="Detalles del partido">
      <article class="panel match-detail-panel">
        <h2>Goles, tarjetas y jugadas</h2>
        {loading ? <p>Cargando incidencias…</p> : error ? <p>{error} <button onClick={retry}>Reintentar</button></p>
         : events.length ? <div class="match-timeline">
            {events.map((e, i) => {
              const item = description(e);
              const club = e.team_id === teams.home.id ? teams.home.name : e.team_id === teams.away.id ? teams.away.name : "Equipo";
              return <div class="timeline-event" key={i}>
                <time>{e.minute ?? "—"}′{e.extra ? `+${e.extra}` : ""}</time>
                <span class="timeline-symbol" aria-hidden="true">{item.icon}</span>
                <div><strong>{e.player || item.label}</strong>
                  <small>{club} · {item.label}{e.assist ? ` · Asistencia: ${e.assist}` : ""}</small>
                  {e.comments && <small>{e.comments}</small>}
                </div>
              </div>;
            })}
          </div>
         : <p class="match-details-unavailable">Todavía no hay incidencias confirmadas para este encuentro.</p>}
      </article>
      <article class="panel match-detail-panel">
        <h2>Formación y táctica en cancha</h2>
        {lineup.length ? <div class="tactics-layout">
          <Pitch lineup={lineup.find(x => x.team_id === teams.home.id) || { team_id: teams.home.id, formation: null, coach: null, start: [], bench: [] }} name={teams.home.name} />
          <Pitch lineup={lineup.find(x => x.team_id === teams.away.id) || { team_id: teams.away.id, formation: null, coach: null, start: [], bench: [] }} name={teams.away.name} />
        </div> : <p class="match-details-unavailable">Las alineaciones y el dibujo táctico aparecerán cuando estén disponibles en los datos del encuentro.</p>}
      </article>
      <article class="panel match-detail-panel">
        <h2>Jugador destacado</h2>
        {best
          ? <div class="best-player"><strong>{best.name}</strong><span>Mejor calificado: {best.rating.toFixed(1)}/10</span><small>Calificación del proveedor, no necesariamente MVP oficial.</small></div>
          : <p class="match-details-unavailable">No hay calificaciones de jugadores para identificar un destacado. No asignamos un MVP sin datos.</p>}
      </article>
      {data && <p class="updated">Ficha basada en información disponible del proveedor. Algunos partidos históricos pueden no tener alineaciones, incidencias o calificaciones.</p>}
    </section>
  );
}
