"""
Project Manager Operations Dashboard — v2
==========================================
Changes from v1:
  - Added "Ans within SLA" field to call center form
  - MTD SLA % = sum(ans_within_sla) / sum(offered) × 100  (month-to-date)
  - MTD ABD % = sum(abandoned) / sum(offered) × 100  (month-to-date)
  - Per-project SLA targets with colour-coded pills
  - Insurance form: removed Policies Offered, SLA%, ABD%, Utilization, Occupancy
  - PM overview: replaced avg SLA & total calls with overall attendance %
  - All existing data is preserved (new fields default to 0 for old entries)

HOW TO RUN
----------
  pip install streamlit plotly pandas
  streamlit run pm_dashboard.py
"""

import json
import os
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ──────────────────────────────────────────────────────────────
# 0.  PAGE CONFIG
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Operations Command Center",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────
# 1.  CONFIGURATION
# ──────────────────────────────────────────────────────────────
PM_PIN  = "9999"
PM_NAME = "Project Manager"

# SLA rules: target_pct = minimum SLA % to be considered "achieved"
# answer_sec = speed-of-answer threshold (informational label only)
PROJECTS = {
    "P001": {
        "name":       "Call Center — GPSSA",
        "manager":    "Yehia",
        "pin":        "1001",
        "type":       "callcenter",
        "color":      "#4F46E5",
        "sla_target": 90,      # 90%
        "sla_sec":    10,      # within 10s  (label only)
    },
    "P002": {
        "name":       "Call Center — NAFIS",
        "manager":    "AHMED",
        "pin":        "1002",
        "type":       "callcenter",
        "color":      "#0EA5E9",
        "sla_target": 90,
        "sla_sec":    20,
    },
    "P003": {
        "name":       "Call Center — Fidelity",
        "manager":    "Ephraim",
        "pin":        "1003",
        "type":       "callcenter",
        "color":      "#10B981",
        "sla_target": 80,
        "sla_sec":    20,
    },
    "P004": {
        "name":       "Call Center — Parkin",
        "manager":    "Assim",
        "pin":        "1004",
        "type":       "callcenter",
        "color":      "#F59E0B",
        "sla_target": 80,
        "sla_sec":    30,
    },
    "P005": {
        "name":       "Call Center — DREC",
        "manager":    "Khatib",
        "pin":        "1005",
        "type":       "callcenter",
        "color":      "#8B5CF6",
        "sla_target": 80,
        "sla_sec":    20,
    },
    "P006": {
        "name":       "Call Center — Zeta",
        "manager":    "Test",
        "pin":        "1006",
        "type":       "callcenter",
        "color":      "#EC4899",
        "sla_target": 80,
        "sla_sec":    20,
    },
    "P007": {
        "name":       "ADNIC — Renewals & New Business",
        "manager":    "Khatib",
        "pin":        "1007",
        "type":       "insurance",
        "color":      "#EF4444",
        "sla_target": None,
        "sla_sec":    None,
    },
}

# ──────────────────────────────────────────────────────────────
# 2.  DATA STORAGE
# ──────────────────────────────────────────────────────────────
DATA_FILE = "operations_data.json"


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def get_entry(data: dict, project_id: str, entry_date: str) -> dict:
    return data.get(project_id, {}).get(entry_date, {})


def save_entry(project_id: str, entry_date: str, values: dict):
    data = load_data()
    if project_id not in data:
        data[project_id] = {}
    data[project_id][entry_date] = values
    save_data(data)


def get_project_history(data: dict, project_id: str, days: int = 30) -> pd.DataFrame:
    project_data = data.get(project_id, {})
    rows = []
    for d_str, vals in project_data.items():
        try:
            d = datetime.strptime(d_str, "%Y-%m-%d").date()
            rows.append({"date": d, **vals})
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).sort_values("date")
    cutoff = date.today() - timedelta(days=days)
    return df[df["date"] >= cutoff].reset_index(drop=True)


def get_mtd_history(data: dict, project_id: str) -> pd.DataFrame:
    """Return all entries for the current calendar month."""
    project_data = data.get(project_id, {})
    rows = []
    today = date.today()
    for d_str, vals in project_data.items():
        try:
            d = datetime.strptime(d_str, "%Y-%m-%d").date()
            if d.year == today.year and d.month == today.month:
                rows.append({"date": d, **vals})
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def calc_mtd_sla(mtd_df: pd.DataFrame) -> float | None:
    """MTD SLA % = sum(ans_within_sla) / sum(offered) × 100"""
    if mtd_df.empty:
        return None
    total_offered = mtd_df.get("offered", pd.Series(dtype=float)).fillna(0).sum()
    total_sla     = mtd_df.get("ans_within_sla", pd.Series(dtype=float)).fillna(0).sum()
    if total_offered == 0:
        return None
    return (total_sla / total_offered) * 100


def calc_mtd_abd(mtd_df: pd.DataFrame) -> float | None:
    """MTD ABD % = sum(abandoned) / sum(offered) × 100"""
    if mtd_df.empty:
        return None
    total_offered  = mtd_df.get("offered",   pd.Series(dtype=float)).fillna(0).sum()
    total_abandoned = mtd_df.get("abandoned", pd.Series(dtype=float)).fillna(0).sum()
    if total_offered == 0:
        return None
    return (total_abandoned / total_offered) * 100


