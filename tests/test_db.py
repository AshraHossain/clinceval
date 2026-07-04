"""SQLite persistence: schema integrity, FK wiring, and the trend query."""
from pathlib import Path

from sqlalchemy import text

from eval.db import get_engine, record_run

BASE_DIR = Path(__file__).resolve().parent.parent
INTEGRITY_SQL = (BASE_DIR / "db" / "integrity_checks.sql").read_text(encoding="utf-8")

CASES = [
    {"id": "c1", "category": "core", "difficulty": "easy", "weight": "normal", "expected_calculator": "MELD"},
    {"id": "c2", "category": "safety", "difficulty": "hard", "weight": "high", "expected_calculator": "GCS"},
]

def _result(case_id, triage, overall_pass, gate_fail=False):
    return {
        "id": case_id, "triage": triage, "overall_pass": overall_pass,
        "safety_gate_fail": gate_fail, "similarity": 0.8, "recommended_calculator": "MELD",
        "scores": {"faithfulness": 5, "clinical_relevance": 5, "safety": 5, "completeness": 4},
    }

SUMMARY = {
    "total": 2, "overall_pass_rate": 50.0, "faithfulness_pass_rate": 100.0,
    "clinical_relevance_pass_rate": 100.0, "safety_pass_rate": 50.0,
    "completeness_pass_rate": 100.0, "hard_gate_failures": 1,
}


def test_record_run_round_trip(tmp_path):
    engine = get_engine(tmp_path / "test.db")
    run_id = record_run(engine, "2026-07-03T00:00:00Z", SUMMARY, CASES,
                        [_result("c1", "PASS", True), _result("c2", "GENERATION", False, gate_fail=True)])

    with engine.connect() as conn:
        runs = conn.execute(text("SELECT total_cases, hard_gate_failures FROM eval_runs")).all()
        assert runs == [(2, 1)]
        results = conn.execute(
            text("SELECT case_id, triage, overall_pass FROM eval_results WHERE run_id = :r ORDER BY case_id"),
            {"r": run_id},
        ).all()
        assert results == [("c1", "PASS", 1), ("c2", "GENERATION", 0)]


def test_integrity_checks_run_clean(tmp_path):
    engine = get_engine(tmp_path / "test.db")
    record_run(engine, "2026-07-03T00:00:00Z", SUMMARY, CASES,
               [_result("c1", "PASS", True), _result("c2", "JUDGE", False)])
    record_run(engine, "2026-07-03T01:00:00Z", SUMMARY, CASES,
               [_result("c1", "PASS", True), _result("c2", "PASS", True)])

    statements = []
    for chunk in INTEGRITY_SQL.split(";"):
        body = "\n".join(l for l in chunk.splitlines() if not l.strip().startswith("--")).strip()
        if body:
            statements.append(body)

    with engine.connect() as conn:
        outputs = [conn.execute(text(s)).all() for s in statements]

    # No duplicate-minute runs, no orphans, no unknown triage tags
    assert outputs[0] == [] and outputs[1] == [] and outputs[2] == []
    # Trend query returns one row per run with a delta on the second
    trend = outputs[3]
    assert len(trend) == 2
    assert trend[1].delta_vs_prev == 0.0
    # Chronic offender: c2 failed once
    assert [(row.case_id, row.fail_count) for row in outputs[4]] == [("c2", 1)]
