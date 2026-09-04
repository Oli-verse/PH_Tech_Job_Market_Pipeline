with locations as (
	select distinct location
	from {{ ref('stg_jobs')}}
	where location is not null
)


select
    {{ dbt_utils.generate_surrogate_key(['location'])}} as location_key,
    location as location_name
from locations
