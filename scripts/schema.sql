-- ============================================================================
-- GRC Risk Register & Controls Tracker
-- SQLite schema — synthetic mid-size organization mapped to NIST CSF 2.0
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- Reference data: NIST Cybersecurity Framework (CSF) 2.0 structure
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS csf_functions (
    function_id   TEXT PRIMARY KEY,          -- e.g. 'GV'
    name          TEXT NOT NULL,             -- e.g. 'Govern'
    description   TEXT NOT NULL,
    sort_order    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS csf_categories (
    category_id   TEXT PRIMARY KEY,          -- e.g. 'GV.OC'
    function_id   TEXT NOT NULL REFERENCES csf_functions(function_id),
    name          TEXT NOT NULL,             -- e.g. 'Organizational Context'
    description   TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- Organization structure
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS business_units (
    unit_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    location      TEXT NOT NULL,
    description   TEXT
);

CREATE TABLE IF NOT EXISTS assets (
    asset_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name               TEXT NOT NULL,
    asset_type         TEXT NOT NULL CHECK (asset_type IN
                        ('Application', 'Data Store', 'Facility', 'Infrastructure',
                         'Third Party', 'Process', 'Fleet / Equipment')),
    business_unit_id   INTEGER REFERENCES business_units(unit_id),
    criticality        TEXT NOT NULL CHECK (criticality IN ('Low', 'Medium', 'High', 'Critical')),
    description        TEXT
);

-- ----------------------------------------------------------------------------
-- Risk register
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS risks (
    risk_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_code             TEXT UNIQUE NOT NULL,   -- e.g. 'RISK-0042'
    title                 TEXT NOT NULL,
    description           TEXT NOT NULL,
    risk_category         TEXT NOT NULL CHECK (risk_category IN
                           ('Cybersecurity', 'Physical Security', 'Operational',
                            'Third-Party', 'Compliance / Regulatory', 'Safety / EHS')),
    asset_id              INTEGER REFERENCES assets(asset_id),
    business_unit_id      INTEGER NOT NULL REFERENCES business_units(unit_id),
    date_identified       TEXT NOT NULL,
    risk_owner            TEXT NOT NULL,
    inherent_likelihood   INTEGER NOT NULL CHECK (inherent_likelihood BETWEEN 1 AND 5),
    inherent_impact       INTEGER NOT NULL CHECK (inherent_impact BETWEEN 1 AND 5),
    inherent_risk_score   INTEGER NOT NULL,        -- likelihood * impact (observed input, not judgment)
    status                TEXT NOT NULL CHECK (status IN ('Open', 'Monitoring', 'Closed'))
);

-- ----------------------------------------------------------------------------
-- Controls (mapped to NIST CSF 2.0 categories)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS controls (
    control_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    control_code             TEXT UNIQUE NOT NULL,  -- e.g. 'CTRL-0031'
    name                     TEXT NOT NULL,
    description              TEXT NOT NULL,
    control_type             TEXT NOT NULL CHECK (control_type IN ('Preventive', 'Detective', 'Corrective')),
    category_id              TEXT NOT NULL REFERENCES csf_categories(category_id),
    control_owner            TEXT NOT NULL,
    implementation_status    TEXT NOT NULL CHECK (implementation_status IN
                              ('Not Implemented', 'Planned', 'Partially Implemented',
                               'Largely Implemented', 'Fully Implemented')),
    last_assessed_date       TEXT
);

CREATE TABLE IF NOT EXISTS risk_control_map (
    risk_id      INTEGER NOT NULL REFERENCES risks(risk_id),
    control_id   INTEGER NOT NULL REFERENCES controls(control_id),
    PRIMARY KEY (risk_id, control_id)
);

-- ----------------------------------------------------------------------------
-- Control assessments — OBSERVED FACTS: what was tested and what was found
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    control_id            INTEGER NOT NULL REFERENCES controls(control_id),
    assessment_date        TEXT NOT NULL,
    assessor               TEXT NOT NULL,
    effectiveness_rating   TEXT NOT NULL CHECK (effectiveness_rating IN
                            ('Ineffective', 'Partially Effective', 'Largely Effective', 'Fully Effective')),
    findings                TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- Residual risk assessments — ANALYTICAL JUDGMENT, explicitly separated from
-- the observed control-status facts above. Every score carries a rationale.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS residual_risk_assessments (
    residual_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_id                INTEGER NOT NULL REFERENCES risks(risk_id),
    assessment_date         TEXT NOT NULL,
    analyst                 TEXT NOT NULL,
    residual_likelihood     INTEGER NOT NULL CHECK (residual_likelihood BETWEEN 1 AND 5),
    residual_impact         INTEGER NOT NULL CHECK (residual_impact BETWEEN 1 AND 5),
    residual_risk_score     INTEGER NOT NULL,
    rationale                TEXT NOT NULL     -- analyst's judgment call, always recorded in the analyst's own words
);

-- ----------------------------------------------------------------------------
-- Remediation tracking
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS remediation_actions (
    action_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    action_code     TEXT UNIQUE NOT NULL,     -- e.g. 'REM-0018'
    risk_id         INTEGER REFERENCES risks(risk_id),
    control_id      INTEGER REFERENCES controls(control_id),
    description     TEXT NOT NULL,
    owner           TEXT NOT NULL,
    priority        TEXT NOT NULL CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
    target_date     TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('Not Started', 'In Progress', 'Completed', 'Overdue')),
    date_closed     TEXT
);

CREATE INDEX IF NOT EXISTS idx_risks_category ON risks(risk_category);
CREATE INDEX IF NOT EXISTS idx_risks_unit ON risks(business_unit_id);
CREATE INDEX IF NOT EXISTS idx_controls_category ON controls(category_id);
CREATE INDEX IF NOT EXISTS idx_remediation_status ON remediation_actions(status);
