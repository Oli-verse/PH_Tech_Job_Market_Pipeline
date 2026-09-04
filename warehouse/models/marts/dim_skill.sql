select
    {{ dbt_utils.generate_surrogate_key(['skill_name']) }} as skill_key,
    skill_name
from {{ ref('skills_list') }}
