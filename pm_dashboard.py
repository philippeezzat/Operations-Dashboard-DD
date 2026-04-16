"""
Project Manager Operations Dashboard
======================================
A multi-project Streamlit web app where:
  - Each Operation Manager logs in with their PIN and submits daily KPIs
  - The Project Manager logs in with the master PIN to see ALL projects

HOW TO RUN
----------
  pip install streamlit plotly pandas
  streamlit run pm_dashboard.py

SHARING WITH YOUR TEAM
-----------------------
  Option A (LAN):  Run on your PC, share your local IP → http://YOUR_IP:8501
  Option B (Cloud): Deploy free on https://share.streamlit.io

CUSTOMISE
---------
  - Edit the PROJECTS dict below to add/rename/remove projects
  - Change PINs in the PROJECTS dict and PM_PIN
  - Add more KPI fields in the FORM_FIELDS section
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
# 1.  CONFIGURATION  ← EDIT THIS SECTION
# ──────────────────────────────────────────────────────────────
PM_PIN = "9999"          # Your master PIN to see ALL projects
PM_NAME = "Project Manager"

PROJECTS = {
    "P001": {
        "name":    "Call Center — GPSSA",
        "manager": "Yehia",
        "pin":     "1001",
        "type":    "callcenter",
        "color":   "#4F46E5",
    },
    "P002": {
        "name":    "Call Center — Nafis",
        "manager": "Ahmed",
        "pin":     "1002",
        "type":    "callcenter",
        "color":   "#0EA5E9",
    },
    "P003": {
        "name":    "Call Center — Fidelity",
        "manager": "Ephraim",
        "pin":     "1003",
        "type":    "callcenter",
        "color":   "#10B981",
    },
    "P004": {
        "name":    "Call Center — Parkin",
        "manager": "Assim",
        "pin":     "1004",
        "type":    "callcenter",
        "color":   "#F59E0B",
    },
    "P005": {
        "name":    "Call Center — DREC",
        "manager": "Mohamed Khatib",
        "pin":     "1005",
        "type":    "callcenter",
        "color":   "#8B5CF6",
    },
    "P006": {
        "name":    "Call Center — Zeta",
        "manager": "Layla",
        "pin":     "1006",
        "type":    "callcenter",
        "color":   "#EC4899",
    },
    "P007": {
        "name":    "Insurance — ADNIC",
        "manager": "Mohamed Khatib",
        "pin":     "1007",
        "type":    "insurance",
        "color":   "#EF4444",
    },
}

# ──────────────────────────────────────────────────────────────
# 2.  DATA STORAGE  (JSON flat-file — no database needed)
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


# ──────────────────────────────────────────────────────────────
# 3.  STYLING
# ──────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* Background */
    .stApp {
        background: #0A0E1A;
        color: #E2E8F0;
    }

    /* Hide default streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }

    /* Top nav bar */
    .top-bar {
        background: linear-gradient(90deg, #0F1629 0%, #141B2E 100%);
        border-bottom: 1px solid #1E2D4A;
        padding: 16px 32px;
        margin: -1rem -1rem 2rem -1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .top-bar h1 {
        font-family: 'Syne', sans-serif;
        font-size: 22px;
        font-weight: 800;
        color: #F8FAFC;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .top-bar .badge {
        font-size: 12px;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
        background: #1E3A5F;
        color: #60A5FA;
        letter-spacing: 0.5px;
    }

    /* Login card */
    .login-wrap {
        max-width: 420px;
        margin: 60px auto;
        background: #0F1629;
        border: 1px solid #1E2D4A;
        border-radius: 16px;
        padding: 40px;
    }
    .login-wrap h2 {
        font-family: 'Syne', sans-serif;
        font-size: 26px;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 4px;
    }
    .login-wrap p { color: #64748B; font-size: 14px; margin-bottom: 28px; }

    /* KPI cards */
    .kpi-card {
        background: #0F1629;
        border: 1px solid #1E2D4A;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        transition: border-color 0.2s;
    }
    .kpi-card:hover { border-color: #2D4A7A; }
    .kpi-label {
        font-size: 11px;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-family: 'Syne', sans-serif;
        font-size: 28px;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.1;
    }
    .kpi-sub { font-size: 12px; color: #475569; margin-top: 4px; }

    /* Project card in PM view */
    .proj-card {
        background: #0F1629;
        border: 1px solid #1E2D4A;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 16px;
        position: relative;
        overflow: hidden;
    }
    .proj-card::before {
        content: '';
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 4px;
        border-radius: 4px 0 0 4px;
    }
    .proj-title {
        font-family: 'Syne', sans-serif;
        font-size: 15px;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 4px;
    }
    .proj-manager { font-size: 12px; color: #64748B; margin-bottom: 16px; }

    /* Status pill */
    .pill {
        display: inline-block;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
        letter-spacing: 0.3px;
    }
    .pill-green  { background: #052E16; color: #4ADE80; }
    .pill-yellow { background: #2D1B00; color: #FCD34D; }
    .pill-red    { background: #2D0707; color: #F87171; }
    .pill-grey   { background: #1E293B; color: #94A3B8; }

    /* Section headers */
    .section-title {
        font-family: 'Syne', sans-serif;
        font-size: 18px;
        font-weight: 700;
        color: #F8FAFC;
        margin: 28px 0 16px;
        padding-bottom: 10px;
        border-bottom: 1px solid #1E2D4A;
    }

    /* Form container */
    .form-section {
        background: #0F1629;
        border: 1px solid #1E2D4A;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 20px;
    }
    .form-section h4 {
        font-family: 'Syne', sans-serif;
        font-size: 15px;
        font-weight: 700;
        color: #60A5FA;
        margin-bottom: 16px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Streamlit widget overrides */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div,
    .stDateInput > div > div > input {
        background: #141B2E !important;
        border: 1px solid #1E2D4A !important;
        border-radius: 8px !important;
        color: #E2E8F0 !important;
    }
    .stButton > button {
        background: #4F46E5 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        width: 100%;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stButton > button:hover {
        background: #4338CA !important;
        transform: translateY(-1px);
    }
    div[data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
    }
    .stSuccess {
        background: #052E16 !important;
        color: #4ADE80 !important;
        border: 1px solid #166534 !important;
        border-radius: 8px !important;
    }
    .stWarning {
        background: #2D1B00 !important;
        color: #FCD34D !important;
        border: 1px solid #92400E !important;
        border-radius: 8px !important;
    }
    label { color: #94A3B8 !important; font-size: 13px !important; }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        color: #64748B;
    }
    .stTabs [aria-selected="true"] { color: #60A5FA !important; }
    </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# 4.  HELPER WIDGETS
# ──────────────────────────────────────────────────────────────
def kpi_card(label, value, sub="", color="#4F46E5"):
    st.markdown(f"""
    <div class="kpi-card" style="border-top: 2px solid {color};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)


