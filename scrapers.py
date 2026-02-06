import pandas as pd
import requests
from jobspy import scrape_jobs
from datetime import datetime

# --- CODEFORCES SCRAPER ---
def get_codeforces_contests():
    url = "https://codeforces.com/api/contest.list?gym=false"
    try:
        resp = requests.get(url, timeout=10).json()
        if resp['status'] != 'OK':
            return []
            
        contests = resp['result']
        upcoming = []
        for c in contests:
            if c['phase'] == 'BEFORE':
                start_time = datetime.fromtimestamp(c['startTimeSeconds']).strftime('%Y-%m-%d %H:%M')
                upcoming.append({
                    "Platform": "Codeforces",
                    "Event": c['name'],
                    "Start": start_time,
                    "Link": "https://codeforces.com/contests"
                })
        return upcoming
    except:
        return []

# --- JOBSPY (LinkedIn/Indeed) SCRAPER ---
def get_jobs(role_search="Software Engineer Intern", location_search="India"):
    try:
        jobs = scrape_jobs(
            site_name=["linkedin", "indeed", "glassdoor"],
            search_term=role_search,
            location=location_search,
            results_wanted=10, 
            hours_old=72, 
            country_watchlist=["India"]
        )
        if jobs.empty:
            return pd.DataFrame()
            
        # Clean columns
        cols = ['company', 'title', 'job_url_direct', 'site', 'date_posted']
        available = [c for c in cols if c in jobs.columns]
        return jobs[available]
    except Exception as e:
        print(f"Scrape Error: {e}")
        return pd.DataFrame()
