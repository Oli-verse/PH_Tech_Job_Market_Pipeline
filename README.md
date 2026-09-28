# PH Tech Job Market Pipeline

An end-to-end ELT (Extract, Load, Transform) pipeline that tracks Data
Engineer and Data Analyst job postings in the Philippines. Job data is
extracted daily from the Jooble API, orchestrated with Apache Airflow,
modeled into a dbt/DuckDB star schema, validated with automated data
quality tests, and served through a live Streamlit dashboard.

---

## Summary

This project was built to demonstrate a complete, production-style data
pipeline rather than a one-off script: scheduled ingestion, incremental
and idempotent loading, a proper dimensional data model, automated data
quality enforcement, and a live-querying dashboard. It also doubles as
market research for the author's own Data Engineer / Data Analyst job
search in the Philippines.

**Architecture (6 layers):**

| # | Layer | What it does |
|---|---|---|
| 1 | Ingestion (Raw) | Pulls postings from the Jooble API daily; lands untouched JSON with an ingestion timestamp. |
| 2 | Orchestration | Apache Airflow schedules and runs the pipeline end to end. |
| 3 | Staging / Transform | dbt cleans raw data — title filtering, salary standardization, deduplication. |
| 4 | Warehouse Model | Star schema in DuckDB: `fact_job_postings` + `dim_company`, `dim_location`, `dim_date`, `dim_skill`. |
| 5 | Data Quality | 21 automated dbt tests (uniqueness, not-null, referential integrity, a custom business-rule test). |
| 6 | Serving | Streamlit dashboard querying the warehouse live. |

**Key findings surfaced by the pipeline:**
- Of 136 distinct postings pulled by keyword search, only ~7% (10 postings) had "Data Engineer"/"Data Analyst"-type terms in the title itself — the rest were snippet-matching noise, corrected for in the staging layer.
- Postings churn ~10–30 per day, motivating a "latest snapshot wins" dedup strategy in staging.
- PH tech postings on Jooble are tagged almost entirely at the country level, with little city-level granularity — likely reflecting the remote/BPO-heavy nature of the market.

---

## Project Structure

```
PH_Tech_Job_Market_Pipeline/
├── .venv/                      # Python virtual environment (not committed)
├── .gitignore
├── Ingestion/
│   ├── extract_raw.py          # Pulls postings from Jooble, lands raw JSON
│   └── raw/jobs/YYYY-MM-DD/    # Raw JSON output, partitioned by day (gitignored)
├── Dags/
│   └── job_market_pipeline_dag.py   # Airflow DAG (daily schedule, failure logging)
├── scripts/
│   └── compare_ids.py          # Validates dedup/ID behavior across day-folders
├── warehouse/                  # dbt project
│   ├── dbt_project.yml
│   ├── load_raw_to_duckdb.py   # Flattens raw JSON into a queryable raw_jobs table
│   ├── dev.duckdb              # Local DuckDB warehouse file (gitignored)
│   ├── seeds/
│   │   └── skills_list.csv     # Seeded skill keyword reference list
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml
│   │   │   ├── stg_jobs.sql
│   │   │   └── schema.yml      # Tests on stg_jobs
│   │   ├── intermediate/
│   │   │   └── int_job_skills.sql   # Many-to-many job↔skill bridge table
│   │   └── marts/
│   │       ├── dim_company.sql
│   │       ├── dim_location.sql
│   │       ├── dim_date.sql
│   │       ├── dim_skill.sql
│   │       ├── fact_job_postings.sql
│   │       └── schema.yml      # Tests on dimensions + fact table
│   └── tests/
│       └── assert_title_filter_holds.sql   # Custom business-rule test
├── Dashboard/
│   └── app.py                  # Streamlit dashboard
├── secret/
│   └── .env                    # API_KEY (gitignored)
└── PROJECT_LOG.md               # Full activity log, findings, and decisions
```

---

## Dependencies

**Environment**
- WSL2 (Ubuntu) — Airflow requires a Linux environment; does not run natively on Windows
- Python 3.10–3.14

**Python packages**
- `requests` — API calls to Jooble
- `python-dotenv` — loading the API key from `.env`
- `apache-airflow` (3.3.1) — orchestration
- `dbt-duckdb` — dbt adapter for the DuckDB warehouse
- `duckdb` — warehouse engine, also used directly by the raw-loading script
- `streamlit` — dashboard framework
- `plotly` — dashboard charts

**External services**
- [Jooble API](https://jooble.org/api/about) — free API key required (register, no cost)

---

## Installation

```bash
# 1. Enter WSL2 (Windows only — skip if already on Linux/macOS)
wsl

# 2. Clone the repository
git clone https://github.com/Oli-verse/PH_Tech_Job_Market_Pipeline.git
cd PH_Tech_Job_Market_Pipeline

# 3. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 4. Install ingestion dependencies
pip install requests python-dotenv

# 5. Add your Jooble API key
mkdir -p secret
echo "API_KEY=your_actual_jooble_key" > secret/.env

# 6. Install Airflow
pip install "apache-airflow==3.3.1" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.3.1/constraints-3.14.txt"

# 7. Install dbt + DuckDB
pip install dbt-duckdb duckdb

# 8. Install the dashboard dependencies
pip install streamlit plotly
```

---

## Manual Commands

**Run ingestion once, manually (without Airflow)**
```bash
cd Ingestion
python3 extract_raw.py
```

**Start Airflow (orchestrates daily ingestion automatically)**
```bash
cd ~/PH_Tech_Job_Market_Pipeline
source .venv/bin/activate
airflow standalone
```
Leave this running — it hosts the scheduler, API server, and DAG processor.
Access the UI at `http://localhost:8080`.

**Validate raw data / dedup logic**
```bash
cd scripts
python3 compare_ids.py
```

**Refresh the warehouse (run after new raw data has been ingested)**
```bash
cd warehouse
python load_raw_to_duckdb.py   # flattens raw JSON into raw_jobs table
dbt seed                       # loads seeds/skills_list.csv
dbt run                        # builds staging + warehouse models
dbt test                       # runs all 21 data quality tests
```

**Launch the dashboard**
```bash
cd warehouse
streamlit run ../Dashboard/app.py
```
Opens at `http://localhost:8501`.

**Typical day-to-day loop**
```bash
# Keep this running continuously (handles daily ingestion automatically):
airflow standalone

# Run periodically, whenever you want the warehouse/dashboard refreshed:
cd warehouse
python load_raw_to_duckdb.py && dbt run && dbt test
```
