"""Three independent historical rankings follow Argentina standings in the RIGHT sidebar."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_home_renders_three_full_historical_tables_in_order():
    main = (ROOT / "frontend/src/main.tsx").read_text(encoding="utf-8")
    assert 'import { WorldScorersPage, WorldScorersSection }' in main
    assert 'import { ClubHonours, NationalHonours }' in main
    fixture_home = main[main.index('function FixturesView('):main.index('function Form(')]
    assert 'class="home-historics"' in fixture_home
    assert 'home-content-columns' in fixture_home
    aside = fixture_home.index('aria-label="Resumen de la jornada e históricos"')
    mini = fixture_home.index('<MiniTable league={league || leagues.find(l => l.id === 128)')
    historical = fixture_home.index('class="home-historics"')
    note = fixture_home.index('<div class="quiet-note">')
    assert fixture_home.index('</section>\n        <aside') < aside < mini < historical < note
    assert 'home-right-column' in fixture_home
    assert 'league || leagues.find(l => l.id === 128)' in fixture_home
    assert fixture_home.index('<WorldScorersSection/>') < fixture_home.index('<ClubHonours/>') < fixture_home.index('<NationalHonours/>')
    assert fixture_home.count('<WorldScorersSection/>') == 1
    assert '<WorldScorersTeaser />' not in fixture_home
    assert '{!league && (' in fixture_home
    assert fixture_home.count('class="home-historics"') == 1
    assert 'document.getElementById("copas-selecciones")?.scrollIntoView' in fixture_home
    assert 'href="#copas-selecciones"' not in fixture_home


def test_historical_tables_keep_independent_components_and_filters():
    scorers = (ROOT / "frontend/src/world-scorers.tsx").read_text(encoding="utf-8")
    honours = (ROOT / "frontend/src/historical-honours.tsx").read_text(encoding="utf-8")
    assert 'export function WorldScorersSection()' in scorers
    assert 'id="goleadores-historicos"' in scorers
    assert 'export function ClubHonours()' in honours
    assert 'id="copas-clubes"' in honours
    assert 'export function NationalHonours()' in honours
    assert 'id="copas-selecciones"' in honours
    assert 'export function HistoricalHonours()' in honours
    assert '<ClubHonours/><NationalHonours/>' in honours
    assert 'setRegion' in honours and 'setOrder' in honours
    assert '<WorldScorersSection/>' in scorers


def test_right_sidebar_independent_scroll_cards_and_mobile_fallback():
    css = (ROOT / "frontend/src/style.css").read_text(encoding="utf-8")
    assert '.home-historics' in css
    assert '.home-historics > .world-scorers-section' in css
    assert '.home-historics > .historical-honours-section' in css
    assert '.content-columns.home-content-columns' in css
    assert '.home-right-column .home-historics' in css
    assert '.home-right-column .home-historics > .world-scorers-section' in css
    assert 'grid-template-columns: minmax(0, 1fr) minmax(350px, 42%)' in css
    assert 'max-height: 360px' in css
    assert '@media (max-width: 1100px)' in css
    assert 'overflow-x: auto' in css
    assert 'min-width: 620px' in css
    assert 'scrollbar-width: thin' in css

def test_home_omits_generic_delay_but_keeps_actionable_alerts():
    main = (ROOT / "frontend/src/main.tsx").read_text(encoding="utf-8")
    assert 'const hideGenericHomeDelay' not in main
    assert '{warning && (' in main
    assert 'status.failed_jobs > 0 ||' not in main
    assert '!status.worker_online ||' in main
    assert 'status.quota_exhausted ||' in main
    assert 'No hay partidos disponibles para hoy' in main
    assert 'Cuota de consultas agotada' in main
    assert 'Actualización automática detenida' in main
    assert 'Algunas actualizaciones están demoradas' not in main
    assert 'meta.updated_at' in main

