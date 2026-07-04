"""Prometheus metrics exporter for ClinCalc-Eval.

Tracks: latency, cost, pass rates, triage distribution per run.
Scrape via FastAPI `/metrics` endpoint.
"""
from prometheus_client import Counter, Gauge, Histogram

# Counters
eval_cases_total = Counter(
    "eval_cases_total",
    "Total cases evaluated",
    ["category", "weight"]
)
eval_passes_total = Counter(
    "eval_passes_total",
    "Total passing cases",
    ["category", "weight"]
)
triage_total = Counter(
    "triage_total",
    "Total cases by triage tag",
    ["tag"]
)
llm_calls_total = Counter(
    "llm_calls_total",
    "Total LLM calls",
    ["model", "mode"]  # mode: mock or live
)

# Gauges
eval_pass_rate = Gauge(
    "eval_pass_rate",
    "Overall pass rate (%)",
    ["axis"]  # overall, faithfulness, clinical_relevance, safety, completeness
)
eval_cost_usd = Gauge(
    "eval_cost_usd",
    "Cost per run (USD)"
)
llm_tokens = Gauge(
    "llm_tokens",
    "Total tokens used",
    ["direction"]  # input or output
)

# Histograms
eval_latency_seconds = Histogram(
    "eval_latency_seconds",
    "Latency per case (seconds)",
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0)
)
llm_latency_seconds = Histogram(
    "llm_latency_seconds",
    "Latency per LLM call (seconds)",
    buckets=(0.1, 0.5, 1.0, 2.0)
)


def record_eval_run(run_summary):
    """Record a full regression run's metrics."""
    for axis in ["overall", "faithfulness", "clinical_relevance", "safety", "completeness"]:
        eval_pass_rate.labels(axis=axis).set(run_summary.get(f"{axis}_pass_rate", 0))
    eval_cost_usd.set(run_summary.get("estimated_cost_usd", 0))
