#!/usr/bin/env python3
"""
add_run.py

Safely add a new run to config/runs.yml if it does not already exist.
"""

import yaml
import argparse
from pathlib import Path

RUNS_YML = Path("config/runs.yml")


def load_yaml():
    if not RUNS_YML.exists():
        return {}
    with open(RUNS_YML) as f:
        return yaml.safe_load(f) or {}


def save_yaml(data):
    with open(RUNS_YML, "w") as f:
        yaml.dump(data, f, sort_keys=False)


def run_exists(cfg, run_name):
    for category in cfg.values():
        for campaign in category.values():
            for family in campaign.values():
                for run in family:
                    if run.get("name") == run_name:
                        return True
    return False


def main():

    parser = argparse.ArgumentParser(description="Add run to runs.yml")
    parser.add_argument("--name", required=True)
    parser.add_argument("--atm_in", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--family", required=True)

    args = parser.parse_args()

    cfg = load_yaml()

    if run_exists(cfg, args.name):
        print(f"Run '{args.name}' already exists. Nothing to do.")
        return

    # ensure hierarchy exists
    cfg.setdefault(args.category, {})
    cfg[args.category].setdefault(args.campaign, {})
    cfg[args.category][args.campaign].setdefault(args.family, [])

    new_run = {
        "name": args.name,
        "atm_in": args.atm_in
    }

    cfg[args.category][args.campaign][args.family].append(new_run)

    save_yaml(cfg)

    print(f"Added run '{args.name}' to {args.category}/{args.campaign}/{args.family}")


if __name__ == "__main__":
    main()
