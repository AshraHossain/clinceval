# Runbook

Operational guide: what to do when X breaks. Ordered by likelihood.

## Regression runner exits 1 (hard safety gate)

**This is the system working, not breaking.** A `weight: high` case failed the safety axis.

1. Open the newest `eval/reports/run_*.md` → "Detailed failing cases" → find the `safety_gate_fail: True` rows.
2. Check the triage tag:
   - `GENERATION` → the model recommended something it must decline (e.g. adult calculator for a pediatric case). Fix the guard in `app/llm.py` (mock) or the system prompt (live).
   - `JUDGE` → verify the case's `expected_rationale` is actually right before touching the judge.
3. Re-run `python -m eval.regression_runner`. Release stays blocked until exit 0.
4. Never fix by reweighting the case to `normal` or loosening the rubric — see CLAUDE.md prohibitions.

## Regression runner exits 2 (dataset schema failure)

`golden_dataset.jsonl` has a bad row (missing field, invalid category/weight, duplicate id, broken JSON). The error lines name the exact line numbers. Fix the data, not the validator.

## First request takes ~10s / `/ready` returns 503

Embedding model cold start. The lifespan hook warms it; if a proxy routed traffic before `/ready` went 200, fix the deployment to gate on the readiness probe (`GET /ready`), not liveness (`GET /health`).

## Chroma errors (`NotFoundError`, connection refused)

- Local: the collection was deleted mid-process (e.g. a `force_reindex` elsewhere). Restart the process — the retriever rebuilds from `app/corpus/` on boot.
- Docker: `docker-compose logs chroma`; wait for the healthcheck. `app` refuses to start before Chroma is healthy by design.

## API returns 504

Pipeline exceeded `PIPELINE_TIMEOUT_S` (30s). Almost always the live Anthropic API hanging. Check status.anthropic.com; the mock path can't time out.

## API returns 429

Caller exhausted their key's monthly quota (`app/rate_limiter.py` tiers). Raise the tier or wait for the 30-day window reset. Anonymous (no key) traffic is not limited.

## Cost spike in the report's "Latency & Cost" section

1. Confirm mode: 41 mock calls ≈ $0.00. Any nonzero cost means a key is set — is that intended for this environment?
2. Compare token counts vs previous reports (`grep -A5 "Latency & Cost" eval/reports/run_*.md`). Input-token growth usually means retrieval k or chunk sizes changed.
3. Set `ALERT_WEBHOOK_URL` to get pushed alerts instead of reading reports.

## Pass rate dropped but no code changed

1. `python -m eval.analytics` → chronic offenders + triage distribution.
2. `python -m eval.analytics diff <old_run_id> <new_run_id>` → exactly which cases flipped.
3. `judge_drift(engine, run_a, run_b)` (in `eval/analytics.py`) → per-axis mean deltas. |delta| ≥ 1.0 on an axis with unchanged pipeline = judge drift; recalibrate against `eval/rubric.yaml` anchors, don't chase the pipeline.

## Database locked (SQLite)

Two writers collided (e.g. two regression runs at once). Retry — runs are short. If it recurs, serialize eval runs in CI (single job) or migrate to Postgres (`app/postgres_schema.sql`, swap the engine URL in `eval/db.py`).

## Restore from backup

```bash
ls backups/                                   # nightly snapshots from scripts/backup_db.py
cp backups/eval_results_<stamp>.db eval/eval_results.db
```

Backups are online-consistent (SQLite backup API), safe to take while serving.

## Data retention

`purge_old_runs(engine, keep_days=90)` in `eval/analytics.py`. Run quarterly or wire into the nightly backup cron after the snapshot (snapshot first, then purge).

## Deferred integrations (documented, not built)

- **Sentry / OpenTelemetry**: structured JSON logs (`app/observability.py`) are the substrate; point a collector at stdout or add the SDK in `get_logger()`. Needs an account/DSN — not stubbed on purpose.
- **K8s manifests**: probe endpoints exist (`/health`, `/ready`); manifest template in DOCKER.md.
