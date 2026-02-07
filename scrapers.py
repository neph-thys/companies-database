import pandas as pd
from jobspy import scrape_jobs
import time
import random
import streamlit as st
from datetime import datetime

# --- CONFIGURATION ---
# The list of distinct roles to capture the whole market
SEARCH_ROLES = [
    "Software Engineer Intern", "Data Science Intern", 
    "Frontend Developer", "Backend Developer", 
    "Machine Learning Engineer", "Cybersecurity Analyst",
    "VLSI Design Engineer", "Embedded Systems Engineer",
    "DevOps Engineer", "Cloud Intern", "System Analyst"
]

# --- THE SAFE AUTO-PILOT ---
# ttl=21600 means "Run this only once every 6 hours"
@st.cache_data(ttl=21600, show_spinner=False)
def get_safe_master_list(location="India", jobs_per_role=25):
    """
    Scrapes multiple roles safely with delays.
    jobs_per_role=25 * 11 roles = ~275 jobs per cycle.
    """
    master_list = []
    seen_urls = set()
    
    # Progress Bar for the "Loading" state
    progress_text = "🔄 Placement OS: Auto-refreshing market data (Safe Mode)..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, role in enumerate(SEARCH_ROLES):
        try:
            # Update Progress
            pct = (i + 1) / len(SEARCH_ROLES)
            my_bar.progress(pct, text=f"Scanning Sector: {role}...")
            
            # CRITICAL SAFETY DELAY: Sleep 4-7 seconds between sectors
            time.sleep(random.uniform(4, 7))
            
            # Scrape
            jobs = scrape_jobs(
                site_name=["linkedin", "glassdoor"], # Indeed is strictest, removed for safety if 500+ needed
                search_term=role,
                location=location,
                results_wanted=jobs_per_role, 
                hours_old=72, # Fresh jobs only
                country_watchlist=["India"]
            )
            
            if not jobs.empty:
                for _, row in jobs.iterrows():
                    # Deduplicate: Don't add the same link twice
                    if row['job_url_direct'] not in seen_urls:
                        
                        # Normalize Salary (Clean up the text)
                        salary = "Not Disclosed"
                        if pd.notnull(row.get('min_amount')) and pd.notnull(row.get('max_amount')):
                            salary = f"{row['min_amount']} - {row['max_amount']}"
                        elif pd.notnull(row.get('min_amount')):
                            salary = str(row['min_amount'])

                        master_list.append({
                            "company": row['company'],
                            "title": row['title'],
                            "role_category": role,
                            "salary": salary,
                            "link": row['job_url_direct'],
                            "source": row['site'],
                            "date": row['date_posted'],
                            "type": "Job Posting"
                        })
                        seen_urls.add(row['job_url_direct'])
                        
        except Exception as e:
            print(f"Skipped {role}: {e}")
            continue

    my_bar.empty() # Clear progress bar
    return pd.DataFrame(master_list)

@st.cache_data(ttl=21600, show_spinner=False)
def get_contest_signals():
    """
    Fetches Codeforces contests as 'Hiring Signals'
    """
    import requests
    try:
        url = "https://codeforces.com/api/contest.list?gym=false"
        resp = requests.get(url, timeout=5).json()
        if resp['status'] != 'OK': return []
        
        signals = []
        hiring_keywords = ["cup", "challenge", "global", "championship", "hiring", "prize", "code", "round"]
        
        for c in resp['result']:
            if c['phase'] == 'BEFORE':
                name_lower = c['name'].lower()
                if any(k in name_lower for k in hiring_keywords):
                    signals.append({
                        "company": f"Codeforces Event: {c['name']}",
                        "title": "Competitive Programming Challenge",
                        "role_category": "Competitive Programming",
                        "salary": "Prize/Hiring",
                        "link": f"https://codeforces.com/contest/{c['id']}",
                        "source": "Codeforces",
                        "date": datetime.fromtimestamp(c['startTimeSeconds']).strftime('%Y-%m-%d'),
                        "type": "Contest"
                    })
        return pd.DataFrame(signals)
    except:
        return pd.DataFrame()
