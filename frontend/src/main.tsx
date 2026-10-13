import { render, type ComponentChildren } from "preact";
import { useEffect, useState } from "preact/hooks";
import { DISPLAY_REFRESH_MS, useApi } from "./api";
import type {
  League,
  Match,
  MatchStatistics,
  Standing,
  Scorer,
  Team,
  TeamDetail,
  Status,
  Meta,
} from "./types";
import "./style.css";
import { observeLanguage } from "./i18n";
import { MatchExtras } from "./match-extras";
import { WatchView } from "./watch-options";
import { PromediosPage } from "./argentina-promedios";
import { FootballAnalytics } from "./football-analytics";
import { sports, SportPage, HistoryPage } from "./other-sports";

const LIVE = new Set(["1H", "HT", "2H", "ET", "BT", "P", "LIVE", "INT"]);
const labels: Record<string, string> = {
  NS: "Por jugar",
  TBD: "A confirmar",
  FT: "Final",
  AET: "Final · TE",
  PEN: "Final · pen.",
  HT: "Entretiempo",
  ET: "Alargue",
  BT: "Pausa",
  P: "Penales",
  SUSP: "Suspendido",
  PST: "Aplazado",
  CANC: "Cancelado",
  ABD: "Abandonado",
  AWD: "Adjudicado",
  WO: "No presentado",
  INT: "Interrumpido",
  LIVE: "En juego",
};
const countryFlags: Record<string, string> = {
  Argentina: "AR",
  England: "GB",
  Inglaterra: "GB",
  Spain: "ES",
  España: "ES",
  Italy: "IT",
  Italia: "IT",
  Germany: "DE",
  Alemania: "DE",
  France: "FR",
  Francia: "FR",
  Brazil: "BR",
  Brasil: "BR",
  World: "INT",
  Europa: "UE",
  Sudamérica: "SA",
};
const countryNames: Record<string, string> = {
  England: "Inglaterra",
  Spain: "España",
  Italy: "Italia",
  Germany: "Alemania",
  France: "Francia",
  Brazil: "Brasil",
  World: "Internacional",
};
const cn = (v: string) => countryNames[v] || v;
const flag = (v: string) => countryFlags[v] || "INT";
const argentina = "America/Argentina/Buenos_Aires";
const systemZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
const number = (v: number | null | undefined) => (v == null ? "—" : v);
const link = (path: string) => `#${path}`;
function formatDay(value: Date, tz = argentina) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: tz,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(value);
}
function shiftDay(day: string, delta: number) {
  const d = new Date(day + "T12:00:00Z");
  d.setUTCDate(d.getUTCDate() + delta);
  return d.toISOString().slice(0, 10);
}
const hour = (date: string, tz: string) =>
  new Intl.DateTimeFormat("es-AR", {
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZone: tz,
  }).format(new Date(date));
const shortDate = (date: string, tz: string) =>
  new Intl.DateTimeFormat("es-AR", {
    day: "numeric",
    month: "short",
    timeZone: tz,
  }).format(new Date(date));

function Icon({ name }: { name: string }) {
  const paths: Record<string, string> = {
    sun: "M12 3v2m0 14v2M3 12h2m14 0h2M5.6 5.6l1.4 1.4m10 10 1.4 1.4M5.6 18.4l1.4-1.4m10-10 1.4-1.4M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
    moon: "M20 15.5A8.5 8.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5Z",
    left: "m14 6-6 6 6 6",
    right: "m10 6 6 6-6 6",
    search: "m21 21-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0",
    cup: "M8 3h8v7a4 4 0 0 1-8 0V3Zm0 2H4v3a4 4 0 0 0 4 4m8-7h4v3a4 4 0 0 1-4 4m-4 2v6m-4 1h8",
    calendar: "M4 5h16v16H4V5Zm0 5h16M8 2v6m8-6v6",
    arrow: "m14 6-6 6 6 6",
    refresh:
      "M20 7v5h-5M4 17v-5h5M6 7a7 7 0 0 1 12-2l2 3M4 16l2 3a7 7 0 0 0 12-2",
  };
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.7"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name] || paths.cup} />
    </svg>
  );
}
function Badge({ team, large = false }: { team: Team; large?: boolean }) {
  const [failed, setFailed] = useState(false);
  const fallback = team.code || team.name.split(" ").filter((x) => x.length > 2).map((x) => x[0]).slice(0, 3).join("").toUpperCase() || team.name.slice(0, 2);
  return (
    <span aria-hidden="true" class={`team-badge tone-${team.id % 8} ${large ? "large" : ""}`}>
      {!failed && team.id > 0 ? (
        <img loading="lazy" decoding="async" alt="" src={`https://media.api-sports.io/football/teams/${team.id}.png`} onError={() => setFailed(true)} />
      ) : fallback}
    </span>
  );
}
function LeagueLogo({ league }: { league: League }) {
  const [failed, setFailed] = useState(false);
  return (
    <span class="league-flag" aria-hidden="true">
      {!failed && league.id > 0 ? (
        <img loading="lazy" decoding="async" alt="" src={`https://media.api-sports.io/football/leagues/${league.id}.png`} onError={() => setFailed(true)} />
      ) : flag(league.country)}
    </span>
  );
}
function Empty({
  title,
  children,
}: {
  title: string;
  children?: ComponentChildren;
}) {
  return (
    <div class="empty">
      <span class="empty-icon">
        <Icon name="calendar" />
      </span>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
    </div>
  );
}
function Loading() {
  return (
    <div class="loading" role="status">
      <span class="spinner" />
      Cargando datos…
    </div>
  );
}
function ErrorBox({ error, retry }: { error: string; retry: () => void }) {
  return (
    <div class="error" role="alert">
      <span>
        {error} Si hay datos anteriores, pueden estar desactualizados.
      </span>
      <button onClick={retry}>Reintentar</button>
    </div>
  );
}
function Updated({ meta }: { meta: Meta | undefined }) {
  if (!meta) return null;
  return (
    <span class="updated">
      {meta.mode === "demo"
        ? "Datos ficticios de demostración"
        : meta.updated_at
          ? `Último dato: ${new Date(meta.updated_at).toLocaleString("es-AR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}`
          : "Esperando datos del proveedor"}
    </span>
  );
}

