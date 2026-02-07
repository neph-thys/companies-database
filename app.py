import streamlit as st
import pandas as pd
from datetime import datetime
from scrapers import get_safe_master_list, get_contest_signals

st.set_page_config(page_title="Placement OS", layout="wide", initial_sidebar_state="expanded")

# --- 1. SESSION STATE INITIALIZATION (FIX IS HERE) ---
# We must create these variables before using them
if 'manual_entries' not in st.session_state:
    st.session_state['manual_entries'] = []
if 'view_company' not in st.session_state:
    st.session_state['view_company'] = None

# --- 2. ADMIN SIDEBAR ---
with st.sidebar:
    st.title("Placement OS 2.0")
    
    # Force Reset Button
    if st.button("🔴 Force Reset / Clear Cache"):
        st.cache_data.clear()
        st.rerun()

    # Manual Entry Form
    with st.expander("Admin: Add Manual Drive"):
        with st.form("manual"):
            m_comp = st.text_input("Company")
            m_role = st.text_input("Role")
            m_link = st.text_input("Link")
            m_sal = st.text_input("Salary (e.g. 12 LPA)")
            if st.form_submit_button("Add"):
                st.session_state['manual_entries'].append({
                    "company": m_comp, "title": m_role, "role_category": "Manual Entry",
                    "salary": m_sal, "link": m_link, "source": "Placement Cell",
                    "date": datetime.now().strftime("%Y-%m-%d"), "type": "Manual Entry", 
                    "Tier": "Verified"
                })
                st.success("Added!")
                st.rerun()

# --- 3. LOGIC ENGINES ---
def get_hiring_confidence(company_df):
    score = 0
    reasons = []
    
    job_count = len(company_df[company_df['type'] == 'Job Posting'])
    if job_count > 0:
        score += 20 + (job_count * 10)
        reasons.append(f"• {job_count} Active Job Posts")
        
    if any(company_df['type'] == 'Manual Entry'):
        score = 100
        reasons.append("• Verified Campus Drive")
        
    if any(company_df['type'] == 'Contest'):
        score += 30
        reasons.append("• Hosting Hiring Contest")

    score = min(score, 100)
    
    if score >= 75: label = "🟢 High"
    elif score >= 40: label = "🟡 Medium"
    else: label = "🔴 Low"
    
    return label, score, reasons

def determine_tier(company_name):
    c_lower = str(company_name).lower()
    if any(t in c_lower for t in ['google', 'microsoft', 'amazon', 'uber', 'atlassian']): return "Tier 1"
    if any(t in c_lower for t in ['swiggy', 'zomato', 'cred', 'flipkart']): return "Tier 2"
    return "Tier 3"

# --- 4. DATA LOADING ---
with st.spinner("Syncing Placement Database..."):
    # Load Scraped Data
    df_jobs = get_safe_master_list(location="India", jobs_per_role=15) 
    df_contests = get_contest_signals()
    
    # Merge Scraped Data + Manual Entries
    frames = []
    if not df_jobs.empty: frames.append(df_jobs)
    if not df_contests.empty: frames.append(df_contests)
    
    # NOW this is safe because we initialized it at the top
    if st.session_state['manual_entries']:
        frames.append(pd.DataFrame(st.session_state['manual_entries']))
        
    master_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    
    if not master_df.empty:
        if 'Tier' not in master_df.columns:
            master_df['Tier'] = master_df['company'].apply(determine_tier)

# --- 5. MAIN UI ---

if st.session_state['view_company']:
    # === DETAIL VIEW ===
    c_name = st.session_state['view_company']
    if not master_df.empty:
        c_data = master_df[master_df['company'] == c_name]
        
        conf_label, conf_score, conf_reasons = get_hiring_confidence(c_data)
        
        st.button("← Back to Master List", on_click=lambda: st.session_state.update(view_company=None))
        st.title(f"{c_name}")
        st.metric("Confidence Score", f"{conf_score}/100", conf_label)
        
        st.subheader("Available Roles")
        st.dataframe(c_data[['title', 'salary', 'source', 'link']], 
                     column_config={"link": st.column_config.LinkColumn("Apply")}, 
                     hide_index=True, use_container_width=True)
    else:
        st.error("Data missing. Please reset.")
        st.button("Back", on_click=lambda: st.session_state.update(view_company=None))

else:
    # === MASTER LIST VIEW ===
    st.subheader(f"🏢 Master Database")
    
    if master_df.empty:
        st.warning("No data found. Click 'Force Reset' in sidebar to restart scraper.")
    else:
        # AGGREGATE STATS
        company_stats = []
        for comp in master_df['company'].unique():
            comp_rows = master_df[master_df['company'] == comp]
            label, score, _ = get_hiring_confidence(comp_rows)
            
            company_stats.append({
                "Company": comp,
                "Tier": comp_rows.iloc[0]['Tier'],
                "Confidence": label,
                "Score": score,
                "Roles": len(comp_rows)
            })
            
        stats_df = pd.DataFrame(company_stats).sort_values(by="Score", ascending=False)
        
        st.write("Click 'View' to see roles.")
        
        for _, row in stats_df.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                c1.markdown(f"**{row['Company']}**")
                c1.caption(row['Tier'])
                c2.write(row['Confidence'])
                c3.write(f"{row['Roles']} Roles")
                if c4.button("View ->", key=f"btn_{row['Company']}"):
                    st.session_state['view_company'] = row['Company']
                    st.rerun()
                st.divider()
