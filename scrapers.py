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
