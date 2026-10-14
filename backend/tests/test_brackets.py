from app.brackets import classify_round, bracket_rows, winner_id

def match(ident, label, home, away, hg=None, ag=None, status="NS", penalty=None):
    return {"id": ident, "round": label, "home": {"id": home, "name": f"Club {home}"},
            "away": {"id": away, "name": f"Club {away}"},
            "home_goals": hg, "away_goals": ag, "status": status,
            "score": {"penalty": penalty} if penalty else {},
            "kickoff": f"2026-06-{ident:02d}T19:00:00+00:00"}

def test_all_six_copa_argentina_knockout_stages():
    titles = ["32avos de Final", "16avos de Final", "Octavos de Final",
              "Cuartos de Final", "Semifinal", "Final"]
    assert [classify_round(x)[1] for x in titles] == [0,1,2,3,4,5]
    assert classify_round("Regular Season - 10") is None
    assert classify_round("Group Stage") is None

def test_only_real_winner_connects_to_next_round():
    rows = bracket_rows([
        match(1,"Round of 32", 10,11,2,0,"FT"),
        match(2,"Round of 16",10,12,None,None,"NS"),
    ])
    assert rows[0]["matches"][0]["next_match_id"] == 2
    assert rows[0]["matches"][0]["winner_id"] == 10

def test_no_fabricated_advancement_from_ties_or_missing_bracket():
    rows = bracket_rows([
        match(1,"Round of 32",10,11,1,1,"FT"),
        match(2,"Round of 16",10,12),
    ])
    assert "next_match_id" not in rows[0]["matches"][0]
    assert winner_id(match(1,"Final",10,11,1,1,"PEN",{"home":4,"away":5})) == 11

def test_semifinal_not_misclassified_as_final():
    assert classify_round("Semi-finals")[1] == 4
