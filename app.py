"""
GRC Risk Register & Controls Tracker
=====================================
A NIST Cybersecurity Framework (CSF) 2.0-aligned risk register and controls
dashboard for a synthetic mid-size organization ("Atlas Meridian Group").

All data is synthetic — see the Methodology tab for details and for the
distinction this project draws between OBSERVED FACTS (control status,
assessment findings) and ANALYTICAL JUDGMENT (residual risk scoring).
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "grc_register.db"

st.set_page_config(
    page_title="GRC Risk Register & Controls Tracker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

RISK_COLOR_SCALE = [(0, "#2e7d32"), (0.35, "#f9a825"), (0.65, "#ef6c00"), (1, "#c62828")]


# ============================================================================
# Data access
# ============================================================================

@st.cache_resource
def get_connection():
    if not DB_PATH.exists():
        st.error(
            "Database not found. Run `python scripts/generate_data.py` from the "
            "project root to build the synthetic dataset before launching the app."
        )
        st.stop()
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data
def load_tables():
    conn = get_connection()
    tables = {}
    for name in [
        "business_units", "assets", "risks", "controls", "risk_control_map",
        "assessments", "residual_risk_assessments", "remediation_actions",
        "csf_functions", "csf_categories",
    ]:
        tables[name] = pd.read_sql_query(f"SELECT * FROM {name}", conn)
    return tables


def risk_band(score: int) -> str:
    if score >= 15:
        return "Critical"
    if score >= 9:
        return "High"
    if score >= 4:
        return "Medium"
    return "Low"


BAND_ORDER = ["Low", "Medium", "High", "Critical"]
BAND_COLORS = {"Low": "#2e7d32", "Medium": "#f9a825", "High": "#ef6c00", "Critical": "#c62828"}


@st.cache_data
def build_risk_view():
    t = load_tables()
    risks = t["risks"].merge(
        t["residual_risk_assessments"][
            ["risk_id", "residual_likelihood", "residual_impact", "residual_risk_score", "rationale", "analyst", "assessment_date"]
        ],
        on="risk_id", how="left",
    )
    risks = risks.merge(t["business_units"], left_on="business_unit_id", right_on="unit_id", how="left", suffixes=("", "_bu"))
    risks = risks.merge(t["assets"][["asset_id", "name"]].rename(columns={"name": "asset_name"}), on="asset_id", how="left")
    risks["inherent_band"] = risks["inherent_risk_score"].apply(risk_band)
    risks["residual_band"] = risks["residual_risk_score"].apply(risk_band)
    risks["risk_reduction"] = risks["inherent_risk_score"] - risks["residual_risk_score"]
    return risks


@st.cache_data
def build_controls_view():
    t = load_tables()
    controls = t["controls"].merge(t["csf_categories"], on="category_id", how="left", suffixes=("", "_cat"))
    controls = controls.merge(t["csf_functions"], on="function_id", how="left", suffixes=("", "_fn"))
    latest_assess = (
        t["assessments"].sort_values("assessment_date")
        .groupby("control_id").tail(1)[["control_id", "effectiveness_rating", "findings", "assessment_date"]]
        .rename(columns={"assessment_date": "latest_assessment_date"})
    )
    controls = controls.merge(latest_assess, on="control_id", how="left")
    return controls


MATURITY_ORDER = ["Not Implemented", "Planned", "Partially Implemented", "Largely Implemented", "Fully Implemented"]
MATURITY_SCORE = {"Not Implemented": 0, "Planned": 1, "Partially Implemented": 2, "Largely Implemented": 3, "Fully Implemented": 4}


# ============================================================================
# Header
# ============================================================================

st.title("🛡️ GRC Risk Register & Controls Tracker")
st.caption(
    "Synthetic mid-size organization · Risk register mapped to **NIST Cybersecurity Framework (CSF) 2.0** · "
    "All data is fictional — see the Methodology tab."
)

risks_df = build_risk_view()
controls_df = build_controls_view()
t = load_tables()

tab_overview, tab_risk, tab_controls, tab_remediation, tab_methodology = st.tabs(
    ["📊 Executive Overview", "📋 Risk Register", "🧭 NIST CSF 2.0 Controls", "🛠️ Remediation Tracker", "📖 Methodology"]
)


# ============================================================================
# TAB: Executive Overview
# ============================================================================

with tab_overview:
    open_risks = risks_df[risks_df["status"] != "Closed"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Open / Monitored Risks", len(open_risks), help="Risks with status Open or Monitoring")
    col2.metric(
        "Critical Residual Risks",
        int((open_risks["residual_band"] == "Critical").sum()),
        help="Residual risk score >= 15 (of a 25-point scale)",
    )
    avg_reduction = open_risks["risk_reduction"].mean()
    col3.metric("Avg. Risk Reduction from Controls", f"{avg_reduction:.1f} pts", help="Inherent score minus residual score, averaged across open risks")
    overdue = t["remediation_actions"][t["remediation_actions"]["status"] == "Overdue"]
    col4.metric("Overdue Remediation Actions", len(overdue))

    st.divider()

    left, right = st.columns([3, 2])

    with left:
        st.subheader("Residual Risk Heatmap (Likelihood x Impact)")
        heat = open_risks.groupby(["residual_likelihood", "residual_impact"]).size().reset_index(name="count")
        grid = pd.DataFrame(
            [(l, i) for l in range(1, 6) for i in range(1, 6)], columns=["residual_likelihood", "residual_impact"]
        ).merge(heat, on=["residual_likelihood", "residual_impact"], how="left").fillna(0)
        pivot = grid.pivot(index="residual_impact", columns="residual_likelihood", values="count").sort_index(ascending=False)
        fig = px.imshow(
            pivot, text_auto=True, color_continuous_scale="YlOrRd",
            labels=dict(x="Likelihood", y="Impact", color="# Risks"),
            aspect="auto",
        )
        fig.update_layout(height=380, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, width='stretch')

    with right:
        st.subheader("Open Risks by Category")
        cat_counts = open_risks["risk_category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig2 = px.bar(cat_counts, x="Count", y="Category", orientation="h", color="Count", color_continuous_scale="Blues")
        fig2.update_layout(height=380, margin=dict(t=10, b=10, l=10, r=10), showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig2, width='stretch')

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Control Implementation Maturity by NIST CSF 2.0 Function")
        fn_maturity = (
            controls_df.groupby("function_id")["implementation_status"]
            .apply(lambda s: s.map(MATURITY_SCORE).mean())
            .reindex(["GV", "ID", "PR", "DE", "RS", "RC"])
            .reset_index(name="avg_maturity")
        )
        fn_names = {"GV": "Govern", "ID": "Identify", "PR": "Protect", "DE": "Detect", "RS": "Respond", "RC": "Recover"}
        fn_maturity["Function"] = fn_maturity["function_id"].map(fn_names)
        fig3 = px.bar(
            fn_maturity, x="Function", y="avg_maturity", range_y=[0, 4],
            color="avg_maturity", color_continuous_scale="RdYlGn",
            labels={"avg_maturity": "Avg. Maturity (0=Not Implemented, 4=Fully Implemented)"},
        )
        fig3.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10), coloraxis_showscale=False)
        st.plotly_chart(fig3, width='stretch')

    with col_b:
        st.subheader("Top 10 Residual Risks")
        top10 = open_risks.sort_values("residual_risk_score", ascending=False).head(10)
        st.dataframe(
            top10[["risk_code", "title", "risk_category", "residual_risk_score", "residual_band"]].rename(
                columns={"risk_code": "ID", "title": "Risk", "risk_category": "Category",
                         "residual_risk_score": "Residual Score", "residual_band": "Band"}
            ),
            hide_index=True, width='stretch', height=350,
        )


# ============================================================================
# TAB: Risk Register
# ============================================================================

with tab_risk:
    st.subheader("Risk Register Explorer")

    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    categories = ["All"] + sorted(risks_df["risk_category"].unique().tolist())
    bands = ["All"] + BAND_ORDER
    statuses = ["All"] + sorted(risks_df["status"].unique().tolist())
    units = ["All"] + sorted(risks_df["name"].dropna().unique().tolist())

    f_category = fcol1.selectbox("Risk Category", categories)
    f_band = fcol2.selectbox("Residual Risk Band", bands)
    f_status = fcol3.selectbox("Status", statuses)
    f_unit = fcol4.selectbox("Business Unit", units)

    filtered = risks_df.copy()
    if f_category != "All":
        filtered = filtered[filtered["risk_category"] == f_category]
    if f_band != "All":
        filtered = filtered[filtered["residual_band"] == f_band]
    if f_status != "All":
        filtered = filtered[filtered["status"] == f_status]
    if f_unit != "All":
        filtered = filtered[filtered["name"] == f_unit]

    st.caption(f"{len(filtered)} of {len(risks_df)} risks shown")
    st.dataframe(
        filtered[[
            "risk_code", "title", "risk_category", "name", "risk_owner", "status",
            "inherent_risk_score", "inherent_band", "residual_risk_score", "residual_band",
        ]].rename(columns={
            "risk_code": "ID", "title": "Risk", "risk_category": "Category", "name": "Business Unit",
            "risk_owner": "Owner", "inherent_risk_score": "Inherent Score", "inherent_band": "Inherent Band",
            "residual_risk_score": "Residual Score", "residual_band": "Residual Band",
        }),
        hide_index=True, width='stretch', height=380,
    )

    st.divider()
    st.subheader("Risk Detail")
    pick = st.selectbox("Select a risk to inspect", filtered["risk_code"] + " — " + filtered["title"])
    if pick:
        rcode = pick.split(" — ")[0]
        row = risks_df[risks_df["risk_code"] == rcode].iloc[0]

        d1, d2 = st.columns([2, 1])
        with d1:
            st.markdown(f"**{row['title']}**")
            st.write(row["description"])
            st.markdown(
                f"- **Category:** {row['risk_category']}  \n"
                f"- **Business Unit:** {row['name']}  \n"
                f"- **Related Asset:** {row['asset_name'] if pd.notna(row['asset_name']) else '—'}  \n"
                f"- **Owner:** {row['risk_owner']}  \n"
                f"- **Date Identified:** {row['date_identified']}  \n"
                f"- **Status:** {row['status']}"
            )
            st.info(f"**Analytical judgment (residual risk rationale):**\n\n{row['rationale']}")

        with d2:
            st.metric("Inherent Risk", f"{row['inherent_risk_score']} ({row['inherent_band']})")
            st.metric("Residual Risk", f"{row['residual_risk_score']} ({row['residual_band']})")
            st.metric("Risk Reduction", f"{int(row['risk_reduction'])} pts")

        st.markdown("**Mapped Controls (observed implementation status)**")
        rid = int(row["risk_id"])
        mapped = t["risk_control_map"][t["risk_control_map"]["risk_id"] == rid]["control_id"]
        mapped_controls = controls_df[controls_df["control_id"].isin(mapped)]
        if mapped_controls.empty:
            st.warning("No controls are currently mapped to this risk.")
        else:
            st.dataframe(
                mapped_controls[["control_code", "name", "category_id", "implementation_status", "effectiveness_rating"]].rename(
                    columns={"control_code": "ID", "name": "Control", "category_id": "CSF Category",
                             "implementation_status": "Implementation Status", "effectiveness_rating": "Latest Effectiveness"}
                ),
                hide_index=True, width='stretch',
            )


# ============================================================================
# TAB: NIST CSF 2.0 Controls
# ============================================================================

with tab_controls:
    st.subheader("NIST CSF 2.0 Controls Explorer")

    fn_names = {"GV": "Govern", "ID": "Identify", "PR": "Protect", "DE": "Detect", "RS": "Respond", "RC": "Recover"}
    fcol1, fcol2 = st.columns(2)
    fn_options = ["All"] + [f"{k} — {v}" for k, v in fn_names.items()]
    f_fn = fcol1.selectbox("CSF Function", fn_options)
    f_impl = fcol2.selectbox("Implementation Status", ["All"] + MATURITY_ORDER)

    cfiltered = controls_df.copy()
    if f_fn != "All":
        cfiltered = cfiltered[cfiltered["function_id"] == f_fn.split(" — ")[0]]
    if f_impl != "All":
        cfiltered = cfiltered[cfiltered["implementation_status"] == f_impl]

    st.caption(f"{len(cfiltered)} of {len(controls_df)} controls shown")
    st.dataframe(
        cfiltered[[
            "control_code", "name", "category_id", "name_cat", "control_type",
            "implementation_status", "effectiveness_rating", "control_owner", "latest_assessment_date",
        ]].rename(columns={
            "control_code": "ID", "name": "Control", "category_id": "CSF Category", "name_cat": "Category Name",
            "control_type": "Type", "implementation_status": "Implementation Status",
            "effectiveness_rating": "Latest Effectiveness", "control_owner": "Owner",
            "latest_assessment_date": "Last Assessed",
        }),
        hide_index=True, width='stretch', height=420,
    )

    st.divider()
    st.subheader("Coverage by Function / Category")
    coverage = controls_df.groupby(["function_id", "category_id", "name_cat"]).agg(
        control_count=("control_id", "count"),
        avg_maturity=("implementation_status", lambda s: s.map(MATURITY_SCORE).mean()),
    ).reset_index()
    coverage["Function"] = coverage["function_id"].map(fn_names)
    fig4 = px.bar(
        coverage.sort_values(["function_id", "category_id"]),
        x="category_id", y="control_count", color="avg_maturity",
        color_continuous_scale="RdYlGn", range_color=[0, 4],
        labels={"category_id": "CSF Category", "control_count": "# Controls", "avg_maturity": "Avg. Maturity"},
        hover_data=["name_cat"],
    )
    fig4.update_layout(height=420, xaxis_tickangle=-45)
    st.plotly_chart(fig4, width='stretch')


# ============================================================================
# TAB: Remediation Tracker
# ============================================================================

with tab_remediation:
    st.subheader("Remediation Action Tracker")

    rem = t["remediation_actions"].merge(
        risks_df[["risk_id", "risk_code", "title", "risk_category"]], on="risk_id", how="left"
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Actions", len(rem))
    m2.metric("In Progress", int((rem["status"] == "In Progress").sum()))
    m3.metric("Overdue", int((rem["status"] == "Overdue").sum()))
    m4.metric("Completed", int((rem["status"] == "Completed").sum()))

    fcol1, fcol2 = st.columns(2)
    f_status2 = fcol1.selectbox("Status", ["All"] + sorted(rem["status"].unique().tolist()), key="rem_status")
    f_priority = fcol2.selectbox("Priority", ["All"] + ["Critical", "High", "Medium", "Low"], key="rem_priority")

    rfiltered = rem.copy()
    if f_status2 != "All":
        rfiltered = rfiltered[rfiltered["status"] == f_status2]
    if f_priority != "All":
        rfiltered = rfiltered[rfiltered["priority"] == f_priority]

    st.dataframe(
        rfiltered[[
            "action_code", "description", "risk_code", "title", "priority", "owner",
            "target_date", "status", "date_closed",
        ]].rename(columns={
            "action_code": "ID", "description": "Action", "risk_code": "Related Risk ID",
            "title": "Related Risk", "priority": "Priority", "owner": "Owner",
            "target_date": "Target Date", "status": "Status", "date_closed": "Closed Date",
        }),
        hide_index=True, width='stretch', height=420,
    )

    st.divider()
    st.subheader("Remediation Status Mix by Priority")
    mix = rem.groupby(["priority", "status"]).size().reset_index(name="count")
    fig5 = px.bar(
        mix, x="priority", y="count", color="status", barmode="stack",
        category_orders={"priority": ["Critical", "High", "Medium", "Low"]},
        color_discrete_map={"Not Started": "#9e9e9e", "In Progress": "#1976d2", "Completed": "#2e7d32", "Overdue": "#c62828"},
    )
    fig5.update_layout(height=360)
    st.plotly_chart(fig5, width='stretch')


# ============================================================================
# TAB: Methodology
# ============================================================================

with tab_methodology:
    st.subheader("Methodology & Data Notes")
    st.markdown(
        """
