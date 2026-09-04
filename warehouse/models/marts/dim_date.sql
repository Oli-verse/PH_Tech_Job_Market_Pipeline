with bounds as (
	select
	    min(cast(fetched_at as date)) as min_date,
	    max(cast(fetched_at as date)) as max_date
	from {{ ref('stg_jobs')}}
),

date_spine as (
	select
	    cast(min_date + (interval '1 day' * generate_series) as date) as date_day
	from bounds, generate_series(0, cast((max_date - min_date) as integer))
)

select
    {{ dbt_utils.generate_surrogate_key(['date_day'])}} as date_key,
    date_day,
    extract(year from date_day) as year,
    extract(month from date_day) as month,
    extract(day from date_day) as day,
    strftime(date_day, '%A') as day_name
from date_spine
