import numpy as np, utils_core
from thanos_council import consult_council


def run_head_coach_logic(roster, odds, weather, opponent=None, sims=500):
    players = []
    try:
        roster_players = roster["fantasy_content"]["team"][1]["roster"]["0"]["players"]
        for k, v in roster_players.items():
            if k == "count":
                continue
            name = v["player"][0][0]["name"]["full"]
            pos = v["player"][0][1]["display_position"]
            base_proj = 10 + np.random.normal(0, 2)
            players.append({"name": name, "pos": pos, "proj": base_proj})
    except:
        players = []
    opp_players = []
    if opponent:
        try:
            opp_roster = opponent["fantasy_content"]["team"][1]["roster"]["0"][
                "players"
            ]
            for k, v in opp_roster.items():
                if k == "count":
                    continue
                name = v["player"][0][0]["name"]["full"]
                pos = v["player"][0][1]["display_position"]
                base_proj = 10 + np.random.normal(0, 2)
                opp_players.append({"name": name, "pos": pos, "proj": base_proj})
        except:
            opp_players = []
    your_scores = []
    opp_scores = []
    for _ in range(sims):
        yt = sum(
            utils_core.apply_projection_adjustments(
                p["proj"] + np.random.normal(0, 3), weather, odds[0] if odds else {}
            )
            for p in players
            if p["pos"] in ["QB", "RB", "WR", "TE"]
        )
        ot = (
            sum(q["proj"] + np.random.normal(0, 3) for q in opp_players)
            if opp_players
            else 100
        )
        your_scores.append(yt)
        opp_scores.append(ot)
    wins = np.mean([1 if y > o else 0 for y, o in zip(your_scores, opp_scores)])
    logic = {
        "floor_lineup": sorted(players, key=lambda x: x["proj"], reverse=True)[:9],
        "boom_lineup": sorted(
            players, key=lambda x: x["proj"] + np.random.normal(0, 5), reverse=True
        )[:9],
        "win_prob": float(wins),
        "distribution": {
            "min": float(np.min(your_scores)),
            "avg": float(np.mean(your_scores)),
            "max": float(np.max(your_scores)),
        },
    }
    council = consult_council("head_coach", logic)
    return {"role": "head_coach", "logic": logic, "council": council}
