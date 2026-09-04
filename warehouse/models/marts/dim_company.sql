with companies as (
	select distinct company
	from {{ ref('stg_jobs')}}
	where company is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['company']) }} as company_key,
    company as company_name
from companies
