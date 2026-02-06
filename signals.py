import pandas as pd

# --- 1. ROLE NORMALIZATION ENGINE ---
ROLE_MAP = {
    "software engineer intern": "SDE Intern",
    "sde intern": "SDE Intern",
    "developer intern": "SDE Intern",
    "graduate engineer trainee": "New Grad SDE",
    "associate software engineer": "New Grad SDE",
    "backend developer": "Backend Engineer",
    "frontend developer": "Frontend Engineer",
    "data analyst": "Data Analyst"
}

def normalize_role(raw_title):
    raw_lower = raw_title.lower()
    for key, standardized in ROLE_MAP.items():
        if key in raw_lower:
            return standardized
    return "Other Tech Role"


# --- 2. SALARY ESTIMATION ENGINE ---
# Tier A has NO upper bound
TIER_SALARY_MAP = {
    "Tier A": {
        "Intern": "₹60k+ / month",
        "New Grad": "₹12 LPA+"
    },
    "Tier B": {
        "Intern": "₹30k – ₹60k / month",
        "New Grad": "₹7 – ₹12 LPA"
    },
    "Tier C": {
        "Intern": "₹10k – ₹30k / month",
        "New Grad": "₹3.5 – ₹7 LPA"
    },
}

# Known company tiers (expandable)
TIER_A_COMPANIES = [
    "google", "microsoft", "amazon", "uber",
    "atlassian", "salesforce", "meta", "apple"
]

TIER_B_COMPANIES = [
    "flipkart", "swiggy", "zomato",
    "razorpay", "phonepe", "meesho",
    "browserstack"
]

def estimate_salary(company_name, role_type="Intern"):
    company_lower = company_name.lower()

    tier = "Tier C"  # Default fallback
    if any(c in company_lower for c in TIER_A_COMPANIES):
        tier = "Tier A"
    elif any(c in company_lower for c in TIER_B_COMPANIES):
        tier = "Tier B"

    salary = TIER_SALARY_MAP[tier].get(role_type, "Not Estimated")
    return salary, tier


# --- 3. HIRING CONFIDENCE ENGINE ---
def calculate_confidence(signals):
    """
    signals = {
        'unstop_drive': True/False,
        'job_postings': int,
        'contest_active': True/False
    }
    """
    score = 0
    reasons = []

    if signals.get('unstop_drive'):
        score += 50
        reasons.append("Active Unstop Drive (+50)")

    if signals.get('job_postings', 0) > 0:
        score += 30
        reasons.append("Recent Job Postings (+30)")

    if signals.get('contest_active'):
        score += 25
        reasons.append("Coding Contest Active (+25)")

    if score >= 70:
        status = "🟢 Actively Hiring"
    elif score >= 40:
        status = "🟡 Likely Hiring"
    else:
        status = "🔴 No Recent Signals"

    return score, status, ", ".join(reasons)
