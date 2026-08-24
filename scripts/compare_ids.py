"""
Compares job posting IDs across multiple days of raw JSON dumps
to validate dedup logic before building the orchestration layer.

Usage:
    Place this script anywhere, then update RAW_DIR to point at
    your Ingestion/raw/jobs folder, and run:

        python compare_ids.py
"""

import json
import os
from pathlib import Path
from collections import defaultdict

# Point this at your raw/jobs folder (contains one subfolder per day)
RAW_DIR = Path("../Ingestion/raw/jobs")


def load_all_ids_by_day(raw_dir: Path):

    days = {}

    for day_folder in sorted(raw_dir.iterdir()):
        if not day_folder.is_dir():
            continue

        day_jobs = {}
        for file in day_folder.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Your wrapper stores the actual API response under "payload"
            jobs = data.get("payload", {}).get("jobs", [])
            for job in jobs:
                job_id = job.get("id")
                if job_id is None:
                    continue
                day_jobs[job_id] = {
                    "title": job.get("title"),
                    "salary": job.get("salary"),
                    "company": job.get("company"),
                    "updated": job.get("updated"),
                }

        days[day_folder.name] = day_jobs

    return days


def compare_days(days: dict):
    day_names = sorted(days.keys())

    if len(day_names) < 2:
        print("Only found 1 day of data — need at least 2 to compare.")
        return

    print(f"Days found: {day_names}\n")

    for i in range(len(day_names) - 1):
        d1, d2 = day_names[i], day_names[i + 1]
        ids1, ids2 = set(days[d1].keys()), set(days[d2].keys())

        seen_both = ids1 & ids2
        only_d1 = ids1 - ids2   # disappeared by d2
        only_d2 = ids2 - ids1   # new on d2

        print(f"=== {d1} -> {d2} ===")
        print(f"  Total on {d1}: {len(ids1)}")
        print(f"  Total on {d2}: {len(ids2)}")
        print(f"  Seen on both days (id repeats correctly): {len(seen_both)}")
        print(f"  Disappeared after {d1} (closed/expired?): {len(only_d1)}")
        print(f"  New on {d2}: {len(only_d2)}")

        # Check for changed fields on repeated ids
        changed = []
        for job_id in seen_both:
            j1, j2 = days[d1][job_id], days[d2][job_id]
            if j1["salary"] != j2["salary"] or j1["title"] != j2["title"]:
                changed.append((job_id, j1, j2))

        if changed:
            print(f"  Repeated ids with CHANGED title/salary: {len(changed)}")
            for job_id, j1, j2 in changed:
                print(f"    id={job_id} | {d1}: {j1['title']} / {j1['salary']}"
                      f"  ->  {d2}: {j2['title']} / {j2['salary']}")
        print()


if __name__ == "__main__":
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Couldn't find {RAW_DIR.resolve()} — update RAW_DIR at the top "
            f"of this script to point at your Ingestion/raw/jobs folder."
        )

    days = load_all_ids_by_day(RAW_DIR)
    compare_days(days)