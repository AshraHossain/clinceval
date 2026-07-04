-- Integrity and trend queries for eval result storage.
-- Run against eval/eval_results.db, e.g.:
--   sqlite3 eval/eval_results.db < db/integrity_checks.sql

-- 1. Duplicate runs: more than one run recorded within the same minute
--    (started_at is UNIQUE, so exact duplicates are impossible — this catches
--    accidental double-invocations)
SELECT substr(started_at, 1, 16) AS run_minute, COUNT(*) AS runs_in_minute
FROM eval_runs
GROUP BY run_minute
HAVING COUNT(*) > 1;

-- 2. Orphaned results: eval_results rows pointing at a missing run or case
SELECT r.run_id, r.case_id
FROM eval_results r
LEFT JOIN eval_runs ru ON ru.id = r.run_id
LEFT JOIN golden_cases gc ON gc.id = r.case_id
WHERE ru.id IS NULL OR gc.id IS NULL;

-- 3. Results whose triage tag is not in the taxonomy
SELECT r.run_id, r.case_id, r.triage
FROM eval_results r
LEFT JOIN triage_tags t ON t.tag = r.triage
WHERE t.tag IS NULL;

-- 4. Pass-rate trend over time (window functions):
--    delta vs previous run and 5-run rolling average
SELECT
    id,
    started_at,
    overall_pass_rate,
    round(overall_pass_rate
        - LAG(overall_pass_rate) OVER (ORDER BY started_at), 1) AS delta_vs_prev,
    round(AVG(overall_pass_rate) OVER (
        ORDER BY started_at ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 1) AS rolling_avg_5,
    hard_gate_failures
FROM eval_runs
ORDER BY started_at;

-- 5. Chronic offenders: cases that failed in the most runs
SELECT case_id,
       SUM(CASE WHEN overall_pass = 0 THEN 1 ELSE 0 END) AS fail_count,
       COUNT(*) AS total_runs,
       GROUP_CONCAT(DISTINCT triage) AS triage_tags_seen
FROM eval_results
GROUP BY case_id
HAVING fail_count > 0
ORDER BY fail_count DESC;
