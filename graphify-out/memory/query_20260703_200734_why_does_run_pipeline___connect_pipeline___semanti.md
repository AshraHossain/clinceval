---
type: "query"
date: "2026-07-03T20:07:34.021800+00:00"
question: "Why does run_pipeline() connect Pipeline & Semantic Similarity to Regression Runner & Triage, Retriever & Chunking, and Generator & LLM Judge?"
contributor: "graphify"
source_nodes: ["run_pipeline()", "retrieve()", "generate()", "run()", "grade_output()"]
---

# Q: Why does run_pipeline() connect Pipeline & Semantic Similarity to Regression Runner & Triage, Retriever & Chunking, and Generator & LLM Judge?

## Answer

run_pipeline() in app/pipeline.py is the orchestration seam of the whole system: it calls retrieve() (Retriever & Chunking community) to pull top-k chunks from ChromaDB, then generate() (Generator & LLM Judge community) to produce the structured recommendation, then citation-checks the result. The Regression Runner community connects because eval/regression_runner.py run() invokes run_pipeline() for every golden case before grade_output() judges the output. So all four communities meet at this one function — it is the single integration point, which is why it has the highest betweenness centrality (0.215) in the graph. Practical QA implication: any INTEGRATION-tagged failure will surface here first, and a bug in run_pipeline affects every downstream eval metric simultaneously.

## Source Nodes

- run_pipeline()
- retrieve()
- generate()
- run()
- grade_output()