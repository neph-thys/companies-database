import streamlit as st
import pandas as pd
from datetime import datetime
from scrapers import get_safe_master_list, get_contest_signals

st.set_page_config(page_title="Placement OS", layout="wide")

if 'manual_entries' not in st.session_state:
    st.session_state['manual_entries'] = []
    
# --- 0. HARD RESET BUTTON (To fix your cache issue) ---
with st.sidebar:
    st.header("⚙️ Admin Controls")
    if st.button("🔴 Force Reset / Clear Cache"):
        st.cache_data.clear()
        st.rerun()

# --- 1. LOGIC ENGINES ---
def get_hiring_confidence(company_df):
    score = 0
    reasons = []
    
    # Simple Logic: More Jobs = Higher Score
    job_count = len(company_df[company_df['type'] == 'Job Posting'])
    if job_count > 0:
        score += 20 + (job_count * 10)
        reasons.append(f"• {job_count} Active Job Posts")
        
    if any(company_df['type'] == 'Manual Entry'):
        score = 100
        reasons.append("• Verified Drive")

    # Seasonality
    current_month = datetime.now().month
    if (1 <= current_month <= 3) or (7 <= current_month <= 9):
        score += 10
        reasons.append("• Peak Season")

    score = min(score, 100)
    
    if score >= 75: label = "🟢 High"
    elif score >= 40: label = "🟡 Medium"
    else: label = "🔴 Low"
    
    return label, score, reasons

def determine_tier(company_name):
    c_lower = str(company_name).lower()
    if any(t in c_lower for t in ['google', 'microsoft', 'amazon', 'uber', 'atlassian', 'linkedin', 'adobe']): return "Tier 1"
    if any(t in c_lower for t in ['swiggy', 'zomato', 'cred', 'flipkart', 'phonepe', 'paytm']): return "Tier 2"
    return "Tier 3"

# --- 2. DATA LOADING ---
if 'manual_entries' not in st.session_state:
    st.session_state['manual_entries'] = []

# Fetch Data
df_jobs = get_safe_master_list(location="India", jobs_per_role=20) 
df_contests = get_contest_signals()

# Merge
frames = [df_jobs]
if not df_contests.empty:
    frames.append(df_contests)
if st.session_state['manual_entries']:
    frames.append(pd.DataFrame(st.session_state['manual_entries']))

master_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

if not master_df.empty:
    master_df['Tier'] = master_df['company'].apply(determine_tier)

# --- 3. UI LAYOUT ---

st.title("🎓 Placement OS")

if master_df.empty:
    st.warning("No data found. Please click 'Force Reset' in the sidebar to restart the scraper.")
    st.stop()

# --- 4. SEPARATE SORT & FILTER ---

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("🔍 Filters")
    # A. FILTERS
    # 1. Hide Contests Toggle
    show_contests = st.checkbox("Show Contests?", value=False)
    
    # 2. Role Filter
    all_roles = list(master_df['role_category'].unique())
    sel_roles = st.multiselect("Tech Roles", all_roles)
    
    # 3. Tier Filter
    sel_tier = st.multiselect("Tier", ["Tier 1", "Tier 2", "Tier 3"])

with col2:
    st.subheader("⚡ Sort By")
    # B. SORTING
    sort_option = st.radio("Arrange Companies By:", 
             ["Hiring Confidence (High -> Low)", "Company Name (A-Z)", "Job Count (Most -> Least)"], 
             horizontal=True)

# --- 5. APPLY LOGIC ---

# 1. Filter out Codeforces Events if checkbox is OFF
filtered_df = master_df.copy()
if not show_contests:
    filtered_df = filtered_df[filtered_df['source'] != 'Codeforces']

# 2. Apply Sidebar Filters
if sel_roles:
    filtered_df = filtered_df[filtered_df['role_category'].isin(sel_roles)]
if sel_tier:
    filtered_df = filtered_df[filtered_df['Tier'].isin(sel_tier)]

# 3. Prepare Stats for Sorting
company_stats = []
unique_companies = filtered_df['company'].unique()

for comp in unique_companies:
    comp_rows = filtered_df[filtered_df['company'] == comp]
    label, score, _ = get_hiring_confidence(comp_rows)
    
    company_stats.append({
        "Company": comp,
        "Tier": comp_rows.iloc[0]['Tier'],
        "Confidence": label,
        "Score": score,
        "Job Count": len(comp_rows),
        "Roles": comp_rows[['title', 'salary', 'link', 'source']]
    })

stats_df = pd.DataFrame(company_stats)

if stats_df.empty:
    st.info("No companies match your filters.")
    st.stop()

# 4. Apply Sorting
if "Confidence" in sort_option:
    stats_df = stats_df.sort_values(by="Score", ascending=False)
elif "Job Count" in sort_option:
    stats_df = stats_df.sort_values(by="Job Count", ascending=False)
else:
    stats_df = stats_df.sort_values(by="Company", ascending=True)

# --- 6. DISPLAY CARDS ---
st.divider()
st.write(f"Showing **{len(stats_df)}** Companies")

for _, row in stats_df.iterrows():
    with st.expander(f"{row['Company']} ({row['Job Count']} Roles) - {row['Confidence']} Confidence"):
        
        c1, c2 = st.columns([1, 3])
        c1.caption("Tier")
        c1.write(row['Tier'])
        
        c2.caption("Available Roles")
        st.dataframe(
            row['Roles'],
            column_config={
                "link": st.column_config.LinkColumn("Apply"),
                "salary": "Salary"
            },
            hide_index=True,
            width="stretch"
        )