function MatchRow({
  match: m,
  tz,
  withDate = false,
}: {
  match: Match;
  tz: string;
  withDate?: boolean;
}) {
  const live = LIVE.has(m.status);
  const minute =
    m.elapsed == null
      ? "En juego"
      : `${m.elapsed}${m.extra ? "+" + m.extra : ""}′`;
  return (
    <div class={`match-row ${live ? "is-live" : ""}`}>
      <div class="match-time">
        {withDate && <span class="match-day">{shortDate(m.kickoff, tz)}</span>}
        <span class={live ? "live-text" : ""}>
          {live
            ? labels[m.status] || minute
            : m.status === "NS"
              ? hour(m.kickoff, tz)
              : labels[m.status] || m.status}
        </span>
        {m.stale && <span class="stale">Demorado</span>}
        {live && <a class="watch-live-link" href={link(`/watch/${m.id}`)} title="Opciones oficiales para ver este partido" aria-label={`Dónde ver ${m.home.name} contra ${m.away.name}`}>📺 Ver</a>}
      </div>
      <a class="team home" href={link(`/team/${m.home.id}`)}>
        <span>{m.home.name}</span>
        <Badge team={m.home} />
      </a>
      <a
        class={`score ${live ? "live-score" : ""}`}
        href={link(`/match/${m.id}`)}
        aria-label={`Ver ${m.home.name} contra ${m.away.name}, ${number(m.home_goals)} a ${number(m.away_goals)}`}
      >
        <span>{number(m.home_goals)}</span>
        <span class="score-divider">:</span>
        <span>{number(m.away_goals)}</span>
      </a>
      <a class="team away" href={link(`/team/${m.away.id}`)}>
        <Badge team={m.away} />
        <span>{m.away.name}</span>
      </a>
      <a
        class="match-more"
        href={link(`/match/${m.id}`)}
        aria-label="Detalle del partido"
      >
        <Icon name="right" />
      </a>
    </div>
  );
}

function LeagueTabs({ league, view }: { league: League; view: string }) {
  return (
    <nav class="subnav" aria-label={`Secciones de ${league.name}`}>
      {[
        ["league", "Partidos"],
        ["table", "Posiciones"],
        ["scorers", "Goleadores"],
        ["teams", "Equipos"],
        ["history", "Históricos"],
        ["analytics", "Estadísticas"],
        ...(league.id === 128 ? [["promedios", "Promedios"]] : []),
      ].map(([key, label]) => (
        <a
          class={view === key ? "active" : ""}
          href={link(`/${key}/${league.id}`)}
          aria-current={view === key ? "page" : undefined}
        >
          {label}
        </a>
      ))}
    </nav>
  );
}

function LeagueHeader({
  league,
  view,
  season,
  setSeason,
}: {
  league: League;
  view: string;
  season?: number;
  setSeason?: (n: number) => void;
}) {
  return (
    <>
      <div class="view-heading">
        <div>
          <span class="eyebrow">
            <LeagueLogo league={league} /> {cn(league.country)}
          </span>
          <h1>{league.name}</h1>
        </div>
        {setSeason ? (
          <label class="season-label">
            Temporada
            <select
              value={season}
              onChange={(e) => setSeason(Number(e.currentTarget.value))}
            >
              {(league.loaded_seasons || [league.season]).map((y) => (
                <option value={y}>{y}</option>
              ))}
            </select>
          </label>
        ) : (
          <span class="season-tag">{league.season}</span>
        )}
      </div>
      <LeagueTabs league={league} view={view} />
    </>
  );
}

function DatePicker({
  day,
  setDay,
  tz,
}: {
  day: string;
  setDay: (d: string) => void;
  tz: string;
}) {
  const today = formatDay(new Date(), tz);
  return (
    <div class="date-box">
      <div class="date-top">
        <div>
          <Icon name="calendar" />
          <strong>
            {new Intl.DateTimeFormat("es-AR", {
              month: "long",
              year: "numeric",
              timeZone: "UTC",
            }).format(new Date(day + "T12:00:00Z"))}
          </strong>
        </div>
        <div>
          <button class="text-button" onClick={() => setDay(today)}>
            Hoy
          </button>
          <input
            type="date"
            aria-label="Elegir fecha de partidos"
            value={day}
            onChange={(e) => {
              if (e.currentTarget.value) setDay(e.currentTarget.value);
            }}
          />
        </div>
      </div>
      <div class="days">
        <button
          class="icon-button"
          aria-label="Día anterior"
          onClick={() => setDay(shiftDay(day, -1))}
        >
          <Icon name="left" />
        </button>
        {[-3, -2, -1, 0, 1, 2, 3].map((delta) => {
          const d = shiftDay(day, delta);
          return (
            <button
              class={`day ${d === day ? "selected" : ""} ${Math.abs(delta) === 3 ? "outer-day" : ""}`}
              aria-pressed={d === day}
              onClick={() => setDay(d)}
            >
              <span>
                {d === today
                  ? "Hoy"
                  : new Intl.DateTimeFormat("es-AR", {
                      weekday: "short",
                      timeZone: "UTC",
                    })
                      .format(new Date(d + "T12:00:00Z"))
                      .replace(".", "")}
              </span>
              <strong>{Number(d.slice(-2))}</strong>
            </button>
          );
        })}
        <button
          class="icon-button"
          aria-label="Día siguiente"
          onClick={() => setDay(shiftDay(day, 1))}
        >
          <Icon name="right" />
        </button>
      </div>
    </div>
  );
}

