import sys
from pathlib import Path
from datetime import datetime

from airflow.sdk import dag, task

PROJECT_ROOT = Path("/home/oliver/PH_Tech_Job_Market_Pipeline")
sys.path.insert(0, str(PROJECT_ROOT / "Ingestion"))

import extract_raw

FAILURE_LOG = PROJECT_ROOT / "Dags" / "failure_log.txt"


def log_failure(context):
    with open(FAILURE_LOG, "a") as f:
        f.write(
            f"{datetime.now().isoformat()} | "
            f"DAG: {context['dag'].dag_id} | "
            f"Task: {context['task_instance'].task_id} | "
            f"Run: {context['run_id']}\n"
        )


@dag(
    dag_id="job_market_pipeline",
    schedule="@daily",
    start_date=datetime(2026, 8, 30),
    catchup=False,
    tags=["job-market", "portfolio"],
    default_args={"on_failure_callback": log_failure},
)
def job_market_pipeline():

    @task
    def extract_data_engineer_jobs():
        for page in range(1, 4):
            data = extract_raw.fetch_jobs("data engineer", page=page)
            extract_raw.save_raw(data, "data engineer")

    @task
    def extract_data_analyst_jobs():
        for page in range(1, 4):
            data = extract_raw.fetch_jobs("data analyst", page=page)
            extract_raw.save_raw(data, "data analyst")

    extract_data_engineer_jobs()
    extract_data_analyst_jobs()


job_market_pipeline()
