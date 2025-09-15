#!/usr/bin/env python3
import argparse
import sys
import os
import json
from datetime import datetime

# Import WatsonAristotle logic modules
from team_logic import run_team_analysis
from waiver_logic import run_general_manager_logic
from scout_logic import run_scout_logic

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
    print(" Running Head Coach logic (WatsonAristotle)")
    try:
        results = run_team_analysis()
        print(" Head Coach results:", results)
        save_results("head_coach", results)
    except Exception as e:
        print(" Head Coach failed:", e)


def run_general_manager():
    print(" Running General Manager logic (WatsonAristotle)")
    try:
        results = run_general_manager_logic()
        print(" GM results:", results)
        save_results("general_manager", results)
    except Exception as e:
        print(" General Manager failed:", e)


def run_scout():
    print(" Running Scout logic (WatsonAristotle)")
    try:
        results = run_scout_logic()
        print(" Scout results:", results)
        save_results("scout", results)
    except Exception as e:
        print(" Scout failed:", e)


def run_all():
    print(" Running full WatsonAristotle tri-cameral AI (HC + GM + Scout)")
    run_head_coach()
    run_general_manager()
    run_scout()


def main():
    parser = argparse.ArgumentParser(description="WatsonAristotle Logic Runner")
    parser.add_argument("--hc", action="store_true", help="Run Head Coach logic only")
    parser.add_argument(
        "--gm", action="store_true", help="Run General Manager logic only"
    )
    parser.add_argument("--scout", action="store_true", help="Run Scout logic only")
    parser.add_argument(
        "--all", action="store_true", help="Run all 3 roles (HC + GM + Scout)"
    )

    args = parser.parse_args()

    if args.hc:
        run_head_coach()
    elif args.gm:
        run_general_manager()
    elif args.scout:
        run_scout()
    elif args.all:
        run_all()
    else:
        print(" Please provide one of: --hc, --gm, --scout, --all")
        sys.exit(1)


if __name__ == "__main__":
    main()