function Focus({ match: m, tz }: { match: Match; tz: string }) {
  return (
    <article class="focus-card">
      <div class="focus-label">
        <span>EN FOCO</span>
        <span class="live-pill">En juego</span>
      </div>
      <p>{m.league.name}</p>
      <div class="focus-score">
        <div>
          <Badge team={m.home} large />
          <strong>{m.home.name}</strong>
        </div>
        <a href={link(`/match/${m.id}`)}>
          {number(m.home_goals)}
          <span>:</span>
          {number(m.away_goals)}
        </a>
        <div>
          <Badge team={m.away} large />
          <strong>{m.away.name}</strong>
        </div>
      </div>
      <div class="focus-footer">
        <span>{labels[m.status] || `${m.elapsed ?? "—"} minutos`}</span>
        <a href={link(`/match/${m.id}`)}>Ver partido</a>
      </div>
      {m.stale && <p>Datos demorados · {hour(m.updated_at, tz)}</p>}
    </article>
  );
}

function MiniTable({ league }: { league: League | undefined }) {
  const { result } = useApi<Standing[]>(
    league ? `/api/leagues/${league.id}/standings` : null,
    DISPLAY_REFRESH_MS,
  );
  if (!league || !result?.data.length) return null;
  const group = result.data[0].group;
  return (
    <article class="mini-table panel">
      <div class="panel-top">
        <h2>Posiciones</h2>
        <Icon name="cup" />
      </div>
      <div class="mini-caption">
        <strong>{league.name}</strong>
        <span>{group}</span>
      </div>
      <div class="mini-head">
        <span>Equipo</span>
        <span>PTS</span>
      </div>
      {result.data
        .filter((r) => r.group === group)
        .slice(0, 5)
        .map((r) => (
          <a class="mini-row" href={link(`/team/${r.team.id}`)}>
            <span class="rank">{r.rank}</span>
            <Badge team={r.team} />
            <span>{r.team.name}</span>
            <strong>{r.points}</strong>
          </a>
        ))}
      <a class="panel-link" href={link(`/table/${league.id}`)}>
        Ver tabla completa
      </a>
    </article>
  );
}

function FixturesView({
  league,
  leagues,
  tz,
  day,
  setDay,
}: {
  league?: League;
  leagues: League[];
  tz: string;
  day: string;
  setDay: (d: string) => void;
}) {
  const [live, setLive] = useState(false),
    [page, setPage] = useState(0);
  useEffect(() => {
    setPage(0);
  }, [day, league?.id, live]);
  const { result, loading, error, retry } = useApi<Match[]>(
    `/api/fixtures?date=${day}&tz=${encodeURIComponent(tz)}&offset=${page * 150}${league ? `&league_id=${league.id}` : ""}${live ? "&live=true" : ""}`,
    DISPLAY_REFRESH_MS,
  );
  const matches = result?.data || [],
    inPlay = matches.filter((m) => LIVE.has(m.status)),
    groups = new Map<number, Match[]>();
  for (const m of matches)
    groups.set(m.league_id, [...(groups.get(m.league_id) || []), m]);
  const sorted = [...groups].sort(
    (a, b) =>
      leagues.findIndex((l) => l.id === a[0]) -
      leagues.findIndex((l) => l.id === b[0]),
  );
  return (
    <>
      <div class="content-columns">
        <section class="main-column">
          {league ? (
            <LeagueHeader league={league} view="league" />
          ) : (
            <div class="view-heading">
              <div>
                <span class="eyebrow">LA JORNADA</span>
                <h1>Partidos</h1>
              </div>
              <span class="today-label">
                {shortDate(day + "T12:00:00Z", tz)}
              </span>
            </div>
          )}
          <DatePicker day={day} setDay={setDay} tz={tz} />
          <div class="match-controls">
            <div class="segmented">
              <button
                aria-pressed={!live}
                class={!live ? "active" : ""}
                onClick={() => setLive(false)}
              >
                Todos <span>{!live ? (result?.meta.total ?? "—") : ""}</span>
              </button>
              <button
                aria-pressed={live}
                class={live ? "active" : ""}
                onClick={() => setLive(true)}
              >
                <span class="live-dot" />
                En vivo {inPlay.length > 0 && <span>{inPlay.length}</span>}
              </button>
            </div>
            <span class="zone-note">
              {tz === argentina ? "Hora argentina" : "Tu hora local"}
            </span>
          </div>
          {error && <ErrorBox error={error} retry={retry} />}
          {loading && <Loading />}
          {!loading && !error && matches.length === 0 && (
            <Empty
              title={
                live
                  ? "No hay partidos en juego"
                  : "Sin partidos para esta fecha"
              }
            >
              {result?.meta.mode === "demo"
                ? "La demostración incluye ayer, hoy y los próximos dos días."
                : "Probá otra fecha o liga. Solo se muestran las temporadas y partidos ya sincronizados."}
            </Empty>
          )}
          {sorted.map(([id, rows]) => (
            <article class="match-group panel">
              <header class="league-bar">
                <LeagueLogo league={rows[0].league} />
                <a href={link(`/league/${id}`)}>
                  <strong>{rows[0].league.name}</strong>
                  <span>
                    {cn(rows[0].league.country)} · {rows.length} partidos
                  </span>
                </a>
                <a class="table-link" href={link(`/table/${id}`)}>
                  Tabla
                  <Icon name="right" />
                </a>
              </header>
              {rows.map((m) => (
                <MatchRow key={m.id} match={m} tz={tz} />
              ))}
            </article>
          ))}
          {(result?.meta.total || 0) > 150 && (
            <div class="pagination">
              <button
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
              >
                Anterior
              </button>
              <span>Página {page + 1}</span>
              <button
                disabled={(page + 1) * 150 >= (result?.meta.total || 0)}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente
              </button>
            </div>
          )}
          <Updated meta={result?.meta} />
        </section>
        <aside class="right-column" aria-label="Resumen de la jornada">
          {inPlay[0] && <Focus match={inPlay[0]} tz={tz} />}
          <MiniTable league={league || leagues[0]} />
          <div class="quiet-note">
            <Icon name="refresh" />
            <div>
              <strong>Los resultados se actualizan solos</strong>
              <p>
                Los marcadores se consultan automáticamente. La frescura depende
                de la cobertura y del plan de datos.
              </p>
            </div>
          </div>
        </aside>
      </div>
    </>
  );
}

