

"""
Loads all raw Jooble JSON dumps into a DuckDB table called raw_jobs.
Place this inside warehouse/ (alongside dbt_project.yml) and run:

    python load_raw_to_duckdb.py

Re-run any time you want to refresh raw_jobs with the latest files
on disk (it fully replaces the table each time — this script's job
is only to make raw JSON queryable, not to dedupe or transform).
"""

import json
import duckdb
from pathlib import Path

# Adjust these two paths if your layout differs
RAW_DIR = Path(__file__).resolve().parent.parent / "Ingestion" / "raw" / "jobs"
DB_PATH = Path(__file__).resolve().parent / "dev.duckdb"


def load_all_postings(raw_dir: Path):
    rows = []
    for day_folder in sorted(raw_dir.iterdir()):
        if not day_folder.is_dir():
            continue
        for file in day_folder.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                wrapper = json.load(f)

            payload = wrapper.get("payload")
            if not payload:
                continue  # skip any leftover null-payload files

            jobs = payload.get("jobs", [])
            fetched_at = wrapper.get("fetched_at")
            query_keywords = wrapper.get("query", {}).get("keywords")

            for job in jobs:
                rows.append({
                    "id": job.get("id"),
                    "title": job.get("title"),
                    "company": job.get("company"),
                    "location": job.get("location"),
                    "salary": job.get("salary"),
                    "snippet": job.get("snippet"),
                    "source_site": job.get("source"),
                    "type": job.get("type"),
                    "link": job.get("link"),
                    "updated": job.get("updated"),
                    "fetched_at": fetched_at,
                    "query_keywords": query_keywords,
                })
    return rows


def main():
    rows = load_all_postings(RAW_DIR)
    print(f"Loaded {len(rows)} posting-snapshots from raw files.")

    con = duckdb.connect(str(DB_PATH))

    con.execute("DROP TABLE IF EXISTS raw_jobs")
    con.execute("""
        CREATE TABLE raw_jobs (
            id BIGINT,
            title VARCHAR,
            company VARCHAR,
            location VARCHAR,
            salary VARCHAR,
            snippet VARCHAR,
            source_site VARCHAR,
            type VARCHAR,
            link VARCHAR,
            updated VARCHAR,
            fetched_at VARCHAR,
            query_keywords VARCHAR
        )
    """)

    con.executemany(
        """
        INSERT INTO raw_jobs
        (id, title, company, location, salary, snippet, source_site, type, link, updated, fetched_at, query_keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                r["id"], r["title"], r["company"], r["location"], r["salary"],
                r["snippet"], r["source_site"], r["type"], r["link"],
                r["updated"], r["fetched_at"], r["query_keywords"],
            )
            for r in rows
        ],
    )

    count = con.execute("SELECT COUNT(*) FROM raw_jobs").fetchone()[0]
    print(f"raw_jobs table now has {count} rows.")
    con.close()


if __name__ == "__main__":
    main()
