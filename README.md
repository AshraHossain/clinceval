# ClinCalc-Eval

QA/evaluation harness for a mock LLM-powered clinical assistant that recommends
medical calculators (CHA₂DS₂-VASc, Wells' Criteria, MELD, CURB-65, …) with cited
rationale. **The evaluation infrastructure is the product** — the assistant exists
to be tested: golden dataset regression, LLM-as-judge scoring, hallucination and
citation checking, retrieval-vs-generation failure triage, Playwright E2E, SQL-backed
result storage, and latency/cost monitoring.

## Architecture

```
             ┌───────────────┐  top-k chunks  ┌────────────────┐
  query ───▶ │   retriever   │ ─────────────▶ │   generator    │──▶ {calculator,
             │ Chroma+MiniLM │  (per-doc cap) │ Haiku / mock   │     rationale,
             └───────────────┘                └───────┬────────┘     citations}
                                                      │ citation check
             ┌────────────────────────────────────────▼───────┐
             │                run_pipeline()                  │  ◀── FastAPI /api/recommend
             └────────────────────────┬───────────────────────┘      (chat UI + Playwright E2E)
                                      │
        golden_dataset.jsonl (41) ───▶│  regression_runner
                                      ▼
                  ┌────────────────────────────────────┐
                  │  judge (Sonnet / mock, 4-axis      │
                  │  rubric) + semantic similarity     │
                  └────────────────┬───────────────────┘
                                   │ triage: RETRIEVAL / GENERATION /
                                   │         JUDGE / INTEGRATION / DATA
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
        report .md            SQLite DB          baseline diff
     (+ latency/cost)     (trend queries)     hard safety gate → exit 1
```

## Quickstart

**Local (venv):**

```bash
make demo          # venv + deps + unit/integration tests + full golden-set eval
make e2e           # Playwright suite (boots the FastAPI app automatically)
make serve         # chat UI at http://localhost:8000
```

**Docker:**

```bash
docker-compose up -d
# Chat UI: http://localhost:8000
# API: http://localhost:8000/api/recommend
```

Or manual venv: `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt`,
then `.venv/bin/python -m eval.regression_runner`.

**Mock-first by design.** Without `ANTHROPIC_API_KEY`, a deterministic keyword-router
stands in for the generator and a rule-based grader for the judge — free, reproducible,
CI-safe. Setting the key switches both to real pinned Claude models with no code changes.

See [DOCKER.md](DOCKER.md) for compose configuration, environment variables, and K8s roadmap.

## The proof: catching planted bugs

Three realistic bugs were deliberately embedded (commit `553b1fb`), one per failure
class. The regression runner caught **all three with correct root-cause tags**:

| Planted bug | Where | Caught as |
|---|---|---|
| Retriever lost its over-fetch → per-doc cap starves competing calculators | `app/retriever.py` | `RETRIEVAL` |
| Pediatric safety guard removed → adult-only calculators recommended for children | `app/llm.py` | `GENERATION` (+2 hard safety gates) |
| Citation-validity check inverted → valid citations penalized | `eval/judge.py` | `JUDGE` |

Before: **0% pass, 2 hard safety gate failures, exit 1** ([phase6_before.md](eval/reports/phase6_before.md)).
After fix: **41/41 pass, exit 0** ([phase6_after.md](eval/reports/phase6_after.md)).

## Design decisions

- **Four judge axes (faithfulness, clinical relevance, safety, completeness), each with
  explicit 1–5 anchors** — "5 = good" left undefined is how judge drift starts; anchors
  make disagreements arbitrable ([rubric.yaml](eval/rubric.yaml)).
- **Judge is a different, version-pinned model from the generator** (Sonnet vs Haiku) —
  a judge sharing the generator's weights shares its blind spots; pinning stops silent
  grading shifts when "latest" moves.
- **Case pass = judge axes AND retrieval AND generation AND citation validity** — a
  lenient judge must not be able to mask a retrieval miss.
- **Hard release gate: safety-axis failure on a `weight: high` case, nothing else** —
  one unambiguous blocker keeps the gate credible; everything else is a warning.
- **Every failure gets exactly one triage tag** (RETRIEVAL/GENERATION/JUDGE/INTEGRATION/DATA)
  — pass rates say *that* it broke; triage says *where to look first*.
- **Semantic similarity is a secondary signal only** — cosine similarity is blind to
  numeric/threshold errors ("GCS 14" ≈ "GCS 15"), so it supplements, never replaces,
  the judge.
- **SQLite over Postgres** — the demo must run from a fresh clone with zero services;
  the SQLAlchemy layer makes the swap trivial when needed.
- **Golden dataset content requires human clinical review** before it's "golden" —
  AI-drafted, human-verified (see merged PR #1).

## Layout

```
app/        retriever, generator, pipeline, LLM wrapper, FastAPI + chat UI
app/corpus/ 13 calculator reference docs (the retrieval corpus)
eval/       golden dataset, rubric, judge, semantic sim, regression runner, SQLite layer
db/         schema.sql, integrity_checks.sql (trend + orphan + duplicate queries)
monitoring/ latency/token/cost tracker (surfaced in every run report)
tests/      pytest unit/integration/adversarial + Playwright E2E (tests/e2e)
```

See [TRACEABILITY.md](TRACEABILITY.md) for the requirement → test → evidence matrix
and [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the build plan.
