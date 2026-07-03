# Graph Report - /Users/ashraf-macbookair/repos/projects/clinceval  (2026-07-03)

## Corpus Check
- Corpus is ~14,899 words - fits in a single context window. You may not need a graph.

## Summary
- 109 nodes · 213 edges · 7 communities detected
- Extraction: 81% EXTRACTED · 18% INFERRED · 1% AMBIGUOUS · INFERRED: 39 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Clinical Calculator Corpus|Clinical Calculator Corpus]]
- [[_COMMUNITY_Regression Runner & Triage|Regression Runner & Triage]]
- [[_COMMUNITY_Retriever & Chunking|Retriever & Chunking]]
- [[_COMMUNITY_Pipeline & Semantic Similarity|Pipeline & Semantic Similarity]]
- [[_COMMUNITY_Generator & LLM Judge|Generator & LLM Judge]]
- [[_COMMUNITY_Plan & Conventions|Plan & Conventions]]
- [[_COMMUNITY_Golden Dataset Tests|Golden Dataset Tests]]

## God Nodes (most connected - your core abstractions)
1. `Regression Runner Report 2026-07-03 09:31:43 (48.8% pass, 3 safety gate failures)` - 15 edges
2. `Regression Runner Report 2026-07-03 09:32:49 (48.8% pass, 3 safety gate failures)` - 15 edges
3. `Corpus & Retriever (Phase 1)` - 14 edges
4. `run()` - 13 edges
5. `Regression Runner Report 2026-07-03 09:18:13 (Baseline, 68.3% pass)` - 13 edges
6. `run_pipeline()` - 9 edges
7. `ClinCalc-Eval Implementation Plan` - 9 edges
8. `grade_output()` - 8 edges
9. `Regression Runner & Failure Triage (Phase 5)` - 8 edges
10. `Retriever` - 7 edges

## Surprising Connections (you probably didn't know these)
- `retrieve()` --references--> `Q&A: Why run_pipeline() bridges all core communities`  [EXTRACTED]
  /Users/ashraf-macbookair/repos/projects/clinceval/app/retriever.py → graphify-out/memory/query_20260703_200734_why_does_run_pipeline___connect_pipeline___semanti.md
- `run()` --references--> `Q&A: Why run_pipeline() bridges all core communities`  [EXTRACTED]
  /Users/ashraf-macbookair/repos/projects/clinceval/eval/regression_runner.py → graphify-out/memory/query_20260703_200734_why_does_run_pipeline___connect_pipeline___semanti.md
- `generate()` --references--> `Q&A: Why run_pipeline() bridges all core communities`  [EXTRACTED]
  /Users/ashraf-macbookair/repos/projects/clinceval/app/generator.py → graphify-out/memory/query_20260703_200734_why_does_run_pipeline___connect_pipeline___semanti.md
- `run_pipeline()` --references--> `Q&A: Why run_pipeline() bridges all core communities`  [EXTRACTED]
  /Users/ashraf-macbookair/repos/projects/clinceval/app/pipeline.py → graphify-out/memory/query_20260703_200734_why_does_run_pipeline___connect_pipeline___semanti.md
- `grade_output()` --references--> `Q&A: Why run_pipeline() bridges all core communities`  [EXTRACTED]
  /Users/ashraf-macbookair/repos/projects/clinceval/eval/judge.py → graphify-out/memory/query_20260703_200734_why_does_run_pipeline___connect_pipeline___semanti.md

## Communities

### Community 0 - "Clinical Calculator Corpus"
Cohesion: 0.11
Nodes (11): generate(), Format retrieved context, call Claude, and return the structured recommendation., grade_output(), Grades the pipeline's output using the pinned Claude 3.5 Sonnet judge.     Falls, get_llm_client(), LLMClient, Calls Claude model (or returns a simulated mock if no API key is set)., Executes the full pipeline:     1. Retrieves top k chunks from ChromaDB     2. I (+3 more)

### Community 1 - "Regression Runner & Triage"
Cohesion: 0.31
Nodes (21): CHA2DS2-VASc Score for Atrial Fibrillation Stroke Risk, Child-Pugh Score for Cirrhosis Mortality, CURB-65 Severity Score for Community-Acquired Pneumonia, Glasgow Coma Scale (GCS), HAS-BLED Score for Major Bleeding Risk, HEART Score for Major Adverse Cardiac Events (MACE), Regression Runner & Failure Triage (Phase 5), Corpus & Retriever (Phase 1) (+13 more)

