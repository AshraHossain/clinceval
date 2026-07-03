import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.pipeline import run_pipeline
from eval.judge import grade_output
from eval.semantic_sim import calculate_semantic_similarity

BASE_DIR = Path(__file__).resolve().parent
GOLDEN_PATH = BASE_DIR / "golden_dataset.jsonl"
BASELINES_DIR = BASE_DIR / "baselines"
REPORTS_DIR = BASE_DIR / "reports"
BASELINE_PATH = BASELINES_DIR / "baseline.json"

AXES = ["faithfulness", "clinical_relevance", "safety", "completeness"]
PASS_THRESHOLD = 4
HARD_GATE_WEIGHT = "high"


def load_golden_cases(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Golden dataset not found at {path}")

    cases = []
    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                cases.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in golden dataset line {index}: {exc}") from exc
    return cases


def normalize_calculator_name(name: Any) -> str:
    if name is None:
        return "none"
    return "".join(ch.lower() for ch in str(name) if ch.isalnum())


def load_baseline(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_baseline(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def create_report(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(content)


def is_retrieval_successful(case: dict[str, Any], retrieved_chunk_ids: list[str]) -> bool:
    required_prefixes = case.get("must_cite", []) or []
    if not required_prefixes:
        return True

    normalized_retrieved = [chunk_id.lower() for chunk_id in retrieved_chunk_ids]
    for prefix in required_prefixes:
        if not any(chunk_id.startswith(prefix.lower()) for chunk_id in normalized_retrieved):
            return False
    return True


def is_generation_successful(case: dict[str, Any], pipeline_result: dict[str, Any]) -> bool:
    expected_calc = normalize_calculator_name(case.get("expected_calculator"))
    recommended_calc = normalize_calculator_name(pipeline_result["recommendation"].get("calculator"))
    if expected_calc == "none":
        return recommended_calc == "none"
    return expected_calc == recommended_calc


def infer_triage_tag(case: dict[str, Any], pipeline_result: dict[str, Any], judge_result: dict[str, Any]) -> str:
    if pipeline_result.get("error"):
        return "INTEGRATION"

    retrieved_ids = [chunk["id"] for chunk in pipeline_result.get("retrieved_chunks", [])]
    retrieval_ok = is_retrieval_successful(case, retrieved_ids)
    generation_ok = is_generation_successful(case, pipeline_result)

    if not retrieval_ok:
        return "RETRIEVAL"

    if not generation_ok:
        return "GENERATION"

    if any(score < PASS_THRESHOLD for score in judge_result["scores"].values()):
        return "JUDGE"

    return "PASS"


def summarize_case(case: dict[str, Any], pipeline_result: dict[str, Any], judge_result: dict[str, Any]) -> dict[str, Any]:
    expected_calc = case.get("expected_calculator")
    recommended_calc = pipeline_result["recommendation"].get("calculator")
    retrieval_ok = is_retrieval_successful(case, [chunk["id"] for chunk in pipeline_result.get("retrieved_chunks", [])])
    generation_ok = is_generation_successful(case, pipeline_result)
    pass_axes = {axis: judge_result["scores"][axis] >= PASS_THRESHOLD for axis in AXES}
    # A case only passes if the pipeline stages succeeded AND the judge axes clear threshold —
    # otherwise a retrieval miss with a lenient judge would count as PASS
    overall_pass = all(pass_axes.values()) and retrieval_ok and generation_ok and pipeline_result.get("citations_valid", False)
    safety_gate_fail = case.get("weight") == HARD_GATE_WEIGHT and not pass_axes["safety"]

    return {
        "id": case.get("id"),
        "category": case.get("category"),
        "weight": case.get("weight"),
        "expected_calculator": expected_calc,
        "recommended_calculator": recommended_calc,
        "retrieval_ok": retrieval_ok,
        "generation_ok": generation_ok,
        "citations_valid": pipeline_result.get("citations_valid", False),
        "scores": judge_result.get("scores", {}),
        "justifications": judge_result.get("justifications", {}),
        "metrics": judge_result.get("metrics", {}),
        "pass_axes": pass_axes,
        "overall_pass": overall_pass,
        "safety_gate_fail": safety_gate_fail,
        "triage": infer_triage_tag(case, pipeline_result, judge_result),
        # Rationale-vs-golden-rationale; falls back to calculator name for cases
        # that predate the expected_rationale field
        "similarity": calculate_semantic_similarity(
            pipeline_result["recommendation"].get("rationale", ""),
            case.get("expected_rationale") or case.get("expected_calculator", "")
        )
    }


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {axis: 0 for axis in AXES}
    summary["overall_passes"] = 0
    summary["total"] = len(results)
    summary["hard_gate_failures"] = 0
    summary["failure_counts"] = {"RETRIEVAL": 0, "GENERATION": 0, "JUDGE": 0, "INTEGRATION": 0, "DATA": 0, "PASS": 0}

    for result in results:
        for axis in AXES:
            if result["pass_axes"].get(axis):
                summary[axis] += 1
        if result["overall_pass"]:
            summary["overall_passes"] += 1
        if result["safety_gate_fail"]:
            summary["hard_gate_failures"] += 1
        summary["failure_counts"][result["triage"]] = summary["failure_counts"].get(result["triage"], 0) + 1

    for axis in AXES:
        summary[f"{axis}_pass_rate"] = round(summary[axis] / summary["total"] * 100, 1) if summary["total"] else 0.0
    summary["overall_pass_rate"] = round(summary["overall_passes"] / summary["total"] * 100, 1) if summary["total"] else 0.0
    return summary


def format_report(current_summary: dict[str, Any], case_results: list[dict[str, Any]], baseline_summary: dict[str, Any] | None, baseline_path: Path | None) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = ["# Regression Runner Report", "", f"Generated: {now}", "", f"Total cases: {current_summary['total']}", ""]
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Overall pass rate: **{current_summary['overall_pass_rate']}%** ({current_summary['overall_passes']}/{current_summary['total']})")
    for axis in AXES:
        lines.append(f"- {axis.replace('_', ' ').title()} pass rate: **{current_summary[f'{axis}_pass_rate']}%** ({current_summary[axis]}/{current_summary['total']})")
    lines.append(f"- Hard safety gate failures: **{current_summary['hard_gate_failures']}**")
    lines.append("")

    if baseline_summary and baseline_path:
        lines.append(f"## Baseline Comparison")
        lines.append("")
        lines.append(f"Baseline file: `{baseline_path}`")
        lines.append("")
        lines.append(f"- Baseline overall pass rate: **{baseline_summary['overall_pass_rate']}%**")
        for axis in AXES:
            lines.append(f"- Baseline {axis.replace('_', ' ').title()} pass rate: **{baseline_summary[f'{axis}_pass_rate']}%**")
        lines.append("")
        lines.append("### Delta vs baseline")
        lines.append("")
        overall_delta = round(current_summary['overall_pass_rate'] - baseline_summary['overall_pass_rate'], 1)
        lines.append(f"- Overall change: **{overall_delta:+.1f}%**")
        for axis in AXES:
            delta = round(current_summary[f'{axis}_pass_rate'] - baseline_summary[f'{axis}_pass_rate'], 1)
            lines.append(f"- {axis.replace('_', ' ').title()} change: **{delta:+.1f}%**")
        lines.append("")

    if current_summary['failure_counts']['PASS'] == current_summary['total']:
        lines.append("All cases passed. No regressions detected.")
        lines.append("")
    else:
        lines.append("## Failures")
        lines.append("")
        lines.append("| Case ID | Category | Weight | Expected | Recommended | Triage | Pass? | Safety Gate Fail |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for result in case_results:
            if result['overall_pass']:
                continue
            lines.append(
                f"| {result['id']} | {result['category']} | {result['weight']} | {result['expected_calculator']} | {result['recommended_calculator']} | {result['triage']} | {result['overall_pass']} | {result['safety_gate_fail']} |"
            )
        lines.append("")
        lines.append("### Detailed failing cases")
        lines.append("")
        for result in case_results:
            if result['overall_pass']:
                continue
            lines.append(f"#### {result['id']}")
            lines.append("")
            lines.append(f"- Category: {result['category']}")
            lines.append(f"- Weight: {result['weight']}")
            lines.append(f"- Expected calculator: {result['expected_calculator']}")
            lines.append(f"- Recommended calculator: {result['recommended_calculator']}")
            lines.append(f"- Triage: {result['triage']}")
            lines.append(f"- Retrieval OK: {result['retrieval_ok']}")
            lines.append(f"- Generation OK: {result['generation_ok']}")
            lines.append(f"- Citations valid: {result['citations_valid']}")
            lines.append(f"- Scores: {json.dumps(result['scores'])}")
            lines.append(f"- Justifications: {json.dumps(result['justifications'])}")
            lines.append(f"- Similarity: {result['similarity']:.3f}")
            lines.append("")

    return "\n".join(lines)


def run():
    baseline_data = load_baseline(BASELINE_PATH)
    cases = load_golden_cases(GOLDEN_PATH)
    results: list[dict[str, Any]] = []
    started = datetime.now(timezone.utc).isoformat()
    for case in cases:
        try:
            pipeline_result = run_pipeline(case["input"], k=3)
            judge_result = grade_output(case, pipeline_result)
            case_result = summarize_case(case, pipeline_result, judge_result)
            case_result["pipeline_result"] = pipeline_result
            case_result["judge_result"] = judge_result
        except Exception as exc:
            case_result = {
                "id": case.get("id"),
                "category": case.get("category"),
                "weight": case.get("weight"),
                "expected_calculator": case.get("expected_calculator"),
                "recommended_calculator": None,
                "retrieval_ok": False,
                "generation_ok": False,
                "citations_valid": False,
                "scores": {axis: 0 for axis in AXES},
                "justifications": {},
                "metrics": {},
                "pass_axes": {axis: False for axis in AXES},
                "overall_pass": False,
                "safety_gate_fail": case.get("weight") == HARD_GATE_WEIGHT,
                "triage": "INTEGRATION",
                "similarity": 0.0,
                "error": str(exc),
                "pipeline_result": {},
                "judge_result": {}
            }
        results.append(case_result)

    current_summary = build_summary(results)
    baseline_summary = build_summary(baseline_data["results"]) if baseline_data else None
    report_body = format_report(current_summary, results, baseline_summary, BASELINE_PATH if baseline_data else None)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORTS_DIR / f"run_{timestamp}.md"
    create_report(report_path, report_body)

    if baseline_data is None:
        save_baseline(BASELINE_PATH, {"created_at": started, "results": results, "summary": current_summary})
        print(f"Baseline created at {BASELINE_PATH}")

    print(report_body)
    print(f"Report written to {report_path}")

    if current_summary["hard_gate_failures"] > 0:
        print("Hard safety gate failure detected. Exiting with status 1.")
        sys.exit(1)

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
