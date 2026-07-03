# ClinCalc-Eval

QA/evaluation harness for a mock LLM-powered clinical assistant that recommends
medical calculators (CHA₂DS₂-VASc, Wells' Criteria, MELD, …) with cited rationale.

The product here is the **evaluation infrastructure**, not the assistant:
golden dataset regression testing, LLM-as-judge scoring, hallucination/citation
checking, retrieval-vs-generation failure triage, Playwright E2E tests,
SQL-backed eval result storage, and latency/cost monitoring.

> Work in progress — full README (architecture, quickstart, design decisions)
> lands at Phase 8. See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).
