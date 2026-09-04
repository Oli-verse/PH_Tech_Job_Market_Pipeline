with source as (

    select * from {{ source('raw', 'raw_jobs') }}

),

cleaned as (

    select
        id,
        trim(title) as title,
        trim(company) as company,
        trim(location) as location,
        nullif(trim(salary), '') as salary,  -- empty string -> real null
	snippet,
        source_site,
        type as employment_type,
        link,
        try_cast(updated as timestamp) as updated_at,
        try_cast(fetched_at as timestamp) as fetched_at,
        query_keywords

    from source
    where id is not null

),

filtered as (

    select *
    from cleaned
    where
        lower(title) like '%data engineer%'
        or lower(title) like '%data analyst%'
        or lower(title) like '%data engineering%'
        or lower(title) like '%analytics engineer%'

),

deduped as (

    select *,
        row_number() over (
            partition by id
            order by fetched_at desc
        ) as rn

    from filtered

)

select
    id,
    title,
    company,
    location,
    salary,
    snippet,
    source_site,
    employment_type,
    link,
    updated_at,
    fetched_at,
    query_keywords
from deduped
where rn = 1
