select
    j.id as job_id,
    s.skill_key,
    s.skill_name
from {{ ref('stg_jobs') }} j
cross join {{ ref('dim_skill') }} s
where lower(j.snippet) like '%' || lower(s.skill_name) || '%'
   or lower(j.title) like '%' || lower(s.skill_name) || '%'
