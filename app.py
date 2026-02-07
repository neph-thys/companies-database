import streamlit as st
import pandas as pd
from scrapers import get_bulk_jobs, get_contest_signals

st.set_page_config(page_title="Placement Committee DB", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if 'master_data' not in st.session_state:
    st.session_state['master_data'] = pd.DataFrame()
if 'manual_data' not in st.session_state:
    st.session_state['manual_data'] = []

st.title("🎓 Placement Committee: Master Hiring Database")
st.markdown("Internal tool for tracking **Jobs**, **Drives**, and **Contests** in one place.")

# --- SIDEBAR: CONTROLS ---
st.sidebar.header("Data Controls")

# 1. DATA REFRESH BUTTON
if st.sidebar.button("🚀 Refresh Master Database"):
    status = st.empty()
    status.info("Step 1/3: Scraping Job Boards (This takes ~40s)...")
    
    # A. Get Jobs
    df_jobs = get_bulk_jobs(limit_per_role=15) # 15 * 8 roles = ~120 jobs
    
    status.info("Step 2/3: Checking Contests...")
    # B. Get Contests
    df_contests = get_contest_signals()
    
    # C. Merge
    status.info("Step 3/3: Merging & Grouping...")
    
    if not df_jobs.empty and not df_contests.empty:
        full_df = pd.concat([df_jobs, df_contests], ignore_index=True)
    elif not df_jobs.empty:
        full_df = df_jobs
    elif not df_contests.empty:
        full_df = df_contests
    else:
        full_df = pd.DataFrame()

    st.session_state['master_data'] = full_df
    
    status.success("Database Updated!")

# 2. MANUAL ENTRY (ADD/REMOVE)
st.sidebar.markdown("---")
st.sidebar.subheader("✍️ Manual Entry (WhatsApp/Email)")

with st.sidebar.form("add_entry"):
    m_company = st.text_input("Company Name")
    m_role = st.text_input("Role / Event Name")
    m_link = st.text_input("Link")
    m_source = st.selectbox("Source", ["Unstop", "Email", "Alumni", "LinkedIn DM"])
    submitted = st.form_submit_button("Add to Database")
    
    if submitted and m_company:
        new_entry = {
            "company": m_company,
            "title": m_role,
            "job_url_direct": m_link,
            "site": m_source,
            "date_posted": "Manual Entry",
            "min_amount": "N/A",
            "Signal Type": "Manual/Drive"
        }
        st.session_state['manual_data'].append(new_entry)
        st.success("Entry Added")

# REMOVE ENTRY OPTION
if st.session_state['manual_data']:
    st.sidebar.markdown("### Remove Entries")
    # Create a list of names to select for deletion
    options = [f"{i}: {d['company']} - {d['title']}" for i, d in enumerate(st.session_state['manual_data'])]
    selected_to_delete = st.sidebar.selectbox("Select to Delete", options)
    if st.sidebar.button("🗑️ Delete Selected"):
        index = int(selected_to_delete.split(":")[0])
        st.session_state['manual_data'].pop(index)
        st.rerun()

# --- MAIN DASHBOARD ---

# 1. MERGE MANUAL DATA WITH SCRAPED DATA
final_df = st.session_state['master_data'].copy()
if st.session_state['manual_data']:
    manual_df = pd.DataFrame(st.session_state['manual_data'])
    # Ensure manual_df has same columns or just concat
    final_df = pd.concat([manual_df, final_df], ignore_index=True)

# 2. DISPLAY LOGIC (GROUPING)
if not final_df.empty:
    # FILTERS
    col1, col2 = st.columns(2)
    search_query = col1.text_input("🔍 Search Company", "")
    type_filter = col2.multiselect("Filter Source", ["Job Posting", "Contest/Challenge", "Manual/Drive"], default=["Job Posting", "Manual/Drive"])
    
    # Apply Filters
    if search_query:
        final_df = final_df[final_df['company'].astype(str).str.contains(search_query, case=False, na=False)]
    if type_filter:
        final_df = final_df[final_df['Signal Type'].isin(type_filter)]

    # GROUPING LOGIC
    # We group by Company Name
    if 'company' in final_df.columns:
        grouped = final_df.groupby('company')
        
        st.write(f"Showing **{len(grouped)}** distinct companies offering **{len(final_df)}** opportunities.")
        
        for company, group in grouped:
            # Determine Card Color based on signal
            is_manual = any(group['Signal Type'] == 'Manual/Drive')
            is_contest = any(group['Signal Type'] == 'Contest/Challenge')
            
            emoji = "🏢"
            if is_manual: emoji = "🚨" # Urgent/Verified
            if is_contest: emoji = "🏆"
            
            with st.expander(f"{emoji} {company} ({len(group)} Opportunities)"):
                # Show all roles for this company in a clean table
                st.dataframe(
                    group[['title', 'Signal Type', 'min_amount', 'site', 'job_url_direct']],
                    column_config={
                        "job_url_direct": st.column_config.LinkColumn("Link"),
                        "min_amount": "Salary/Prize"
                    },
                    hide_index=True,
                    use_container_width=True
                )
    else:
         st.error("Data Error: 'company' column missing.")

else:
    st.info("Database is empty. Click 'Refresh Master Database' in the sidebar to start collecting data.")
