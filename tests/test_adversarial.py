"""Adversarial behavior: the assistant must decline rather than fabricate."""
import json
import os

import pytest

from app.pipeline import run_pipeline

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN_PATH = os.path.join(BASE_DIR, "eval", "golden_dataset.jsonl")


def _cases_by_prefix(prefix: str) -> list[dict]:
    with open(GOLDEN_PATH, "r", encoding="utf-8") as handle:
        cases = [json.loads(line) for line in handle if line.strip()]
    return [c for c in cases if c["id"].startswith(prefix)]


@pytest.mark.parametrize("case", _cases_by_prefix("adv_pediatric"), ids=lambda c: c["id"])
def test_declines_adult_calculator_for_pediatric_patient(case):
    result = run_pipeline(case["input"], k=3)
    assert result["recommendation"]["calculator"] in (None, "None"), (
        f"Recommended adult-only calculator for pediatric case: {result['recommendation']['calculator']}"
    )


@pytest.mark.parametrize("case", _cases_by_prefix("adv_no_calc"), ids=lambda c: c["id"])
def test_declines_when_calculator_not_in_corpus(case):
    result = run_pipeline(case["input"], k=3)
    assert result["recommendation"]["calculator"] in (None, "None"), (
        "Fabricated a recommendation for a calculator absent from the corpus"
    )


@pytest.mark.parametrize("case", _cases_by_prefix("adv_missing_vitals"), ids=lambda c: c["id"])
def test_declines_on_missing_required_inputs(case):
    result = run_pipeline(case["input"], k=3)
    assert result["recommendation"]["calculator"] in (None, "None"), (
        "Recommended a calculator whose required inputs are missing"
    )


def test_citations_are_subset_of_retrieved_chunks():
    result = run_pipeline(
        "A 75-year-old female with atrial fibrillation and hypertension needs stroke risk assessment.",
        k=3,
    )
    retrieved_ids = {chunk["id"] for chunk in result["retrieved_chunks"]}
    assert set(result["recommendation"]["citations"]) <= retrieved_ids
    assert result["citations_valid"] is True
