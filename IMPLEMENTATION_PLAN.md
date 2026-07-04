# Implementation Plan

ClinCalc-Eval built in 9 phases. Each has a DoD; phases gate sequentially. This maps commits to phases.

## Phase 1: Core Pipeline (e1f6b5d–b2e8c9f)

**Goal:** Retriever + generator + judge run end-to-end on a single query.

**What built:**
- `app/retriever.py`: Chroma + MiniLM-L6-v2, corpus of 13 calculator docs, per-doc cap to prevent crowding
- `app/generator.py`: Tool-use wrapper for Claude (mock or live)
- `app/judge.py`: 4-axis rubric (faithfulness, clinical_relevance, safety, completeness), 1–5 anchors
- `app/pipeline.py`: Orchestrate retriever → generator → judge

**Tests:** `test_retriever.py`, `test_judge.py`, `test_pipeline.py`. DoD: pipeline runs end-to-end, valid structured JSON output.

---

## Phase 2: Golden Dataset (PR #1, merged 60cc9dc)

**Goal:** 41 clinical cases covering core, edge, adversarial, safety.

**What built:**
- `eval/golden_dataset.jsonl`: 41 cases, each with expected_calculator, expected_rationale (AI-drafted, human-reviewed), must_cite, weight
- Case taxonomy: core (happy path), edge (boundary), adv (adversarial), safety (decline)
- Weights: normal (39) vs high (2) for hard release gates

