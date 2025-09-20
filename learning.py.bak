import numpy as np, random

history_memory = []


def refine_strategy():
    global history_memory
    if not history_memory:
        history_memory = [
            {"week": 1, "decision": "safe", "win": True},
            {"week": 2, "decision": "boom", "win": False},
        ]
    win_rate = np.mean([1 if h["win"] else 0 for h in history_memory])
    boom_bias = sum(1 for h in history_memory if h["decision"] == "boom")
    safe_bias = sum(1 for h in history_memory if h["decision"] == "safe")
    adjust = "Shift to boom" if win_rate < 0.5 else "Stay balanced"
    rune_memory = random.uniform(0.4, 0.9)
    return {
        "role": "learning",
        "history_len": len(history_memory),
        "win_rate": win_rate,
        "bias": {"boom": boom_bias, "safe": safe_bias},
        "logic": {"rune_memory": rune_memory},
        "adjustment": adjust,
        "rationale": "Rune memory adapts weights from past outcomes into evolving strategy",
    }
