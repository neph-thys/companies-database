import streamlit as st
import pandas as pd
from signals import normalize_role, estimate_salary, calculate_confidence
from scrapers import get_jobs, get_codeforces_contests

st.set_page_config(page_title="Placement Intelligence", layout="wide")

# --- HEADER ---
st.title("🎓 Placement Intelligence Platform")
st.markdown("""
**System Status:** 🟢 Online | **Data Mode:** Signal-Based Aggregation
This tool tracks hiring signals from LinkedIn, Unstop, and Coding Platforms to calculate a **Hiring Confidence Score**.
""")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Intelligence Controls")
target_role = st.sidebar.text_input("Target Role", "SDE Intern")
target_loc = st.sidebar.text_input("Region", "India")

# --- MANUAL OVERRIDE (For Placement Cell) ---
st.sidebar.markdown("---")
st.sidebar.subheader("📥 Add Unstop/Drive Signal")
with st.sidebar.form("manual_signal"):
    m_company = st.text_input("Company Name")
    m_has_drive = st.checkbox("Has Active Drive/Hackathon?")
    m_link = st.text_input("Application Link")
    add_signal = st.form_submit_button("Inject Signal")
    
    if add_signal and m_company:
        if 'manual_signals' not in st.session_state:
            st.session_state['manual_signals'] = []
        st.session_state['manual_signals'].append({
            "company": m_company,
            "has_drive": m_has_drive,
            "link": m_link
        })
        st.success(f"Signal added for {m_company}")

# --- MAIN TABS ---
tab1, tab2 = st.tabs(["📊 Company Intelligence Board", "🏆 Contest Tracker"])

with tab1:
    st.subheader(f"Live Market Intelligence: {target_role}")
    
    if st.button("🔄 Scan Market Signals"):
        with st.spinner("Aggregating Signals (LinkedIn + Indeed + Manual Inputs)..."):
            
            # 1. Get Live Jobs
            df_jobs = get_jobs(target_role, target_loc)
            
            # 2. Process Signals & Build Master List
            intelligence_data = []
            
            # A. Process Scraped Jobs
            if not df_jobs.empty:
                for index, row in df_jobs.iterrows():
                    norm_role = normalize_role(row['title'])
                    salary_est, tier = estimate_salary(row['company'], "Intern" if "intern" in target_role.lower() else "New Grad")
                    
                    # Calculate Score
                    signals = {'job_postings': 1, 'unstop_drive': False, 'contest_active': False}
                    score, status, reason = calculate_confidence(signals)
                    
                    intelligence_data.append({
                        "Company": row['company'],
                        "Tier": tier,
                        "Role": norm_role,
                        "Est. Salary": salary_est,
                        "Confidence": status,
                        "Signal Source": "LinkedIn/Indeed Job",
                        "Action": row.get('job_url_direct', '#')
                    })
            
            # B. Process Manual Signals (Unstop)
            if 'manual_signals' in st.session_state:
                for item in st.session_state['manual_signals']:
                    salary_est, tier = estimate_salary(item['company'], "Intern")
                    signals = {'job_postings': 0, 'unstop_drive': True, 'contest_active': False}
                    score, status, reason = calculate_confidence(signals)
                    
                    intelligence_data.append({
                        "Company": item['company'],
                        "Tier": tier,
                        "Role": target_role,
                        "Est. Salary": salary_est,
                        "Confidence": status,
                        "Signal Source": "Placement Cell Input (Unstop)",
                        "Action": item['link']
                    })

            # Display Dashboard
            if intelligence_data:
                df_main = pd.DataFrame(intelligence_data)
                st.dataframe(
                    df_main,
                    column_config={
                        "Action": st.column_config.LinkColumn("Apply Link"),
                        "Confidence": st.column_config.TextColumn("Hiring Status")
                    },
                    use_container_width=True
                )
            else:
                st.warning("No active signals found. Try adding a Manual Signal in the sidebar.")

with tab2:
    st.subheader("Upcoming Coding Contests (Signal: Skill Hiring)")
    if st.button("Fetch Contests"):
        data = get_codeforces_contests()
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No contests found.")