This project models a **synthetic** mid-size organization ("Atlas Meridian Group" —
a fictional logistics, industrial services, and international security-consulting
company). No real organization's data, employer records, or confidential information
is represented here. The dataset is generated by `scripts/generate_data.py` with a
fixed random seed for reproducibility.

### Observed facts vs. analytical judgment

This project deliberately separates two kinds of information, the same way a
production GRC program should:

- **Observed facts** — recorded directly, without interpretation: control
  *implementation status* (is it built and running?), assessment *findings* and
  *effectiveness ratings* (what did the assessor actually see?), and remediation
  *status* (what is actually done?). These live in the `controls`, `assessments`,
  and `remediation_actions` tables.
- **Analytical judgment** — a risk professional's interpretation of what those
  facts mean for residual exposure. Every residual risk score in this project is
  stored in its own table (`residual_risk_assessments`) with a mandatory,
  human-readable **rationale** field explaining how the analyst got from inherent
  risk and observed control status to a residual score. The point is traceability:
  a reader should always be able to see *which facts* a judgment call rests on,
  and never mistake a scored opinion for a measured fact.

### Risk scoring

- **Inherent risk** = Likelihood (1–5) × Impact (1–5), assigned at the time the
  risk was identified, before considering controls.
- **Residual risk** = Likelihood and Impact adjusted down based on the average
  implementation maturity of the risk's mapped controls, computed by
  `generate_data.py`. This is a simplified, transparent scoring model chosen for
  this demonstration project — a production risk register would typically use a
  more elaborate, organization-specific residual scoring methodology, additional
  scoring factors (e.g. velocity, detectability), and analyst override capability
  rather than a purely formulaic reduction.
