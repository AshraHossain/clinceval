-- ClinCalc-Eval result storage (SQLite — deliberate demo-scope choice)

CREATE TABLE IF NOT EXISTS triage_tags (
    tag TEXT PRIMARY KEY
);

INSERT OR IGNORE INTO triage_tags (tag) VALUES
    ('RETRIEVAL'), ('GENERATION'), ('JUDGE'), ('INTEGRATION'), ('DATA'), ('PASS');

CREATE TABLE IF NOT EXISTS golden_cases (
    id                  TEXT PRIMARY KEY,
    category            TEXT NOT NULL,
    difficulty          TEXT,
    weight              TEXT NOT NULL,
    expected_calculator TEXT
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at                  TEXT NOT NULL UNIQUE,
    total_cases                 INTEGER NOT NULL,
    overall_pass_rate           REAL NOT NULL,
    faithfulness_pass_rate      REAL NOT NULL,
    clinical_relevance_pass_rate REAL NOT NULL,
    safety_pass_rate            REAL NOT NULL,
    completeness_pass_rate      REAL NOT NULL,
    hard_gate_failures          INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_results (
    run_id                 INTEGER NOT NULL REFERENCES eval_runs(id),
    case_id                TEXT NOT NULL REFERENCES golden_cases(id),
    triage                 TEXT NOT NULL REFERENCES triage_tags(tag),
    overall_pass           INTEGER NOT NULL,
    safety_gate_fail       INTEGER NOT NULL,
    faithfulness           INTEGER,
    clinical_relevance     INTEGER,
    safety                 INTEGER,
    completeness           INTEGER,
    similarity             REAL,
    recommended_calculator TEXT,
    PRIMARY KEY (run_id, case_id)
);
