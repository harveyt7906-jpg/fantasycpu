import utils_core
import numpy as np
from datetime import datetime

def run_trade_logic(roster, odds, weather, free_agents=None, opponents=None):
    try:
        fa = free_agents if free_agents else utils_core.fetch_free_agents()
        opps = opponents if opponents else utils_core.load_opponents()

        # Baseline valuations
        roster_vals = {p["id"]: _player_value(p, odds, weather) for p in roster}
        fa_vals = {p["id"]: _player_value(p, odds, weather) for p in fa}

        # Opponent roster needs
        opp_gaps = {o["team"]: _assess_needs(o["roster"], odds, weather) for o in opps}

        proposals = []
        for o in opps:
            needs = opp_gaps[o["team"]]
            for pid, val in roster_vals.items():
                pos = _pos_from_id(pid)
                if pos in needs and val < np.mean(list(roster_vals.values())):
                    target = _find_upgrade(fa_vals, pos)
                    if target:
                        proposals.append({
                            "partner": o["team"],
                            "give": utils_core.lookup_player(pid),
                            "get": target,
                            "rationale": f"Trade with {o['team']} improves {pos}: "
                                         f"give {pid}, get {target['id']} ({target['name']})"
                        })

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "trade_proposals": proposals,
            "summary": f"{len(proposals)} viable trades identified",
        }

    except Exception as e:
        return {"error": str(e)}

def _player_value(player, odds, weather):
    base = player.get("projection", 0.0)
    opp = player.get("opponent", "")
    odds_boost, weather_penalty = 0.0, 0.0

    if opp in odds:
        line = odds[opp].get("line", 0)
        odds_boost = line * 0.01
    if opp in weather and weather[opp].get("wind", 0) > 20:
        weather_penalty = 0.1 * base

    return base + odds_boost - weather_penalty

def _assess_needs(roster, odds, weather):
    vals = [_player_value(p, odds, weather) for p in roster]
    if not vals:
        return set()
    avg_val = np.mean(vals)
    needs = []
    for p in roster:
        if _player_value(p, odds, weather) < 0.7 * avg_val:
            needs.append(_pos_from_id(p["id"]))
    return set(needs)

def _find_upgrade(fa_vals, pos):
    candidates = [utils_core.lookup_player(pid) for pid in fa_vals if _pos_from_id(pid) == pos]
    candidates = [c for c in candidates if c]  # filter None
    candidates = sorted(candidates, key=lambda p: fa_vals.get(p["id"], 0), reverse=True)
    return candidates[0] if candidates else None

def _pos_from_id(pid):
    try:
        return pid.split("_")[0]  # e.g. "RB_123" -> "RB"
    except Exception:
        return "FLEX"