function Form({ value }: { value: string | null }) {
  return (
    <span
      class="form"
      aria-label={
        value
          ? `Últimos resultados: ${value
              .split("")
              .map(
                (c) => ({ W: "ganado", D: "empatado", L: "perdido" })[c] || c,
              )
              .join(", ")}`
          : "Sin datos"
      }
    >
      {value
        ? value
            .slice(-5)
            .split("")
            .map((c) => (
              <i class={`form-${c}`}>
                {({ W: "G", D: "E", L: "P" } as Record<string, string>)[c] || c}
              </i>
            ))
        : "—"}
    </span>
  );
}
function TableView({ league }: { league: League }) {
  const [season, setSeason] = useState(league.season);
  const { result, loading, error, retry } = useApi<Standing[]>(
    `/api/leagues/${league.id}/standings?season=${season}`,
    DISPLAY_REFRESH_MS,
  );
  const groups = [...new Set(result?.data.map((r) => r.group) || [])];
  return (
    <>
      <LeagueHeader
        league={league}
        view="table"
        season={season}
        setSeason={setSeason}
      />
      {error && <ErrorBox error={error} retry={retry} />}
      {result?.meta.provisional && (
        <div class="coverage-notice" role="note">
          <strong>Tabla parcial, no oficial.</strong> Calculada con {result.meta.matches_used ?? 0} partidos terminados disponibles en Latente. Puede faltar gran parte de la temporada, equipos y descuentos de puntos.
        </div>
      )}
      {loading ? (
        <Loading />
      ) : !result?.data.length ? (
        <Empty title="Todavía no hay una tabla disponible">
          {result?.meta.coverage === false
            ? "El proveedor no ofrece posiciones para esta competición."
            : "Puede tratarse de una copa eliminatoria o de datos pendientes de sincronización."}
        </Empty>
      ) : (
        groups.map((group) => (
          <article class="panel standings-panel">
            <div class="panel-top">
              <h2>{group}</h2>
              <span>{season}</span>
            </div>
            <div
              class="table-scroll"
              tabIndex={0}
              role="region"
              aria-label={`Tabla ${group}`}
            >
              <table>
                <caption class="sr-only">
                  Posiciones de {league.name}, {group}, temporada {season}
                </caption>
                <thead>
                  <tr>
                    <th scope="col">#</th>
                    <th scope="col" class="club-cell">
                      Equipo
                    </th>
                    {[
                      "PTS",
                      "PJ",
                      "G",
                      "E",
                      "P",
                      "GF",
                      "GC",
                      "DIF",
                      "Últimos 5",
                    ].map((x) => (
                      <th scope="col">{x}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.data
                    .filter((r) => r.group === group)
                    .map((r) => (
                      <tr>
                        <td class="rank">{r.rank}</td>
                        <th scope="row" class="club-cell">
                          <a href={link(`/team/${r.team.id}`)}>
                            <Badge team={r.team} />
                            {r.team.name}
                          </a>
                          {r.description && <small>{r.description}</small>}
                        </th>
                        <td class="points">{r.points}</td>
                        <td>{r.played}</td>
                        <td>{r.won}</td>
                        <td>{r.drawn}</td>
                        <td>{r.lost}</td>
                        <td>{r.goals_for}</td>
                        <td>{r.goals_against}</td>
                        <td>
                          {r.difference > 0 ? "+" : ""}
                          {r.difference}
                        </td>
                        <td>
                          <Form value={r.form} />
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </article>
        ))
      )}
      <p class="table-key">
        PTS: puntos · PJ: jugados · G/E/P: ganados, empatados y perdidos ·
        GF/GC: goles a favor y en contra · DIF: diferencia.
      </p>
      <Updated meta={result?.meta} />
    </>
  );
}

function ScorersView({ league }: { league: League }) {
  const [season, setSeason] = useState(league.season);
  const { result, loading, error, retry } = useApi<Scorer[]>(
    `/api/leagues/${league.id}/scorers?season=${season}`,
    DISPLAY_REFRESH_MS,
  );
  return (
    <>
      <LeagueHeader
        league={league}
        view="scorers"
        season={season}
        setSeason={setSeason}
      />
      {result?.meta.provisional && <div class="coverage-notice" role="note">
        <strong>Goleadores parciales, no oficiales.</strong> Solo se contabilizan los autores
        verificados en {result.meta.matches_used ?? 0} partidos con eventos importados.
        Pueden faltar encuentros y jugadores; los autogoles no suman al ranking.
      </div>}
      {error && <ErrorBox error={error} retry={retry} />}
      {loading ? (
        <Loading />
      ) : !result?.data.length ? (
        <Empty title="Sin goleadores disponibles">
          {result?.meta.coverage === false
            ? "Esta competición no tiene cobertura de goleadores."
            : "Las estadísticas aparecerán al completar la sincronización."}
        </Empty>
      ) : (
        <article class="panel">
          <div class="panel-top">
            <h2>La carrera por el gol</h2>
            <span>{season}</span>
          </div>
          <div
            class="table-scroll"
            role="region"
            tabIndex={0}
            aria-label="Tabla de goleadores"
          >
            <table class="scorers-table">
              <thead>
                <tr>
                  <th scope="col">#</th>
                  <th scope="col" class="club-cell">
                    Jugador
                  </th>
                  <th scope="col">Goles</th>
                  <th scope="col">Asist.</th>
                  <th scope="col">PJ</th>
                  <th scope="col">Penales</th>
                </tr>
              </thead>
              <tbody>
                {result.data.map((r) => (
                  <tr key={`${r.player_id}-${r.team.id}`}>
                    <td class="rank">{r.rank}</td>
                    <th scope="row" class="club-cell">
                      <div class="player">
                        <Badge team={r.team} />
                        <div>
                          {r.name}
                          <a
                            class="player-team"
                            href={link(`/team/${r.team.id}`)}
                          >
                            {r.team.name}
                          </a>
                        </div>
                      </div>
                    </th>
                    <td class="goal-count">{r.goals}</td>
                    <td>{number(r.assists)}</td>
                    <td>{number(r.appearances)}</td>
                    <td>{number(r.penalties)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      )}
      <p class="table-key">
        Ranking y estadísticas informados por el proveedor. Un jugador
        transferido puede tener registros por equipo.
      </p>
      <Updated meta={result?.meta} />
    </>
  );
}

function TeamsView({ league }: { league: League }) {
  const [query, setQuery] = useState(""),
    [season, setSeason] = useState(league.season);
  const { result, loading, error, retry } = useApi<Team[]>(
    `/api/teams?league_id=${league.id}&season=${season}`,
  );
  const teams = (result?.data || []).filter((t) =>
    t.name
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .includes(
        query
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .toLowerCase(),
      ),
  );
  return (
    <>
      <LeagueHeader
        league={league}
        view="teams"
        season={season}
        setSeason={setSeason}
      />
      <label class="search team-search">
        <Icon name="search" />
        <input
          placeholder="Buscar equipo"
          aria-label="Buscar equipo"
          value={query}
          onInput={(e) => setQuery(e.currentTarget.value)}
        />
      </label>
      {error && <ErrorBox error={error} retry={retry} />}
      {loading ? (
        <Loading />
      ) : !teams.length ? (
        <Empty title="No encontramos equipos">
          Probá otro nombre o esperá a la primera sincronización.
        </Empty>
      ) : (
        <div class="teams-grid">
          {teams.map((t) => (
            <a class="team-card panel" href={link(`/team/${t.id}`)}>
              <Badge team={t} large />
              <h2>{t.name}</h2>
              <p>{t.city || cn(t.country || league.country)}</p>
              <span>
                Ver equipo <Icon name="right" />
              </span>
            </a>
          ))}
        </div>
      )}
    </>
  );
}

function TeamView({ id, tz }: { id: number; tz: string }) {
  const { result, loading, error, retry } = useApi<TeamDetail>(
    `/api/teams/${id}`,
    DISPLAY_REFRESH_MS,
  );
  const t = result?.data;
  return (
    <>
      <a class="back-link" href="#/">
        <Icon name="left" />
        Volver a partidos
      </a>
      {error && <ErrorBox error={error} retry={retry} />}
      {loading ? (
        <Loading />
      ) : (
        t && (
          <>
            <div class="team-heading">
              <Badge team={t} large />
              <div>
                <span class="eyebrow">{cn(t.country || "Equipo")}</span>
                <h1>{t.name}</h1>
              </div>
            </div>
            <div class="team-facts">
              <div>
                <span>Fundación</span>
                <strong>{number(t.founded)}</strong>
              </div>
              <div>
                <span>Estadio</span>
                <strong>{t.venue || "Sin información"}</strong>
              </div>
              <div>
                <span>Ciudad</span>
                <strong>{t.city || "—"}</strong>
              </div>
              <div>
                <span>Capacidad</span>
                <strong>{t.capacity?.toLocaleString("es-AR") || "—"}</strong>
              </div>
            </div>
            {[
              ["Próximos partidos", t.upcoming],
              ["Últimos partidos", t.recent],
            ].map(([title, items]) => (
              <section class="team-section">
                <h2>{title as string}</h2>
                {(items as Match[]).length ? (
                  <div class="panel">
                    {(items as Match[]).map((m) => (
                      <MatchRow match={m} tz={tz} withDate />
                    ))}
                  </div>
                ) : (
                  <Empty title="No hay partidos sincronizados" />
                )}
              </section>
            ))}
          </>
        )
      )}
    </>
  );
}

const statisticLabels: Record<string, string> = {
  "Shots on Goal": "Tiros al arco", "Shots off Goal": "Tiros afuera",
  "Total Shots": "Tiros totales", "Blocked Shots": "Tiros bloqueados",
  "Shots insidebox": "Tiros dentro del área", "Shots outsidebox": "Tiros fuera del área",
  "Fouls": "Faltas", "Corner Kicks": "Córners", "Offsides": "Fuera de juego",
  "Ball Possession": "Posesión", "Yellow Cards": "Tarjetas amarillas",
  "Red Cards": "Tarjetas rojas", "Goalkeeper Saves": "Atajadas",
  "Total passes": "Pases", "Passes accurate": "Pases precisos",
  "Passes %": "Precisión de pases", "expected_goals": "Goles esperados (xG)",
  "goals_prevented": "Goles evitados",
};

function MatchStats({ match }: { match: Match }) {
  const { result, loading, error, retry } = useApi<MatchStatistics[]>(
    `/api/fixtures/${match.id}/statistics`,
  );
  const home = result?.data.find((row) => row.team.id === match.home.id)?.statistics || [];
  const away = result?.data.find((row) => row.team.id === match.away.id)?.statistics || [];
  const types = [...new Set([...home, ...away].map((row) => row.type))];
  return (
    <article class="panel match-statistics">
      <h2>Estadísticas del partido</h2>
      <p class="updated">Vista actualizada cada 5 s · disponibilidad según el proveedor</p>
      {error && <ErrorBox error={error} retry={retry} />}
      {loading ? <Loading /> : types.length ? (
        <>
          <table>
            <caption class="sr-only">Comparación de estadísticas entre los dos equipos</caption>
            <thead><tr><th scope="col">{match.home.name}</th><th scope="col">Estadística</th><th scope="col">{match.away.name}</th></tr></thead>
            <tbody>{types.map((type) => (
              <tr key={type}>
                <td>{home.find((row) => row.type === type)?.value ?? "—"}</td>
                <th scope="row">{statisticLabels[type] || type}</th>
                <td>{away.find((row) => row.type === type)?.value ?? "—"}</td>
              </tr>
            ))}</tbody>
          </table>
          {result?.meta.stale && <p class="stale">Las estadísticas están demoradas. Conservamos el último dato recibido.</p>}
          <Updated meta={result?.meta} />
        </>
      ) : !error && (
        <Empty title={result?.meta.coverage === false ? "Sin cobertura estadística" : "Todavía no hay estadísticas"}>
          {result?.meta.mode === "demo" ? "Las estadísticas reales se habilitarán al conectar el proveedor." : "Aparecerán cuando el proveedor publique datos de este partido. Los valores ausentes no se cuentan como cero."}
        </Empty>
      )}
    </article>
  );
}

function MatchView({ id, tz }: { id: number; tz: string }) {
  const { result, loading, error, retry } = useApi<Match>(
    `/api/fixtures/${id}`,
    DISPLAY_REFRESH_MS,
  );
  const m = result?.data;
  return (
    <>
      <a class="back-link" href="#/">
        <Icon name="left" />
        Volver a partidos
      </a>
      {error && <ErrorBox error={error} retry={retry} />}
      {loading ? (
        <Loading />
      ) : (
        m && (
          <>
            <article class="detail-score panel">
              <a class="eyebrow" href={link(`/league/${m.league_id}`)}>
                <LeagueLogo league={m.league} /> {m.league.name}
              </a>
              <p>
                {m.round || "Partido"} · {shortDate(m.kickoff, tz)} ·{" "}
                {hour(m.kickoff, tz)}
              </p>
              <div class="big-score">
                <a href={link(`/team/${m.home.id}`)}>
                  <Badge team={m.home} large />
                  <h1>{m.home.name}</h1>
                </a>
                <div>
                  <strong>
                    {number(m.home_goals)} <em>:</em> {number(m.away_goals)}
                  </strong>
                  <span class={LIVE.has(m.status) ? "live-text" : ""}>
                    {labels[m.status] || `${m.elapsed ?? "—"}′`}
                  </span>
                </div>
                <a href={link(`/team/${m.away.id}`)}>
                  <Badge team={m.away} large />
                  <h1>{m.away.name}</h1>
                </a>
              </div>
              {m.stale && (
                <p class="stale">
                  El último dato está demorado. El marcador puede haber
                  cambiado.
                </p>
              )}
              <a class="watch-detail-link" href={link(`/watch/${m.id}`)}>📺 Dónde ver · Plataformas oficiales</a>
              <Updated meta={result.meta} />
            </article>
            <div class="team-facts">
              <div>
                <span>Estadio</span>
                <strong>{m.venue || "Sin información"}</strong>
              </div>
              <div>
                <span>Árbitro</span>
                <strong>{m.referee || "Sin información"}</strong>
              </div>
              <div>
                <span>Temporada</span>
                <strong>{m.season}</strong>
              </div>
            </div>
            {Object.keys(m.score).length > 0 && (
              <article class="panel score-breakdown">
                <h2>Marcador por período</h2>
                {Object.entries(m.score).map(([period, value]) => (
                  <div>
                    <span>
                      {(
                        {
                          halftime: "Entretiempo",
                          fulltime: "Tiempo reglamentario",
                          extratime: "Prórroga",
                          penalty: "Penales",
                        } as Record<string, string>
                      )[period] || period}
                    </span>
                    <strong>
                      {number(value?.home)} : {number(value?.away)}
                    </strong>
                  </div>
                ))}
              </article>
            )}
            <MatchExtras id={m.id} teams={{home: m.home, away: m.away}} />
            <MatchStats match={m} />
          </>
        )
      )}
    </>
  );
}

function LeaguesView({ leagues }: { leagues: League[] }) {
  const [query, setQuery] = useState("");
  const [visible, setVisible] = useState(60);
  useEffect(() => setVisible(60), [query]);
  const list = leagues.filter((l) =>
    `${l.name} ${cn(l.country)}`.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <>
      <div class="view-heading">
        <div>
          <span class="eyebrow">EL MAPA DEL FÚTBOL</span>
          <h1>Ligas y copas</h1>
        </div>
        <span class="season-tag">{leagues.length} torneos</span>
      </div>
      <label class="search team-search">
        <Icon name="search" />
        <input
          aria-label="Buscar liga"
          placeholder="Buscar una liga o un país"
          value={query}
          onInput={(e) => setQuery(e.currentTarget.value)}
        />
      </label>
      <div class="leagues-grid">
        {list.slice(0, visible).map((l) => (
          <a class="league-card panel" href={link(`/league/${l.id}`)}>
            <LeagueLogo league={l} />
            <div>
              <span class="eyebrow">{cn(l.country)}</span>
              <h2>{l.name}</h2>
              <p>Temporada {l.season}</p>
            </div>
            <Icon name="right" />
          </a>
        ))}
      </div>
      {list.length > visible && (
        <button class="panel-link" onClick={() => setVisible((n) => n + 60)}>
          Mostrar más ligas ({visible} de {list.length})
        </button>
      )}
      {!list.length && (
        <Empty title="No hay ligas disponibles">
          Revisá la búsqueda o el estado de la sincronización.
        </Empty>
      )}
    </>
  );
}

function App() {
  const [route, setRoute] = useState(location.hash.slice(1) || "/"),
    [theme, setTheme] = useState(
      document.documentElement.dataset.theme || "light",
    ),
    [tz, setTz] = useState(argentina),
    [day, setDay] = useState(formatDay(new Date())),
    [leagueSearch, setLeagueSearch] = useState(""),
    [language, setLanguage] = useState<"es" | "en">(() => localStorage.getItem("latente-language") === "en" ? "en" : "es");
  useEffect(() => observeLanguage(language), [language]);
  useEffect(() => {
    const changed = () => {
      setRoute(location.hash.slice(1) || "/");
      window.scrollTo({ top: 0 });
    };
    window.addEventListener("hashchange", changed);
    return () => window.removeEventListener("hashchange", changed);
  }, []);
  const leaguesApi = useApi<League[]>("/api/leagues", DISPLAY_REFRESH_MS),
    statusApi = useApi<Status>("/api/status", DISPLAY_REFRESH_MS);
  const leagues = leaguesApi.result?.data || [],
    status = statusApi.result?.data;
  const mode = status?.mode || leaguesApi.result?.meta.mode;
  const [, view = "", rawId = ""] = route.split("/"),
    id = Number(rawId),
    league = leagues.find((l) => l.id === id),
    first = leagues[0]?.id || 128;
  const isLeagueView = ["league", "table", "scorers", "teams", "history", "promedios", "analytics"].includes(view);
  useEffect(() => {
    document.title = `${league?.name || ({ leagues: "Ligas y copas", team: "Equipo", match: "Partido", watch: "Dónde ver el partido" } as Record<string, string>)[view] || "Resultados"} · Latente`;
  }, [route, league?.name]);
  const toggleTheme = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("latente-theme", next);
    } catch {
      /* navegación privada */
    }
  };
  const warning =
    status?.mode === "api" &&
    (!status.configured ||
      !status.worker_online ||
      status.quota_exhausted ||
      status.failed_jobs > 0 ||
      (status.fixtures_today === 0 && (status.leagues_loaded ?? 0) > 0));
  return (
    <>
      <a
        class="skip-link"
        href="#main"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main")?.focus();
        }}
      >
        Saltar al contenido
      </a>
      <header class="header">
        <div class="header-inner">
          <a href="#/" class="brand" aria-label="LATENTE.CFD, inicio">
            <img src="/latente-mark.png?v=3" width="43" height="43" alt="" />
            <span class="brand-wordmark"><span class="brand-late">late</span><span class="brand-nte">nte</span><span class="brand-tld">.cfd</span></span>
          </a>
          <nav class="top-nav" aria-label="Navegación principal">
            {[
              ["/", "Partidos"],
              ["/leagues", "Ligas"],
              [`/table/${first}`, "Posiciones"],
              [`/scorers/${first}`, "Goleadores"],
              ...sports.map(sport => [`/sport/${sport.slug}`, `${sport.emoji} ${sport.name}`]),
            ].map(([path, label]) => (
              <a
                class={
                  (path.startsWith("/sport/") ? route === path : ((view === "" && path === "/") || path.split("/")[1] === view))
                    ? "active"
                    : ""
                }
                href={link(path)}
              >
                {label}
              </a>
            ))}
          </nav>
          <div class="header-actions">
            <button class="language-toggle" type="button"
              aria-label={language === "es" ? "Switch to English" : "Cambiar a español"}
              title={language === "es" ? "English" : "Español"}
              onClick={() => {
                const next = language === "es" ? "en" : "es";
                localStorage.setItem("latente-language", next);
                setLanguage(next);
              }}>{language === "es" ? "EN" : "ES"}</button>
            {status?.mode === "api" && (
              <span class="api-usage" title="Solicitudes al proveedor utilizadas hoy. No incluye las consultas de los visitantes a Latente.">
                API {status.requests_today}/{status.daily_budget}
              </span>
            )}
            {mode === "demo" && <span class="demo-badge">DEMO</span>}
            <button
              class="icon-button theme-button"
              aria-label={`Activar modo ${theme === "light" ? "oscuro" : "claro"}`}
              onClick={toggleTheme}
            >
              <Icon name={theme === "light" ? "moon" : "sun"} />
            </button>
          </div>
        </div>
      </header>
      <div class="app-shell">
        <aside class="sidebar">
          <div class="sidebar-heading">
            COMPETICIONES <Icon name="cup" />
          </div>
          <label class="search">
            <Icon name="search" />
            <input
              aria-label="Filtrar competiciones"
              placeholder="Buscar liga"
              value={leagueSearch}
              onInput={(e) => setLeagueSearch(e.currentTarget.value)}
            />
          </label>
          <a class={`all-matches ${!view ? "selected" : ""}`} href="#/">
            <Icon name="calendar" />
            Todos los partidos
          </a>
          {["Argentina", "Internacional"].map((group) => (
            <div class="league-nav-group">
              <h2>{group}</h2>
              {leagues
                .filter(
                  (l) =>
                    (group === "Argentina"
                      ? l.country === "Argentina"
                      : l.country !== "Argentina") &&
                    `${l.name} ${cn(l.country)}`.toLowerCase().includes(leagueSearch.toLowerCase()),
                )
                .slice(0, leagueSearch ? 30 : 12)
                .map((l) => (
                  <a
                    class={l.id === id && isLeagueView ? "selected" : ""}
                    href={link(`/league/${l.id}`)}
                  >
                    <LeagueLogo league={l} />
                    <span>{l.name}</span>
                  </a>
                ))}
            </div>
          ))}
          <a class="panel-link" href={link("/leagues")}>
            Explorar todas las ligas ({leagues.length})
          </a>
          <div class="sidebar-bottom">
            <img class="source-logo" src="/latente-mark.png?v=3" width="40" height="40" alt="" />
            <div>
              <strong>© {new Date().getFullYear()} Latente</strong>
              <p>Todos los derechos reservados.</p>
            </div>
          </div>
        </aside>
        <main id="main" tabIndex={-1}>
          <div class="utility-bar">
            <span>LATENTE.CFD - Clubes, Fútbol y Deportes</span>
            <label class="timezone">
              Horarios
              <select
                aria-label="Zona horaria"
                value={tz}
                onChange={(e) => setTz(e.currentTarget.value)}
              >
                <option value={argentina}>Argentina (UTC−3)</option>
                {systemZone !== argentina && (
                  <option value={systemZone}>Mi zona horaria</option>
                )}
                <option value="UTC">UTC</option>
              </select>
            </label>
          </div>
          {mode === "demo" && (
            <div class="notice demo-notice">
              <strong>Modo demostración</strong>
              <span>
                Marcadores, fechas, tablas y jugadores ficticios. No son
                resultados reales.
              </span>
            </div>
          )}
          {warning && (
            <div class="notice warning" role="status">
              <strong>
                {!status.configured
                  ? "Falta activar la fuente de datos"
                  : status.quota_exhausted
                    ? "Cuota de consultas agotada"
                    : !status.worker_online
                      ? "Actualización automática detenida"
                      : (status.restricted_jobs ?? 0) > 0
                        ? "Algunas fechas o temporadas no están disponibles"
                        : status.fixtures_today === 0
                          ? "No hay partidos disponibles para hoy"
                          : "Algunas actualizaciones están demoradas"}
              </strong>
              <span>
                {!status.configured
                  ? "Configurá la clave de API en el servidor."
                  : status.quota_exhausted
                    ? "Se conserva la última copia; las consultas se reanudan al renovar la cuota diaria."
                    : (status.restricted_jobs ?? 0) > 0
                      ? "Algunos datos están restringidos por el plan de cobertura contratado."
                      : status.fixtures_today === 0
                        ? "Las ligas están disponibles, pero todavía no hay partidos recibidos para esta fecha."
                        : "Mostramos los últimos datos recibidos. Revisá la hora de actualización."}
              </span>
            </div>
          )}
          {leaguesApi.error && (
            <ErrorBox error={leaguesApi.error} retry={leaguesApi.retry} />
          )}
          {statusApi.error && !leaguesApi.error && (
            <div class="notice warning">
              No pudimos verificar el estado de actualización.
            </div>
          )}
          {leaguesApi.loading ? (
            <Loading />
          ) : isLeagueView ? (
            league ? (
              <div key={`${view}-${id}`}>
                {view === "league" ? (
                  <FixturesView
                    league={league}
                    leagues={leagues}
                    tz={tz}
                    day={day}
                    setDay={setDay}
                  />
                ) : view === "table" ? (
                  <TableView league={league} />
                ) : view === "analytics" ? (
                  <FootballAnalytics league={league} />
                ) : view === "history" ? (
                  <HistoryPage league={league} />
                ) : view === "promedios" && league.id === 128 ? (
                  <PromediosPage league={league} />
                ) : view === "scorers" ? (
                  <ScorersView league={league} />
                ) : (
                  <TeamsView league={league} />
                )}
              </div>
            ) : (
              <Empty title="Liga aún no disponible">
                La primera sincronización puede tardar varios minutos.
              </Empty>
            )
          ) : view === "sport" ? (
            <SportPage slug={rawId} />
          ) : view === "leagues" ? (
            <LeaguesView leagues={leagues} />
          ) : view === "team" ? (
            <TeamView id={id} tz={tz} />
          ) : view === "match" ? (
            <MatchView id={id} tz={tz} />
          ) : view === "watch" ? (
            <WatchView id={id} />
          ) : view === "" ? (
            <FixturesView leagues={leagues} tz={tz} day={day} setDay={setDay} />
          ) : (
            <Empty title="Página no encontrada">
              <a href="#/">Volver a partidos</a>
            </Empty>
          )}
          <footer>
            <a href="#/" class="footer-brand">
              latente.
            </a>
            <span>
              © {new Date().getFullYear()} Latente. Todos los derechos reservados.
            </span>
            <span>Hecho para seguir el juego.</span>
          </footer>
        </main>
      </div>
    </>
  );
}

render(<App />, document.getElementById("app")!);
