# GRC Risk Register & Controls Tracker

**NIST CSF 2.0-aligned enterprise risk register · SQL · Python · Streamlit**

> ⚠️ **All data in this repository is synthetic.** "Atlas Meridian Group," its business
> units, assets, risks, controls, assessments, and remediation actions are fictional
> and were generated for demonstration purposes. No real organization's confidential
> or proprietary information is represented here.

**Live dashboard:** [grc-risk-register-tracker-n8evb3x9hoyuttcgxrs2du.streamlit.app](https://grc-risk-register-tracker-n8evb3x9hoyuttcgxrs2du.streamlit.app/)

**Companion project:** [OpenAI Abuse Investigation Portfolio](https://github.com/jvandenhouten/openai-abuse-investigator-portfolio) — a synthetic investigative-analytics case study using the same "observed facts vs. analytical judgment" discipline described below.

---

## What this is

A working GRC (Governance, Risk, and Compliance) tool: a risk register for a
synthetic mid-size organization, with every control mapped to the **NIST
Cybersecurity Framework (CSF) 2.0** (all 6 Functions, all 23 Categories), an
interactive Streamlit dashboard, and a SQL/Jupyter analysis notebook.

It's built to demonstrate the same skill set a Chief Risk Officer, Director of
GRC, or enterprise risk analyst applies in practice: structuring a risk
register that survives scrutiny, mapping controls to a recognized framework
rather than an ad-hoc list, scoring residual risk in a way that's
*traceable back to the evidence it's based on*, and presenting all of it in a
form an executive can actually use.

### Core questions this tool is built to answer

- Where does the organization carry the most residual risk, right now, once
  existing controls are accounted for?
- Which NIST CSF 2.0 functions and categories have the weakest control
  maturity, relative to how much risk depends on them?
- Which risks have no mapped controls at all?
- Is the remediation backlog shrinking, and is it prioritized correctly —
  or is high-priority work sitting overdue while lower-priority work gets done?
- For any given risk score, what's the actual reasoning behind it — not just
  the number?

## Observed facts vs. analytical judgment

This is the same analytical discipline used in the companion investigation
project, applied to GRC:

- **Observed facts** — recorded directly: control *implementation status*,
  assessment *findings and effectiveness ratings*, remediation *status*.
  These are things that were actually checked and recorded, not opinions.
- **Analytical judgment** — every **residual risk score** is stored
  separately from the facts above, together with a mandatory, human-readable
  **rationale** explaining how an analyst got from inherent risk and observed
  control maturity to that score. A reader should never have to take a risk
  score on faith — the reasoning and the evidence behind it are both right
  there.

See the app's **Methodology** tab (or [`app.py`](app.py)) for the full
scoring methodology, its limitations, and how physical security / safety /
compliance risks (which sit outside CSF's native cybersecurity scope) are
cross-mapped to the framework.

## Project status

**Complete** — synthetic dataset, full NIST CSF 2.0 mapping, interactive
dashboard, and SQL analysis notebook are all built and reproducible from
scratch via the scripts in this repo.

## Repository structure

```
grc-risk-register-tracker/
├── app.py                        # Streamlit dashboard (5 tabs, see below)
├── requirements.txt
├── data/
│   ├── csf2_reference.json       # NIST CSF 2.0 functions & categories (reference data)
│   └── grc_register.db           # Generated SQLite database (build with generate_data.py)
├── scripts/
│   ├── schema.sql                # Full database schema
│   ├── generate_data.py          # Builds the synthetic dataset end-to-end
│   └── build_notebook.py         # Generates notebooks/analysis.ipynb from code
├── notebooks/
│   └── analysis.ipynb            # SQL/pandas analysis, outputs pre-run and committed
└── .streamlit/
    └── config.toml
```

## Data model

Eight tables: `business_units`, `assets`, `risks`, `controls`,
`risk_control_map` (many-to-many), `assessments`, `residual_risk_assessments`,
and `remediation_actions` — plus the NIST CSF 2.0 reference tables
(`csf_functions`, `csf_categories`). Full schema in
[`scripts/schema.sql`](scripts/schema.sql).

The synthetic organization: a fictional mid-size logistics, industrial
services, and international security-consulting company headquartered in
Austin, TX, with field operations across Texas and a regional office in
Riyadh, Saudi Arabia — 8 business units, 28 assets, 45 risks across six
categories (Cybersecurity, Physical Security, Operational, Third-Party,
Compliance/Regulatory, Safety/EHS), and 50 controls mapped across all 23 NIST
CSF 2.0 categories.

## Dashboard

The Streamlit app has five tabs:

1. **Executive Overview** — key metrics, a residual-risk heatmap, open risk
   volume by category, control maturity by CSF function, and the top 10
   residual risks.
2. **Risk Register** — filterable risk register with a detail view per risk,
   including its full residual-risk rationale and mapped controls.
3. **NIST CSF 2.0 Controls** — filterable control inventory with a
   function/category coverage chart.
4. **Remediation Tracker** — remediation action status, filterable by status
   and priority, with a stacked status-by-priority chart.
5. **Methodology** — the full scoring methodology, data notes, and stated
   limitations.

## Local setup

```bash
git clone https://github.com/<your-username>/grc-risk-register-tracker.git
cd grc-risk-register-tracker
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python scripts/generate_data.py   # builds data/grc_register.db
streamlit run app.py
```

To regenerate the analysis notebook's outputs after changing the dataset:

```bash
python scripts/build_notebook.py
jupyter nbconvert --to notebook --execute --inplace notebooks/analysis.ipynb
```

## Deployment

The dashboard is built to deploy directly to
[Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, create a new app pointing at this repo,
   branch `main`, main file `app.py`.
3. `data/grc_register.db` is committed to the repo, so no build step is
   required — the app reads it directly. If you change the dataset, re-run
   `python scripts/generate_data.py` and commit the updated `.db` file.

Once deployed, add the live URL at the top of this README.

## Tech stack

Python · SQLite · SQL · pandas · Streamlit · Plotly · Jupyter/nbconvert

## About

Built by **Joel Vandenhouten** — retired U.S. Army Major and enterprise risk,
physical security, and GRC executive, currently completing a Master of Legal
Studies in Cybersecurity Law & Policy at Texas A&M University School of Law.
Career background spans military intelligence and Red Team operations,
corporate physical security and EHS leadership, and international (MENA)
business operations — the domains this project's synthetic risk register is
modeled on.