### Community 2 - "Retriever & Chunking"
Cohesion: 0.27
Nodes (16): build_summary(), create_report(), format_report(), infer_triage_tag(), is_generation_successful(), is_retrieval_successful(), load_baseline(), load_golden_cases() (+8 more)

### Community 3 - "Pipeline & Semantic Similarity"
Cohesion: 0.2
Nodes (9): chunk_markdown_file(), Loads and indexes all markdown files from the corpus directory., Retrieves the top k chunks matching the query.         Returns a list of dicts c, Parses a markdown file and chunks it by paragraph, tracking section headers., retrieve(), Retriever, initialized_retriever(), test_basic_retrieval() (+1 more)

### Community 4 - "Generator & LLM Judge"
Cohesion: 0.24
Nodes (10): ClinCalc-Eval Project Conventions, ClinCalc-Eval Implementation Plan, Deliberately Embedded Bugs (Phase 6), Generator & Pipeline (Phase 2), Golden Dataset (Phase 3), LLM-as-Judge Evaluation Layer (Phase 4), Separate/Pinned Judge Model: Shared-Bias Avoidance Rationale, Deliberately Simple Pipeline: Bugs Must Be Traceable Rationale (+2 more)

### Community 5 - "Plan & Conventions"
Cohesion: 0.31
Nodes (5): calculate_semantic_similarity(), get_embedding_model(), Computes cosine similarity between two text strings using sentence-transformers., test_judge_calibration(), test_semantic_similarity_basic()

### Community 6 - "Golden Dataset Tests"
Cohesion: 0.67
Nodes (2): test_golden_dataset_exists(), test_golden_dataset_validation()

## Ambiguous Edges - Review These
- `ClinCalc-Eval Project (README)` → `Wells' Criteria for Pulmonary Embolism (PE)`  [AMBIGUOUS]
  README.md · relation: cites
- `ClinCalc-Eval Project (README)` → `Wells' Criteria for Deep Vein Thrombosis (DVT)`  [AMBIGUOUS]
  README.md · relation: cites

## Knowledge Gaps
- **9 isolated node(s):** `Parses a markdown file and chunks it by paragraph, tracking section headers.`, `Loads and indexes all markdown files from the corpus directory.`, `Retrieves the top k chunks matching the query.         Returns a list of dicts c`, `Calls Claude model (or returns a simulated mock if no API key is set).`, `Format retrieved context, call Claude, and return the structured recommendation.` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Golden Dataset Tests`** (4 nodes): `test_golden_dataset_exists()`, `test_golden_dataset_validation()`, `test_golden_dataset.py`, `test_golden_dataset.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ClinCalc-Eval Project (README)` and `Wells' Criteria for Pulmonary Embolism (PE)`?**
  _Edge tagged AMBIGUOUS (relation: cites) - confidence is low._
- **What is the exact relationship between `ClinCalc-Eval Project (README)` and `Wells' Criteria for Deep Vein Thrombosis (DVT)`?**
  _Edge tagged AMBIGUOUS (relation: cites) - confidence is low._
- **Why does `run()` connect `Retriever & Chunking` to `Clinical Calculator Corpus`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Why does `retrieve()` connect `Pipeline & Semantic Similarity` to `Clinical Calculator Corpus`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Why does `run_pipeline()` connect `Clinical Calculator Corpus` to `Retriever & Chunking`, `Pipeline & Semantic Similarity`, `Plan & Conventions`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Regression Runner Report 2026-07-03 09:31:43 (48.8% pass, 3 safety gate failures)` (e.g. with `Deliberately Embedded Bugs (Phase 6)` and `Regression Runner Report 2026-07-03 09:18:13 (Baseline, 68.3% pass)`) actually correct?**
  _`Regression Runner Report 2026-07-03 09:31:43 (48.8% pass, 3 safety gate failures)` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Regression Runner Report 2026-07-03 09:32:49 (48.8% pass, 3 safety gate failures)` (e.g. with `Deliberately Embedded Bugs (Phase 6)` and `Regression Runner Report 2026-07-03 09:18:13 (Baseline, 68.3% pass)`) actually correct?**
  _`Regression Runner Report 2026-07-03 09:32:49 (48.8% pass, 3 safety gate failures)` has 3 INFERRED edges - model-reasoned connections that need verification._