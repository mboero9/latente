import { useState } from "preact/hooks";
import { useApi } from "./api";

type League = { id: number; name: string; country: string; type?: string };
const focus = [
  { group: "Argentina · UAR y clubes", words: /argentina|urba|top.?12|nacional de clubes|torneo del interior|unión argentina|uar/i },
  { group: "Selecciones y torneos internacionales", words: /rugby championship|six nations|world cup|nations cup|test match|autumn nations/i },
  { group: "Grandes ligas del mundo", words: /super rugby|premiership|top 14|united rugby|urc|champions cup|major league rugby|currie cup/i },
];
export function RugbyCompetitions() {
  const { result, loading, error } = useApi<League[]>(
    "/api/sports/rugby/dataset?kind=leagues&ref=catalog", 3600000
  );
  const [filter, setFilter] = useState("");
  const entries = result?.data || [];
  const display = entries.filter(x => !filter || (x.name + " " + x.country).toLowerCase().includes(filter.toLowerCase()));
  return <section class="rugby-competitions">
    <h2 class="sport-section-title">Rugby · ligas y selecciones</h2>
    <p class="updated">Prioridad: Rugby Championship (Los Pumas), torneos UAR y URBA, Super Rugby, Six Nations, Rugby World Cup y ligas principales de Europa.</p>
    {loading ? <p>Cargando catálogo disponible…</p> : error ? <p>Catálogo en preparación.</p> :
      !entries.length ? <p class="coverage-notice">Todavía no hay un catálogo de rugby importado. La API de Rugby debe estar habilitada en la cuenta para identificar competiciones y temporadas reales, incluida la cobertura argentina.</p> : <>
        <input aria-label="Buscar competiciones de rugby" placeholder="Buscar liga o país" value={filter} onInput={e=>setFilter(e.currentTarget.value)} />
        {focus.map(group => {
          const matches = display.filter(x => group.words.test(x.name + " " + x.country));
          return <div key={group.group}>
            <h3>{group.group}</h3>
            {matches.length ? <div class="sports-clubs">{matches.map(x=><span class="sports-club" key={x.id}>{x.name} · {x.country}</span>)}</div> :
            <p class="updated">No se encontraron competiciones de este grupo en la cobertura importada.</p>}
          </div>;
        })}
        <p class="updated">{entries.length} competiciones identificadas en el catálogo. Las tablas y resultados se publicarán por ID y temporada solo después de verificar su cobertura.</p>
      </>}
  </section>;
}
