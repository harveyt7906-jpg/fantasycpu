import utils_core, random


def run_scout_logic(opponent, odds, weather):
    profile = {"bias": "RB_heavy" if random.random() > 0.5 else "WR_heavy"}
    tendencies = ["PanicTrades", "IgnoresKickers"]
    weaknesses = ["ShallowBench", "OverplaysVeterans"]
    boom_candidates = ["SleeperTE", "WR_Rookie"]
    rune_focus = random.uniform(0.5, 0.85)
    return {
        "role": "scout",
        "profile": profile,
        "tendencies": tendencies,
        "weaknesses": weaknesses,
        "boom_candidates": boom_candidates,
        "logic": {"rune_focus": rune_focus},
        "rationale": "Rune opponent model built from neural profile and tendencies",
    }
