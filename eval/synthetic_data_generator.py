"""Synthetic data generation: mine failure patterns, generate similar cases.

Phase 10e: Find edge cases by similarity to failures.
"""
from typing import List, Dict, Any
from app.retriever import embed_text


def find_chronic_offenders(eval_db) -> List[Dict[str, Any]]:
    """Cases that fail most frequently (from db/integrity_checks.sql query #5)."""
    # Query: SELECT case_id, fail_count FROM (SELECT case_id, COUNT(*) as fail_count ...)
    # Stub: return cases with fail_count > 3
    return []


def mine_similar_cases(
    failure_case: Dict[str, Any],
    golden_cases: List[Dict[str, Any]],
    similarity_threshold: float = 0.8
) -> List[Dict[str, Any]]:
    """Find golden cases similar to a failure case (cosine sim on embeddings)."""
    failure_embedding = embed_text(failure_case["input"])
    similar = []

    for case in golden_cases:
        case_embedding = embed_text(case["input"])
        # Cosine similarity: dot(a, b) / (norm(a) * norm(b))
        similarity = float(
            failure_embedding @ case_embedding
            / (
                (failure_embedding @ failure_embedding) ** 0.5
                * (case_embedding @ case_embedding) ** 0.5
            )
        )
        if similarity > similarity_threshold:
            similar.append({**case, "similarity": similarity})

    return sorted(similar, key=lambda x: x["similarity"], reverse=True)


def generate_synthetic_case(
    template_case: Dict[str, Any],
    perturbation: str = "swap_calculator"
) -> Dict[str, Any]:
    """Generate a new test case by perturbing an existing one.

    Perturbations:
    - swap_calculator: change expected_calculator to a different one (should decline)
    - missing_vital: remove a required input
    - boundary_value: change a numeric input to its boundary (e.g., age 65 -> 64)
    - adversarial: add contradictory inputs
    """
    new_case = template_case.copy()

    if perturbation == "swap_calculator":
        # Change to a wrong but plausible calculator
        other_calcs = [
            "MELD Score",
            "CURB-65 Score",
            "Wells' Criteria for PE",
            "CHA2DS2-VASc Score",
        ]
        current = template_case.get("expected_calculator")
        new_case["expected_calculator"] = next(
            (c for c in other_calcs if c != current), "None"
        )
        new_case["id"] = f"{template_case['id']}_syn_swap_calc"

    elif perturbation == "missing_vital":
        # Remove a required input (e.g., "no systolic BP provided")
        new_case["input"] = template_case["input"].replace("systolic BP", "").strip()
        new_case["expected_calculator"] = "None"  # Should decline
        new_case["id"] = f"{template_case['id']}_syn_missing_vital"

    elif perturbation == "boundary_value":
        # Age boundary: 65 vs 64 (may change point allocation)
        new_case["input"] = template_case["input"].replace("age 65", "age 64")
        new_case["id"] = f"{template_case['id']}_syn_boundary"

    elif perturbation == "adversarial":
        # Add contradiction: "pediatric" + "adult calculator"
        new_case["input"] = (
            "3-month-old with " + template_case["input"]
        )  # Force pediatric
        new_case["expected_calculator"] = "None"  # Must decline
        new_case["id"] = f"{template_case['id']}_syn_adversarial"

    return new_case


def augment_golden_dataset(
    golden_cases: List[Dict[str, Any]],
    failures: List[Dict[str, Any]],
    augment_ratio: float = 0.2  # 20% new synthetic cases
) -> List[Dict[str, Any]]:
    """Augment golden dataset with synthetic variants of failure cases."""
    augmented = golden_cases.copy()

    for failure_case in failures:
        # Mine similar cases in golden set
        similar = mine_similar_cases(failure_case, golden_cases, similarity_threshold=0.7)

        if similar:
            # Generate synthetic variants
            template = similar[0]  # Use most similar case
            for perturbation in ["missing_vital", "boundary_value", "adversarial"]:
                synthetic = generate_synthetic_case(template, perturbation)
                augmented.append(synthetic)

    return augmented[: int(len(augmented) * (1 + augment_ratio))]
