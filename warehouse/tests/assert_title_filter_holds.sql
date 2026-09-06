-- This test FAILS if it returns any rows.
-- Asserts every row in stg_jobs actually matches the intended title allowlist —
-- catches a regression if stg_jobs.sql's WHERE clause is ever changed incorrectly.

select id, title
from {{ ref('stg_jobs') }}
where not (
    lower(title) like '%data engineer%'
    or lower(title) like '%data analyst%'
    or lower(title) like '%data engineering%'
    or lower(title) like '%analytics engineer%'
)
