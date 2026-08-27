# PH Tech Job Market Pipeline — Project Log

A running record of what's been built, what broke, what was learned, and why
decisions were made. Kept alongside the code so the reasoning isn't lost
useful for picking the project back up later, and for interview conversations.

---

## Project Goal

Track the Philippine tech job market (Data Engineer / Data Analyst roles)
over time by pulling job postings on a schedule and building a warehouse
that shows how demand, skills, and salaries shift. The project is designed
to demonstrate orchestration, incremental/idempotent loading, proper data
modeling, and data quality checks,not just a one-time extract-transform-load.

**Planned architecture:** Ingestion → Airflow orchestration → dbt staging/marts
(star schema) → data quality tests → dashboard.

---

## Activity Log

### Phase 1 — Source selection

- Evaluated Adzuna API - ruled out, does not support the Philippines.
- Selected **Jooble API** - free tier, no country restriction, returns
  structured JSON. Registered for a personal API key.
- Noted: Jooble requests are POST with a JSON body (not GET with query
  params) the key is embedded in the URL path.

### Phase 2 — Initial extraction script

- Built `extract_raw.py`: queries Jooble for "data engineer" and
  "data analyst" postings (location: Philippines), saves each response
  as raw JSON under `raw/jobs/YYYY-MM-DD/`.
- Raw files wrapped with metadata: `fetched_at` timestamp, `source`,
  and the `query` used payload itself left untouched, per raw-layer
  best practice (never transform at ingestion).
- Loaded the API key via `.env` + `python-dotenv`, kept out of version
  control under `secret/.env`.

### Phase 3 — Git / environment setup

- Hit several environment snags common to first-time repo setup:
  - PowerShell's `curl` alias ≠ real curl - had to use `curl.exe` or
    `Invoke-RestMethod` instead.
  - `.gitignore` initially placed inside `.venv/` instead of the project
    root - had no effect on what Git tracked.
  - `.venv/`, `Lib/`, and other virtual environment files were already
    committed before the `.gitignore` was corrected — required
    `git rm -r --cached .` to untrack everything and re-add cleanly.
  - Git push failures traced back to: no Git identity configured
    (`user.email` / `user.name` unset), and no commits existing yet
    despite branch rename attempts (`git branch -M main` doesn't create
    commits, only renames existing branches).
- Resolved by setting Git identity, committing, then pushing.

### Phase 4 — Validation (id / dedup logic)

- Built `compare_ids.py` to compare job posting `id`s across days of
  raw JSON dumps — checks for: ids repeating (dedup key reliability),
  ids disappearing (closed/expired postings), new ids appearing, and
  whether repeated ids show changed title/salary (would indicate need
  for SCD Type 2 history tracking).
- **Bug found (path resolution):** initial `RAW_DIR` used a relative
  path that only worked depending on which folder the script was run
  from. Fixed by resolving the path relative to the script's own file
  location (`Path(__file__).resolve().parent...`) instead of the
  current working directory.
- **Bug found (silent data loss in `extract_raw.py`):**
  `if resp.raise_for_status():` was used to gate returning the parsed
  JSON. `raise_for_status()` returns `None` on success and raises an
  exception on failure — it never returns a truthy value. This meant
  the condition was always `False` on successful requests, so
  `fetch_jobs()` silently returned `None` every time, even when the
  API call worked. Every extraction run between roughly Aug 12–24
  saved `"payload": null` instead of real data.
- **Second bug in the same function:** the request payload used the
  `keywords` variable as a dict key instead of the literal string
  `"keywords"`, meaning Jooble was receiving malformed query
  parameters regardless of the first bug.
- Fixed both issues, added a try/except around the extraction loop so
  future failures are logged instead of silently saved as null.
- Deleted the affected all-null day-folders (Aug 12–24) rather than
  keeping unusable data.

### Phase 5 — Re-validation with fixed script

- Re-ran extraction (3x/day) for Aug 25–27.
- `compare_ids.py` results:
  - Aug 25 → 26: 99 total → 82 total; 72 ids repeated; 27 disappeared;
    10 new.
  - Aug 26 → 27: 82 total → 101 total; 72 ids repeated; 10 disappeared;
    29 new.
  - No repeated ids showed changed title/salary in this window.
- Confirms the `id` field is a reliable dedup/natural key, and that
  postings genuinely churn day to day (supports needing an
  `is_active` / `last_seen_date` field in the eventual data model,
  not a static table).

---

## Findings & Decisions

| Finding                                                                                                                           | Decision / Implication                                                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Adzuna has no PH coverage                                                                                                         | Use Jooble instead                                                                                                                                                  |
| Jooble keyword search matches snippet text, not just title (e.g. "Golang Engineer" matched on the word "data" in the description) | Raw layer stays unfiltered (correct — don't clean at ingestion); title filtering will be enforced explicitly in the dbt **staging** layer with a title allowlist    |
| `salary` field returned empty (`""`) on every observed posting so far                                                             | Needs further checking across more data before relying on it for any salary-based dashboard metric — may be a PH-specific gap in Jooble's data                      |
| Job postings churn noticeably day to day (~10–30 changes per day-pair)                                                            | Data model needs an `is_active` or `last_seen_date` concept, not just insert-once rows                                                                              |
| No observed title/salary changes on repeated ids (small sample)                                                                   | Tentatively simple upsert (SCD Type 1) is sufficient; revisit if a longer observation window shows fields changing on existing ids                                  |
| `id` field is stable and reliable across days                                                                                     | Use as the natural/dedup key in staging and warehouse layers                                                                                                        |
| Manual runs had gaps in coverage (e.g. Aug 14 → Aug 23)                                                                           | Not a blocker for now, but reinforces the need for Airflow scheduling + failure alerting once orchestration is built, so missed runs are visible rather than silent |

---

## Bugs Fixed (Reference)

1. **`raise_for_status()` misuse** — treated as a boolean return value; it
   isn't one. Fixed to call it standalone (raises on error) and return
   `resp.json()` unconditionally after.
2. **Wrong dict key in request payload** — `{keywords: keywords, ...}`
   used the variable as the key instead of `"keywords"`.
3. **Relative path bugs** (`.env` loading, `RAW_DIR` in `compare_ids.py`)
   — both fixed by resolving paths relative to `Path(__file__)` instead
   of the current working directory, making scripts runnable from any
   working directory.
4. **`.gitignore` scope** — placed inside `.venv/` initially, had no
   effect; moved to project root and re-applied with `git rm -r --cached .`
   to untrack already-committed files.

---

## Current Status

- ✅ Ingestion script working and validated (Aug 25–27 data confirmed
  reliable id behavior)
- ✅ Repo structure and Git tracking cleaned up
- ⏳ Next: Airflow orchestration — need to decide run frequency
  (daily vs multiple times/day) before defining the DAG schedule and
  finalizing "new vs seen" logic
- 🔜 Not yet started: dbt staging/marts, data quality tests, dashboard

---

## Project Structure (target)

```
Market Pipeline/
├── ingestion/
│   ├── extract_raw.py
│   └── raw/jobs/YYYY-MM-DD/
├── scripts/
│   └── compare_ids.py
├── dags/                  (planned)
├── warehouse/             (planned — dbt project)
├── dashboard/             (planned)
├── secret/.env            (gitignored)
└── .gitignore
```
