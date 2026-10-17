import type { Match } from "./types";

export type LiveIncident = {
  kind: "goal" | "yellow" | "red";
  minute: number | null;
  extra: number | null;
  team_id: number;
  player: string;
  own_goal: boolean;
  penalty: boolean;
};
export type LiveIncidentSnapshot = {
  fixture_id: number;
  checked_at: string | null;
  events: LiveIncident[];
};

function timeLabel(event: LiveIncident) {
  return event.minute == null
    ? ""
    : `${event.minute}${event.extra ? "+" + event.extra : ""}′ `;
}

export function LiveIncidentStrip({
  match,
  snapshot,
}: {
  match: Match;
  snapshot?: LiveIncidentSnapshot;
}) {
  // Missing and empty event reports are NOT zero goals or zero cards.
  const incidents = snapshot?.events ?? [];
  const visible = incidents.slice(0, 5);
  const pending = !snapshot?.checked_at;
  const delayed = Boolean(
    snapshot?.checked_at &&
    Date.now() - new Date(snapshot.checked_at).getTime() > 20 * 60_000,
  );

  return (
    <div class="live-incidents" aria-label={`Goles y tarjetas: ${match.home.name} contra ${match.away.name}`}>
      {visible.length ? <>
        <span class="live-incidents-caption">Goles y tarjetas</span>
        <span class="live-incidents-items">
          {visible.map((event, index) => {
            const name = event.team_id === match.home.id ? match.home.name
              : event.team_id === match.away.id ? match.away.name : "Equipo";
            const icon = event.kind === "goal" ? "⚽" : event.kind === "red" ? "🟥" : "🟨";
            const qualifier = event.own_goal ? " · e/c"
              : event.penalty ? " · penal" : "";
            return <span key={`${event.team_id}-${event.minute}-${index}`}
              class="live-incident" title={`${name}: ${event.player || "Autor sin informar"}${qualifier}`}>
              <span aria-hidden="true">{icon}</span>
              <span>{timeLabel(event)}{event.player || name}{qualifier}</span>
            </span>;
          })}
          {incidents.length > visible.length && <a href={`#/match/${match.id}`}
            class="live-incidents-more">+{incidents.length - visible.length} más</a>}
        </span>
        {delayed && <span class="live-incidents-delayed" title="La API todavía no actualizó estas incidencias">Datos demorados</span>}
      </> : <span class="live-incidents-pending">
        ⚽ 🟨 🟥 {pending ? "Incidencias pendientes del proveedor" : "Sin detalle de goles o tarjetas confirmado"}
      </span>}
      <a class="live-incidents-detail" href={`#/match/${match.id}`}>Detalle ↗</a>
    </div>
  );
}
