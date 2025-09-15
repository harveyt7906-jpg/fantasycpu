from thanos_council import consult_council


def run_scout_logic(opponent, odds, weather):
    opp = {"strengths": [], "weaknesses": [], "blocks": []}
    try:
        opp_roster = opponent["fantasy_content"]["team"][1]["roster"]["0"]["players"]
        pos_counts = {}
        for k, v in opp_roster.items():
            if k == "count":
                continue
            pos = v["player"][0][1]["display_position"]
            pos_counts[pos] = pos_counts.get(pos, 0) + 1
        if pos_counts.get("RB", 0) < 2:
            opp["weaknesses"].append("thin RB depth")
        if pos_counts.get("WR", 0) > 4:
            opp["strengths"].append("stacked WR core")
        if "thin RB depth" in opp["weaknesses"]:
            opp["blocks"].append("claim RB before opponent")
    except:
        pass
    if odds and isinstance(odds, list):
        opp["strengths"].append("aligned with high total games")
    if weather and weather.get("main", {}).get("temp", 70) < 40:
        opp["weaknesses"].append("cold exposure risk")
    council = consult_council("scout", opp)
    return {"role": "scout", "logic": opp, "council": council}
