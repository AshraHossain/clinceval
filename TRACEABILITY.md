# Traceability Matrix

Requirement → verification → evidence, DO-178C style: every requirement is
verified by a named, runnable check, and every check leaves an inspectable artifact.

| # | Requirement | Verified by | Evidence |
|---|---|---|---|
| R1 | Retriever returns the correct calculator chunk in top-3 (recall@3 ≥ 90%) | `tests/test_retriever.py::test_recall_at_three` | pytest output; per-doc cap in `app/retriever.py` |
| R2 | One calculator doc cannot crowd competitors out of top-k | `tests/test_retriever.py` + golden case `edge_qsofa_01` | commit `2f8d88e` (qsofa@rank-5 fix) |
| R3 | Generator output is structured JSON (calculator, rationale, confidence, citations) | `tests/test_pipeline.py::test_pipeline_e2e` | tool-use schema in `app/generator.py` |
| R4 | Citations must be a subset of retrieved chunks | `tests/test_adversarial.py::test_citations_are_subset_of_retrieved_chunks` | `citations_valid` flag in pipeline output |
| R5 | Assistant declines when no corpus calculator matches | `tests/test_adversarial.py::test_declines_when_calculator_not_in_corpus` | golden cases `adv_no_calc_*` |
| R6 | Assistant declines adult-only calculators for pediatric patients | `tests/test_adversarial.py::test_declines_adult_calculator_for_pediatric_patient` + E2E decline test | golden cases `adv_pediatric_*` (weight: high) |
| R7 | Assistant declines when required inputs are missing | `tests/test_adversarial.py::test_declines_on_missing_required_inputs` | golden cases `adv_missing_vitals_*` |
| R8 | Judge scores 4 axes against explicit 1–5 anchors | `tests/test_judge.py` | `eval/rubric.yaml` anchor definitions |
| R9 | Judge agreement with hand labels ≥ 80% | `tests/test_judge.py::test_judge_calibration` | `eval/calibration_set.json` |
| R10 | Every failing case receives exactly one triage tag | `tests/test_regression_runner.py`; Phase 6 demonstration | `phase6_before.md` (3 bug classes, 3 correct tags) |
| R11 | Safety-axis failure on a high-weight case blocks release (exit ≠ 0) | `tests/test_integration_failures.py` (SystemExit 1) | `phase6_before.md`: 2 hard gates, exit 1 |
| R12 | Pipeline/judge crashes degrade to INTEGRATION-tagged results, never a crash | `tests/test_integration_failures.py` (both tests) | report still written under total failure |
| R13 | Every run is diffed against a stored baseline | `eval/regression_runner.py::load_baseline` + report delta section | `eval/baselines/baseline.json`; any `run_*.md` |
| R14 | Eval results are queryable in SQL with referential integrity | `tests/test_db.py` (round-trip + integrity checks) | `db/schema.sql`, `db/integrity_checks.sql` |
| R15 | Pass-rate trend over time is queryable (window functions) | `tests/test_db.py::test_integrity_checks_run_clean` | trend query #4 in `db/integrity_checks.sql` |
| R16 | Chat UI renders recommendation, loading, error, and decline states | Playwright `tests/e2e/chat.spec.ts` (4 tests) + `smoke.spec.ts` | Playwright report |
| R17 | E2E assertions are semantic, not exact-match | `chat.spec.ts` happy path (regex on calculator concept) | spec source |
| R18 | Every LLM call is metered: latency, tokens, estimated cost per run | `monitoring/latency_cost_tracker.py` via the single LLM wrapper | "Latency & Cost" section in every run report |
| R19 | Full demo runs offline and deterministically (no API key) | entire pytest + Playwright + runner suite in CI | `.github/workflows/ci.yml` |
| R20 | Golden dataset content is human-reviewed before merge | PR review process | merged PR #1 (clinical review checklist) |
