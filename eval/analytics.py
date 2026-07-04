"""Query analytics over stored eval runs: chronic offenders, triage distribution,
judge drift, run-vs-run diff, and retention cleanup.

CLI: python -m eval.analytics [diff RUN_A RUN_B]
"""
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.engine import Engine

AXES = ["faithfulness", "clinical_relevance", "safety", "completeness"]


def chronic_offenders(engine: Engine, min_failures: int = 1) -> list[dict]:
    """Cases failing most often across all runs — fix these first."""
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT case_id, COUNT(*) AS fail_count, "
            "GROUP_CONCAT(DISTINCT triage) AS triage_tags "
            "FROM eval_results WHERE overall_pass = 0 "
            "GROUP BY case_id HAVING COUNT(*) >= :min_failures "
            "ORDER BY fail_count DESC"
        ), {"min_failures": min_failures}).mappings().all()
    return [dict(r) for r in rows]


def triage_distribution(engine: Engine, run_id: int | None = None) -> dict[str, int]:
    """Failure counts per triage tag; latest run by default."""
    with engine.connect() as conn:
        if run_id is None:
            run_id = conn.execute(text("SELECT MAX(id) FROM eval_runs")).scalar()
        rows = conn.execute(text(
            "SELECT triage, COUNT(*) AS n FROM eval_results "
            "WHERE run_id = :run_id GROUP BY triage"
        ), {"run_id": run_id}).all()
    return {tag: n for tag, n in rows}


def judge_drift(engine: Engine, run_a: int, run_b: int) -> dict[str, float]:
    """Mean per-axis score delta between two runs. |delta| >= 1.0 on any axis
    suggests the judge (or its anchors) shifted, not the system under test."""
    drift = {}
    with engine.connect() as conn:
        for axis in AXES:
            deltas = conn.execute(text(
                f"SELECT AVG(b.{axis}) - AVG(a.{axis}) "
                f"FROM eval_results a JOIN eval_results b ON a.case_id = b.case_id "
                f"WHERE a.run_id = :run_a AND b.run_id = :run_b"
            ), {"run_a": run_a, "run_b": run_b}).scalar()
            drift[axis] = round(deltas or 0.0, 2)
    return drift


def show_diff(engine: Engine, run_a: int, run_b: int) -> list[dict]:
    """Cases whose pass/fail flipped between two runs."""
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT a.case_id, a.overall_pass AS pass_a, b.overall_pass AS pass_b, "
            "a.triage AS triage_a, b.triage AS triage_b "
            "FROM eval_results a JOIN eval_results b ON a.case_id = b.case_id "
            "WHERE a.run_id = :run_a AND b.run_id = :run_b "
            "AND a.overall_pass != b.overall_pass"
        ), {"run_a": run_a, "run_b": run_b}).mappings().all()
    return [dict(r) for r in rows]


def retriever_diversity(retrieved_chunks: list[dict]) -> float:
    """Distinct docs / chunks in a retrieval result. 1.0 = every chunk from a
    different doc; low values mean one calculator is crowding out the rest."""
    if not retrieved_chunks:
        return 0.0
    docs = {chunk["id"].rsplit("_chunk_", 1)[0] for chunk in retrieved_chunks}
    return round(len(docs) / len(retrieved_chunks), 2)


def purge_old_runs(engine: Engine, keep_days: int = 90) -> int:
    """Retention: delete runs (and their results, via FK cascade) older than
    keep_days. Returns number of runs deleted."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=keep_days)).isoformat()
    with engine.begin() as conn:
        old_ids = [r[0] for r in conn.execute(
            text("SELECT id FROM eval_runs WHERE started_at < :cutoff"), {"cutoff": cutoff}
        ).all()]
        for run_id in old_ids:
            conn.execute(text("DELETE FROM eval_results WHERE run_id = :r"), {"r": run_id})
            conn.execute(text("DELETE FROM eval_runs WHERE id = :r"), {"r": run_id})
    return len(old_ids)


if __name__ == "__main__":
    from eval.db import get_engine

    engine = get_engine()
    if len(sys.argv) == 4 and sys.argv[1] == "diff":
        for row in show_diff(engine, int(sys.argv[2]), int(sys.argv[3])):
            print(row)
    else:
        print("Chronic offenders:", chronic_offenders(engine) or "none")
        print("Latest triage distribution:", triage_distribution(engine))
