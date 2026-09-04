select
    j.id as job_id,
    c.company_key,
    l.location_key,
    d.date_key,
    j.title,
    j.salary,
    j.employment_type,
    j.source_site,
    j.link,
    j.fetched_at
from {{ ref('stg_jobs') }} j
left join {{ ref('dim_company') }} c on j.company = c.company_name
left join {{ ref('dim_location') }} l on j.location = l.location_name
left join {{ ref('dim_date') }} d on cast(j.fetched_at as date) = d.date_day
