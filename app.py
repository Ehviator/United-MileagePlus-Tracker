import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Updated 2025/2026 United MileagePlus Thresholds
TIERS = {
    "Member": {"pqp_only": 0, "pqp_pqf": 0, "pqf": 0},
    "Silver": {"pqp_only": 6000, "pqp_pqf": 5000, "pqf": 15},
    "Gold": {"pqp_only": 12000, "pqp_pqf": 10000, "pqf": 30},
    "Platinum": {"pqp_only": 18000, "pqp_pqf": 15000, "pqf": 45},
    "1K": {"pqp_only": 28000, "pqp_pqf": 22000, "pqf": 60}
}

DATA_FILE = "mileageplus_ledger.csv"

# Load or Create Ledger
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["Date", "Activity Type", "Description", "Award Miles", "PQP", "PQF", "United Flight Count"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Logic to calculate current Premier Status
def get_current_status(pqp, pqf, united_flights):
    if united_flights < 4:
        return "Member (Needs 4 UA flights)"
    
    if pqp >= TIERS["1K"]["pqp_only"] or (pqp >= TIERS["1K"]["pqp_pqf"] and pqf >= TIERS["1K"]["pqf"]): return "1K"
    if pqp >= TIERS["Platinum"]["pqp_only"] or (pqp >= TIERS["Platinum"]["pqp_pqf"] and pqf >= TIERS["Platinum"]["pqf"]): return "Platinum"
    if pqp >= TIERS["Gold"]["pqp_only"] or (pqp >= TIERS["Gold"]["pqp_pqf"] and pqf >= TIERS["Gold"]["pqf"]): return "Gold"
    if pqp >= TIERS["Silver"]["pqp_only"] or (pqp >= TIERS["Silver"]["pqp_pqf"] and pqf >= TIERS["Silver"]["pqf"]): return "Silver"
    return "Member"

# UI Setup
st.set_page_config(page_title="MileagePlus Tracker", page_icon="✈️", layout="wide")
st.title("✈️ United MileagePlus Tracker")

df = load_data()

# Account Totals
total_miles = int(df["Award Miles"].sum())
total_pqp = int(df["PQP"].sum())
total_pqf = int(df["PQF"].sum())
total_ua_flights = int(df["United Flight Count"].sum())

current_status = get_current_status(total_pqp, total_pqf, total_ua_flights)

# Dashboard Metrics
st.header(f"🏆 Current Status: {current_status}")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Award Miles Balance", f"{total_miles:,}")
col2.metric("Total PQP", f"{total_pqp:,}")
col3.metric("Total PQF", f"{total_pqf}")
col4.metric("United Flights (Min 4)", f"{total_ua_flights}")

st.divider()

# Status Progress Tracker
st.subheader("📊 Premier Status Progress")

def draw_progress(tier_name, req_pqp_only, req_pqp_pqf, req_pqf):
    st.markdown(f"**{tier_name} Requirements:** {req_pqp_pqf:,} PQP + {req_pqf} PQF &nbsp; *OR* &nbsp; {req_pqp_only:,} PQP")
    
    pqp_pct = min(total_pqp / req_pqp_pqf, 1.0) if req_pqp_pqf else 1.0
    pqf_pct = min(total_pqf / req_pqf, 1.0) if req_pqf else 1.0
    pqp_only_pct = min(total_pqp / req_pqp_only, 1.0) if req_pqp_only else 1.0
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption(f"PQP (Combo): {int(pqp_pct*100)}%")
        st.progress(pqp_pct)
    with c2:
        st.caption(f"PQF (Combo): {int(pqf_pct*100)}%")
        st.progress(pqf_pct)
    with c3:
        st.caption(f"PQP (Only): {int(pqp_only_pct*100)}%")
        st.progress(pqp_only_pct)
    st.write("---")

# Draw Progress for Tiers
for tier in ["Silver", "Gold", "Platinum", "1K"]:
    draw_progress(tier, TIERS[tier]["pqp_only"], TIERS[tier]["pqp_pqf"], TIERS[tier]["pqf"])

st.divider()

# Data Entry Form
st.subheader("➕ Log New Activity")
with st.form("add_activity", clear_on_submit=True):
    a_date = st.date_input("Date", datetime.today())
    a_type = st.selectbox("Activity Type", ["Flight", "Chase Credit Card Spend", "Starter PQP", "Other Bonus/Promo"])
    a_desc = st.text_input("Description (e.g., SFO to EWR, Chase Monthly PQP)")
    
    colA, colB, colC = st.columns(3)
    with colA:
        a_miles = st.number_input("Award Miles Earned", value=0)
    with colB:
        a_pqp = st.number_input("PQP Earned", value=0)
    with colC:
        a_pqf = st.number_input("PQF Earned", value=0)
        
    is_ua_flight = st.checkbox("Is this a United/United Express operated flight? (Required for the 4 flight minimum)")
    
    submitted = st.form_submit_button("Add Activity to Ledger")
    
    if submitted:
        ua_count = 1 if (is_ua_flight and a_type == "Flight") else 0
        new_row = {
            "Date": a_date.strftime("%Y-%m-%d"),
            "Activity Type": a_type,
            "Description": a_desc,
            "Award Miles": a_miles,
            "PQP": a_pqp,
            "PQF": a_pqf,
            "United Flight Count": ua_count
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("Activity Added Successfully!")
        st.rerun()

# Data Table Display
st.subheader("📋 Account Ledger")
if not df.empty:
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.info("No activities logged yet. Add a flight above to get started!")