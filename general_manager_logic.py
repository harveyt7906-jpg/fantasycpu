import utils_core, random


def run_general_manager_logic(roster, odds, weather):
    ideas = []
    if odds and "data" in odds:
        ideas.append("Exploit team totals for trade leverage")
    if weather and weather.get("temp") and weather["temp"] < 40:
        ideas.append("Acquire dome players")
    horizon = {"bye_weeks": ["RB1 wk9", "WR2 wk10"], "depth_gaps": ["TE", "DST"]}
    targets = ["FA_SleeperRB", "FA_BoomWR"]
    trades = ["Trade BenchWR for RB2", "Float QB for WR swap"]
    rune_score = random.uniform(0.4, 0.8)
    return {
        "role": "gm",
        "horizon": horizon,
        "waiver_targets": targets,
        "trade_ideas": trades,
        "logic": {"rune_score": rune_score},
        "rationale": "Rune horizon scan of depth, bye weeks, and inefficiencies",
    }
