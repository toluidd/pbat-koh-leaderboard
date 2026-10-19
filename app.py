import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & HIGH-CONTRAST APC THEMING
# ---------------------------------------------------------
st.set_page_config(
    page_title="PBAT–KOH 2027 APC Campaign Leaderboards",
    page_icon="🗳️",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Global App Background */
    .stApp {
        background-color: #F4F6F9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Header Banner */
    .campaign-header {
        background: linear-gradient(135deg, #008751 0%, #005A36 50%, #0A192F 100%);
        padding: 2.2rem;
        border-radius: 14px;
        color: #FFFFFF !important;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 6px 18px rgba(0,0,0,0.12);
        border-bottom: 6px solid #FFD700;
    }
    .campaign-header h1 {
        color: #FFFFFF !important;
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .campaign-header h3 {
        color: #FFD700 !important;
        font-weight: 700;
        font-size: 1.25rem;
        margin-top: 0;
    }
    
    /* Metric Cards - High Contrast */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border-left: 6px solid #008751;
    }
    div[data-testid="stMetricLabel"] {
        color: #333333 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }
    div[data-testid="stMetricValue"] {
        color: #008751 !important;
        font-weight: 800 !important;
    }

    /* Podium Card Styling */
    .podium-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 2px solid #E0E0E0;
        margin-bottom: 15px;
    }
    .podium-gold {
        border: 3px solid #FFD700 !important;
        background: linear-gradient(180deg, #FFFDF0 0%, #FFFFFF 100%);
    }
    .podium-silver {
        border: 3px solid #C0C0C0 !important;
        background: linear-gradient(180deg, #F8F9FA 0%, #FFFFFF 100%);
    }
    .podium-bronze {
        border: 3px solid #CD7F32 !important;
        background: linear-gradient(180deg, #FFF8F2 0%, #FFFFFF 100%);
    }
    .podium-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0A192F;
        margin-bottom: 4px;
    }
    .podium-sub {
        font-size: 0.9rem;
        color: #555555;
        margin-bottom: 10px;
        font-weight: 600;
    }
    .podium-score {
        font-size: 1.4rem;
        font-weight: 800;
        color: #008751;
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
        <h3>ALL PROGRESSIVES CONGRESS (APC) | LAGOS STATE</h3>
        <h1>PBAT–KOH 2027 CAMPAIGN COUNCIL</h1>
        <p style="font-size: 1.1rem; opacity: 0.95; margin-bottom: 0;">
            <b>Contact & Mobilization Directorate</b> | Statewide Dual-Tier Performance Leaderboard
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 3. DATA SOURCES (CSV URLS)
# ---------------------------------------------------------
SHEET_A_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQeqUcc-k4fLZtbMqFJTee35KNlX_2jLsV4ucz9yic1O8vlz0SZ2vc_bXA6aO1XazAV1ygcBkB5zX4X/pub?gid=309814162&single=true&output=csv"
SHEET_B_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRo-g0a6T4pxPa1CnTwZ4bOhYrOqQFvNdWQ5s3twMZhVhoRAwI3dvMn3eUeukk-79MZpudOTpZkPgOs/pub?gid=142668791&single=true&output=csv"


@st.cache_data(ttl=30)
def fetch_sheet_data(url):
  try:
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df
  except Exception:
    return pd.DataFrame()


df_coordinators = fetch_sheet_data(SHEET_A_URL)
df_activity = fetch_sheet_data(SHEET_B_URL)

# ---------------------------------------------------------
# 4. DATA PROCESSING & MEDAL SCORING ENGINE
# ---------------------------------------------------------


def find_col(df, keywords):
  for col in df.columns:
    for kw in keywords:
      if kw.lower() in col.lower():
        return col
  return df.columns[0] if len(df.columns) > 0 else "Ward"


ward_col_a = find_col(df_coordinators, ["ward"])
coord_col_a = find_col(df_coordinators, ["coordinator", "name", "full name"])

ward_col_b = find_col(df_activity, ["ward"])
sub_col_b = find_col(df_activity, ["name", "sub-coordinator", "full name"])
sector_col_b = find_col(
    df_activity, ["sector", "occupation", "profile", "association", "ethnic"]
)
feedback_col_b = find_col(
    df_activity, ["feedback", "concern", "needs", "major concerns"]
)

# --- PROCESS SUB-COORDINATOR LEADERBOARD (TIER 2) ---
if not df_activity.empty:
  sub_activity = (
      df_activity.groupby([sub_col_b, ward_col_b])
      .agg(
          Total_Submissions=(sector_col_b, "count"),
          Sectors_Covered=(sector_col_b, "nunique"),
          Detailed_Feedbacks=(
              feedback_col_b,
              lambda x: x.dropna().astype(str).str.len().gt(15).sum(),
          ),
      )
      .reset_index()
  )

  # Calculate Medal Counts for Sub-Coordinators
  sub_activity["Gold_Medals"] = np.where(
      (sub_activity["Total_Submissions"] >= 3)
      & (sub_activity["Sectors_Covered"] >= 2),
      1,
      0,
  )
  sub_activity["Silver_Medals"] = np.where(
      (sub_activity["Total_Submissions"] >= 2)
      & (sub_activity["Gold_Medals"] == 0),
      1,
      0,
  )
  sub_activity["Bronze_Medals"] = np.where(
      (sub_activity["Total_Submissions"] >= 1)
      & (sub_activity["Gold_Medals"] == 0)
      & (sub_activity["Silver_Medals"] == 0),
      1,
      0,
  )

  # Total Score Formula
  sub_activity["Campaign_Points"] = (
      (sub_activity["Total_Submissions"] * 10)
      + (sub_activity["Sectors_Covered"] * 15)
      + (sub_activity["Detailed_Feedbacks"] * 5)
  )

  # Performance Sorting: Rank by Gold count, then Silver, then Bronze, then total points
  sub_activity = sub_activity.sort_values(
      by=[
          "Gold_Medals",
          "Silver_Medals",
          "Bronze_Medals",
          "Campaign_Points",
          "Total_Submissions",
      ],
      ascending=[False, False, False, False, False],
  ).reset_index(drop=True)
  sub_activity.insert(0, "Rank", sub_activity.index + 1)
else:
  sub_activity = pd.DataFrame(
      columns=[
          "Rank",
          sub_col_b,
          ward_col_b,
          "Total_Submissions",
          "Sectors_Covered",
          "Gold_Medals",
          "Silver_Medals",
          "Bronze_Medals",
          "Campaign_Points",
      ]
  )

# --- PROCESS WARD COORDINATOR LEADERBOARD (TIER 1) ---
if not df_coordinators.empty or not sub_activity.empty:
  if not df_coordinators.empty:
    ward_df = df_coordinators[[ward_col_a, coord_col_a]].drop_duplicates()
  else:
    ward_df = pd.DataFrame({ward_col_a: [], coord_col_a: []})

  if not sub_activity.empty:
    ward_summary = (
        sub_activity.groupby(ward_col_b)
        .agg(
            Active_SubCoordinators=(sub_col_b, "nunique"),
            Total_Ward_Recruits=("Total_Submissions", "sum"),
            Total_Ward_Gold=("Gold_Medals", "sum"),
            Total_Ward_Silver=("Silver_Medals", "sum"),
            Total_Ward_Bronze=("Bronze_Medals", "sum"),
            Cumulative_Ward_Score=("Campaign_Points", "sum"),
        )
        .reset_index()
    )

    ward_leaderboard = pd.merge(
        ward_df,
        ward_summary,
        left_on=ward_col_a,
        right_on=ward_col_b,
        how="outer",
    )
  else:
    ward_leaderboard = ward_df.copy()
    ward_leaderboard["Active_SubCoordinators"] = 0
    ward_leaderboard["Total_Ward_Recruits"] = 0
    ward_leaderboard["Total_Ward_Gold"] = 0
    ward_leaderboard["Total_Ward_Silver"] = 0
    ward_leaderboard["Total_Ward_Bronze"] = 0
    ward_leaderboard["Cumulative_Ward_Score"] = 0

  ward_leaderboard[ward_col_a] = ward_leaderboard[ward_col_a].fillna(
      ward_leaderboard[ward_col_b]
  )
  ward_leaderboard[coord_col_a] = ward_leaderboard[coord_col_a].fillna(
      "Unassigned / Pending Form A"
  )
  ward_leaderboard.fillna(0, inplace=True)

  ward_leaderboard["Team Mobilization (%)"] = (
      (ward_leaderboard["Active_SubCoordinators"] / 15) * 100
  ).clip(upper=100)

  ward_leaderboard = ward_leaderboard.sort_values(
      by=[
          "Total_Ward_Gold",
          "Total_Ward_Silver",
          "Total_Ward_Bronze",
          "Cumulative_Ward_Score",
          "Active_SubCoordinators",
      ],
      ascending=[False, False, False, False, False],
  ).reset_index(drop=True)
  ward_leaderboard.insert(0, "Rank", ward_leaderboard.index + 1)
else:
  ward_leaderboard = pd.DataFrame()


# ---------------------------------------------------------
# 5. TOP STATEWIDE KPI METRICS
# ---------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)
with m1:
  st.metric(
      "Reporting Wards",
      f"{len(ward_leaderboard)} Wards" if not ward_leaderboard.empty else "0 Wards",
  )
with m2:
  total_recs = (
      int(sub_activity["Total_Submissions"].sum())
      if not sub_activity.empty
      else 0
  )
  st.metric("Total Field Recruits Logged", total_recs)
with m3:
  total_subs = (
      int(sub_activity[sub_col_b].nunique()) if not sub_activity.empty else 0
  )
  st.metric("Active Sub-Coordinators", total_subs)
with m4:
  total_golds = (
      int(sub_activity["Gold_Medals"].sum()) if not sub_activity.empty else 0
  )
  st.metric("🥇 Gold Medal Performers", total_golds)

st.markdown("---")

# ---------------------------------------------------------
# 6. DUAL LEADERBOARD TABS
# ---------------------------------------------------------
tab1, tab2 = st.tabs([
    "🏆 Ward Coordinators Leaderboard (Tier 1)",
    "🥇 Ward Sub-Coordinators Standings (Tier 2)",
])

# =========================================================
# TAB 1: WARD COORDINATORS LEADERBOARD
# =========================================================
with tab1:
  st.subheader("🥇 Ward Coordinators Statewide Medal Standings")
  st.caption(
      "Ranked primarily by the total Gold Medals earned by their 15"
      " Sub-Coordinators, followed by Silver and Bronze tallies."
  )

  if ward_leaderboard.empty:
    st.info(
        "⏳ Awaiting Google Form responses from Ward Coordinators and"
        " Sub-Coordinators."
    )
  else:
    st.markdown("### 🏆 Top 3 Performing Ward Coordinators")
    p1, p2, p3 = st.columns(3)

    for col, idx, medal_emoji, border_class in zip(
        [p1, p2, p3],
        [0, 1, 2],
        ["🥇 1st Rank (Gold)", "🥈 2nd Rank (Silver)", "🥉 3rd Rank (Bronze)"],
        ["podium-gold", "podium-silver", "podium-bronze"],
    ):
      with col:
        if len(ward_leaderboard) > idx:
          row = ward_leaderboard.iloc[idx]
          st.markdown(
              f"""
                    <div class="podium-card {border_class}">
                        <div style="font-size: 1.5rem; margin-bottom: 5px;">{medal_emoji}</div>
                        <div class="podium-title">{row[coord_col_a]}</div>
                        <div class="podium-sub">Ward: {row[ward_col_a]}</div>
                        <div class="podium-score">{int(row['Cumulative_Ward_Score'])} Points</div>
                        <div style="margin-top: 8px; font-size: 0.9rem; color: #333;">
                            🥇 {int(row['Total_Ward_Gold'])} Gold | 🥈 {int(row['Total_Ward_Silver'])} Silver | 🥉 {int(row['Total_Ward_Bronze'])} Bronze
                        </div>
                    </div>
                    """,
              unsafe_allow_html=True,
          )

    st.markdown("---")

    search_ward = st.text_input(
        "🔍 Search Ward Coordinator or Ward Name:", ""
    )
    filtered_ward_df = ward_leaderboard.copy()
    if search_ward:
      filtered_ward_df = filtered_ward_df[
          filtered_ward_df[coord_col_a]
          .astype(str)
          .str.contains(search_ward, case=False)
          | filtered_ward_df[ward_col_a]
          .astype(str)
          .str.contains(search_ward, case=False)
      ]

    st.dataframe(
        filtered_ward_df,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
            ward_col_a: "Ward Name",
            coord_col_a: "Ward Coordinator Name",
            "Active_SubCoordinators": st.column_config.NumberColumn(
                "Active Sub-Coordinators", format="%d / 15"
            ),
            "Team Mobilization (%)": st.column_config.ProgressColumn(
                "Team Setup Progress", format="%.0f%%", min_value=0, max_value=100
            ),
            "Total_Ward_Gold": st.column_config.NumberColumn(
                "🥇 Ward Gold", format="%d"
            ),
            "Total_Ward_Silver": st.column_config.NumberColumn(
                "🥈 Ward Silver", format="%d"
            ),
            "Total_Ward_Bronze": st.column_config.NumberColumn(
                "🥉 Ward Bronze", format="%d"
            ),
            "Total_Ward_Recruits": st.column_config.NumberColumn(
                "Total Ward Recruits", format="%d"
            ),
            "Cumulative_Ward_Score": st.column_config.NumberColumn(
                "Total Campaign Score", format="%d pts"
            ),
            ward_col_b: None,
        },
        hide_index=True,
        use_container_width=True,
    )

# =========================================================
# TAB 2: WARD SUB-COORDINATORS MASTER LEADERBOARD
# =========================================================
with tab2:
  st.subheader("⭐ Statewide Sub-Coordinators Master Leaderboard")
  st.caption(
      "Individual performance standings for all Sub-Coordinators across Lagos"
      " State based on recruit volume, sector diversity, and feedback logging."
  )

  if sub_activity.empty:
    st.info("⏳ No field responses submitted by sub-coordinators yet.")
  else:
    st.markdown("### 🏆 Top 3 Field Sub-Coordinators")
    s1, s2, s3 = st.columns(3)

    for col, idx, medal_emoji, border_class in zip(
        [s1, s2, s3],
        [0, 1, 2],
        ["🥇 Gold Rank", "🥈 Silver Rank", "🥉 Bronze Rank"],
        ["podium-gold", "podium-silver", "podium-bronze"],
    ):
      with col:
        if len(sub_activity) > idx:
          srow = sub_activity.iloc[idx]
          st.markdown(
              f"""
                    <div class="podium-card {border_class}">
                        <div style="font-size: 1.5rem; margin-bottom: 5px;">{medal_emoji}</div>
                        <div class="podium-title">{srow[sub_col_b]}</div>
                        <div class="podium-sub">Ward: {srow[ward_col_b]}</div>
                        <div class="podium-score">{int(srow['Campaign_Points'])} Points</div>
                        <div style="margin-top: 8px; font-size: 0.9rem; color: #333;">
                            Recruits: {int(srow['Total_Submissions'])} | Sectors: {int(srow['Sectors_Covered'])}
                        </div>
                    </div>
                    """,
              unsafe_allow_html=True,
          )

    st.markdown("---")

    search_sub = st.text_input(
        "🔍 Search Sub-Coordinator Name or Ward:", "", key="sub_search"
    )
    filtered_sub_df = sub_activity.copy()
    if search_sub:
      filtered_sub_df = filtered_sub_df[
          filtered_sub_df[sub_col_b]
          .astype(str)
          .str.contains(search_sub, case=False)
          | filtered_sub_df[ward_col_b]
          .astype(str)
          .str.contains(search_sub, case=False)
      ]

    st.dataframe(
        filtered_sub_df,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="#%d"),
            sub_col_b: "Sub-Coordinator Name",
            ward_col_b: "Ward Name",
            "Gold_Medals": st.column_config.NumberColumn(
                "🥇 Gold", format="%d"
            ),
            "Silver_Medals": st.column_config.NumberColumn(
                "🥈 Silver", format="%d"
            ),
            "Bronze_Medals": st.column_config.NumberColumn(
                "🥉 Bronze", format="%d"
            ),
            "Total_Submissions": st.column_config.NumberColumn(
                "Total Entries Logged", format="%d"
            ),
            "Sectors_Covered": st.column_config.NumberColumn(
                "Sectors Covered", format="%d"
            ),
            "Detailed_Feedbacks": st.column_config.NumberColumn(
                "Quality Feedbacks Logged", format="%d"
            ),
            "Campaign_Points": st.column_config.NumberColumn(
                "Total Score", format="%d pts"
            ),
        },
        hide_index=True,
        use_container_width=True,
    )
