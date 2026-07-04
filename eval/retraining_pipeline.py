"""Continuous retraining: auto fine-tune Haiku when new golden cases land.

Phase 10g: Feedback loop for production use.
"""
import json
from pathlib import Path
from typing import List, Dict, Any


def detect_new_cases(
    current_dataset_path: Path,
    last_trained_hash: str
) -> List[Dict[str, Any]]:
    """Detect new or modified cases since last training run."""
    with open(current_dataset_path, "r") as f:
        cases = [json.loads(line) for line in f]

    # Stub: hash dataset and compare to stored hash
    # In practice: git diff golden_dataset.jsonl, track case versions
    new_cases = [c for c in cases if c.get("_added_after_training", False)]
    return new_cases


def schedule_retraining(
    new_cases: List[Dict[str, Any]],
    min_threshold: int = 50  # Retrain when 50+ new cases accumulate
):
    """Schedule retraining job if threshold exceeded."""
    if len(new_cases) < min_threshold:
        return {"status": "waiting", "cases_accumulated": len(new_cases)}

    # Enqueue job: {type: "retrain_haiku", payload: new_cases, priority: "background"}
    return {
        "status": "scheduled",
        "job_id": "retrain_haiku_20260704",
        "cases_to_train": len(new_cases),
    }


def retrain_haiku(
    training_cases: List[Dict[str, Any]],
    base_model: str = "claude-3-5-haiku",
    output_model_name: str = "haiku-ft-20260704"
):
    """Fine-tune Haiku on actual retrieved context from new cases.

    Goal: reduce input tokens by 30-40% for domain-specific prompts.
    Requires: Anthropic API fine-tuning beta access.
    """
    # Stub: prepare_datasets → format JSONL for fine-tuning
    # {
    #   "system": "You are a clinical calculator recommender...",
    #   "user": "...",
    #   "assistant": "..."
    # }

    # Call Anthropic fine-tuning API
    # response = client.beta.model_garden.create_fine_tune_job(
    #   base_model=base_model,
    #   training_data=training_dataset,
    #   training_config={...}
    # )

    return {
        "status": "enqueued",
        "job_id": "ft_haiku_20260704",
        "model_name": output_model_name,
        "training_cases": len(training_cases),
        "eta_minutes": 30,
    }


def evaluate_new_model(
    new_model_id: str,
    golden_dataset: List[Dict[str, Any]],
    baseline_pass_rate: float = 0.95
) -> Dict[str, Any]:
    """A/B test new fine-tuned model vs baseline Haiku."""
    # Run regression on baseline and new model
    # Stub: compare pass rates, latency, cost

    return {
        "baseline_pass_rate": baseline_pass_rate,
        "new_model_pass_rate": 0.96,
        "latency_improvement_pct": -10,
        "cost_reduction_pct": -25,
        "recommendation": "Promote to production",
    }


# Config
RETRAINING_CONFIG = {
    "enabled": False,  # Enable after 100+ golden cases, regular updates
    "trigger": "new_cases_accumulated",
    "threshold": 50,  # Retrain every 50 new cases
    "schedule": "weekly",  # Or "on_demand"
    "base_model": "claude-3-5-haiku",
    "lora_rank": 8,
    "lora_alpha": 16,
}
