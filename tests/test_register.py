"""Integrity checks for the synthetic GRC register."""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "grc_register.db"
SCHEMA = ROOT / "scripts" / "schema.sql"


def connect() -> sqlite3.Connection:
    assert DB.exists(), f"missing database: {DB}"
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def test_schema_file_present() -> None:
    assert SCHEMA.exists()
    text = SCHEMA.read_text(encoding="utf-8")
    for table in (
        "csf_functions",
        "csf_categories",
        "risks",
        "controls",
        "residual_risk_assessments",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in text


def test_csf_coverage() -> None:
    con = connect()
    functions = con.execute("SELECT COUNT(*) FROM csf_functions").fetchone()[0]
    categories = con.execute("SELECT COUNT(*) FROM csf_categories").fetchone()[0]
    assert functions == 6
    assert categories == 23
    mapped = con.execute("SELECT COUNT(DISTINCT category_id) FROM controls").fetchone()[0]
    assert mapped == 23


def test_register_counts() -> None:
    con = connect()
    risks = con.execute("SELECT COUNT(*) FROM risks").fetchone()[0]
    controls = con.execute("SELECT COUNT(*) FROM controls").fetchone()[0]
    residuals = con.execute("SELECT COUNT(*) FROM residual_risk_assessments").fetchone()[0]
    assert risks == 45
    assert controls == 50
    assert residuals >= risks


def test_inherent_and_residual_score_math() -> None:
    con = connect()
    bad_inh = con.execute(
        "SELECT COUNT(*) FROM risks WHERE inherent_risk_score != inherent_likelihood * inherent_impact"
    ).fetchone()[0]
    bad_res = con.execute(
        """
        SELECT COUNT(*) FROM residual_risk_assessments
        WHERE residual_risk_score != residual_likelihood * residual_impact
        """
    ).fetchone()[0]
    assert bad_inh == 0
    assert bad_res == 0


def test_residual_rationale_required() -> None:
    con = connect()
    empty = con.execute(
        """
        SELECT COUNT(*) FROM residual_risk_assessments
        WHERE rationale IS NULL OR TRIM(rationale) = ''
        """
    ).fetchone()[0]
    assert empty == 0


def test_risk_score_bounds() -> None:
    con = connect()
    out = con.execute(
        """
        SELECT COUNT(*) FROM risks
        WHERE inherent_likelihood NOT BETWEEN 1 AND 5
           OR inherent_impact NOT BETWEEN 1 AND 5
           OR inherent_risk_score NOT BETWEEN 1 AND 25
        """
    ).fetchone()[0]
    assert out == 0


def test_referential_integrity() -> None:
    con = connect()
    orphan_assets = con.execute(
        """
        SELECT COUNT(*) FROM assets a
        LEFT JOIN business_units u ON a.business_unit_id = u.unit_id
        WHERE a.business_unit_id IS NOT NULL AND u.unit_id IS NULL
        """
    ).fetchone()[0]
    orphan_map = con.execute(
        """
        SELECT COUNT(*) FROM risk_control_map m
        LEFT JOIN risks r ON m.risk_id = r.risk_id
        LEFT JOIN controls c ON m.control_id = c.control_id
        WHERE r.risk_id IS NULL OR c.control_id IS NULL
        """
    ).fetchone()[0]
    orphan_ctrl_cat = con.execute(
        """
        SELECT COUNT(*) FROM controls c
        LEFT JOIN csf_categories cat ON c.category_id = cat.category_id
        WHERE cat.category_id IS NULL
        """
    ).fetchone()[0]
    assert orphan_assets == 0
    assert orphan_map == 0
    assert orphan_ctrl_cat == 0
