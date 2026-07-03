# ClinCalc-Eval — Implementation Plan

## Project goal

Build **ClinCalc-Eval**, a QA/evaluation harness for a mock LLM-powered clinical
assistant that recommends medical calculators (CHA₂DS₂-VASc, Wells' Criteria, MELD,
etc.) based on patient symptoms, with cited rationale. The point of the project is
not the assistant itself — it's the **evaluation and QA infrastructure around it**:
golden dataset regression testing, LLM-as-judge scoring, hallucination/citation
checking, retrieval-vs-generation failure triage, Playwright E2E tests, SQL-backed
eval result storage, and latency/cost monitoring. Portfolio project for an AI
Product QA Engineer interview at MDCalc — demoable end-to-end in under 5 minutes,
every design decision justified in one sentence.

**Process rule: stop and report after every phase before starting the next.**

---

## Phase 0 — Repo & environment setup

1. `git init`, GitHub repo `AshraHossain/clinceval`, `.gitignore` (Python), MIT license.
2. Python 3.12 virtualenv. `requirements.txt`: anthropic, chromadb, sentence-transformers,
   pytest, pandas, pyyaml, fastapi, uvicorn, sqlalchemy. SQLite (stdlib) not Postgres —
   deliberate demo-scope decision.
3. `playwright install` for Node/TS E2E side; separate `package.json` in `tests/e2e/`.
4. `CLAUDE.md` with project conventions.
5. Top-level `README.md` stub (filled fully at Phase 8).

**DoD:** `pytest` runs (even with zero tests), `playwright test` runs, repo pushed to
GitHub with clean initial commit.

---

## Phase 1 — Corpus & retriever (`app/retriever.py`)

1. Corpus: 10-15 markdown/JSON docs on real calculators — CHA₂DS₂-VASc, Wells' (PE and
   DVT), MELD, CURB-65, HEART Score, Glasgow Coma Scale. Each: name, purpose, inputs
   required, scoring logic, interpretation bands.
2. Paragraph-level chunking (don't over-engineer).
3. Embed with sentence-transformers `all-MiniLM-L6-v2` into local vector store (Chroma).
4. `retrieve(query: str, k: int) -> list[Chunk]`.
5. `tests/test_retriever.py`: recall@k tests, 8-10 hand-picked queries with known chunk IDs.

**DoD:** recall@3 ≥ 90% on hand-picked test queries; tests pass in CI.

---

## Phase 2 — Generator & pipeline (`app/generator.py`, `app/pipeline.py`)

1. `generate(query, retrieved_context) -> {calculator, rationale, citations}` — Anthropic
   API, system prompt: recommend only from provided context, cite input fields used.
2. Structured output via tool-use/JSON (calculator, rationale, confidence, citations as
   chunk IDs) — deterministic downstream parsing.
3. `pipeline.py`: retrieve → generate → citation-check → structured result.
4. Deliberately simple — it's the thing under test. Bugs added later (Phase 6) must be traceable.

**DoD:** pipeline runs end-to-end on a manual test query, returns valid structured JSON.

**Checkpoint:** install graphify (`pip install graphifyy && graphify install --platform claude --project`).

---

## Phase 3 — Golden dataset (`eval/golden_dataset.jsonl`)

1. 40-60 cases, four buckets: core (~25), edge/ambiguous (~15), adversarial/
   hallucination-inducing (~10), safety-critical (~10, overlap allowed, `weight: high`).
2. Each case: `id`, `input`, `expected_calculator`, `expected_score_range`,
   `must_cite`, `category`, `difficulty`, `weight`.
3. Adversarial: no-matching-calculator (must decline), contradictory inputs, pediatric
   case vs adult-only calculator, missing required vitals.
4. JSONL, one case per line.

**DoD:** 40+ cases committed, **human-reviewed for clinical plausibility before "golden".**

---

## Phase 4 — Evaluation layer (`eval/judge.py`, `eval/rubric.yaml`, `eval/semantic_sim.py`)

1. `rubric.yaml`: 4 axes — faithfulness, clinical relevance, safety, completeness —
   1-5 scale with explicit anchor descriptions per level. Run design past
   "ask the council" before finalizing.
2. `judge.py`: separate LLM call, different/pinned model vs generator (shared-bias
   avoidance), scores output vs rubric given golden reference.
3. `semantic_sim.py`: embedding cosine sim generated-vs-golden rationale — cheap secondary
   signal; note in comments it misses numeric/threshold errors.
4. Judge calibration set: 10-15 hand-labeled cases, measure judge agreement.

**DoD:** judge scores all golden cases; calibration ≥80% agreement with hand labels
(or an articulated explanation + next step).

---

## Phase 5 — Regression runner & failure triage (`eval/regression_runner.py`)

1. Full golden set through pipeline, judge-scored, pass rate per axis + overall,
   diff vs stored baseline in `eval/baselines/`.
2. Auto-triage failing cases: RETRIEVAL / GENERATION / JUDGE / INTEGRATION / DATA
   (expected chunk not in top-k → RETRIEVAL; retrieved but wrong output → GENERATION;
   judge disagrees with known-correct calibration case → JUDGE; exception/timeout →
   INTEGRATION).
3. Run report `eval/reports/run_<timestamp>.md`: pass rate, per-axis breakdown, failures
   with triage tags, delta vs baseline.
4. Release gate: safety-axis failure on `weight: high` case = hard block; other
   regressions = warning.

**DoD:** `python -m eval.regression_runner` produces full report, exits non-zero on
hard-gate failure.

---

## Phase 6 — Deliberately embed 3 bugs + adversarial/integration tests

1. 3 realistic bugs, one per category: retrieval (off-by-one/case-sensitivity in chunk
   lookup), generation (prompt doesn't forbid out-of-context calculator → hallucination
   on adversarial cases), scoring (rubric weight/division error in aggregate).
2. `tests/test_adversarial.py`, `tests/test_integration_failures.py` (mock timeout/
   rate-limit, assert graceful degradation).
3. Regression runner catches all 3 with correct triage tags; fix; before/after reports.

**DoD:** "before" report showing 3 caught regressions with correct root-cause tags +
"after" report showing clean pass.

---

## Phase 7 — Playwright E2E + SQL layer

Playwright (`tests/e2e/`):
1. Minimal chat UI (simple page hitting FastAPI endpoint wrapping `pipeline.py`).
2. E2E: happy path, loading state, error state (mock API failure), semantic assertion.

SQL (`db/`):
1. `schema.sql`: `eval_runs`, `eval_results`, `golden_cases`, `triage_tags` with FKs.
2. Wire regression runner to SQLite via SQLAlchemy.
3. `integrity_checks.sql`: duplicate runs, orphaned results, pass-rate trend
   (window function).

**DoD:** Playwright suite green; eval results queryable, one trend query demoed.

---

## Phase 8 — Docs, monitoring, polish

1. `monitoring/latency_cost_tracker.py`: wraps generator/judge calls, logs tokens +
   latency + estimated cost per run, surfaced in report.
2. Full `README.md`: architecture diagram, quickstart, before/after bug-catch report,
   "design decisions" section (why 4 axes, why separate judge model, why SQLite).
3. `TRACEABILITY.md`: requirement → test → evidence matrix (DO-178C callback).
4. GitHub Actions CI: pytest + playwright + regression_runner on every PR; fail build
   on hard-gate safety regression.

**DoD:** fresh clone → one command → full demo under 5 minutes; README interview-ready;
CI green on GitHub.
