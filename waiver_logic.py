import utils_core, numpy as np
from thanos_council import consult_council


def run_waiver_logic(roster, odds, weather, replacement_level=8):
    moves = []
    try:
        sleeper = utils_core.fetch_sleeper_players()
        for pid, p in list(sleeper.items())[:50]:
            proj = 10 + np.random.normal(0, 3)
            if proj > replacement_level:
                moves.append(
                    {
                        "add": p.get("full_name", "?"),
                        "pos": p.get("position"),
                        "proj": proj,
                        "delta": proj - replacement_level,
                    }
                )
    except:
        pass
    ranked = sorted(moves, key=lambda x: x["delta"], reverse=True)[:10]
    council = consult_council("waiver", ranked)
    return {"role": "waiver", "logic": ranked, "council": council}
