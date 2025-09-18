import utils_core, random


def run_waiver_logic(roster, odds, weather):
    recs = []
    if odds and "data" in odds:
        recs.append({"player": "FA_BoomWR", "score": random.uniform(0.6, 0.9)})
    if weather and weather.get("wind") and weather["wind"] > 20:
        recs.append({"player": "FA_RB_Grinder", "score": random.uniform(0.5, 0.7)})
    if not recs:
        recs.append({"player": "Hold", "score": 0.5})
    return {
        "role": "waiver",
        "waiver_recs": recs,
        "rationale": "Rune scoring system rates FA pickups and decoy claims",
    }
