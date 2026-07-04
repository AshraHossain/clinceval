"""Tests for the Phase 10 modules with real logic: cost attribution and
synthetic case generation. (Declared stubs are coverage-omitted in pyproject.)"""
from eval.cost_attribution import attribute_costs, optimize_expensive_cases
from eval.synthetic_data_generator import generate_synthetic_case, mine_similar_cases

RESULTS = [
    {"id": "c1", "cost_usd": 0.004, "difficulty": "easy", "weight": "normal",
     "category": "core", "expected_calculator": "MELD"},
    {"id": "c2", "cost_usd": 0.020, "difficulty": "hard", "weight": "high",
     "category": "safety", "expected_calculator": "GCS"},
]


def test_cost_attribution_aggregates():
    attribution = attribute_costs(RESULTS)
    assert attribution["total_cost_usd"] == 0.024
    assert attribution["by_weight"] == {"normal": 0.004, "high": 0.020}
    assert attribution["by_calculator"]["GCS"] == 0.020
    assert attribution["cost_per_case_amortized"] == 0.012
    assert attribution["cost_per_safety_case"] == 0.020


def test_expensive_case_recommendations():
    report = optimize_expensive_cases(attribute_costs(RESULTS), budget_per_case_usd=0.01)
    assert len(report["recommendations"]) == 1
    assert report["recommendations"][0]["case_id"] == "c2"
    assert round(report["overage_usd"], 4) == 0.004


BASE_CASE = {
    "id": "core_meld_01",
    "input": "58M cirrhosis, age 65, creatinine 2.1, bilirubin 3.0, INR 1.8, systolic BP 100",
    "expected_calculator": "MELD Score",
    "category": "core", "difficulty": "easy", "weight": "normal",
}


def test_synthetic_perturbations():
    swapped = generate_synthetic_case(BASE_CASE, "swap_calculator")
    assert swapped["expected_calculator"] != "MELD Score"
    assert swapped["id"].endswith("_syn_swap_calc")

    missing = generate_synthetic_case(BASE_CASE, "missing_vital")
    assert "systolic BP" not in missing["input"]
    assert missing["expected_calculator"] == "None"

    boundary = generate_synthetic_case(BASE_CASE, "boundary_value")
    assert "age 64" in boundary["input"]

    adversarial = generate_synthetic_case(BASE_CASE, "adversarial")
    assert adversarial["input"].startswith("3-month-old")
    assert adversarial["expected_calculator"] == "None"
    # original untouched (no mutation)
    assert BASE_CASE["expected_calculator"] == "MELD Score"


def test_mine_similar_cases_ranks_by_embedding_similarity():
    pool = [
        {"id": "a", "input": "60M with liver cirrhosis, high bilirubin and INR"},
        {"id": "b", "input": "toddler fell off a couch, brief loss of consciousness"},
    ]
    similar = mine_similar_cases(BASE_CASE, pool, similarity_threshold=0.1)
    assert similar[0]["id"] == "a"  # cirrhosis case must outrank the head-injury case
