import utils_core, numpy as np
from thanos_council import consult_council


def run_general_manager_logic(roster, odds, weather, league_avg=None):
    recs = {"waivers": [], "trades": [], "depth": []}
    try:
        roster_players = roster["fantasy_content"]["team"][1]["roster"]["0"]["players"]
        roster_size = len([k for k in roster_players if k != "count"])
        mean_proj = np.mean([10 for k in roster_players if k != "count"])
        if roster_size < 12:
            recs["waivers"].append({"target": "RB/WR", "reason": "thin roster"})
        if mean_proj < 9:
            recs["waivers"].append({"target": "QB", "reason": "weak projections"})
        if league_avg and roster_size < league_avg:
            recs["depth"].append({"note": "add depth to match league baseline"})
        if weather and weather.get("wind", {}).get("speed", 0) > 15:
            recs["trades"].append(
                {"target": "indoor WR", "reason": "avoid windy games"}
            )
        if odds and isinstance(odds, list):
            recs["trades"].append(
                {"target": "high total offense", "reason": "exploit upside"}
            )
    except:
        pass
    council = consult_council("gm", recs)
    return {"role": "gm", "logic": recs, "council": council}
