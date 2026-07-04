"""Cost attribution: break down cost per case, per difficulty, per calculator.

Phase 10f: Justify eval spend, optimize expensive cases.
"""
from typing import List, Dict, Any


def attribute_costs(eval_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Attribute total cost across cases by difficulty and weight."""
    attribution = {
        "total_cost_usd": 0.0,
        "by_difficulty": {},  # easy, medium, hard
        "by_weight": {},      # normal, high
        "by_category": {},    # core, edge, adv, safety
        "by_calculator": {},  # calculator name -> cost
        "cost_per_case_usd": {},  # case_id -> cost
    }

    for result in eval_results:
        case_id = result.get("id")
        case_cost = result.get("cost_usd", 0.0)
        difficulty = result.get("difficulty")
        weight = result.get("weight")
        category = result.get("category")
        calculator = result.get("expected_calculator")

        attribution["total_cost_usd"] += case_cost
        attribution["cost_per_case_usd"][case_id] = case_cost

        # Aggregate by difficulty
        if difficulty not in attribution["by_difficulty"]:
            attribution["by_difficulty"][difficulty] = 0.0
        attribution["by_difficulty"][difficulty] += case_cost

        # Aggregate by weight
        if weight not in attribution["by_weight"]:
            attribution["by_weight"][weight] = 0.0
        attribution["by_weight"][weight] += case_cost

        # Aggregate by category
        if category not in attribution["by_category"]:
            attribution["by_category"][category] = 0.0
        attribution["by_category"][category] += case_cost

        # Aggregate by calculator
        if calculator not in attribution["by_calculator"]:
            attribution["by_calculator"][calculator] = 0.0
        attribution["by_calculator"][calculator] += case_cost

    # Compute cost per case amortized
    num_cases = len(eval_results)
    attribution["cost_per_case_amortized"] = (
        attribution["total_cost_usd"] / num_cases if num_cases > 0 else 0.0
    )

    # ROI: cost per high-weight safety case
    high_weight_cases = [r for r in eval_results if r.get("weight") == "high"]
    if high_weight_cases:
        attribution["cost_per_safety_case"] = (
            sum(r.get("cost_usd", 0.0) for r in high_weight_cases)
            / len(high_weight_cases)
        )

    return attribution


def optimize_expensive_cases(
    attribution: Dict[str, Any],
    budget_per_case_usd: float = 0.01
) -> Dict[str, Any]:
    """Identify overly expensive cases and suggest optimizations."""
    recommendations = []

    for case_id, cost in attribution["cost_per_case_usd"].items():
        if cost > budget_per_case_usd:
            recommendations.append({
                "case_id": case_id,
                "cost_usd": cost,
                "excess_usd": cost - budget_per_case_usd,
                "suggestion": "Quantize judge or use cheaper generator model",
            })

    return {
        "total_cost_usd": attribution["total_cost_usd"],
        "target_budget_usd": budget_per_case_usd * len(attribution["cost_per_case_usd"]),
        "overage_usd": max(
            0,
            attribution["total_cost_usd"]
            - (budget_per_case_usd * len(attribution["cost_per_case_usd"]))
        ),
        "recommendations": recommendations,
    }
