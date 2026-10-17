"""Public score UI deliberately omits 'Demorado' labels while retaining integrity checks."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

def test_no_public_delayed_labels_on_score_pages():
    for path in ("frontend/src/main.tsx","frontend/src/live-incidents.tsx",
                 "frontend/src/i18n.ts"):
        source=read(path)
        assert not re.search(r"demorad[oa]s?",source,re.IGNORECASE), path
        assert "Datos demorados" not in source
    main=read("frontend/src/main.tsx")
    assert "const hideGenericHomeDelay" not in main
    assert '"Algunas actualizaciones están demoradas"' not in main

def test_real_integrity_signals_remain_available():
    main=read("frontend/src/main.tsx")
    assert "if (m.stale) score -= 120" in main  # keep less fresh games deprioritized
    assert "meta.updated_at" in main  # readers can inspect actual update time
    assert '"Cuota de consultas agotada"' in main
    assert '"Actualización automática detenida"' in main
    assert "status.worker_online" in main
    assert "const warning =" in main
    assert "status.failed_jobs > 0 ||" not in main

def test_outdated_betting_prices_remain_clearly_labeled():
    odds=read("frontend/src/match-odds.tsx")
    assert "if (stale)" in odds
    assert "Últimas cuotas registradas: datos anteriores" in odds
    assert "Cuotas históricas sin comparación vigente" in odds
