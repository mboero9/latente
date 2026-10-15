"""Three independently scrollable historical rankings must sit in home RIGHT column."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_home_renders_three_full_historical_tables_in_order():
    main = (ROOT / "frontend/src/main.tsx").read_text(encoding="utf-8")
    assert 'import { WorldScorersPage, WorldScorersSection }' in main
    assert 'import { ClubHonours, NationalHonours }' in main
    fixture_home = main[main.index('function FixturesView('):main.index('function Form(')]
    assert 'class="home-historics"' in fixture_home
    assert 'home-content-columns' in fixture_home
    aside = fixture_home.index('aria-label={league ? "Resumen de la jornada"')
    historical = fixture_home.index('class="home-historics"')
    assert aside < historical
    assert fixture_home.index('</section>\n        <aside') < historical
    assert 'home-right-column' in fixture_home
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


def test_right_sidebar_uses_independent_scroll_cards_and_mobile_fallback():
    css = (ROOT / "frontend/src/style.css").read_text(encoding="utf-8")
    assert '.home-historics' in css
    assert '.home-historics > .world-scorers-section' in css
    assert '.home-historics > .historical-honours-section' in css
    assert '.content-columns.home-content-columns' in css
    assert 'grid-template-columns: minmax(0, 1.16fr) minmax(340px, .87fr)' in css
    assert '.content-columns.home-content-columns .home-right-column' in css
    assert '@media (min-width: 1024px)' in css
    assert '@media (max-width: 1023px)' in css
    assert 'max-height: 390px' in css
    assert 'overflow-x: auto' in css
    assert 'min-width: 620px' in css
    assert 'scrollbar-width: thin' in css
