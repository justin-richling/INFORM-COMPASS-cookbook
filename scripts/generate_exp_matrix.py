#!/usr/bin/env python3
"""
generate_exp_matrix.py

Generates a hierarchical run matrix JSON file from a YAML configuration.
Supports categories → campaigns → case families → runs.
Supports `update: true` in YAML to force overwrite of existing JSON entries.
License: MIT
"""

import yaml
import json
import os
import sys
from pathlib import Path
from parse_namelist import summarize_atm_in
from datetime import datetime

OUT_JSON = Path("docs/run_matrix.json")

# ----------------------------
# Terminal colors
# ----------------------------

class C:
    ADD = "\033[32m"      # green
    REMOVE = "\033[31m"   # red
    CHANGE = "\033[33m"   # yellow
    HEADER = "\033[36m"   # cyan
    END = "\033[0m"

# ----------------------------
# Helper functions
# ----------------------------

def print_grouped_diffs(diffs):

    if not diffs:
        print("   No visible differences")
        return

    for section, changes in diffs.items():

        print(f"\n  {C.HEADER}{section}{C.END}")

        for c in changes:
            print("   ", c)


def dict_diff(old, new, path=""):
    """
    Recursively compute differences between dictionaries/lists.
    Returns grouped differences.
    """

    diffs = {}

    def record(section, msg):
        diffs.setdefault(section, []).append(msg)

    def recurse(o, n, p=""):
        section = p.split(".")[0] if p else "root"

        if isinstance(o, dict) and isinstance(n, dict):
            keys = set(o) | set(n)

            for k in keys:
                new_path = f"{p}.{k}" if p else k

                if k not in o:
                    record(section, f"{C.ADD}+ {new_path}: {n[k]}{C.END}")

                elif k not in n:
                    record(section, f"{C.REMOVE}- {new_path}: {o[k]}{C.END}")

                else:
                    recurse(o[k], n[k], new_path)

        elif isinstance(o, list) and isinstance(n, list):

            added = set(n) - set(o)
            removed = set(o) - set(n)

            if added:
                record(section, f"{C.ADD}+ {p}: {sorted(added)}{C.END}")

            if removed:
                record(section, f"{C.REMOVE}- {p}: {sorted(removed)}{C.END}")

        else:
            if o != n:
                record(section, f"{C.CHANGE}~ {p}: {o} -> {n}{C.END}")

    recurse(old, new)

    return diffs


'''def dict_diff(old, new, path=""):
    """
    Recursively find differences between two dictionaries/lists.
    Returns a list of readable change strings.
    """
    changes = []

    # Dict comparison
    if isinstance(old, dict) and isinstance(new, dict):
        keys = set(old) | set(new)
        for k in keys:
            p = f"{path}.{k}" if path else k
            if k not in old:
                changes.append(f"+ {p}: {new[k]}")
            elif k not in new:
                changes.append(f"- {p}: {old[k]}")
            else:
                changes.extend(dict_diff(old[k], new[k], p))

    # List comparison
    elif isinstance(old, list) and isinstance(new, list):
        if old != new:
            added = set(new) - set(old)
            removed = set(old) - set(new)

            if added:
                changes.append(f"+ {path}: {sorted(added)}")
            if removed:
                changes.append(f"- {path}: {sorted(removed)}")

    # Primitive comparison
    else:
        if old != new:
            changes.append(f"~ {path}: {old} -> {new}")

    return changes'''


def push_github():
    print("Pushing run_matrix.json changes to GitHub...")
    os.system("git add docs/run_matrix.json")
    os.system("git commit -m 'Update run matrix [skip ci]' || echo 'No changes to commit'")
    os.system("git push origin HEAD:add-cesm-job-matrix")
    print("Pushed changes to GitHub successfully.")


def load_matrix(path=OUT_JSON):
    if not path.exists() or path.stat().st_size == 0:
        path.write_text("[]")
        return []
    with open(path) as f:
        return json.load(f)


def delete_entry(matrix, run_name):
    new_matrix = [r for r in matrix if r.get("run_name") != run_name]
    if len(new_matrix) < len(matrix):
        print(f"  Deleted run: {run_name}")
    else:
        print(f"  Delete requested, but run not found: {run_name}")
    return new_matrix


