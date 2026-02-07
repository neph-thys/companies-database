import pandas as pd
from jobspy import scrape_jobs
import time
import random

# --- CONFIGURATION ---
# We split searches to look like human behavior
SEARCH_ROLES = [
    "Software Engineer Intern", "Data Science Intern", 
    "Frontend Developer", "Backend Developer", 
    "Machine Learning Engineer", "Cybersecurity Analyst",
    "VLSI Design Engineer", "Embedded Systems",
    "Java Developer", "Python Developer"
]

def get_bulk_jobs(location="India", limit_per_role=15):
    """
    Fetches a large volume of jobs by iterating through roles with delays.
    """
    master_list = []
    
    print("--- STARTING BULK SCRAPE ---")
    
    for role in SEARCH_ROLES:
        try:
            # Random delay between 2-5 seconds to avoid IP bans (Gentle Scraping)
            sleep_time = random.uniform(2, 5)
            time.sleep(sleep_time)
            
            print(f"Scraping {role}...")
            
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "glassdoor"],
                search_term=role,
                location=location,
                results_wanted=limit_per_role, 
                hours_old=72, # Only fresh jobs (3 days)
                country_watchlist=["India"]
            )
            
            if not jobs.empty:
                # Add a 'Source Type' column to distinguish from contests
                jobs['Signal Type'] = 'Job Posting'
                jobs['Role Category'] = role
                master_list.append(jobs)
                
        except Exception as e:
            print(f"Error scraping {role}: {e}")
            continue

    if not master_list:
        return pd.DataFrame()
    
    # Combine everything
    df = pd.concat(master_list, ignore_index=True)
    
    # Standardize Columns
    # We ensure these columns exist even if some sources didn't return them
    expected_cols = ['company', 'title', 'job_url_direct', 'site', 'date_posted', 'min_amount', 'Signal Type']
    for c in expected_cols:
        if c not in df.columns:
            df[c] = None
            
    return df[expected_cols]

def get_contest_signals():
    """
    Fetches contests but formats them exactly like a Job Posting
    so they can be merged into the main list.
    """
    import requests
    from datetime import datetime
    
    url = "https://codeforces.com/api/contest.list?gym=false"
    try:
        resp = requests.get(url, timeout=10).json()
        if resp['status'] != 'OK':
            return []
            
        contests = resp['result']
        signals = []
        
        # Keywords indicating it's a HIRING contest, not just fun
        hiring_keywords = ["cup", "challenge", "global", "championship", "hiring", "prize", "code", "round"]
        
        for c in contests:
            if c['phase'] == 'BEFORE':
                name_lower = c['name'].lower()
                
                # Check if it looks like a hiring event
                if any(k in name_lower for k in hiring_keywords):
                    # We create a "Fake Job" row for this contest
                    # So it fits into our main table perfectly
                    signals.append({
                        "company": f"Codeforces Event: {c['name']}",
                        "title": "Competitive Programming Challenge",
                        "job_url_direct": f"https://codeforces.com/contest/{c['id']}",
                        "site": "Codeforces",
                        "date_posted": datetime.fromtimestamp(c['startTimeSeconds']).strftime('%Y-%m-%d'),
                        "min_amount": "Prize/Hiring",
                        "Signal Type": "Contest/Challenge"
                    })
        
        return pd.DataFrame(signals)
    except:
        return pd.DataFrame()
