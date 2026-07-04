# API Reference

## POST /api/recommend

Recommend a clinical calculator for a patient query.

### Request

```json
{
  "query": "A 75-year-old female with atrial fibrillation and hypertension needs stroke risk assessment."
}
```

### Response (Success)

```json
{
  "recommendation": {
    "calculator": "CHA2DS2-VASc Score",
    "rationale": "AFib + HTN + female age 75 (2 points each) → stroke risk calculation. CHA2DS2 requires AFib, age/sex weighting, and HTN; unlike CHADS (no vascular disease weight) or QRISK (primary prevention, not AFib-specific).",
    "citations": [
      "chads2_vasc_chunk_0",
      "chads2_vasc_chunk_3"
    ],
    "confidence": 0.95
  },
  "citations_valid": true,
  "retrieved_chunks": [
    {
      "id": "chads2_vasc_chunk_0",
      "text": "CHA2DS2-VASc Score for stroke risk in atrial fibrillation..."
    },
    {
      "id": "chads2_vasc_chunk_3",
      "text": "Age and sex points in CHA2DS2-VASc: female age ≥65..."
    }
  ]
}
```

### Response (Decline)

```json
{
  "recommendation": {
    "calculator": "None",
    "rationale": "Pediatric patient (3-month-old). All recommended calculators are for adults (≥18 years). PECARN tools (head injury, pneumonia) are specialized for children but do not generalize to this query. Defer to pediatrician.",
    "citations": [],
    "confidence": 0.99
  },
  "citations_valid": true,
  "retrieved_chunks": []
}
```

### Response (Error)

```json
{
  "error": "Internal server error",
  "detail": "Chroma collection not found"
}
```

HTTP 500 for crashes; 400 for validation (blank query); 422 for schema (missing `query` field).

### Rate Limiting

None enforced (mock mode is free; API mode charges per call). Future: implement per-IP or per-API-key limits.

### Latency

**Mock mode:** ~10ms (keyword router + rule-based judge).
**API mode:** ~2–3s (retriever boot once, then ~500ms retrieve + 1500ms generate + 500ms judge).

### Cost

**Mock mode:** $0.00.
**API mode:** ~$0.003–0.01 per call (Haiku gen: 10K tokens in, 6K tokens out @ Haiku pricing).
Reported in regression runner "Latency & Cost" section.

---

## GET /

Serve the chat UI (static HTML).

---

## Internal (Eval Runner)

### run_pipeline(query: str) → dict

```python
{
  "recommendation": {"calculator": str, "rationale": str, "citations": list[str], "confidence": float},
  "citations_valid": bool,
  "retrieved_chunks": list[{"id": str, "text": str}],
  "error": str | None
}
```

Called by regression runner for each golden case. In API mode, `/api/recommend` wraps this.

### grade_output(case: dict, pipeline_result: dict) → dict

```python
{
  "scores": {
    "faithfulness": int (1–5),
    "clinical_relevance": int (1–5),
    "safety": int (1–5),
    "completeness": int (1–5)
  }
}
```

Mock judge for reproducibility in CI; swap to Claude Sonnet in production (set `JUDGE_MODEL` env var).

---

## Database (SQL)

See `db/schema.sql` for full schema. Key tables:

- `eval_runs`: started_at (UNIQUE), overall_pass_rate, hard_gate_failures
- `eval_results`: run_id (FK), case_id (FK), triage (ENUM), overall_pass, safety_gate_fail, 4-axis scores
- `golden_cases`: id (PK), category, difficulty, weight, expected_calculator
- `triage_tags`: ENUM(RETRIEVAL, GENERATION, JUDGE, INTEGRATION, DATA, PASS)

Query example: Pass-rate trend over last 5 runs.

```sql
SELECT id, overall_pass_rate, LAG(overall_pass_rate) OVER (ORDER BY started_at) AS prev_rate
FROM eval_runs
ORDER BY started_at DESC LIMIT 5;
```

See `db/integrity_checks.sql` for more.
