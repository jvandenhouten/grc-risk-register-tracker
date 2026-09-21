# GRC Risk Register & Controls Tracker

**NIST CSF 2.0-aligned enterprise risk register · SQL · Python · Streamlit**

> ⚠️ **All data in this repository is synthetic.** "Atlas Meridian Group," its business
> units, assets, risks, controls, assessments, and remediation actions are fictional
> and were generated for demonstration purposes. No real organization's confidential
> or proprietary information is represented here.

**Live dashboard:** [grc-risk-register-tracker-n8evb3x9hoyuttcgxrs2du.streamlit.app](https://grc-risk-register-tracker-n8evb3x9hoyuttcgxrs2du.streamlit.app/)

**Companion project:** [Abuse Investigation & Detection Portfolio](https://github.com/jvandenhouten/openai-abuse-investigator-portfolio)

**AI governance note:** [docs/AI_GOVERNANCE_RELEVANCE.md](docs/AI_GOVERNANCE_RELEVANCE.md) · **Worked AI-risk example:** [docs/AI_RISK_EXAMPLE.md](docs/AI_RISK_EXAMPLE.md)

---

## What this is

A working GRC tool: a risk register for a synthetic mid-size organization, with every control mapped to the **NIST Cybersecurity Framework (CSF) 2.0** (all 6 Functions, all 23 Categories), an interactive Streamlit dashboard, and a SQL/Jupyter analysis notebook.

It demonstrates the same skill set a Chief Risk Officer, Director of GRC, or AI-governance lead applies in practice: structuring a register that survives scrutiny, mapping controls to a recognized framework, scoring residual risk so it is *traceable to evidence*, and presenting the result in a form an executive can use.

### Core questions this tool is built to answer

- Where does the organization carry the most residual risk once existing controls are accounted for?
- Which NIST CSF 2.0 functions and categories have the weakest control maturity relative to the risk that depends on them?
- Which risks have no mapped controls?
- Is the remediation backlog shrinking, and is it prioritized correctly?
- For any given risk score, what is the actual reasoning — not just the number?
- How would a generative-AI / third-party-model risk be owned, controlled, exception-handled, and closed? See the worked example.

## Observed facts vs. analytical judgment

- **Observed facts** — control implementation status, assessment findings and effectiveness ratings, remediation status.
- **Analytical judgment** — every **residual risk score** is stored separately from those facts, with a mandatory human-readable **rationale**. A reader should never take a score on faith.

See the app **Methodology** tab and [docs/AI_GOVERNANCE_RELEVANCE.md](docs/AI_GOVERNANCE_RELEVANCE.md).

## Project status

**v1.1 hardening (2026-09-21)** — synthetic dataset, full NIST CSF 2.0 mapping, dashboard, analysis notebook, CI tests, security policy, and an AI-risk worked example.

Automated checks in CI:

- database file present and readable
- six CSF functions and 23 categories
- residual scores equal likelihood × impact
- every residual assessment has a non-empty rationale
- every CSF category has at least one mapped control

## Local setup

```bash
git clone https://github.com/jvandenhouten/grc-risk-register-tracker.git
cd grc-risk-register-tracker
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python scripts/generate_data.py   # rebuilds data/grc_register.db if you change the generator
streamlit run app.py
python -m pytest tests/ -q
```

## What this is not

This repository does not claim measured AI-accuracy improvement, ISO/IEC 42001 certification, or implementation of a production model-risk program. Those terms are used only as mapping language in the worked example.

## Tech stack

Python · SQLite · SQL · pandas · Streamlit · Plotly · pytest · GitHub Actions

## About

Built by **Joel Vandenhouten** — retired U.S. Army Major; intelligence, investigations, enterprise security, and GRC executive; Texas A&M University School of Law, Master of Legal Studies in Cybersecurity Law & Policy (expected December 2026).
