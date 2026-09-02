"""
build_notebook.py
==================
Generates notebooks/analysis.ipynb from code, so the notebook's cells are kept
in a diff-friendly, review-friendly Python source instead of hand-edited JSON.

Run:
    python scripts/build_notebook.py
Then execute the notebook to populate outputs:
    jupyter nbconvert --to notebook --execute --inplace notebooks/analysis.ipynb
"""

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent
NB_PATH = ROOT / "notebooks" / "analysis.ipynb"

nb = nbf.v4.new_notebook()
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))


md("""# GRC Risk Register & Controls Tracker — SQL Analysis

Exploratory analysis of the synthetic risk register, run directly against the
SQLite database with SQL queries (via `pandas.read_sql_query`), matching the
style of the companion [OpenAI Abuse Investigation Portfolio](https://github.com/jvandenhouten/openai-abuse-investigator-portfolio)
project.

**Note:** all data here is synthetic (see `README.md` / the app's Methodology
tab). This notebook demonstrates the SQL and analytical approach, not a real
organization's risk posture.
""")

code("""import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")
pd.set_option("display.max_colwidth", 80)

DB_PATH = Path("..") / "data" / "grc_register.db"
conn = sqlite3.connect(DB_PATH)
""")

md("## 1. Risk register overview")

code("""df = pd.read_sql_query(\"\"\"
    SELECT risk_code, title, risk_category, status, inherent_risk_score
    FROM risks
    ORDER BY inherent_risk_score DESC
\"\"\", conn)
print(f"{len(df)} risks in register")
df.head(10)
""")

code("""df["risk_category"].value_counts().plot(kind="barh", figsize=(7, 4), color="#1976d2")
plt.title("Risk Count by Category")
plt.xlabel("# Risks")
plt.tight_layout()
plt.show()
""")

md("""## 2. Inherent vs. residual risk

The residual score reflects the *analytical judgment* layer described in the
Methodology tab: inherent risk adjusted for the observed maturity of mapped
controls. We join `risks` to `residual_risk_assessments` to compare the two.
""")

code("""residual = pd.read_sql_query(\"\"\"
    SELECT r.risk_code, r.title, r.risk_category, r.status,
           r.inherent_risk_score, rr.residual_risk_score, rr.rationale
    FROM risks r
    JOIN residual_risk_assessments rr ON rr.risk_id = r.risk_id
    ORDER BY r.inherent_risk_score - rr.residual_risk_score DESC
\"\"\", conn)
residual["risk_reduction"] = residual["inherent_risk_score"] - residual["residual_risk_score"]
residual.head(10)
""")

code("""fig, ax = plt.subplots(figsize=(7, 6))
ax.scatter(residual["inherent_risk_score"], residual["residual_risk_score"],
           alpha=0.7, s=60, c=residual["risk_reduction"], cmap="RdYlGn")
ax.plot([0, 25], [0, 25], linestyle="--", color="gray", linewidth=1, label="No reduction")
ax.set_xlabel("Inherent Risk Score")
ax.set_ylabel("Residual Risk Score")
ax.set_title("Inherent vs. Residual Risk (color = points of reduction)")
ax.legend()
plt.tight_layout()
plt.show()
""")

md("""**Reading this chart:** every point below the diagonal line represents a
risk where mapped controls measurably reduced exposure. Points close to the
diagonal are risks where controls exist on paper but are not yet mature enough
to meaningfully change the residual score — a useful prioritization signal for
where control investment would have the most impact.
""")

md("## 3. Top residual risks (where to focus first)")

code("""top_risks = residual.sort_values("residual_risk_score", ascending=False).head(10)
top_risks[["risk_code", "title", "risk_category", "inherent_risk_score", "residual_risk_score"]]
""")

md("## 4. Control maturity by NIST CSF 2.0 function")

code("""maturity_map = {
    "Not Implemented": 0, "Planned": 1, "Partially Implemented": 2,
    "Largely Implemented": 3, "Fully Implemented": 4,
}

controls = pd.read_sql_query(\"\"\"
    SELECT c.control_code, c.name, c.implementation_status, c.category_id,
           cat.name AS category_name, f.function_id, f.name AS function_name
    FROM controls c
    JOIN csf_categories cat ON cat.category_id = c.category_id
    JOIN csf_functions f ON f.function_id = cat.function_id
\"\"\", conn)
controls["maturity"] = controls["implementation_status"].map(maturity_map)

fn_order = ["GV", "ID", "PR", "DE", "RS", "RC"]
fn_maturity = controls.groupby("function_id")["maturity"].mean().reindex(fn_order)
fn_maturity
""")

code("""fig, ax = plt.subplots(figsize=(7, 4))
colors = plt.cm.RdYlGn(fn_maturity / 4)
ax.bar(fn_maturity.index, fn_maturity.values, color=colors)
ax.set_ylim(0, 4)
ax.set_ylabel("Avg. Maturity (0=Not Implemented, 4=Fully Implemented)")
ax.set_title("Control Maturity by NIST CSF 2.0 Function")
plt.tight_layout()
plt.show()
""")

md("""## 5. Category-level control maturity (lowest first)

Categories with the lowest average maturity relative to the number of risks
mapped into them are reasonable candidates for the next control-investment
cycle.
""")

code("""cat_maturity = controls.groupby(["function_id", "category_id", "category_name"])["maturity"].mean()
cat_maturity = cat_maturity.reset_index().sort_values("maturity")
cat_maturity.head(10)
""")

md("## 6. Remediation backlog analysis")

code("""remediation = pd.read_sql_query(\"\"\"
    SELECT ra.action_code, ra.description, ra.priority, ra.status, ra.target_date,
           r.risk_code, r.title, r.risk_category
    FROM remediation_actions ra
    LEFT JOIN risks r ON r.risk_id = ra.risk_id
\"\"\", conn)

status_by_priority = pd.crosstab(remediation["priority"], remediation["status"])
status_by_priority = status_by_priority.reindex(["Critical", "High", "Medium", "Low"])
status_by_priority
""")

code("""status_by_priority.plot(kind="bar", stacked=True, figsize=(7, 4),
                          color={"Not Started": "#9e9e9e", "In Progress": "#1976d2",
                                 "Completed": "#2e7d32", "Overdue": "#c62828"})
plt.title("Remediation Action Status by Priority")
plt.ylabel("# Actions")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()
""")

code("""overdue = remediation[remediation["status"] == "Overdue"].sort_values("priority")
print(f"{len(overdue)} overdue remediation action(s)")
overdue[["action_code", "description", "priority", "risk_code", "title", "target_date"]]
""")

md("""## 7. Summary

- Residual risk scoring measurably reduces exposure across most of the
  register, but a handful of risks remain in the Critical band even after
  accounting for mapped controls — these are the natural starting point for
  the next remediation cycle (see Section 3).
- Control maturity is uneven across NIST CSF 2.0 functions (Section 4/5); the
  lowest-maturity categories, weighted by how many risks depend on them, are
  where control investment would have the most leverage.
- The remediation backlog (Section 6) shows a mix of in-progress and overdue
  actions concentrated at higher priority levels, consistent with an
  organization actively working down a known set of gaps rather than one with
  an unmanaged backlog.

See `app.py` (Streamlit dashboard) for an interactive version of these views,
and the project `README.md` for the full data model and methodology notes.
""")

code("""conn.close()""")

nb["cells"] = cells
NB_PATH.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, NB_PATH)
print(f"Notebook written: {NB_PATH}")
