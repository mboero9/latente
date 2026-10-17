"""Prevent Argentine Primera Nacional from appearing as Copa Argentina."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def test_copa_argentina_and_primera_nacional_exact_ids():
    ui=(ROOT/"frontend/src/main.tsx").read_text(encoding="utf-8")
    demo=(ROOT/"backend/app/demo.py").read_text(encoding="utf-8")
    assert '{id:130,label:"🏆 Copa Argentina"}' in ui
    assert '{id:129,label:"🏆 Copa Argentina"}' not in ui
    assert '129: 790, 130: 1560' in ui
    # Demo's source of truth declares 129 Primera Nacional and 130 Copa Argentina.
    assert '129,' in demo and '"Primera Nacional"' in demo
    assert '130,' in demo and '"Copa Argentina"' in demo
