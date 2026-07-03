# ClinCalc-Eval — Project Conventions

## Purpose
QA/eval portfolio project for an AI Product QA Engineer interview (MDCalc).
The evaluation infrastructure is the product under test, not the assistant itself.

## Workflow
Follow the Superpowers discipline: clarify -> design -> plan -> code -> verify.
Stop and report after each phase in IMPLEMENTATION_PLAN.md before proceeding to the next.

## Plugins active on this project
- **Superpowers** — governs the phase discipline above. Do not skip clarify/design for a "simple" step.
- **ponytail** — active by default (YAGNI, stdlib-first, no unrequested abstractions). Toggle `off` only for Phase 4-5 (eval/judge logic), where deliberate structure is warranted — say so explicitly when you do.
- **graphify** — once installed (post-Phase 2), consult the knowledge graph before grepping the repo for context.
- **ask the council** — reserved for the Phase 4 rubric design decision. Don't invoke it for routine implementation choices; it's for the few decisions worth defending in an interview.

## Conventions
- Python 3.12, pytest for unit/integration tests, Playwright (TS) for E2E.
- SQLite for local demo simplicity (not Postgres) — call this out as a deliberate
  demo-scope decision, not an oversight.
- All LLM calls go through a single wrapper so token/latency/cost logging is centralized.
- Judge model must be pinned by version string, never "latest".
- Every failing eval case must get a triage tag (RETRIEVAL/GENERATION/JUDGE/INTEGRATION/DATA)
  before it's considered actionable.
- Safety-axis failures on high-weight golden cases are hard release gates. Nothing else is.

## What Claude/Cowork should never do
- Never silently loosen a rubric threshold to make tests pass.
- Never fabricate golden dataset cases without flagging them for human clinical-plausibility review.
- Never remove a failing test instead of fixing or explicitly deferring it with a reason.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
