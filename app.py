import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM APC BRANDING
# ---------------------------------------------------------
st.set_page_config(
    page_title="PBAT–KOH 2027 Ward Campaign Leaderboard",
    page_icon="🗳️",
    layout="wide",
)

# Custom CSS for APC Campaign Theme & Styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    
    .campaign-header {
        background: linear-gradient(135deg, #008751 0%, #005a36 60%, #00A3E0 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        border-bottom: 5px solid #FFD700;
    }
    
    .campaign-header h1 {
        color: #FFFFFF !important;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .campaign-header h3 {
        color: #FFD700 !important;
        font-weight: 600;
        font-size: 1.2rem;
        margin-top: 0;
    }

    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 5px solid #008751;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2. HEADER BANNER
# ---------------------------------------------------------
st.markdown(
    """
    <div class="campaign-header">
        <h3>ALL PROGRESSIVES CONGRESS (APC)</h3>
        <h1>PBAT–KOH 2027 CAMPAIGN COUNCIL</h1>
        <p style="font-size: 1.1rem; opacity: 0.95; margin-bottom: 0;">
            <b>Contact & Mobilization Directorate</b> | Ward Coordinators Strategy Leaderboard
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 3. DATA LOADING
# ---------------------------------------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRo-g0a6T4pxPa1CnTwZ4bOhYrOqQFvNdWQ5s3twMZhVhoRAwI3dvMn3eUeukk-79MZpudOTpZkPgOs/pub?output=csv"


@st.cache_data(ttl=30)  # Refresh every 30 seconds
def load_data(url):
  try:
    df = pd.read_csv(url)
    return df
  except Exception:
    return None


df = load_data(SHEET_URL)

if df is None or df.empty:
  st.warning(
      "⚠️ Awaiting Google Form submissions or data sheet is empty."
  )
else:
  # Clean column headers
  df.columns = df.columns.str.strip()

  # Map form columns (fuzzy match to avoid column name discrepancies)
  col_map = {}
  for col in df.columns:
    col_lower = col.lower()
    if "coordinator" in col_lower or "name" in col_lower:
      col_map["coordinator"] = col
    elif "ward" in col_lower:
      col_map["ward"] = col
    elif "category" in col_lower or "sector" in col_lower:
      col_map["category"] = col
    elif "timestamp" in col_lower:
      col_map["timestamp"] = col

  coord_col = col_map.get("coordinator", df.columns[1] if len(df.columns) > 1 else df.columns[0])
  ward_col = col_map.get("ward", df.columns[2] if len(df.columns) > 2 else df.columns[0])
  cat_col = col_map.get("category", df.columns[3] if len(df.columns) > 3 else df.columns[0])
  ts_col = col_map.get("timestamp", df.columns[0])

  # ---------------------------------------------------------
  # 4. LEADERBOARD CALCULATIONS
  # ---------------------------------------------------------
  leaderboard = (
      df.groupby([ward_col, coord_col])
      .agg(
          Total_Recruits=(cat_col, "count"),
          Unique_Categories=(cat_col, "nunique"),
          PWD_Inclusion=(
              cat_col,
              lambda x: x.astype(str)
              .str.contains("Special People|PWD|Disabil", case=False)
              .any(),
          ),
          Last_Submission=(ts_col, "max"),
      )
      .reset_index()
  )

  # Derived Metrics
  leaderboard["Diversity Rate (%)"] = (
      (leaderboard["Unique_Categories"] / 10) * 100
  ).clip(upper=100)

  leaderboard["Composite Score"] = (
      (leaderboard["Total_Recruits"] * 10)
      + (leaderboard["Unique_Categories"] * 15)
      + (leaderboard["PWD_Inclusion"].astype(int) * 10)
  )

  def assign_status(row):
    if row["Total_Recruits"] >= 15 and row["Unique_Categories"] >= 6:
      return "🟢 Fully Mobilized"
    elif row["Total_Recruits"] >= 15:
      return "🟡 Target Met (Low Diversity)"
    elif row["Total_Recruits"] > 0:
      return "🟠 In Progress"
    else:
      return "🔴 Inactive"

  leaderboard["Mobilization Status"] = leaderboard.apply(assign_status, axis=1)

  # Sort Leaderboard
  leaderboard = leaderboard.sort_values(
      by=["Composite Score", "Last_Submission"], ascending=[False, True]
  ).reset_index(drop=True)

  leaderboard.insert(0, "Rank", leaderboard.index + 1)

  # ---------------------------------------------------------
  # 5. TOP SUMMARY KPIs
  # ---------------------------------------------------------
  c1, c2, c3, c4 = st.columns(4)
  with c1:
    st.metric("Reporting Wards", f"{len(leaderboard)} / 57 Wards")
  with c2:
    st.metric("Total Recruits Mobilized", int(leaderboard["Total_Recruits"].sum()))
  with c3:
    target_met = len(leaderboard[leaderboard["Total_Recruits"] >= 15])
    st.metric("Target Achieved (15+ Recruits)", f"{target_met} Wards")
  with c4:
    pwd_count = leaderboard["PWD_Inclusion"].sum()
    st.metric("Wards with PWD Inclusion", f"{pwd_count} Wards")

  st.markdown("---")

  # ---------------------------------------------------------
  # 6. LEADERBOARD TABLE DISPLAY
  # ---------------------------------------------------------
  st.subheader("🏆 Live Ward Mobilization Standings")

  st.dataframe(
      leaderboard,
      column_config={
          "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
          ward_col: "Ward Name / Number",
          coord_col: "Ward Coordinator",
          "Total_Recruits": st.column_config.ProgressColumn(
              "Recruits (Target: 15)", format="%d", min_value=0, max_value=15
          ),
          "Unique_Categories": st.column_config.NumberColumn(
              "Sectors Covered", format="%d / 10"
          ),
          "Diversity Rate (%)": st.column_config.ProgressColumn(
              "Sector Spread", format="%.0f%%", min_value=0, max_value=100
          ),
          "Composite Score": st.column_config.NumberColumn(
              "Campaign Score",
              help="Includes recruits count + sector diversity + PWD bonus.",
          ),
          "PWD_Inclusion": st.column_config.CheckboxColumn("PWD Included?"),
          "Mobilization Status": "Status",
          "Last_Submission": None,
      },
      hide_index=True,
      use_container_width=True,
  )

  # ---------------------------------------------------------
  # 7. RAW RESPONSES LOG
  # ---------------------------------------------------------
  with st.expander("📝 View Direct Submissions Log"):
    st.dataframe(df, use_container_width=True)