- **Risk bands:** Low (1–3), Medium (4–8), High (9–14), Critical (15–25).

### NIST CSF 2.0 mapping

All 50 controls are mapped to one of the 23 categories across the 6 CSF 2.0
Functions (Govern, Identify, Protect, Detect, Respond, Recover), per NIST CSWP 29
(February 2024). Physical security, safety/EHS, and regulatory-compliance controls
— which sit outside CSF's native cybersecurity scope — are cross-mapped to the
closest applicable CSF category (e.g., badge access control under **PR.AA**,
DOT/OSHA programs under **GV.PO**). This is a common, defensible practice for
organizations that use CSF as a general-purpose risk taxonomy rather than a
cyber-only framework, and is called out explicitly here rather than presented as
an unqualified 1:1 mapping.

### Limitations

This is a portfolio / demonstration project, not a production GRC tool. Notably:
scoring is intentionally simple and transparent rather than statistically
validated; the dataset is synthetic and does not reflect any real organization's
actual risk posture; and the project does not implement authentication,
audit logging of user edits, or workflow approvals that a production system
would require.
        """
    )

    st.divider()
    st.caption(
        "Built by Joel Vandenhouten — retired U.S. Army Major and enterprise risk / physical security / "
        "GRC executive, currently completing a Master of Legal Studies in Cybersecurity Law & Policy at "
        "Texas A&M University School of Law. See the companion "
        "[OpenAI Abuse Investigation Portfolio](https://github.com/jvandenhouten/openai-abuse-investigator-portfolio) "
        "project for related work."
    )
