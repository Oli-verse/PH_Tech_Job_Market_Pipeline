import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from pathlib import Path

# --- Connect to the warehouse (read-only) ---
DB_PATH = Path(__file__).resolve().parent.parent / "warehouse" / "dev.duckdb"

@st.cache_data(ttl=600)
def load_data():
    con = duckdb.connect(str(DB_PATH), read_only=True)

    postings = con.execute("""
        SELECT
            f.job_id,
            f.title,
            c.company_name,
            l.location_name,
            f.salary,
            f.employment_type,
            f.source_site,
            d.date_day
        FROM fact_job_postings f
        LEFT JOIN dim_company c ON f.company_key = c.company_key
        LEFT JOIN dim_location l ON f.location_key = l.location_key
        LEFT JOIN dim_date d ON f.date_key = d.date_key
    """).fetchdf()

    skills = con.execute("""
        SELECT job_id, skill_name
        FROM int_job_skills
    """).fetchdf()

    con.close()
    return postings, skills

postings, skills = load_data()

# --- Page setup ---
st.set_page_config(page_title="PH Tech Job Market", layout="wide")
st.title("PH Tech Job Market Dashboard")
st.caption("Data Engineer & Data Analyst postings - Jooble API, refreshed daily via Airflow")

# --- Top metrics row ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Postings", len(postings))
col2.metric("Unique Companies", postings["company_name"].nunique())
col3.metric("Unique Locations", postings["location_name"].nunique())
col4.metric("Skills Detected", skills["skill_name"].nunique() if not skills.empty else 0)

st.divider()

# --- Postings by company ---
left, right = st.columns(2)

with left:
    st.subheader("Postings by Company")
    company_counts = postings["company_name"].value_counts().reset_index()
    company_counts.columns = ["company_name", "count"]
    fig = px.bar(company_counts, x="count", y="company_name", orientation="h")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=400)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Skill Mentions")
    if not skills.empty:
        skill_counts = skills["skill_name"].value_counts().reset_index()
        skill_counts.columns = ["skill_name", "count"]
        fig = px.bar(skill_counts, x="count", y="skill_name", orientation="h")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No skill mentions detected yet in the current dataset.")

st.divider()

# --- Postings over time ---
st.subheader("Postings Fetched Over Time")
if not postings.empty:
    daily_counts = postings.groupby("date_day").size().reset_index(name="postings")
    fig = px.line(daily_counts, x="date_day", y="postings", markers=True)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Raw table ---
st.subheader("All Postings")
st.dataframe(
    postings[["title", "company_name", "location_name", "employment_type", "source_site", "date_day"]],
    use_container_width=True,
    hide_index=True,
)