def add_entry(matrix, new_entry, update=False):
    for i, existing in enumerate(matrix):
        if not isinstance(existing, dict):
            continue
        if existing.get("run_name") == new_entry.get("run_name"):
            if not update and existing.get("atm_in_sha256") == new_entry.get("atm_in_sha256"):
                print(f"  Run '{new_entry['run_name']}' already exists (identical atm_in). Skipping.")
                return matrix

            print(f"  Same run_name but different atm_in or update=True detected: {new_entry['run_name']}")
            print("  Differences:")
            try:
                """from pprint import pprint
                print("  Differences:")
                pprint({k: {"old": existing.get(k), "new": new_entry.get(k)}
                        for k in ["nudged_vars","cosp_vars","fincl","other_vars"]})"""
                diffs = dict_diff(existing, new_entry)

                print_grouped_diffs(diffs)

                # Flatten changes for history storage
                history_changes = []

                for section in diffs.values():
                    history_changes.extend(section)

                timestamp = datetime.utcnow().isoformat()

                history_entry = {
                    "timestamp": timestamp,
                    "changes": history_changes
                }

                existing.setdefault("history", []).append(history_entry)

                # update entry
                existing.update(new_entry)
            except Exception:
                pass

            if update or existing.get("atm_in_sha256") != new_entry.get("atm_in_sha256"):
                matrix[i] = new_entry
                print(f"  Updated existing run: {new_entry['run_name']}")
            return matrix

    # Insert new entry at the front if not found
    matrix.insert(0, new_entry)
    print(f"  Added new run: {new_entry['run_name']}")
    return matrix


# ----------------------------
# Load YAML configuration
# ----------------------------

cfg_path = Path("config/runs.yml")
if not cfg_path.exists():
    print(f"{cfg_path} not found, skipping YAML load")
    cfg = {}
else:
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

# ----------------------------
# Load existing JSON
# ----------------------------

matrix = load_matrix()
matrix0 = len(matrix)
print(f"Runs in matrix before check: {matrix0}")

# ----------------------------
# Flatten YAML to list of run summaries
# ----------------------------

yaml_run_names = set()
new_runs = []

for category, campaigns in cfg.items():
    print(f"\nProcessing category: {category}")

    if not isinstance(campaigns, dict):
        print(f" Warning: category '{category}' is not a dict, skipping")
        continue

    for campaign_name, case_families in campaigns.items():
        print(f" Processing campaign: {campaign_name}")

        if not isinstance(case_families, dict):
            print(f"  Warning: campaign '{campaign_name}' is not a dict, skipping")
            continue

        for case_family_name, runs_list in case_families.items():
            print(f"  Processing case family: {case_family_name}")

            if not isinstance(runs_list, list):
                print(f"   Warning: case family '{case_family_name}' is not a list, skipping")
                continue

            for run_dict in runs_list:
                if not isinstance(run_dict, dict):
                    print(f"    Warning: skipping malformed run entry: {run_dict}")
                    continue

                if run_dict.get("delete", False):
                    matrix = delete_entry(matrix, run_dict["name"])
                    continue

                summary = summarize_atm_in(run_dict.get("atm_in"))
                if summary is None:
                    continue

                summary["run_name"] = run_dict["name"]
                summary["category"] = category
                summary["campaign"] = campaign_name
                summary["case_family"] = case_family_name

                # Keep both summary and YAML dict together
                new_runs.append((summary, run_dict))
                yaml_run_names.add(run_dict["name"])

# ----------------------------
# Remove stale runs
# ----------------------------

removed_runs = [r["run_name"] for r in matrix if r.get("run_name") not in yaml_run_names]
matrix = [r for r in matrix if r.get("run_name") in yaml_run_names]

if removed_runs:
    print(f"\nRemoved {len(removed_runs)} stale runs from JSON:")
    for r in removed_runs:
        print(f" - {r}")

# ----------------------------
# Add new/updated runs
# ----------------------------

for summary, run_dict in new_runs:
    update_flag = run_dict.get("update", False)
    matrix = add_entry(matrix, summary, update=update_flag)

print(f"\nRuns in matrix after update: {len(matrix)} (previously {matrix0})")

from datetime import datetime
import shutil

if OUT_JSON.exists():
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    backup = OUT_JSON.parent / f"run_matrix_backup_{timestamp}.json"
    shutil.copy2(OUT_JSON, backup)
    print(f"Backup created: {backup}")

# ----------------------------
# Write JSON
# ----------------------------

with open(OUT_JSON, "w") as f:
    json.dump(matrix, f, indent=2)

# ----------------------------
# GitHub push
# ----------------------------

push_github()

"""# ----------------------------
# Optional GitHub push
# ----------------------------

if len(sys.argv) > 1 and sys.argv[1] == "push-github":
    push_github()"""