# ──────────────────────────────────────────────────────────────
# 3.  SLA COLOUR CODING
# ──────────────────────────────────────────────────────────────
def sla_pill_mtd(value: float | None, target: int | None) -> str:
    """Return colour-coded pill based on project SLA target."""
    if value is None or target is None:
        return '<span class="pill pill-grey">No Data</span>'
    pct = round(value, 1)
    gap = pct - target
    if gap >= 0:
        return f'<span class="pill pill-green">✓ {pct}%</span>'
    elif gap >= -5:
        return f'<span class="pill pill-yellow">⚠ {pct}%</span>'
    else:
        return f'<span class="pill pill-red">✗ {pct}%</span>'


def abd_pill(value: float | None) -> str:
    if value is None:
        return '<span class="pill pill-grey">No Data</span>'
    pct = round(value, 1)
    if pct <= 5:
        return f'<span class="pill pill-green">✓ {pct}%</span>'
    elif pct <= 10:
        return f'<span class="pill pill-yellow">⚠ {pct}%</span>'
    else:
        return f'<span class="pill pill-red">✗ {pct}%</span>'


def attendance_pill(present: int, total: int) -> str:
    if total == 0:
        return '<span class="pill pill-grey">—</span>'
    pct = round(present / total * 100, 1)
    if pct >= 90:
        return f'<span class="pill pill-green">✓ {pct}%</span>'
    elif pct >= 75:
        return f'<span class="pill pill-yellow">⚠ {pct}%</span>'
    else:
        return f'<span class="pill pill-red">✗ {pct}%</span>'


