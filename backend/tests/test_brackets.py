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


def test_libertadores_two_legs_link_to_verified_qualification_not_first_leg_winner():
    # River loses the first leg, wins on aggregate and appears in next round.
    # Both legs must lead into one and the same next-round TIE, not two edges.
    matches = [
        match(1, "Round of 16", 10, 11, 0, 2, "FT"),
        match(2, "Round of 16", 11, 10, 0, 3, "FT"),
        match(3, "Round of 16", 12, 13, 1, 0, "FT"),
        match(4, "Round of 16", 13, 12, 0, 1, "FT"),
        match(5, "Quarter-finals", 10, 12, 1, 1, "FT"),
        match(6, "Quarter-finals", 12, 10, None, None, "NS"),
    ]
    stages=bracket_rows(matches)
    assert stages[0]["tie_count"] == 2
    assert stages[1]["tie_count"] == 1
    assert len(stages[0]["matches"]) == 4
    by_id={m["id"]:m for stage in stages for m in stage["matches"]}
    assert {by_id[i].get("next_match_id") for i in (1,2,3,4)} == {5}
    assert {by_id[i].get("qualified_team_id") for i in (1,2)} == {10}
    assert {by_id[i].get("qualified_team_id") for i in (3,4)} == {12}
    # The 0:2 first-leg score never incorrectly labels club 11 as the qualifier.
    assert by_id[1]["qualified_team_id"] != winner_id(by_id[1])


def test_sudamericana_pending_second_leg_does_not_invent_qualifier():
    rows=bracket_rows([
        match(1,"Round of 16",10,11,2,0,"FT"),
        match(2,"Round of 16",11,10,None,None,"NS"),
        match(3,"Quarter-finals",30,31,None,None,"NS"),
    ])
    assert rows[0]["tie_count"]==1
    assert all("next_match_id" not in m for m in rows[0]["matches"])
    assert all("qualified_team_id" not in m for m in rows[0]["matches"])


def test_copa_argentina_single_leg_both_winners_connect_to_quarterfinal():
    rows=bracket_rows([
        match(1,"Octavos de Final",10,11,1,0,"FT"),
        match(2,"Octavos de Final",12,13,2,0,"FT"),
        match(3,"Cuartos de Final",10,12,None,None,"NS"),
    ])
    assert rows[0]["tie_count"]==2
    assert rows[1]["tie_count"]==1
    assert [r.get("next_match_id") for r in rows[0]["matches"]]==[3,3]


def test_bracket_no_links_across_missing_rounds_or_two_possible_destinations():
    skipped=bracket_rows([
        match(1,"Round of 16",10,11,2,0,"FT"),
        match(2,"Semi-finals",10,20,None,None,"NS"),
    ])
    assert "next_match_id" not in skipped[0]["matches"][0]
    ambiguous=bracket_rows([
        match(1,"Round of 16",10,11,2,0,"FT"),
        match(2,"Quarter-finals",10,12,None,None,"NS"),
        match(3,"Quarter-finals",11,13,None,None,"NS"),
    ])
    assert "next_match_id" not in ambiguous[0]["matches"][0]


def test_bracket_unknown_team_ids_do_not_get_merged_into_fictitious_ties():
    a=match(1,"Round of 16",10,11)
    b=match(2,"Round of 16",10,12)
    a["home"]["id"]=None
    b["home"]["id"]=None
    rows=bracket_rows([a,b])
    assert rows[0]["tie_count"]==2


def test_repeated_processing_clears_stale_route_linkage():
    row=match(1,"Round of 16",10,11)
    row["next_match_id"]=999
    row["winner_id"]=42
    assert "next_match_id" not in bracket_rows([row])[0]["matches"][0]
    assert "winner_id" not in bracket_rows([row])[0]["matches"][0]


def test_bracket_frontend_draws_tie_edges_not_each_fixture():
    from pathlib import Path
    src=(Path(__file__).resolve().parents[2]/"frontend/src/cup-bracket.tsx").read_text()
    css=(Path(__file__).resolve().parents[2]/"frontend/src/style.css").read_text()
    assert "groupBracketTies(stage.matches)" in src
    assert "data-tie-key" in src
    assert '.closest<HTMLElement>(".knockout-tie")' in src
    assert "seen.has(key)" in src
    assert "drawn.push(" in src
    assert "ResizeObserver" in src
    assert "Ida" in src and "Vuelta" in src
    assert "cruces ·" in src
    assert ".knockout-links path" in css
    assert ".knockout-round-body" in css
