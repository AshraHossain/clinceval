"""SQLite persistence for eval runs via SQLAlchemy Core."""
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"
DEFAULT_DB_PATH = BASE_DIR / "eval" / "eval_results.db"


def get_engine(db_path: Path = DEFAULT_DB_PATH) -> Engine:
    engine = create_engine(f"sqlite:///{db_path}")
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = ON")
        for statement in schema.split(";"):
            if statement.strip():
                conn.execute(text(statement))
    return engine


def record_run(
    engine: Engine,
    started_at: str,
    summary: dict[str, Any],
    cases: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> int:
    """Persist one regression run: upserts golden cases, inserts the run row,
    then one result row per case. Returns the run id."""
    with engine.begin() as conn:
        for case in cases:
            conn.execute(
                text(
                    "INSERT OR REPLACE INTO golden_cases "
                    "(id, category, difficulty, weight, expected_calculator) "
                    "VALUES (:id, :category, :difficulty, :weight, :expected_calculator)"
                ),
                {
                    "id": case.get("id"),
                    "category": case.get("category"),
                    "difficulty": case.get("difficulty"),
                    "weight": case.get("weight"),
                    "expected_calculator": case.get("expected_calculator"),
                },
            )

        run_row = conn.execute(
            text(
                "INSERT INTO eval_runs (started_at, total_cases, overall_pass_rate, "
                "faithfulness_pass_rate, clinical_relevance_pass_rate, safety_pass_rate, "
                "completeness_pass_rate, hard_gate_failures) "
                "VALUES (:started_at, :total, :overall, :faith, :rel, :safety, :comp, :gates)"
            ),
            {
                "started_at": started_at,
                "total": summary["total"],
                "overall": summary["overall_pass_rate"],
                "faith": summary["faithfulness_pass_rate"],
                "rel": summary["clinical_relevance_pass_rate"],
                "safety": summary["safety_pass_rate"],
                "comp": summary["completeness_pass_rate"],
                "gates": summary["hard_gate_failures"],
            },
        )
        run_id = run_row.lastrowid

        for result in results:
            scores = result.get("scores", {})
            conn.execute(
                text(
                    "INSERT INTO eval_results (run_id, case_id, triage, overall_pass, "
                    "safety_gate_fail, faithfulness, clinical_relevance, safety, "
                    "completeness, similarity, recommended_calculator) "
                    "VALUES (:run_id, :case_id, :triage, :overall_pass, :gate_fail, "
                    ":faith, :rel, :safety, :comp, :sim, :rec)"
                ),
                {
                    "run_id": run_id,
                    "case_id": result["id"],
                    "triage": result["triage"],
                    "overall_pass": int(result["overall_pass"]),
                    "gate_fail": int(result["safety_gate_fail"]),
                    "faith": scores.get("faithfulness"),
                    "rel": scores.get("clinical_relevance"),
                    "safety": scores.get("safety"),
                    "comp": scores.get("completeness"),
                    "sim": result.get("similarity"),
                    "rec": result.get("recommended_calculator"),
                },
            )
    return run_id
