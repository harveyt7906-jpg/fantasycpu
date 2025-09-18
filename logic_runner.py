#!/usr/bin/env python3
import argparse, sys, os, json
from datetime import datetime

import utils_core, team_logic, general_manager_logic, waiver_logic, scout_logic, learning
from trade_logic import run_trade_logic

OUT_DIR = "out"
os.makedirs(OUT_DIR, exist_ok=True)

def save_results(role: str, results: dict):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUT_DIR, f"{role}_{ts}.json")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f" Saved {role} results -> {filename}")
    except Exception as e:
        print(f" Could not save {role} results:", e)

def run_head_coach():
    roster, odds, weather = utils_core.load_roster(), utils_core.fetch_vegas_odds(), utils_core.fetch_weather_data()
    results = team_logic.run_head_coach_logic(roster, odds, weather, None)
    save_results("head_coach", results)
    return results

def run_general_manager():
    roster, odds, weather = utils_core.load_roster(), utils_core.fetch_vegas_odds(), utils_core.fetch_weather_data()
    results = general_manager_logic.run_general_manager_logic(roster, odds, weather)
    save_results("general_manager", results)
    return results

def run_waiver():
    roster, odds, weather = utils_core.load_roster(), utils_core.fetch_vegas_odds(), utils_core.fetch_weather_data()
    results = waiver_logic.run_waiver_logic(roster, odds, weather)
    save_results("waiver", results)
    return results

def run_scout():
    roster, odds, weather = utils_core.load_roster(), utils_core.fetch_vegas_odds(), utils_core.fetch_weather_data()
    results = scout_logic.run_scout_logic(roster, odds, weather)
    save_results("scout", results)
    return results

def run_trade():
    roster, odds, weather = utils_core.load_roster(), utils_core.fetch_vegas_odds(), utils_core.fetch_weather_data()
    results = run_trade_logic(roster, odds, weather)
    save_results("trade", results)
    return results

def run_learning():
    results = learning.refine_strategy()
    save_results("learning", results)
    return results

def run_all():
    return {
        "head_coach": run_head_coach(),
        "gm": run_general_manager(),
        "waiver": run_waiver(),
        "scout": run_scout(),
        "trade": run_trade(),
        "learning": run_learning(),
    }

def main():
    parser = argparse.ArgumentParser(description="Thanos Rune Logic Runner")
    parser.add_argument("--hc", action="store_true", help="Run Head Coach only")
    parser.add_argument("--gm", action="store_true", help="Run GM only")
    parser.add_argument("--waiver", action="store_true", help="Run Waiver only")
    parser.add_argument("--scout", action="store_true", help="Run Scout only")
    parser.add_argument("--trade", action="store_true", help="Run Trade only")
    parser.add_argument("--learning", action="store_true", help="Run Learning only")
    parser.add_argument("--all", action="store_true", help="Run all roles")
    args = parser.parse_args()

    if args.hc: run_head_coach()
    elif args.gm: run_general_manager()
    elif args.waiver: run_waiver()
    elif args.scout: run_scout()
    elif args.trade: run_trade()
    elif args.learning: run_learning()
    elif args.all: run_all()
    else:
        print(" Please provide one of: --hc, --gm, --waiver, --scout, --trade, --learning, --all")
        sys.exit(1)

if __name__ == "__main__":
    main()
