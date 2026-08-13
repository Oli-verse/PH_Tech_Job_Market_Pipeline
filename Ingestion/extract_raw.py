import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path="../secret/.env")  # path relative to Ingestion/ folder

API_KEY = os.getenv("API_KEY")

if API_KEY is None:
    raise ValueError("API_KEY not found — check your .env path and variable name")

url = f"https://jooble.org/api/{API_KEY}"

def fetch_jobs(keywords, location="Philippines", page=1):
    payload = {keywords: keywords, "location": location, "page": str(page)}
    resp = requests.post(url, json=payload)
    if resp.raise_for_status():
        return resp.json()

def save_raw(data, keywords):
    now = datetime.now()
    folder = f"raw/jobs/{now.strftime('%Y-%m-%d')}"
    os.makedirs(folder, exist_ok=True)
    filename = f"{folder}/{keywords.replace(' ', '_')}_{now.strftime('%H%M%S')}.json"

    wrapper = {
        "fetched_at": now.isoformat(),
        "source": "jooble",
        "query": {"keywords": keywords, "location": "Philippines"},
        "payload": data
    }
    with open(filename, "w") as f:
        json.dump(wrapper, f, indent=2)
    print(f"Saved {filename}")

if __name__ == "__main__":
    for role in ["data engineer", "data analyst"]:
        for page in range(1, 4):  
            data = fetch_jobs(role, page=page)
            save_raw(data, role) 