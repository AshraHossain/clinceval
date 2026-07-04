"""CLI wrapper around eval/synthetic_data_generator.py.

Usage: python scripts/generate_test_cases.py --count 5 --perturbation boundary_value
Output: JSONL to stdout — review manually, then append approved cases to
eval/golden_dataset.jsonl (never auto-append; golden means human-reviewed).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.synthetic_data_generator import generate_synthetic_case

GOLDEN_PATH = Path(__file__).resolve().parent.parent / "eval" / "golden_dataset.jsonl"
PERTURBATIONS = ["swap_calculator", "missing_vital", "boundary_value", "adversarial"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--perturbation", choices=PERTURBATIONS, default="boundary_value")
    parser.add_argument("--category", default=None, help="only perturb cases from this category")
    args = parser.parse_args()

    with open(GOLDEN_PATH, encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]
    if args.category:
        cases = [c for c in cases if c.get("category") == args.category]

    for case in cases[: args.count]:
        synthetic = generate_synthetic_case(case, args.perturbation)
        synthetic["_needs_clinical_review"] = True
        print(json.dumps(synthetic))


if __name__ == "__main__":
    main()
