-- Phase 10j: PostgreSQL schema (replaces SQLite for multi-instance/K8s)
-- Use with SQLAlchemy: create_engine("postgresql://user:pass@localhost/clinceval")

CREATE TABLE triage_tags (
  id SERIAL PRIMARY KEY,
  tag VARCHAR(50) UNIQUE NOT NULL  -- RETRIEVAL, GENERATION, JUDGE, INTEGRATION, DATA, PASS
);

INSERT INTO triage_tags (tag) VALUES ('RETRIEVAL'), ('GENERATION'), ('JUDGE'), ('INTEGRATION'), ('DATA'), ('PASS');

CREATE TABLE golden_cases (
  id VARCHAR(100) PRIMARY KEY,
  category VARCHAR(50) NOT NULL,  -- core, edge, adv, safety
  difficulty VARCHAR(50),         -- easy, medium, hard
  weight VARCHAR(50),             -- normal, high
  expected_calculator VARCHAR(255),
  must_cite TEXT[],               -- Array of chunk IDs
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE eval_runs (
  id SERIAL PRIMARY KEY,
  started_at TIMESTAMP UNIQUE NOT NULL,
  ended_at TIMESTAMP,
  total_cases INT,
  overall_passes INT,
  overall_pass_rate NUMERIC(5, 2),
  faithfulness NUMERIC(5, 2),
  clinical_relevance NUMERIC(5, 2),
  safety NUMERIC(5, 2),
  completeness NUMERIC(5, 2),
  hard_gate_failures INT DEFAULT 0,
  cost_usd NUMERIC(10, 4),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE eval_results (
  id SERIAL PRIMARY KEY,
  run_id INT NOT NULL REFERENCES eval_runs(id) ON DELETE CASCADE,
  case_id VARCHAR(100) NOT NULL REFERENCES golden_cases(id),
  triage_id INT REFERENCES triage_tags(id),
  overall_pass BOOLEAN,
  safety_gate_fail BOOLEAN,
  faithfulness INT,
  clinical_relevance INT,
  safety INT,
  completeness INT,
  similarity NUMERIC(4, 2),
  recommended_calculator VARCHAR(255),
  cost_usd NUMERIC(10, 4),
  latency_ms INT,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(run_id, case_id)
);

CREATE INDEX idx_eval_results_run_id ON eval_results(run_id);
CREATE INDEX idx_eval_results_case_id ON eval_results(case_id);
CREATE INDEX idx_eval_results_triage_id ON eval_results(triage_id);

-- View: Pass rate trend with rolling average
CREATE VIEW eval_trend AS
SELECT
  id,
  started_at,
  overall_pass_rate,
  LAG(overall_pass_rate) OVER (ORDER BY started_at) AS prev_rate,
  overall_pass_rate - LAG(overall_pass_rate) OVER (ORDER BY started_at) AS delta_vs_prev,
  AVG(overall_pass_rate) OVER (ORDER BY started_at ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS rolling_avg_5
FROM eval_runs
ORDER BY started_at DESC;

-- View: Cost per run
CREATE VIEW cost_analysis AS
SELECT
  run_id,
  SUM(cost_usd) as total_cost,
  AVG(cost_usd) as avg_cost_per_case,
  COUNT(*) as case_count
FROM eval_results
GROUP BY run_id
ORDER BY run_id DESC;

-- Connection pooling config (in app):
-- PgBouncer or:
-- engine = create_engine(
--   "postgresql://user:pass@localhost/clinceval",
--   pool_size=10,
--   max_overflow=20,
--   pool_pre_ping=True
-- )
