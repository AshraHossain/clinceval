import os
import json
import sys
import tempfile
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from eval.regression_runner import (
    BASELINES_DIR,
    REPORTS_DIR,
    BASELINE_PATH,
    load_golden_cases,
    load_baseline,
    save_baseline,
    build_summary,
    run,
)

BASE_DIR = Path(__file__).resolve().parent.parent
GOLDEN_PATH = BASE_DIR / "eval" / "golden_dataset.jsonl"


def test_load_golden_cases():
    cases = load_golden_cases(GOLDEN_PATH)
    assert isinstance(cases, list)
    assert len(cases) > 0
    assert all("id" in case and "input" in case for case in cases)


def test_baseline_round_trip(tmp_path):
    data = {"created_at": "2026-01-01T00:00:00Z", "results": [], "summary": {}}
    baseline_file = tmp_path / "baseline.json"
    save_baseline(baseline_file, data)

    loaded = load_baseline(baseline_file)
    assert loaded == data


def test_build_summary_empty():
    summary = build_summary([])
    assert summary["total"] == 0
    assert summary["overall_pass_rate"] == 0.0


@pytest.mark.skipif(
    os.environ.get("ANTHROPIC_API_KEY") is None,
    reason="Skip full regression runner test when Anthropics API key is unavailable"
)
def test_full_runner_creates_report(tmp_path, monkeypatch):
    # Override baseline and report paths to isolate the test environment
    monkeypatch.setenv("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
    report_dir = tmp_path / "reports"
    baseline_dir = tmp_path / "baselines"
    monkeypatch.setattr("eval.regression_runner.REPORTS_DIR", report_dir)
    monkeypatch.setattr("eval.regression_runner.BASELINE_PATH", baseline_dir / "baseline.json")

    from eval import regression_runner

    # Force a smaller dataset if available to reduce test runtime
    cases = load_golden_cases(GOLDEN_PATH)
    assert len(cases) > 0

    exit_code = regression_runner.run()
    assert exit_code == 0 or exit_code == 1
    assert report_dir.exists()
    assert any(report_dir.iterdir())
    assert baseline_dir.exists()
    assert (baseline_dir / "baseline.json").exists()
