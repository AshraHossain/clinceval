import os
import json
import pytest

GOLDEN_DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "eval",
    "golden_dataset.jsonl"
)

def test_golden_dataset_exists():
    assert os.path.exists(GOLDEN_DATASET_PATH), "golden_dataset.jsonl does not exist"

def test_golden_dataset_validation():
    required_keys = {
        "id",
        "input",
        "expected_calculator",
        "expected_score_range",
        "must_cite",
        "category",
        "difficulty",
        "weight"
    }
    
    valid_categories = {"core", "edge", "adversarial", "safety"}
    valid_difficulties = {"easy", "medium", "hard"}
    valid_weights = {"normal", "high"}
    
    cases = []
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                case = json.loads(line)
            except json.JSONDecodeError as e:
                pytest.fail(f"Line {idx} is not valid JSON: {e}")
                
            # Assert keys
            for key in required_keys:
                assert key in case, f"Line {idx} missing key '{key}'"
                
            # Assert field types and values
            assert isinstance(case["id"], str), f"Line {idx} id must be string"
            assert isinstance(case["input"], str), f"Line {idx} input must be string"
            assert case["expected_calculator"] is None or isinstance(case["expected_calculator"], str)
            assert case["expected_score_range"] is None or (isinstance(case["expected_score_range"], list) and len(case["expected_score_range"]) == 2)
            assert isinstance(case["must_cite"], list), f"Line {idx} must_cite must be a list"
            
            assert case["category"] in valid_categories, f"Line {idx} invalid category '{case['category']}'"
            assert case["difficulty"] in valid_difficulties, f"Line {idx} invalid difficulty '{case['difficulty']}'"
            assert case["weight"] in valid_weights, f"Line {idx} invalid weight '{case['weight']}'"
            
            cases.append(case)
            
    # DoD requires 40+ cases
    assert len(cases) >= 40, f"Expected at least 40 cases, got {len(cases)}"
    
    # Check count of categories to ensure representation
    categories = [c["category"] for c in cases]
    assert categories.count("core") >= 15, "Expected at least 15 core cases"
    assert categories.count("edge") >= 10, "Expected at least 10 edge cases"
    assert categories.count("adversarial") >= 5, "Expected at least 5 adversarial cases"
    assert categories.count("safety") >= 5, "Expected at least 5 safety cases"
