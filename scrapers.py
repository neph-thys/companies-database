import pandas as pd
from jobspy import scrape_jobs
import time
import random
import streamlit as st
import requests
from datetime import datetime

# --- SEARCH CONFIG ---
SEARCH_ROLES = [
    "Software Engineer Intern",
    "Data Science Intern",
    "Frontend Developer",
    "Backend Developer",
    "Machine Learning Engineer"
]

@st.cache_data(ttl=3600, show_spinner=False)
def get_safe_master_list(location="India", jobs_per_role=15):
    """
    ULTRA-SAFE MODE:
    - Fetches only 15 jobs per role.
    - Removed 'glassdoor' to prevent 403 errors and speed up execution.
    """
    master_list = []
    seen_urls = set()
    
    # Progress Bar (So you know it's working)
    progress_text = "🔄 Safe-Scraper: Fetching fresh jobs..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, role in enumerate(SEARCH_ROLES):
        try:
            # Update Progress Bar
            pct = (i + 1) / len(SEARCH_ROLES)
            my_bar.progress(pct, text=f"Scraping Sector: {role}...")
            
            # SAFETY DELAY: Sleep 3-5 seconds between sectors
            time.sleep(random.uniform(3, 5))
            
            # The Scrape Request
            # FIXED: Removed "glassdoor" to stop the 403 errors
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed"], 
                search_term=role,
                location=location,
                results_wanted=jobs_per_role, 
                hours_old=72, # Last 3 days only
                country_watchlist=["India"]
            )
            
            if not jobs.empty:
                for _, row in jobs.iterrows():
                    # Deduplication: Don't add the same link twice
                    if row['job_url_direct'] not in seen_urls:
                        
                        # Clean Salary Formatting
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
            # If one role fails (e.g. LinkedIn blocks us), just skip to the next one
            print(f"Skipped {role}: {e}")
            continue

    my_bar.empty() # Remove progress bar when done
    return pd.DataFrame(master_list)

@st.cache_data(ttl=3600, show_spinner=False)
def get_contest_signals():
    """
    Fetches Codeforces contests (Very safe, official API)
    """
    try:
        url = "https://codeforces.com/api/contest.list?gym=false"
        resp = requests.get(url, timeout=5).json()
        if resp['status'] != 'OK': return pd.DataFrame()
        
        signals = []
        hiring_keywords = ["cup", "challenge", "global", "championship", "hiring", "prize"]
        
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
