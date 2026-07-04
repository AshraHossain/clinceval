# Model Card — ClinCalc-Eval

## System overview

| Component | Mock mode (default) | API mode (`ANTHROPIC_API_KEY` set) |
|---|---|---|
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (local, both modes) | same |
| Generator | Deterministic keyword router (`app/llm.py`) | `claude-3-5-haiku-20241022` (pinned) |
| Judge | Rule-based grader (`eval/judge.py`) | `claude-3-5-sonnet-20241022` (pinned) |

Models are **version-pinned**, never "latest": an unnoticed model upgrade would silently shift judge grading and invalidate baseline comparisons.

## Intended use

Portfolio/demo QA harness for evaluating calculator-recommendation quality. **Not a medical device. Not for clinical decision-making.** Recommendations are grounded only in the 13-document demo corpus, which is illustrative, not authoritative.

## Training data

No component is trained by this project. Embeddings and Claude models are used as released by their vendors. The golden dataset (41 cases) is AI-drafted and human-reviewed (PR #1) — it is evaluation data, not training data.

## Known limitations

- **Mock router is keyword-based**: handles the 41 golden queries and near neighbors; arbitrary free-text queries can misroute. It exists to test the *eval harness*, not to be a good assistant.
- **Semantic similarity is threshold-blind**: "GCS 14" and "GCS 15" embed nearly identically. That's why it's a secondary signal under the judge, never a gate.
- **Mock judge misses paraphrase-level unfaithfulness**: it checks citation validity and calculator match, not sentence-level grounding. The live Sonnet judge is stricter.
- **Corpus coverage**: 13 calculators. Queries about anything else must decline; a decline is correct behavior, not a failure.
- **English only.**

## Bias & fairness

- Golden cases span adult ages 3 months–89 years, both sexes, and 4 case categories; per-category pass rates are queryable (`eval_results` joined to `golden_cases.category`).
- Pediatric safety is the one hard release gate — biased failure against the most vulnerable group blocks release outright.
- No demographic fine-tuning is performed; vendor-model biases pass through and are only partially observable through the 41-case lens. A production deployment would need a dedicated fairness eval set stratified by demographics.

## Privacy

- Queries may contain PHI-like text. Logs pass through `redact_pii()` (SSN/MRN/email/phone patterns) before writing; raw queries are never logged.
- Eval results retained 90 days by default (`purge_old_runs`).
- In API mode, queries are sent to Anthropic — review Anthropic's data-usage policy before pointing real patient text at it.

## Evaluation

41-case golden regression, 4-axis judge rubric (1–5 anchored), pass threshold 4, hard gate on high-weight safety failures. Current state: 41/41 pass in mock mode, coverage 87%, CI-gated. Full evidence chain in [TRACEABILITY.md](TRACEABILITY.md).
