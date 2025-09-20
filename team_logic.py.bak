import random, numpy as np, utils_core


def simulate_matchup(roster, odds, weather, trials=500):
    win_scores = []
    for _ in range(trials):
        base = random.uniform(0.4, 0.6)
        if odds and "data" in odds:
            base += 0.05
        if weather and weather.get("wind") and weather["wind"] > 20:
            base -= 0.05
        win_scores.append(max(0, min(1, base + random.gauss(0, 0.1))))
    return (
        np.mean(win_scores),
        np.percentile(win_scores, 10),
        np.percentile(win_scores, 90),
    )


def run_head_coach_logic(roster, odds, weather, opponent=None):
    win, floor, ceiling = simulate_matchup(roster, odds, weather)
    lineup = ["Starter_" + str(i) for i in range(1, 10)]
    bench = ["Bench_" + str(i) for i in range(1, 7)]
    return {
        "role": "head_coach",
        "lineup": lineup,
        "bench": bench,
        "logic": {"win_prob": win, "floor": floor, "ceiling": ceiling},
        "odds": odds,
        "weather": weather,
        "rationale": f"Monte Carlo {int(500)} trials show win {win:.2f}, floor {floor:.2f}, ceiling {ceiling:.2f}",
    }
