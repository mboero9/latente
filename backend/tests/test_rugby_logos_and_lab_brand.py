"""Guard the URBA Top 14 crest mapping and LAB editorial display."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_urba_crest_names_and_source_are_available_in_frontend():
    source = (ROOT / "frontend/src/team-mark.tsx").read_text(encoding="utf-8")
    for short in ("hindu", "lostilos", "laplata", "sic", "belgrano", "casi",
                  "cuba", "newman", "alumni", "losmatreros", "bacrc",
                  "regatasbellavista", "champagnat", "rosario"):
        assert f':"{short}"' in source
    assert "https://api.urba.org.ar/img/clubs/" in source
    assert 'sport==="rugby" ? urbaLogo(name)' in source


def test_argentine_basketball_label_and_local_editorial_mark():
    source = (ROOT / "frontend/src/other-sports.tsx").read_text(encoding="utf-8")
    nav = (ROOT / "frontend/src/sport-nav-logo.tsx").read_text(encoding="utf-8")
    badge = (ROOT / "frontend/public/lab-mark.svg").read_text(encoding="utf-8")
    assert 'name: "Liga Argentina"' in source
    assert 'src="/lab-mark.svg"' in source
    assert 'src="/lab-mark.svg"' in nav
    assert "LAB" in badge
