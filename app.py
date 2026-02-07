import streamlit as st
import pandas as pd
from datetime import datetime
from scrapers import get_safe_master_list, get_contest_signals

st.set_page_config(page_title="Placement OS", layout="wide", initial_sidebar_state="expanded")

# --- 1. LOGIC ENGINES ---

def get_hiring_confidence(company_df):
    """
    Calculates a score (0-100) based on signals.
    """
    score = 0
    reasons = []
    
    # Factor 1: Volume of Signals (More jobs = Higher confidence)
    job_count = len(company_df[company_df['type'] == 'Job Posting'])
    if job_count > 0:
        score += 20 + (job_count * 10) # Base 20 + 10 per job
        reasons.append(f"• {job_count} Active Job Posts detected")
        
    # Factor 2: Manual/Verified Drive
    if any(company_df['type'] == 'Manual Entry'):
        score += 50
        reasons.append("• Verified Campus Drive (Admin Entry)")
        
    # Factor 3: Contests
    if any(company_df['type'] == 'Contest'):
        score += 30
        reasons.append("• Hosting Hiring Contest")
        
    # Factor 4: Seasonality (India Specific)
    current_month = datetime.now().month
    # Peak: Jan-Mar (1-3) and Jul-Sep (7-9)
    if (1 <= current_month <= 3) or (7 <= current_month <= 9):
        score += 10
        reasons.append("• Currently Peak Hiring Season")
        
    # Cap score at 100
    score = min(score, 100)
    
    # Determine Label
    if score >= 75: label = "🟢 High (Active)"
    elif score >= 40: label = "🟡 Medium (Possible)"
    else: label = "🔴 Low (Passive)"
    
    return label, score, reasons

def determine_tier(company_name):
    c_lower = str(company_name).lower()
    tier_a = ['google', 'microsoft', 'amazon', 'uber', 'atlassian', 'linkedin', 'salesforce', 'adobe', 'goldman', 'apple', 'deshaw', 'arcesium']
    tier_b = ['swiggy', 'zomato', 'cred', 'razorpay', 'flipkart', 'meesho', 'phonepe', 'paytm', 'oracle', 'cisco', 'samsung']
    
    if any(t in c_lower for t in tier_a): return "Tier 1 (Big Tech)"
    if any(t in c_lower for t in tier_b): return "Tier 2 (Product/Unicorn)"
    return "Tier 3 / Startup"

# --- 2. DATA LOADING ---

if 'manual_entries' not in st.session_state:
    st.session_state['manual_entries'] = []
    
# Auto-Load Data (Runs once every 6 hours)
with st.spinner("Syncing Placement Database..."):
    df_jobs = get_safe_master_list(location="India", jobs_per_role=25) 
    df_contests = get_contest_signals()
    
    # Merge Scraped Data
    frames = [df_jobs, df_contests]
    if st.session_state['manual_entries']:
        frames.append(pd.DataFrame(st.session_state['manual_entries']))
        
    master_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    
    if not master_df.empty:
        master_df['Tier'] = master_df['company'].apply(determine_tier)

# --- 3. NAVIGATION STATE ---
if 'view_company' not in st.session_state:
    st.session_state['view_company'] = None

def open_company_details(company_name):
    st.session_state['view_company'] = company_name

def close_details():
    st.session_state['view_company'] = None

# --- 4. SIDEBAR ---
st.sidebar.title("Placement OS 2.0")

# Filters (Only show on Master List)
if st.session_state['view_company'] is None:
    st.sidebar.header("🔍 Filter Database")
    
    if not master_df.empty:
        # Role Filter
        all_roles = list(master_df['role_category'].unique())
        sel_roles = st.sidebar.multiselect("Tech Roles", all_roles)
        
        # Tier Filter
        sel_tier = st.sidebar.multiselect("Company Tier", ["Tier 1 (Big Tech)", "Tier 2 (Product/Unicorn)", "Tier 3 / Startup"])
        
        # Confidence Filter
        sel_conf = st.sidebar.multiselect("Hiring Confidence", ["🟢 High (Active)", "🟡 Medium (Possible)", "🔴 Low (Passive)"])

# Admin Panel
with st.sidebar.expander("Admin: Add Manual Drive"):
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
                "Tier": determine_tier(m_comp)
            })
            st.rerun()

# --- 5. MAIN PAGE ---

if st.session_state['view_company']:
    # === DETAIL PAGE ===
    c_name = st.session_state['view_company']
    c_data = master_df[master_df['company'] == c_name]
    
    # Recalculate Confidence for this specific company
    conf_label, conf_score, conf_reasons = get_hiring_confidence(c_data)
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.button("← Back", on_click=close_details)
    with col2:
        st.title(f"{c_name}")
    
    # Metrics Row
    m1, m2, m3 = st.columns(3)
    m1.metric("Confidence Score", f"{conf_score}/100", conf_label)
    m2.metric("Tier", c_data.iloc[0]['Tier'])
    m3.metric("Open Roles", len(c_data))
    
    st.divider()
    
    # Detailed Analysis
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("📊 Why this score?")
        st.progress(conf_score / 100)
        for r in conf_reasons:
            st.write(r)
            
    with c2:
        st.subheader("📋 Available Roles")
        st.dataframe(
            c_data[['title', 'salary', 'source', 'link']],
            column_config={
                "link": st.column_config.LinkColumn("Apply Link"),
                "salary": "Salary",
                "source": "Source"
            },
            hide_index=True,
            use_container_width=True
        )

else:
    # === MASTER LIST PAGE ===
    st.subheader(f"🏢 Master Company Database ({len(master_df)} opportunities)")
    
    if master_df.empty:
        st.info("System initializing... First scrape takes about 60 seconds.")
    else:
        # APPLY FILTERS
        filtered_df = master_df.copy()
        
        if sel_roles:
            filtered_df = filtered_df[filtered_df['role_category'].isin(sel_roles)]
        if sel_tier:
            filtered_df = filtered_df[filtered_df['Tier'].isin(sel_tier)]
            
        # PREPARE AGGREGATED TABLE
        company_stats = []
        for comp in filtered_df['company'].unique():
            comp_rows = filtered_df[filtered_df['company'] == comp]
            label, score, _ = get_hiring_confidence(comp_rows)
            
            if sel_conf and label not in sel_conf:
                continue
                
            company_stats.append({
                "Company": comp,
                "Tier": comp_rows.iloc[0]['Tier'],
                "Confidence": label,
                "Score": score, # For sorting
                "Roles": len(comp_rows),
                "Latest Role": comp_rows.iloc[0]['title']
            })
            
        # DISPLAY LOGIC
        if company_stats:
            # Sort by Confidence Score (High -> Low) by default
            stats_df = pd.DataFrame(company_stats).sort_values(by="Score", ascending=False)
            
            # Interactive Data Editor (Like a Spreadsheet)
            # We use this instead of expnders for a cleaner "List View"
            st.write("Click on any header to sort.")
            
            # Custom layout for cards
            for _, row in stats_df.iterrows():
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                    c1.markdown(f"**{row['Company']}**")
                    c1.caption(row['Tier'])
                    
                    c2.caption("Confidence")
                    c2.write(row['Confidence'])
                    
                    c3.caption("Openings")
                    c3.write(f"{row['Roles']} Roles")
                    
                    # The "View" Button
                    if c4.button("View ->", key=f"btn_{row['Company']}"):
                        open_company_details(row['Company'])
                        st.rerun()
                    st.divider()
        else:
            st.warning("No companies match your filters.")
