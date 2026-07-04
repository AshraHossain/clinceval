"""Integration failure handling: API timeouts must degrade gracefully, not crash."""
import pytest

import eval.regression_runner as runner


def test_pipeline_exception_becomes_integration_triage(monkeypatch, tmp_path):
    """A crashing pipeline (timeout, rate limit, ...) must yield INTEGRATION-tagged
    case results and a written report — never an unhandled crash."""

    def exploding_pipeline(query, k=3):
        raise TimeoutError("simulated API timeout")

    monkeypatch.setattr(runner, "run_pipeline", exploding_pipeline)
    monkeypatch.setattr(runner, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(runner, "BASELINE_PATH", tmp_path / "baseline.json")
    monkeypatch.setattr(runner, "DB_PATH", tmp_path / "eval.db")

    # High-weight cases crashing => safety gate => exit 1, which is the correct
    # release-blocking behavior for a fully broken pipeline
    with pytest.raises(SystemExit) as excinfo:
        runner.run()
    assert excinfo.value.code == 1

    reports = list((tmp_path / "reports").glob("run_*.md"))
    assert len(reports) == 1, "Report must still be written when every case crashes"
    body = reports[0].read_text()
    assert "INTEGRATION" in body


def test_judge_exception_is_not_swallowed(monkeypatch, tmp_path):
    """Judge failures must also surface as INTEGRATION, not silently pass cases."""

    def exploding_judge(case, pipeline_output):
        raise RuntimeError("simulated judge rate limit")

    monkeypatch.setattr(runner, "grade_output", exploding_judge)
    monkeypatch.setattr(runner, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(runner, "BASELINE_PATH", tmp_path / "baseline.json")
    monkeypatch.setattr(runner, "DB_PATH", tmp_path / "eval.db")

    with pytest.raises(SystemExit) as excinfo:
        runner.run()
    assert excinfo.value.code == 1

    reports = list((tmp_path / "reports").glob("run_*.md"))
    assert len(reports) == 1
    assert "INTEGRATION" in reports[0].read_text()