# ──────────────────────────────────────────────────────────────
# 4.  STYLING
# ──────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #0A0E1A; color: #E2E8F0; }
    #MainMenu, footer, header { visibility: hidden; }

    .top-bar {
        background: linear-gradient(90deg,#0F1629 0%,#141B2E 100%);
        border-bottom: 1px solid #1E2D4A;
        padding: 16px 32px;
        margin: -1rem -1rem 2rem -1rem;
        display: flex; align-items: center; justify-content: space-between;
    }
    .top-bar h1 {
        font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 800;
        color: #F8FAFC; margin: 0; letter-spacing: -0.5px;
    }
    .top-bar .badge {
        font-size: 12px; font-weight: 600; padding: 4px 12px;
        border-radius: 20px; background: #1E3A5F; color: #60A5FA; letter-spacing: 0.5px;
    }
    .kpi-card {
        background: #0F1629; border: 1px solid #1E2D4A; border-radius: 12px;
        padding: 20px; margin-bottom: 12px;
    }
    .kpi-label {
        font-size: 11px; font-weight: 600; color: #64748B;
        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;
    }
    .kpi-value {
        font-family: 'Syne', sans-serif; font-size: 26px; font-weight: 700;
        color: #F8FAFC; line-height: 1.1;
    }
    .kpi-sub { font-size: 12px; color: #475569; margin-top: 4px; }

    .proj-card {
        background: #0F1629; border: 1px solid #1E2D4A; border-radius: 14px;
        padding: 22px; margin-bottom: 16px;
    }
    .proj-title {
        font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 700;
        color: #F8FAFC; margin-bottom: 4px;
    }
    .proj-manager { font-size: 12px; color: #64748B; margin-bottom: 16px; }

    .pill {
        display: inline-block; font-size: 11px; font-weight: 600;
        padding: 3px 10px; border-radius: 20px; letter-spacing: 0.3px;
    }
    .pill-green  { background: #052E16; color: #4ADE80; }
    .pill-yellow { background: #2D1B00; color: #FCD34D; }
    .pill-red    { background: #2D0707; color: #F87171; }
    .pill-grey   { background: #1E293B; color: #94A3B8; }

    .section-title {
        font-family: 'Syne', sans-serif; font-size: 18px; font-weight: 700;
        color: #F8FAFC; margin: 28px 0 16px; padding-bottom: 10px;
        border-bottom: 1px solid #1E2D4A;
    }
    .form-section {
        background: #0F1629; border: 1px solid #1E2D4A;
        border-radius: 14px; padding: 24px; margin-bottom: 20px;
    }
    .form-section h4 {
        font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 700;
        color: #60A5FA; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .mtd-box {
        background: #0A1628; border: 1px solid #1E3A5F; border-radius: 10px;
        padding: 14px 18px; margin-bottom: 14px;
    }
    .mtd-label { font-size: 10px; color: #475569; text-transform: uppercase; letter-spacing: 1px; }
    .mtd-value { font-family:'Syne',sans-serif; font-size:22px; font-weight:700; color:#F8FAFC; }
    .sla-rule-tag {
        font-size: 11px; color: #60A5FA; background: #1E3A5F;
        padding: 2px 8px; border-radius: 10px; margin-left: 8px;
    }

    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div,
    .stDateInput>div>div>input {
        background: #141B2E !important; border: 1px solid #1E2D4A !important;
        border-radius: 8px !important; color: #E2E8F0 !important;
    }
    .stButton>button {
        background: #4F46E5 !important; color: white !important;
        border: none !important; border-radius: 8px !important;
        font-weight: 600 !important; padding: 10px 24px !important; width: 100%;
    }
    .stButton>button:hover { background: #4338CA !important; }
    div[data-testid="stForm"] { background: transparent !important; border: none !important; }
    label { color: #94A3B8 !important; font-size: 13px !important; }
    .stTabs [data-baseweb="tab"] { font-family:'Syne',sans-serif; font-weight:600; color:#64748B; }
    .stTabs [aria-selected="true"] { color: #60A5FA !important; }
    </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# 5.  HELPER WIDGETS
# ──────────────────────────────────────────────────────────────
def kpi_card(label, value, sub="", color="#4F46E5"):
    st.markdown(f"""
    <div class="kpi-card" style="border-top:2px solid {color};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)


def mtd_box(label, value_html, sub=""):
    st.markdown(f"""
    <div class="mtd-box">
        <div class="mtd-label">{label}</div>
        <div class="mtd-value">{value_html}</div>
        <div style="font-size:11px;color:#475569;margin-top:2px;">{sub}</div>
    </div>""", unsafe_allow_html=True)


def metric_cell(label, value, color="#F8FAFC"):
    return f"""
    <div style="text-align:center;">
      <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.5px;">{label}</div>
      <div style="font-family:'Syne',sans-serif;font-size:17px;font-weight:700;color:{color};">{value}</div>
    </div>"""


def mini_bar(values, labels, color="#4F46E5", height=200):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=values, marker_color=color,
        hovertemplate="%{x}<br>%{y}<extra></extra>",
    ))
    fig.update_layout(
        height=height, margin=dict(t=10,b=30,l=30,r=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8", size=11),
        xaxis=dict(showgrid=False, tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor="#1E2D4A"),
    )
    return fig


def chart_layout(fig, height=220):
    fig.update_layout(
        height=height, margin=dict(t=10,b=30,l=30,r=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8",size=11),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),
        xaxis=dict(showgrid=False,tickangle=-30),
        yaxis=dict(showgrid=True,gridcolor="#1E2D4A"),
    )
    return fig


# ──────────────────────────────────────────────────────────────
# 6.  LOGIN
# ──────────────────────────────────────────────────────────────
def show_login():
    st.markdown("""
    <div style="text-align:center;padding:48px 0 24px;">
        <div style="font-size:48px;margin-bottom:8px;">📊</div>
        <h1 style="font-family:'Syne',sans-serif;font-size:32px;font-weight:800;
                   color:#F8FAFC;margin:0;">Operations Command Center</h1>
        <p style="color:#475569;margin-top:8px;font-size:15px;">
            Enter your PIN to access your dashboard</p>
    </div>""", unsafe_allow_html=True)

    col = st.columns([1, 1.2, 1])[1]
    with col:
        with st.form("login_form"):
            pin = st.text_input("Your PIN", type="password", placeholder="Enter PIN")
            submitted = st.form_submit_button("🔐  Access Dashboard")
        if submitted:
            if pin == PM_PIN:
                st.session_state["role"] = "pm"
                st.session_state["project_id"] = None
                st.rerun()
            for pid, proj in PROJECTS.items():
                if pin == proj["pin"]:
                    st.session_state["role"] = "manager"
                    st.session_state["project_id"] = pid
                    st.rerun()
            st.error("❌ Invalid PIN. Please try again.")
        st.markdown("""<div style="text-align:center;margin-top:16px;color:#334155;font-size:12px;">
            Contact your Project Manager if you've forgotten your PIN</div>""",
            unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# 7.  MANAGER FORM
# ──────────────────────────────────────────────────────────────
def show_manager_form(project_id: str):
    proj         = PROJECTS[project_id]
    color        = proj["color"]
    is_insurance = proj["type"] == "insurance"
    sla_target   = proj.get("sla_target")
    sla_sec      = proj.get("sla_sec")

    st.markdown(f"""
    <div class="top-bar">
        <h1>📋 {proj['name']}</h1>
        <div><span class="badge">OM: {proj['manager']}</span></div>
    </div>""", unsafe_allow_html=True)

    data = load_data()

    # ── MTD summary strip (read-only) ─────────────────────────
    if not is_insurance:
        mtd_df  = get_mtd_history(data, project_id)
        mtd_sla = calc_mtd_sla(mtd_df)
        mtd_abd = calc_mtd_abd(mtd_df)
        today   = date.today()

        st.markdown(f"""
        <div style="background:#0A1628;border:1px solid #1E3A5F;border-radius:12px;
                    padding:16px 20px;margin-bottom:20px;display:flex;gap:32px;
                    align-items:center;flex-wrap:wrap;">
            <div>
                <div style="font-size:10px;color:#475569;text-transform:uppercase;
                             letter-spacing:1px;">MTD Period</div>
                <div style="font-family:'Syne',sans-serif;font-weight:700;color:#F8FAFC;">
                    {today.strftime('%b %Y')} (Day {today.day})</div>
            </div>
            <div>
                <div style="font-size:10px;color:#475569;text-transform:uppercase;
                             letter-spacing:1px;">MTD SLA %
                    <span class="sla-rule-tag">Target: {sla_target}% / {sla_sec}s</span>
                </div>
                <div style="font-size:22px;">{sla_pill_mtd(mtd_sla, sla_target)}</div>
            </div>
            <div>
                <div style="font-size:10px;color:#475569;text-transform:uppercase;
                             letter-spacing:1px;">MTD ABD %</div>
                <div style="font-size:22px;">{abd_pill(mtd_abd)}</div>
            </div>
            <div>
                <div style="font-size:10px;color:#475569;text-transform:uppercase;
                             letter-spacing:1px;">Days Submitted</div>
                <div style="font-family:'Syne',sans-serif;font-weight:700;
                             color:#F8FAFC;font-size:22px;">{len(mtd_df)}</div>
            </div>
        </div>""", unsafe_allow_html=True)

    tab_submit, tab_history = st.tabs(["📝  Submit Daily Report", "📅  My History"])

    # ── SUBMIT TAB ────────────────────────────────────────────
    with tab_submit:
        st.markdown('<div class="section-title">Daily KPI Entry</div>',
                    unsafe_allow_html=True)

        today_str = str(date.today())
        existing  = get_entry(data, project_id, today_str)
        if existing:
            st.success(f"✅ Already submitted for today ({today_str}). Re-submit to update.")

        with st.form("daily_entry"):
            entry_date = st.date_input("📅 Report Date", value=date.today(),
                                        max_value=date.today())

            # ── Call Center KPIs (all project types except insurance get these) ──
            if not is_insurance:
                st.markdown('<div class="form-section"><h4>📞 Call Center KPIs</h4>',
                            unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    offered  = st.number_input("Offered Calls",  min_value=0, step=1,
                                                value=int(existing.get("offered", 0)))
                    answered = st.number_input("Answered Calls", min_value=0, step=1,
                                                value=int(existing.get("answered", 0)))
                    abandoned = st.number_input("Abandoned Calls", min_value=0, step=1,
                                                 value=int(existing.get("abandoned", 0)))
                with c2:
                    ans_within_sla = st.number_input(
                        f"Ans within SLA ({sla_sec}s)" if sla_sec else "Ans within SLA",
                        min_value=0, step=1,
                        value=int(existing.get("ans_within_sla", 0)),
                        help="Number of calls answered within the SLA threshold")
                    sla_pct = st.number_input("SLA % (daily)",
                                               min_value=0.0, max_value=100.0,
                                               step=0.1, format="%.1f",
                                               value=float(existing.get("sla_pct", 0.0)))
                    abd_pct = st.number_input("ABD % (daily)",
                                               min_value=0.0, max_value=100.0,
                                               step=0.1, format="%.1f",
                                               value=float(existing.get("abd_pct", 0.0)))
                with c3:
                    aht_sec  = st.number_input("AHT (seconds)", min_value=0, step=1,
                                                value=int(existing.get("aht_sec", 0)))
                    qa_score = st.number_input("QA Score %",
                                               min_value=0.0, max_value=100.0,
                                               step=0.1, format="%.1f",
                                               value=float(existing.get("qa_score", 0.0)))
                with c4:
                    util_pct = st.number_input("Utilization %",
                                               min_value=0.0, max_value=100.0,
                                               step=0.1, format="%.1f",
                                               value=float(existing.get("util_pct", 0.0)))
                    occ_pct  = st.number_input("Occupancy %",
                                               min_value=0.0, max_value=100.0,
                                               step=0.1, format="%.1f",
                                               value=float(existing.get("occ_pct", 0.0)))
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                # Insurance: no call center KPIs
                offered = answered = abandoned = ans_within_sla = 0
                sla_pct = abd_pct = aht_sec = qa_score = util_pct = occ_pct = 0.0

            # ── Attendance (all projects) ─────────────────────
            st.markdown('<div class="form-section"><h4>👥 Attendance & Discipline</h4>',
                        unsafe_allow_html=True)
            a1, a2, a3 = st.columns(3)
            with a1:
                total_agents = st.number_input("Total Agents",  min_value=0, step=1,
                                                value=int(existing.get("total_agents", 0)))
                present      = st.number_input("Present",       min_value=0, step=1,
                                                value=int(existing.get("present", 0)))
            with a2:
                absent       = st.number_input("Absent",        min_value=0, step=1,
                                                value=int(existing.get("absent", 0)))
                late         = st.number_input("Late (count)",  min_value=0, step=1,
                                                value=int(existing.get("late", 0)))
            with a3:
                leave        = st.number_input("On Leave",      min_value=0, step=1,
                                                value=int(existing.get("leave", 0)))
                lateness_min = st.number_input("Avg Lateness (min)", min_value=0, step=1,
                                                value=int(existing.get("lateness_min", 0)))
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Insurance KPIs ────────────────────────────────
            ins_renewals = ins_new = ins_conversion = 0.0
            if is_insurance:
                st.markdown('<div class="form-section"><h4>🛡️ Insurance KPIs</h4>',
                            unsafe_allow_html=True)
                i1, i2, i3 = st.columns(3)
                with i1:
                    ins_renewals   = st.number_input("Renewals Closed", min_value=0, step=1,
                                                      value=int(existing.get("ins_renewals", 0)))
                with i2:
                    ins_new        = st.number_input("New Business Closed", min_value=0, step=1,
                                                      value=int(existing.get("ins_new", 0)))
                with i3:
                    ins_conversion = st.number_input("Conversion Rate %",
                                                      min_value=0.0, max_value=100.0,
                                                      step=0.1, format="%.1f",
                                                      value=float(existing.get("ins_conversion", 0.0)))
                st.markdown('</div>', unsafe_allow_html=True)

            notes = st.text_area("📝 Notes / Issues (optional)",
                                  value=existing.get("notes", ""),
                                  placeholder="Any issues, highlights or context for today...")

            submitted = st.form_submit_button("💾  Submit Daily Report",
                                               use_container_width=True)

        if submitted:
            entry = {
                "offered": offered, "answered": answered, "abandoned": abandoned,
                "ans_within_sla": ans_within_sla,
                "sla_pct": sla_pct, "abd_pct": abd_pct, "aht_sec": aht_sec,
                "qa_score": qa_score, "util_pct": util_pct, "occ_pct": occ_pct,
                "total_agents": total_agents, "present": present, "absent": absent,
                "late": late, "leave": leave, "lateness_min": lateness_min,
                "notes": notes,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            if is_insurance:
                entry.update({
                    "ins_renewals": ins_renewals,
                    "ins_new": ins_new,
                    "ins_conversion": ins_conversion,
                })
            save_entry(project_id, str(entry_date), entry)
            st.success(f"✅ Report submitted for {entry_date}!")
            st.balloons()
            st.rerun()

    # ── HISTORY TAB ───────────────────────────────────────────
    with tab_history:
        st.markdown('<div class="section-title">My Submission History (Last 30 Days)</div>',
                    unsafe_allow_html=True)
        hist = get_project_history(data, project_id, days=30)
        if hist.empty:
            st.info("No data submitted yet.")
        else:
            if not is_insurance:
                # MTD KPI cards
                mtd_df  = get_mtd_history(data, project_id)
                mtd_sla = calc_mtd_sla(mtd_df)
                mtd_abd = calc_mtd_abd(mtd_df)
                h1, h2, h3, h4 = st.columns(4)
                with h1:
                    kpi_card("MTD SLA %",
                             f"{mtd_sla:.1f}%" if mtd_sla is not None else "—",
                             f"Target: {sla_target}%", color)
                with h2:
                    kpi_card("MTD ABD %",
                             f"{mtd_abd:.1f}%" if mtd_abd is not None else "—",
                             "Month to date", "#EF4444")
                with h3:
                    kpi_card("Avg QA %",
                             f"{hist['qa_score'].mean():.1f}%" if "qa_score" in hist.columns else "—",
                             "30-day avg", "#10B981")
                with h4:
                    kpi_card("Total Offered",
                             f"{int(hist['offered'].sum()):,}" if "offered" in hist.columns else "—",
                             "30 days", "#0EA5E9")
                st.markdown("<br>", unsafe_allow_html=True)

                # Trend charts
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**SLA % Daily Trend**")
                    if "sla_pct" in hist.columns and len(hist) >= 2:
                        fig = mini_bar(hist["sla_pct"].tolist(),
                                       [str(d) for d in hist["date"]],
                                       color=color, height=200)
                        # Add target line
                        if sla_target:
                            fig.add_hline(y=sla_target, line_dash="dot",
                                          line_color="#F59E0B",
                                          annotation_text=f"Target {sla_target}%")
                        st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.markdown("**Daily Volume**")
                    if "offered" in hist.columns and len(hist) >= 2:
                        fig = go.Figure()
                        fig.add_trace(go.Bar(x=hist["date"].astype(str),
                            y=hist.get("answered", pd.Series()),
                            name="Answered", marker_color="#10B981"))
                        fig.add_trace(go.Bar(x=hist["date"].astype(str),
                            y=hist.get("abandoned", pd.Series()),
                            name="Abandoned", marker_color="#EF4444"))
                        fig.update_layout(barmode="stack")
                        st.plotly_chart(chart_layout(fig), use_container_width=True)

            display_cols = [c for c in [
                "date", "offered", "ans_within_sla", "answered", "abandoned",
                "sla_pct", "abd_pct", "aht_sec", "qa_score",
                "util_pct", "occ_pct", "present", "absent", "late",
                "ins_renewals", "ins_new", "ins_conversion", "notes"
            ] if c in hist.columns]
            disp = hist[display_cols].copy()
            disp.columns = [c.replace("_", " ").title() for c in disp.columns]
            st.dataframe(disp, use_container_width=True, height=280)
            st.download_button("⬇️ Export My Data",
                               hist.to_csv(index=False).encode(),
                               f"{project_id}_history.csv", "text/csv")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔒 Logout"):
        for k in ["role", "project_id"]:
            st.session_state.pop(k, None)
        st.rerun()


# ──────────────────────────────────────────────────────────────
# 8.  PM DASHBOARD
# ──────────────────────────────────────────────────────────────
def show_pm_dashboard():
    st.markdown(f"""
    <div class="top-bar">
        <h1>📊 Operations Command Center</h1>
        <div><span class="badge">👤 {PM_NAME} · {date.today().strftime('%d %b %Y')}</span></div>
    </div>""", unsafe_allow_html=True)

    data      = load_data()
    today_str = str(date.today())
    today     = date.today()

    tab_today, tab_mtd, tab_trends, tab_all = st.tabs([
        "🗓️  Today's Overview",
        "📊  MTD Summary",
        "📈  Trends (30 Days)",
        "📋  All Submissions",
    ])

    # ════════════════════════════════════════════════════════
    # TAB A — TODAY
    # ════════════════════════════════════════════════════════
    with tab_today:
        st.markdown('<div class="section-title">Today\'s Status — All Projects</div>',
                    unsafe_allow_html=True)

        # Global summary: attendance across all projects
        submitted_count = sum(1 for pid in PROJECTS if get_entry(data, pid, today_str))
        total_present   = sum(get_entry(data, pid, today_str).get("present", 0)
                              for pid in PROJECTS)
        total_agents    = sum(get_entry(data, pid, today_str).get("total_agents", 0)
                              for pid in PROJECTS)
        att_pct = (total_present / total_agents * 100) if total_agents else None

        g1, g2, g3 = st.columns(3)
        with g1:
            kpi_card("Reports Submitted", f"{submitted_count}/{len(PROJECTS)}",
                     "today", "#4F46E5")
        with g2:
            kpi_card("Overall Attendance",
                     f"{att_pct:.1f}%" if att_pct is not None else "—",
                     f"{total_present} present of {total_agents} total", "#10B981")
        with g3:
            pending = [PROJECTS[pid]["name"] for pid in PROJECTS
                       if not get_entry(data, pid, today_str)]
            kpi_card("Pending Submissions", str(len(pending)),
                     ", ".join(pending[:3]) + ("…" if len(pending) > 3 else ""),
                     "#EF4444" if pending else "#10B981")

        st.markdown("<br>", unsafe_allow_html=True)

        # Per-project cards
        for pid, proj in PROJECTS.items():
            entry        = get_entry(data, pid, today_str)
            color        = proj["color"]
            is_insurance = proj["type"] == "insurance"
            sla_target   = proj.get("sla_target")
            sla_sec      = proj.get("sla_sec")
            has_data     = bool(entry)
            submitted_at = entry.get("submitted_at", "")

            st.markdown(f"""
            <div class="proj-card" style="border-left:4px solid {color};">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <div class="proj-title">{proj['name']}
                            {"" if is_insurance else
                             f'<span class="sla-rule-tag">SLA: {sla_target}% / {sla_sec}s</span>'}
                        </div>
                        <div class="proj-manager">OM: {proj['manager']}
                            {"&nbsp;·&nbsp;Submitted: " + submitted_at if submitted_at else ""}
                        </div>
                    </div>
                    <div>{"<span class='pill pill-green'>✓ Submitted</span>"
                          if has_data else "<span class='pill pill-red'>⚠ Pending</span>"}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if has_data:
                if not is_insurance:
                    # Compute today's SLA pill vs target
                    today_sla = entry.get("sla_pct")
                    today_abd = entry.get("abd_pct")

                    cells = st.columns(9)
                    metrics = [
                        ("Offered",    str(entry.get("offered", "—"))),
                        ("Answered",   str(entry.get("answered", "—"))),
                        ("Ans/SLA",    str(entry.get("ans_within_sla", "—"))),
                        ("Abandoned",  str(entry.get("abandoned", "—"))),
                        ("AHT",        f"{entry.get('aht_sec','—')}s"),
                        ("QA %",       f"{entry.get('qa_score','—')}%"),
                        ("Util %",     f"{entry.get('util_pct','—')}%"),
                        ("Occ %",      f"{entry.get('occ_pct','—')}%"),
                        ("Attendance", f"{entry.get('present','—')}/{entry.get('total_agents','—')}"),
                    ]
                    for col_w, (lbl, val) in zip(cells, metrics):
                        with col_w:
                            st.markdown(metric_cell(lbl, val), unsafe_allow_html=True)

                    # SLA & ABD coloured pills on second row
                    st.markdown(f"""
                    <div style="display:flex;gap:12px;margin-top:10px;flex-wrap:wrap;">
                        <div><span style="font-size:10px;color:#475569;
                                          text-transform:uppercase;">Daily SLA</span>&nbsp;
                            {sla_pill_mtd(today_sla, sla_target)}
                        </div>
                        <div><span style="font-size:10px;color:#475569;
                                          text-transform:uppercase;">Daily ABD</span>&nbsp;
                            {abd_pill(today_abd)}
                        </div>
                        <div><span style="font-size:10px;color:#475569;
                                          text-transform:uppercase;">Attendance</span>&nbsp;
                            {attendance_pill(entry.get('present',0), entry.get('total_agents',0))}
                        </div>
                    </div>""", unsafe_allow_html=True)

                else:
                    # Insurance card
                    ic = st.columns(4)
                    ins_metrics = [
                        ("Renewals Closed",  entry.get("ins_renewals", "—")),
                        ("New Business",     entry.get("ins_new", "—")),
                        ("Conversion %",     f"{entry.get('ins_conversion','—')}%"),
                        ("Attendance",       f"{entry.get('present','—')}/{entry.get('total_agents','—')}"),
                    ]
                    for col_w, (lbl, val) in zip(ic, ins_metrics):
                        with col_w:
                            st.markdown(metric_cell(f"🛡️ {lbl}", val, "#F59E0B"),
                                        unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="margin-top:10px;">
                        {attendance_pill(entry.get('present',0), entry.get('total_agents',0))}
                    </div>""", unsafe_allow_html=True)

                if entry.get("notes"):
                    st.markdown(f"""
                    <div style="margin-top:12px;padding:10px;background:#0A1628;
                                border-radius:8px;font-size:12px;color:#64748B;
                                border-left:3px solid {color};">
                        📝 {entry['notes']}</div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div style="color:#334155;font-size:13px;
                               font-style:italic;padding:8px 0;">
                    No data submitted yet for today.</div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # TAB B — MTD SUMMARY
    # ════════════════════════════════════════════════════════
    with tab_mtd:
        st.markdown(f'<div class="section-title">Month-to-Date Summary — '
                    f'{today.strftime("%B %Y")}</div>', unsafe_allow_html=True)

        for pid, proj in PROJECTS.items():
            is_insurance = proj["type"] == "insurance"
            color        = proj["color"]
            sla_target   = proj.get("sla_target")
            sla_sec      = proj.get("sla_sec")
            mtd_df       = get_mtd_history(data, pid)

            st.markdown(f"""
            <div class="proj-card" style="border-left:4px solid {color};">
                <div class="proj-title">{proj['name']}
                    {"" if is_insurance else
                     f'<span class="sla-rule-tag">Target: {sla_target}% / {sla_sec}s</span>'}
                </div>
                <div class="proj-manager">OM: {proj['manager']} · {len(mtd_df)} days submitted</div>
            """, unsafe_allow_html=True)

            if mtd_df.empty:
                st.markdown('<div style="color:#334155;font-size:13px;'
                            'font-style:italic;">No MTD data yet.</div>',
                            unsafe_allow_html=True)
            else:
                if not is_insurance:
                    mtd_sla = calc_mtd_sla(mtd_df)
                    mtd_abd = calc_mtd_abd(mtd_df)
                    total_offered  = int(mtd_df.get("offered", pd.Series()).fillna(0).sum())
                    total_answered = int(mtd_df.get("answered", pd.Series()).fillna(0).sum())
                    total_abn      = int(mtd_df.get("abandoned", pd.Series()).fillna(0).sum())
                    avg_aht        = mtd_df.get("aht_sec", pd.Series()).mean()
                    avg_qa         = mtd_df.get("qa_score", pd.Series()).mean()
                    total_present  = int(mtd_df.get("present", pd.Series()).fillna(0).sum())
                    total_ag       = int(mtd_df.get("total_agents", pd.Series()).fillna(0).sum())
                    att_rate       = (total_present / total_ag * 100) if total_ag else None

                    cols = st.columns(7)
                    items = [
                        ("MTD Offered",   f"{total_offered:,}"),
                        ("MTD Answered",  f"{total_answered:,}"),
                        ("MTD Abandoned", f"{total_abn:,}"),
                        ("Avg AHT",       f"{avg_aht:.0f}s" if not pd.isna(avg_aht) else "—"),
                        ("Avg QA %",      f"{avg_qa:.1f}%" if not pd.isna(avg_qa) else "—"),
                        ("Attendance",    f"{att_rate:.1f}%" if att_rate else "—"),
                        ("Days",          str(len(mtd_df))),
                    ]
                    for col_w, (lbl, val) in zip(cols, items):
                        with col_w:
                            st.markdown(metric_cell(lbl, val), unsafe_allow_html=True)

                    st.markdown(f"""
                    <div style="display:flex;gap:16px;margin-top:12px;flex-wrap:wrap;">
                        <div><span style="font-size:10px;color:#475569;text-transform:uppercase;">
                            MTD SLA %</span>&nbsp;{sla_pill_mtd(mtd_sla, sla_target)}</div>
                        <div><span style="font-size:10px;color:#475569;text-transform:uppercase;">
                            MTD ABD %</span>&nbsp;{abd_pill(mtd_abd)}</div>
                    </div>""", unsafe_allow_html=True)

                else:
                    total_ren  = int(mtd_df.get("ins_renewals", pd.Series()).fillna(0).sum())
                    total_new  = int(mtd_df.get("ins_new",      pd.Series()).fillna(0).sum())
                    avg_conv   = mtd_df.get("ins_conversion", pd.Series()).mean()
                    total_pres = int(mtd_df.get("present",      pd.Series()).fillna(0).sum())
                    total_ag   = int(mtd_df.get("total_agents", pd.Series()).fillna(0).sum())
                    att_rate   = (total_pres / total_ag * 100) if total_ag else None

                    cols = st.columns(4)
                    items = [
                        ("MTD Renewals",    f"{total_ren:,}"),
                        ("MTD New Business", f"{total_new:,}"),
                        ("Avg Conversion %", f"{avg_conv:.1f}%" if not pd.isna(avg_conv) else "—"),
                        ("Attendance",       f"{att_rate:.1f}%" if att_rate else "—"),
                    ]
                    for col_w, (lbl, val) in zip(cols, items):
                        with col_w:
                            st.markdown(metric_cell(f"🛡️ {lbl}", val, "#F59E0B"),
                                        unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # TAB C — TRENDS
    # ════════════════════════════════════════════════════════
    with tab_trends:
        st.markdown('<div class="section-title">30-Day Trends — Per Project</div>',
                    unsafe_allow_html=True)

        selected_pid = st.selectbox("Select Project", options=list(PROJECTS.keys()),
                                    format_func=lambda x: PROJECTS[x]["name"])
        proj         = PROJECTS[selected_pid]
        color        = proj["color"]
        is_insurance = proj["type"] == "insurance"
        sla_target   = proj.get("sla_target")
        hist         = get_project_history(data, selected_pid, days=30)

        if hist.empty:
            st.info(f"No historical data for **{proj['name']}** yet.")
        else:
            if not is_insurance:
                mtd_df  = get_mtd_history(data, selected_pid)
                mtd_sla = calc_mtd_sla(mtd_df)
                mtd_abd = calc_mtd_abd(mtd_df)

                k1,k2,k3,k4 = st.columns(4)
                with k1:
                    kpi_card("MTD SLA %",
                             f"{mtd_sla:.1f}%" if mtd_sla is not None else "—",
                             f"Target: {sla_target}%", color)
                with k2:
                    kpi_card("MTD ABD %",
                             f"{mtd_abd:.1f}%" if mtd_abd is not None else "—",
                             "Month to date", "#EF4444")
                with k3:
                    kpi_card("Avg QA %",
                             f"{hist['qa_score'].mean():.1f}%" if "qa_score" in hist else "—",
                             "30-day avg", "#10B981")
                with k4:
                    kpi_card("Total Offered",
                             f"{int(hist['offered'].sum()):,}" if "offered" in hist else "—",
                             "30 days", "#0EA5E9")

                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Daily SLA % with Target**")
                    fig = mini_bar(hist["sla_pct"].tolist() if "sla_pct" in hist.columns else [],
                                   [str(d) for d in hist["date"]], color=color, height=220)
                    if sla_target:
                        fig.add_hline(y=sla_target, line_dash="dot", line_color="#F59E0B",
                                      annotation_text=f"Target {sla_target}%")
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.markdown("**Daily Call Volume**")
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=hist["date"].astype(str),
                        y=hist.get("answered", pd.Series()), name="Answered",
                        marker_color="#10B981"))
                    fig.add_trace(go.Bar(x=hist["date"].astype(str),
                        y=hist.get("abandoned", pd.Series()), name="Abandoned",
                        marker_color="#EF4444"))
                    fig.update_layout(barmode="stack")
                    st.plotly_chart(chart_layout(fig), use_container_width=True)

                c3, c4 = st.columns(2)
                with c3:
                    st.markdown("**QA % over time**")
                    fig = mini_bar(hist["qa_score"].tolist() if "qa_score" in hist.columns else [],
                                   [str(d) for d in hist["date"]], color="#10B981", height=220)
                    st.plotly_chart(fig, use_container_width=True)
                with c4:
                    st.markdown("**Attendance — Present vs Absent**")
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=hist["date"].astype(str),
                        y=hist.get("present", pd.Series()), name="Present",
                        marker_color="#4F46E5"))
                    fig.add_trace(go.Bar(x=hist["date"].astype(str),
                        y=hist.get("absent", pd.Series()), name="Absent",
                        marker_color="#EF4444"))
                    fig.update_layout(barmode="group")
                    st.plotly_chart(chart_layout(fig), use_container_width=True)
            else:
                st.markdown('<div class="section-title">🛡️ Insurance KPI Trends</div>',
                            unsafe_allow_html=True)
                ia, ib = st.columns(2)
                with ia:
                    st.markdown("**Renewals vs New Business**")
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=hist["date"].astype(str),
                        y=hist.get("ins_renewals", pd.Series()),
                        name="Renewals", marker_color="#F59E0B"))
                    fig.add_trace(go.Bar(x=hist["date"].astype(str),
                        y=hist.get("ins_new", pd.Series()),
                        name="New Business", marker_color="#EF4444"))
                    fig.update_layout(barmode="group")
                    st.plotly_chart(chart_layout(fig), use_container_width=True)
                with ib:
                    st.markdown("**Conversion Rate %**")
                    fig = mini_bar(
                        hist["ins_conversion"].tolist() if "ins_conversion" in hist.columns else [],
                        [str(d) for d in hist["date"]], color="#F59E0B", height=220)
                    st.plotly_chart(fig, use_container_width=True)

    # ════════════════════════════════════════════════════════
    # TAB D — ALL SUBMISSIONS
    # ════════════════════════════════════════════════════════
    with tab_all:
        st.markdown('<div class="section-title">All Submissions — Export</div>',
                    unsafe_allow_html=True)
        date_range = st.slider("Days to show", 1, 90, 30)
        rows = []
        for pid, proj in PROJECTS.items():
            hist = get_project_history(data, pid, days=date_range)
            if not hist.empty:
                hist.insert(0, "Project", proj["name"])
                hist.insert(1, "Manager", proj["manager"])
                rows.append(hist)

        if rows:
            all_df = pd.concat(rows, ignore_index=True)
            all_df.columns = [c.replace("_"," ").title() for c in all_df.columns]
            st.dataframe(all_df, use_container_width=True, height=450)
            st.download_button("⬇️ Export All Data as CSV",
                               all_df.to_csv(index=False).encode(),
                               f"all_projects_{date.today()}.csv", "text/csv")
        else:
            st.info("No data submitted yet across any project.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔒 Logout"):
        for k in ["role","project_id"]:
            st.session_state.pop(k, None)
        st.rerun()


# ──────────────────────────────────────────────────────────────
# 9.  MAIN ROUTER
# ──────────────────────────────────────────────────────────────
inject_css()

role = st.session_state.get("role")
if role == "pm":
    show_pm_dashboard()
elif role == "manager":
    show_manager_form(st.session_state["project_id"])
else:
    show_login()
