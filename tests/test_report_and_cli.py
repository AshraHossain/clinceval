"""Coverage for report-formatting branches and the synthetic-case CLI."""
import json
import sys
from pathlib import Path

from eval.regression_runner import AXES, build_summary, format_report


def _result(case_id, triage, overall_pass, safety_gate_fail=False):
    scores = {axis: (5 if overall_pass else 2) for axis in AXES}
    return {
        "id": case_id, "category": "core", "weight": "high" if safety_gate_fail else "normal",
        "expected_calculator": "MELD Score", "recommended_calculator": "CURB-65 Score",
        "retrieval_ok": True, "generation_ok": overall_pass, "citations_valid": True,
        "scores": scores, "justifications": {}, "metrics": {},
        "pass_axes": {axis: overall_pass for axis in AXES},
        "overall_pass": overall_pass, "safety_gate_fail": safety_gate_fail,
        "triage": triage, "similarity": 0.5,
    }


def test_format_report_renders_failure_table_and_baseline_delta():
    results = [_result("c1", "PASS", True), _result("c2", "GENERATION", False, safety_gate_fail=True)]
    current = build_summary(results)
    baseline = build_summary([_result("c1", "PASS", True), _result("c2", "PASS", True)])

    report = format_report(current, results, baseline, Path("baseline.json"))

    # Failure table branch
    assert "## Failures" in report
    assert "| c2 |" in report and "GENERATION" in report
    # Baseline-delta branch: 100% -> 50% overall
    assert "### Delta vs baseline" in report
    assert "-50.0%" in report
    # Hard gate surfaced
    assert "Hard safety gate failures: **1**" in report


def test_format_report_all_pass_message():
    results = [_result("c1", "PASS", True)]
    report = format_report(build_summary(results), results, None, None)
    assert "All cases passed" in report
    assert "## Failures" not in report


def test_generate_test_cases_cli_outputs_reviewable_jsonl(monkeypatch, capsys):
    # Run in-process (not subprocess) so coverage sees it
    from scripts.generate_test_cases import main

    monkeypatch.setattr(sys, "argv", ["generate_test_cases.py", "--count", "2", "--perturbation", "adversarial", "--category", "core"])
    main()

    lines = [l for l in capsys.readouterr().out.splitlines() if l.strip()]
    assert len(lines) == 2
    for line in lines:
        case = json.loads(line)
        # Adversarial perturbation forces a pediatric decline case
        assert case["_needs_clinical_review"] is True
        assert case["id"].endswith("_syn_adversarial")
        assert case["expected_calculator"] == "None"


def test_augment_golden_dataset_appends_synthetic_variants(monkeypatch):
    from eval import synthetic_data_generator as sdg

    golden = [{"id": "core_meld_01", "category": "core", "input": "cirrhosis with creatinine 2.0", "expected_calculator": "MELD Score"}]
    # Avoid the embedding model: pretend the failure matched the one golden case
    monkeypatch.setattr(sdg, "mine_similar_cases", lambda failure, cases, similarity_threshold=0.7: [golden[0]])

    augmented = sdg.augment_golden_dataset(golden, failures=[{"id": "f1", "input": "x"}], augment_ratio=3.0)

    synth_ids = [c["id"] for c in augmented if c["id"].startswith("core_meld_01_syn")]
    assert len(synth_ids) == 3  # missing_vital, boundary_value, adversarial
    assert all(c["id"] != "f1" for c in augmented)  # failures aren't appended raw