def sla_pill(val):
    if val is None or val == "":
        return '<span class="pill pill-grey">No Data</span>'
    try:
        v = float(val)
        if v >= 80:   return f'<span class="pill pill-green">✓ {v:.1f}%</span>'
        if v >= 65:   return f'<span class="pill pill-yellow">⚠ {v:.1f}%</span>'
        return f'<span class="pill pill-red">✗ {v:.1f}%</span>'
    except Exception:
        return '<span class="pill pill-grey">—</span>'


def sparkline(values, color="#4F46E5", height=60):
    if not values or len(values) < 2:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=values, mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=color.replace(")", ", 0.1)").replace("rgb", "rgba")
            if "rgb" in color else color + "18",
    ))
    fig.update_layout(
        height=height, margin=dict(t=0,b=0,l=0,r=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return fig


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


# ──────────────────────────────────────────────────────────────
# 5.  LOGIN SCREEN
# ──────────────────────────────────────────────────────────────
def show_login():
    st.markdown("""
    <div style="text-align:center; padding: 48px 0 24px;">
        <div style="font-size:48px; margin-bottom:8px;">📊</div>
        <h1 style="font-family:'Syne',sans-serif; font-size:32px; font-weight:800;
                   color:#F8FAFC; margin:0;">Operations Command Center</h1>
        <p style="color:#475569; margin-top:8px; font-size:15px;">
            Enter your PIN to access your dashboard
        </p>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 1.2, 1])[1]
    with col:
        with st.form("login_form"):
            pin = st.text_input("Your PIN", type="password",
                                placeholder="Enter 4-digit PIN")
            submitted = st.form_submit_button("🔐  Access Dashboard")

        if submitted:
            # Check PM
            if pin == PM_PIN:
                st.session_state["role"]       = "pm"
                st.session_state["project_id"] = None
                st.rerun()
            # Check each manager
            for pid, proj in PROJECTS.items():
                if pin == proj["pin"]:
                    st.session_state["role"]       = "manager"
                    st.session_state["project_id"] = pid
                    st.rerun()
            st.error("❌ Invalid PIN. Please try again.")

        st.markdown("""
        <div style="text-align:center; margin-top:20px; color:#334155; font-size:12px;">
            Contact your Project Manager if you've forgotten your PIN
        </div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# 6.  MANAGER DATA ENTRY FORM
# ──────────────────────────────────────────────────────────────
def show_manager_form(project_id: str):
    proj = PROJECTS[project_id]
    color = proj["color"]
    is_insurance = proj["type"] == "insurance"

    # Top bar
    st.markdown(f"""
    <div class="top-bar">
        <h1>📋 {proj['name']}</h1>
        <div>
            <span class="badge">OM: {proj['manager']}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    data = load_data()

    # Tabs: Submit | History
    tab_submit, tab_history = st.tabs(["📝  Submit Daily Report", "📅  My History"])

    # ── SUBMIT TAB ────────────────────────────────────────────
    with tab_submit:
        st.markdown(f"""
        <div class="section-title">Daily KPI Entry
            <span style="font-size:13px; font-weight:400; color:#475569;
                         margin-left:12px;">Fill in today's numbers</span>
        </div>""", unsafe_allow_html=True)

        today_str = str(date.today())
        existing  = get_entry(data, project_id, today_str)
        if existing:
            st.success(f"✅ You've already submitted data for today ({today_str}). "
                       "You can re-submit to update.")

        with st.form("daily_entry"):
            # ── Date ──────────────────────────────────────────
            entry_date = st.date_input("📅 Report Date", value=date.today(),
                                        max_value=date.today())

            # ── Call Center KPIs ──────────────────────────────
            st.markdown('<div class="form-section"><h4>📞 Call Center KPIs</h4>',
                        unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                offered   = st.number_input("Offered Calls",   min_value=0, step=1,
                                             value=int(existing.get("offered", 0)))
                answered  = st.number_input("Answered Calls",  min_value=0, step=1,
                                             value=int(existing.get("answered", 0)))
                abandoned = st.number_input("Abandoned Calls", min_value=0, step=1,
                                             value=int(existing.get("abandoned", 0)))
            with c2:
                sla_pct   = st.number_input("SLA %",    min_value=0.0, max_value=100.0,
                                             step=0.1, format="%.1f",
                                             value=float(existing.get("sla_pct", 0.0)))
                abd_pct   = st.number_input("ABD %",    min_value=0.0, max_value=100.0,
                                             step=0.1, format="%.1f",
                                             value=float(existing.get("abd_pct", 0.0)))
                aht_sec   = st.number_input("AHT (seconds)", min_value=0, step=1,
                                             value=int(existing.get("aht_sec", 0)))
            with c3:
                qa_score  = st.number_input("QA Score %",      min_value=0.0, max_value=100.0,
                                             step=0.1, format="%.1f",
                                             value=float(existing.get("qa_score", 0.0)))
                util_pct  = st.number_input("Utilization %",   min_value=0.0, max_value=100.0,
                                             step=0.1, format="%.1f",
                                             value=float(existing.get("util_pct", 0.0)))
                occ_pct   = st.number_input("Occupancy %",     min_value=0.0, max_value=100.0,
                                             step=0.1, format="%.1f",
                                             value=float(existing.get("occ_pct", 0.0)))
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Attendance ────────────────────────────────────
            st.markdown('<div class="form-section"><h4>👥 Attendance & Discipline</h4>',
                        unsafe_allow_html=True)
            a1, a2, a3 = st.columns(3)
            with a1:
                total_agents  = st.number_input("Total Agents",   min_value=0, step=1,
                                                 value=int(existing.get("total_agents", 0)))
                present       = st.number_input("Present",        min_value=0, step=1,
                                                 value=int(existing.get("present", 0)))
            with a2:
                absent        = st.number_input("Absent",         min_value=0, step=1,
                                                 value=int(existing.get("absent", 0)))
                late           = st.number_input("Late (count)",   min_value=0, step=1,
                                                 value=int(existing.get("late", 0)))
            with a3:
                leave          = st.number_input("On Leave",       min_value=0, step=1,
                                                 value=int(existing.get("leave", 0)))
                lateness_min   = st.number_input("Avg Lateness (min)", min_value=0, step=1,
                                                  value=int(existing.get("lateness_min", 0)))
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Insurance-only KPIs ───────────────────────────
            ins_offered = ins_renewals = ins_new = ins_conversion = 0.0
            if is_insurance:
                st.markdown('<div class="form-section"><h4>🛡️ Insurance KPIs</h4>',
                            unsafe_allow_html=True)
                i1, i2, i3, i4 = st.columns(4)
                with i1:
                    ins_offered    = st.number_input("Policies Offered",   min_value=0, step=1,
                                                      value=int(existing.get("ins_offered", 0)))
                with i2:
                    ins_renewals   = st.number_input("Renewals Closed",    min_value=0, step=1,
                                                      value=int(existing.get("ins_renewals", 0)))
                with i3:
                    ins_new        = st.number_input("New Business Closed", min_value=0, step=1,
                                                      value=int(existing.get("ins_new", 0)))
                with i4:
                    ins_conversion = st.number_input("Conversion Rate %",  min_value=0.0,
                                                      max_value=100.0, step=0.1, format="%.1f",
                                                      value=float(existing.get("ins_conversion", 0.0)))
                st.markdown('</div>', unsafe_allow_html=True)

            # ── Notes ─────────────────────────────────────────
            notes = st.text_area("📝 Notes / Issues (optional)",
                                  value=existing.get("notes", ""),
                                  placeholder="Any issues, highlights or context for today...")

            submitted = st.form_submit_button("💾  Submit Daily Report", use_container_width=True)

        if submitted:
            entry = {
                "offered": offered, "answered": answered, "abandoned": abandoned,
                "sla_pct": sla_pct, "abd_pct": abd_pct, "aht_sec": aht_sec,
                "qa_score": qa_score, "util_pct": util_pct, "occ_pct": occ_pct,
                "total_agents": total_agents, "present": present,
                "absent": absent, "late": late, "leave": leave,
                "lateness_min": lateness_min, "notes": notes,
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            if is_insurance:
                entry.update({
                    "ins_offered": ins_offered, "ins_renewals": ins_renewals,
                    "ins_new": ins_new, "ins_conversion": ins_conversion,
                })
            save_entry(project_id, str(entry_date), entry)
            st.success(f"✅ Report submitted successfully for {entry_date}!")
            st.balloons()

    # ── HISTORY TAB ───────────────────────────────────────────
    with tab_history:
        st.markdown('<div class="section-title">My Submission History (Last 30 Days)</div>',
                    unsafe_allow_html=True)
        hist = get_project_history(data, project_id, days=30)
        if hist.empty:
            st.info("No data submitted yet. Use the Submit tab to add your first report.")
        else:
            # Mini KPI trend charts
            if "sla_pct" in hist.columns and len(hist) >= 2:
                col_s, col_a, col_q = st.columns(3)
                with col_s:
                    st.markdown("**SLA % Trend**")
                    fig = sparkline(hist["sla_pct"].tolist(), color=color)
                    if fig: st.plotly_chart(fig, use_container_width=True)
                with col_a:
                    st.markdown("**ABD % Trend**")
                    fig = sparkline(hist["abd_pct"].tolist(), color="#EF4444")
                    if fig: st.plotly_chart(fig, use_container_width=True)
                with col_q:
                    st.markdown("**QA Score Trend**")
                    fig = sparkline(hist["qa_score"].tolist(), color="#10B981")
                    if fig: st.plotly_chart(fig, use_container_width=True)

            # Raw history table
            display_cols = [c for c in [
                "date","offered","answered","abandoned","sla_pct","abd_pct",
                "aht_sec","qa_score","util_pct","occ_pct","present","absent",
                "late","notes"
            ] if c in hist.columns]
            disp = hist[display_cols].copy()
            disp.columns = [c.replace("_", " ").title() for c in disp.columns]
            st.dataframe(disp, use_container_width=True, height=300)
            st.download_button("⬇️ Export My Data",
                               hist.to_csv(index=False).encode(),
                               f"{project_id}_history.csv", "text/csv")

    # Logout
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔒 Logout", use_container_width=False):
        for key in ["role","project_id"]:
            st.session_state.pop(key, None)
        st.rerun()


# ──────────────────────────────────────────────────────────────
# 7.  PM MASTER DASHBOARD
# ──────────────────────────────────────────────────────────────
def show_pm_dashboard():
    st.markdown(f"""
    <div class="top-bar">
        <h1>📊 Operations Command Center</h1>
        <div>
            <span class="badge">👤 {PM_NAME}  ·  {date.today().strftime('%d %b %Y')}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    data = load_data()
    today_str = str(date.today())

    # ── Tabs ──────────────────────────────────────────────────
    tab_today, tab_trends, tab_all = st.tabs([
        "🗓️  Today's Overview",
        "📈  Trends (30 Days)",
        "📋  All Submissions",
    ])

    # ════════════════════════════════════════════════════════
    # TAB A — TODAY'S OVERVIEW
    # ════════════════════════════════════════════════════════
    with tab_today:
        st.markdown('<div class="section-title">Today\'s Status — All Projects</div>',
                    unsafe_allow_html=True)

        # Summary pills row
        submitted_today = sum(
            1 for pid in PROJECTS if get_entry(data, pid, today_str)
        )
        col_s, col_p, col_t = st.columns(3)
        with col_s: kpi_card("Reports Submitted", f"{submitted_today}/{len(PROJECTS)}",
                              "today", "#4F46E5")
        with col_p:
            all_sla = [get_entry(data, pid, today_str).get("sla_pct")
                       for pid in PROJECTS
                       if get_entry(data, pid, today_str).get("sla_pct") is not None]
            avg_sla = sum(all_sla) / len(all_sla) if all_sla else None
            kpi_card("Avg SLA % Today",
                     f"{avg_sla:.1f}%" if avg_sla is not None else "—",
                     "across all projects", "#10B981")
        with col_t:
            all_vol = [get_entry(data, pid, today_str).get("offered", 0)
                       for pid in PROJECTS]
            kpi_card("Total Offered Calls", f"{sum(all_vol):,}", "all projects", "#0EA5E9")

        st.markdown("<br>", unsafe_allow_html=True)

        # Per-project cards
        for pid, proj in PROJECTS.items():
            entry = get_entry(data, pid, today_str)
            color = proj["color"]

            has_data = bool(entry)
            submitted_at = entry.get("submitted_at", "")

            st.markdown(f"""
            <div class="proj-card" style="border-left: 4px solid {color};">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div class="proj-title">{proj['name']}</div>
                        <div class="proj-manager">OM: {proj['manager']}
                            {"&nbsp;·&nbsp;Submitted: " + submitted_at if submitted_at else ""}
                        </div>
                    </div>
                    <div>
                        {"<span class='pill pill-green'>✓ Submitted</span>" if has_data
                         else "<span class='pill pill-red'>⚠ Pending</span>"}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if has_data:
                kc = st.columns(8)
                metrics = [
                    ("Offered",     entry.get("offered", "—")),
                    ("Answered",    entry.get("answered", "—")),
                    ("Abandoned",   entry.get("abandoned", "—")),
                    ("SLA %",       f"{entry.get('sla_pct','—')}%"
                                    if entry.get('sla_pct') is not None else "—"),
                    ("ABD %",       f"{entry.get('abd_pct','—')}%"
                                    if entry.get('abd_pct') is not None else "—"),
                    ("AHT",         f"{entry.get('aht_sec','—')}s"
                                    if entry.get('aht_sec') is not None else "—"),
                    ("QA %",        f"{entry.get('qa_score','—')}%"
                                    if entry.get('qa_score') is not None else "—"),
                    ("Attendance",  f"{entry.get('present','—')}/{entry.get('total_agents','—')}"),
                ]
                for col_w, (lbl, val) in zip(kc, metrics):
                    with col_w:
                        st.markdown(f"""
                        <div style="text-align:center;">
                          <div style="font-size:10px;color:#475569;text-transform:uppercase;
                                      letter-spacing:0.5px;">{lbl}</div>
                          <div style="font-family:'Syne',sans-serif;font-size:18px;
                                      font-weight:700;color:#F8FAFC;">{val}</div>
                        </div>""", unsafe_allow_html=True)

                # Insurance extras
                if proj["type"] == "insurance" and entry.get("ins_offered"):
                    st.markdown("<br>", unsafe_allow_html=True)
                    ic = st.columns(4)
                    ins_metrics = [
                        ("Policies Offered",  entry.get("ins_offered", "—")),
                        ("Renewals Closed",   entry.get("ins_renewals", "—")),
                        ("New Business",      entry.get("ins_new", "—")),
                        ("Conversion %",      f"{entry.get('ins_conversion','—')}%"),
                    ]
                    for col_w, (lbl, val) in zip(ic, ins_metrics):
                        with col_w:
                            st.markdown(f"""
                            <div style="text-align:center; background:#0A1628;
                                        border-radius:8px; padding:8px;">
                              <div style="font-size:10px;color:#475569;text-transform:uppercase;">
                                  🛡️ {lbl}</div>
                              <div style="font-family:'Syne',sans-serif;font-size:16px;
                                          font-weight:700;color:#F59E0B;">{val}</div>
                            </div>""", unsafe_allow_html=True)

                if entry.get("notes"):
                    st.markdown(f"""
                    <div style="margin-top:12px; padding:10px; background:#0A1628;
                                border-radius:8px; font-size:12px; color:#64748B;
                                border-left:3px solid {color};">
                        📝 {entry['notes']}
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="color:#334155; font-size:13px; font-style:italic;
                             padding: 8px 0;">
                    No data submitted yet for today.
                </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # TAB B — 30-DAY TRENDS
    # ════════════════════════════════════════════════════════
    with tab_trends:
        st.markdown('<div class="section-title">30-Day Trends — Per Project</div>',
                    unsafe_allow_html=True)

        selected_pid = st.selectbox(
            "Select Project",
            options=list(PROJECTS.keys()),
            format_func=lambda x: PROJECTS[x]["name"],
        )
        proj = PROJECTS[selected_pid]
        color = proj["color"]
        hist = get_project_history(data, selected_pid, days=30)

        if hist.empty:
            st.info(f"No historical data for **{proj['name']}** yet.")
        else:
            # KPI summary
            k1,k2,k3,k4 = st.columns(4)
            with k1: kpi_card("Avg SLA %",
                               f"{hist['sla_pct'].mean():.1f}%" if "sla_pct" in hist else "—",
                               "30-day average", color)
            with k2: kpi_card("Total Offered",
                               f"{int(hist['offered'].sum()):,}" if "offered" in hist else "—",
                               "30 days", "#0EA5E9")
            with k3: kpi_card("Avg QA %",
                               f"{hist['qa_score'].mean():.1f}%" if "qa_score" in hist else "—",
                               "30-day average", "#10B981")
            with k4: kpi_card("Avg ABD %",
                               f"{hist['abd_pct'].mean():.1f}%" if "abd_pct" in hist else "—",
                               "30-day average", "#EF4444")

            st.markdown("<br>", unsafe_allow_html=True)

            # Charts
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**SLA % over time**")
                if "sla_pct" in hist.columns:
                    fig = mini_bar(hist["sla_pct"].tolist(),
                                   [str(d) for d in hist["date"].tolist()],
                                   color=color, height=220)
                    st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.markdown("**Daily Call Volume**")
                if "offered" in hist.columns:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=hist["date"].astype(str),
                                         y=hist.get("answered", []),
                                         name="Answered", marker_color="#10B981"))
                    fig.add_trace(go.Bar(x=hist["date"].astype(str),
                                         y=hist.get("abandoned", []),
                                         name="Abandoned", marker_color="#EF4444"))
                    fig.update_layout(barmode="stack", height=220,
                        margin=dict(t=10,b=30,l=30,r=10),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#94A3B8", size=11),
                        legend=dict(orientation="h", yanchor="bottom",
                                    y=1.02, xanchor="right", x=1),
                        xaxis=dict(showgrid=False, tickangle=-30),
                        yaxis=dict(showgrid=True, gridcolor="#1E2D4A"))
                    st.plotly_chart(fig, use_container_width=True)

            c3, c4 = st.columns(2)
            with c3:
                st.markdown("**QA % over time**")
                if "qa_score" in hist.columns:
                    fig = mini_bar(hist["qa_score"].tolist(),
                                   [str(d) for d in hist["date"].tolist()],
                                   color="#10B981", height=220)
                    st.plotly_chart(fig, use_container_width=True)
            with c4:
                st.markdown("**Attendance — Present vs Absent**")
                if "present" in hist.columns:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=hist["date"].astype(str),
                                         y=hist.get("present",[]),
                                         name="Present", marker_color="#4F46E5"))
                    fig.add_trace(go.Bar(x=hist["date"].astype(str),
                                         y=hist.get("absent",[]),
                                         name="Absent", marker_color="#EF4444"))
                    fig.update_layout(barmode="group", height=220,
                        margin=dict(t=10,b=30,l=30,r=10),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#94A3B8", size=11),
                        legend=dict(orientation="h", yanchor="bottom",
                                    y=1.02, xanchor="right", x=1),
                        xaxis=dict(showgrid=False, tickangle=-30),
                        yaxis=dict(showgrid=True, gridcolor="#1E2D4A"))
                    st.plotly_chart(fig, use_container_width=True)

            # Insurance specific
            if proj["type"] == "insurance" and "ins_offered" in hist.columns:
                st.markdown('<div class="section-title">🛡️ Insurance KPI Trends</div>',
                            unsafe_allow_html=True)
                ia, ib = st.columns(2)
                with ia:
                    st.markdown("**Renewals vs New Business**")
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=hist["date"].astype(str),
                                         y=hist.get("ins_renewals",[]),
                                         name="Renewals", marker_color="#F59E0B"))
                    fig.add_trace(go.Bar(x=hist["date"].astype(str),
                                         y=hist.get("ins_new",[]),
                                         name="New Business", marker_color="#EF4444"))
                    fig.update_layout(barmode="group", height=220,
                        margin=dict(t=10,b=30,l=30,r=10),
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#94A3B8",size=11),
                        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),
                        xaxis=dict(showgrid=False,tickangle=-30),
                        yaxis=dict(showgrid=True,gridcolor="#1E2D4A"))
                    st.plotly_chart(fig, use_container_width=True)
                with ib:
                    st.markdown("**Conversion Rate % over time**")
                    fig = mini_bar(hist["ins_conversion"].tolist(),
                                   [str(d) for d in hist["date"].tolist()],
                                   color="#F59E0B", height=220)
                    st.plotly_chart(fig, use_container_width=True)

    # ════════════════════════════════════════════════════════
    # TAB C — ALL SUBMISSIONS TABLE
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
            st.download_button(
                "⬇️ Export All Data as CSV",
                all_df.to_csv(index=False).encode(),
                f"all_projects_{date.today()}.csv", "text/csv",
            )
        else:
            st.info("No data submitted yet across any project.")

    # Logout
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔒 Logout"):
        for key in ["role","project_id"]:
            st.session_state.pop(key, None)
        st.rerun()


# ──────────────────────────────────────────────────────────────
# 8.  MAIN ROUTER
# ──────────────────────────────────────────────────────────────
inject_css()

role = st.session_state.get("role")

if role == "pm":
    show_pm_dashboard()
elif role == "manager":
    show_manager_form(st.session_state["project_id"])
else:
    show_login()