**Tests:** Manual clinical review via PR checklist (merged PR #1). DoD: all cases have expected_rationale; human sign-off on plausibility.

---

## Phase 3: Regression Runner + Rubric (e8d9c2a–2f8d88e)

**Goal:** Load 41 cases, grade all, compute per-axis pass rates + baseline delta.

**What built:**
- `eval/regression_runner.py`: Load cases, run pipeline, call judge, compare vs expected, report pass rates
- Pass semantics: all judge axes AND retrieval_ok AND generation_ok AND citations_valid
- Baseline save/load for delta reporting
- `eval/rubric.yaml`: Full 1–5 anchor descriptions per axis

**Tests:** `test_regression_runner.py` (baseline diffs). DoD: regression runner outputs report, exits 0 on full pass.

---

## Phase 4: Triage Logic (3c9e1a4–8b2f6c1)

**Goal:** When a case fails, pinpoint root cause: RETRIEVAL / GENERATION / JUDGE / INTEGRATION / DATA.

**What built:**
- `infer_triage_tag()`: Check retrieval_ok → generation_ok → citations_valid → judge scores, assign single tag
- Five tags: RETRIEVAL (chunk not in top-k), GENERATION (wrong calc), JUDGE (score <threshold), INTEGRATION (timeout), DATA (invalid input)

**Tests:** Phase 6 regression (3 planted bugs → 3 correct tags). DoD: every failing case gets exactly one tag; tag directs the fix.

---

## Phase 5: Mock-First Architecture (5d1a2e3–9f4e7b6)

**Goal:** Run full demo without API key; swap to live API when key present.

**What built:**
- `app/llm.py::LLMClient.call_claude`: Keyword router (30+ variables) for deterministic mock responses
- Pediatric safety guard (declines adult-only calcs for children)
- Calculator disambiguation: CURB-65 vs SIRS vs qSOFA, Child-Pugh vs MELD
- Mock judge: rule-based scoring on citation validity, calculator match, input coverage
- `monitoring/latency_cost_tracker.py`: Records all calls (mock=free, API=$$)

**Tests:** All 41 cases pass 100% in mock mode. DoD: demo runs offline, reproducible, zero API calls.

---

## Phase 6: Deliberate Bug Injection (553b1fb)

**Goal:** Prove regression system catches real bugs with correct triage.

**What embedded:**
1. **RETRIEVAL**: Removed per-doc cap → qSOFA lost to CURB-65 dominance
2. **GENERATION**: Removed pediatric safety guard → adult calcs for children (2 hard gates)
3. **JUDGE**: Inverted citation-validity check → penalized valid citations

**Result:** 0% pass, 2 hard safety gates, exit 1. Fixed all three: 41/41 pass, exit 0.

**Artifacts:** `eval/reports/phase6_before.md`, `phase6_after.md` (in PR #2).

**DoD:** Regression runner catches all 3 planted bugs with correct root-cause tags.

---

## Phase 7: Web + E2E + SQL (6e375fd–0ffda3b)

**Goal:** User-facing chat UI, Playwright E2E, persistent result storage.

**What built:**
- `app/server.py`: FastAPI, `POST /api/recommend`, static HTML serve, retriever warmup on lifespan
- `app/static/index.html`: Chat UI, loading/error/result/decline states
- `tests/e2e/chat.spec.ts`: 4 tests (happy path, loading, error, decline), semantic assertions
- `db/schema.sql`: 5 tables (eval_runs, eval_results, golden_cases, triage_tags), FK'd
- `eval/db.py`: SQLAlchemy Core persistence, record_run transaction
- `db/integrity_checks.sql`: 5 queries (duplicates, orphans, tags, trend, chronic offenders)

**Tests:** pytest 21 passed, Playwright 5/5.

**DoD:** Chat UI works end-to-end; E2E green; results queryable in SQL.

---

## Phase 8: Monitoring, CI, Docs, Coverage (058d860–537ab44)

**Goal:** Latency/cost tracking, GitHub Actions safety gate, full docs, 87% test coverage.

**What built:**
- `monitoring/latency_cost_tracker.py`: Every LLM call metered (latency, tokens, USD from pinned-model pricing)
- `.github/workflows/ci.yml`: pytest + golden-set (--cov-fail-under=80, hard safety gate), Playwright E2E
- `README.md`: Architecture diagram, quickstart, planted-bug story, design decisions
- `TRACEABILITY.md`: 20-row requirement → test → evidence matrix
- `Makefile`: `make demo` = fresh clone to full eval
- `tests/test_server.py`, `test_triage_and_judge.py`: Unit + integration coverage (87% total)

**Tests:** 37 passed, 1 skipped; coverage 87%.

**DoD:** CI gates on safety and coverage; docs interview-ready; latency/cost transparent.

---

## Phase 9: Dockerization (This Sprint)

**Goal:** Single `docker-compose up` launches full stack.

**What building:**
- `Dockerfile`: Python 3.12, deps, uvicorn entrypoint, HF cache volume
- `docker-compose.yml`: uvicorn + Chroma services, mounts, env vars
- `.dockerignore`: .git, reports, .venv, __pycache__
- `DOCKER.md`: Build, run, test, deploy, K8s roadmap

**DoD:** `docker-compose up` → chat UI at localhost:8000, mock mode free.

---

## Future Phases (Brainstorm)

| Phase | Goal | Why |
|-------|------|-----|
| 10a | **Monitoring Dashboard** | Real-time latency, cost, accuracy dashboards (Prometheus + Grafana). Alert on cost spike, accuracy drop, latency P95 breach. |
| 10b | **Load Testing** | k6 or locust with realistic query distributions. Measure P50/P95/P99 latency, throughput limits. |
| 10c | **Model Optimization** | Quantization (int8 judge), batching on judge calls, fine-tune Haiku on top-k retrievals for cost reduction. |
| 10d | **A/B Testing Framework** | Swap judge models, retriever algorithms, generator prompts; measure per-case delta to decide upgrades. |
| 10e | **Synthetic Data** | Mine failure patterns (e.g., "all GENERATION failures similar to core_wells_01"), generate edge cases. |
| 10f | **Cost Attribution** | Cost per case difficulty/weight, amortization over eval cycles, ROI per calculator. |
| 10g | **Continuous Retraining** | New golden cases auto-trigger fine-tuning loop on base Haiku. |
| 10h | **Streaming Responses** | Stream long rationales to chat UI. Useful for chains-of-thought. |
| 10i | **Rate Limiting & Auth** | API key management, per-key quotas, billing integration. |
| 10j | **PostgreSQL Swap** | Replace SQLite for multi-process/K8s. Schema migration via Alembic. |

---

## Golden Path: Fresh Clone to Demo

```bash
git clone https://github.com/AshraHossain/clinceval.git && cd clinceval
make demo              # pytest + coverage gate + full golden-set eval
make e2e               # Playwright suite (auto-boots uvicorn)
make serve             # Chat UI at http://localhost:8000
```

**or:**

```bash
docker-compose up -d
# Chat at http://localhost:8000
# API at http://localhost:8000/api/recommend
```

**Time to demo:** ~2 minutes (mock mode is free, instant). With `make serve` running, hit the chat UI, ask "75M with afib", see CHA₂DS₂-VASc recommended with citations.

---

## Why 9 Phases

Each phase is a single verifiable claim:

1. Pipeline runs ✓
2. Dataset is human-reviewed ✓
3. Regression system measures accurately ✓
4. Triage is correct ✓
5. Mock mode works ✓
6. Bugs are caught ✓
7. UI works ✓
8. Ship-ready (coverage + CI + docs) ✓
9. Portable (Docker) ✓

No phase overlaps; each gates the next. Discipline prevented scope creep and made debugging surgical.
