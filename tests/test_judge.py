import os
import json
import pytest
from app.pipeline import run_pipeline
from eval.judge import grade_output
from eval.semantic_sim import calculate_semantic_similarity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALIBRATION_PATH = os.path.join(BASE_DIR, "eval", "calibration_set.json")
GOLDEN_PATH = os.path.join(BASE_DIR, "eval", "golden_dataset.jsonl")

def test_semantic_similarity_basic():
    # Test identical text
    sim_identical = calculate_semantic_similarity("The patient has atrial fibrillation.", "The patient has atrial fibrillation.")
    assert sim_identical > 0.99
    
    # Test completely different text
    sim_diff = calculate_semantic_similarity("atrial fibrillation risk", "Model for End-Stage Liver Disease calculation")
    assert sim_diff < sim_identical
    
    # Test blank inputs
    assert calculate_semantic_similarity("", "text") == 0.0

def test_judge_calibration():
    # Load calibration set
    with open(CALIBRATION_PATH, "r", encoding="utf-8") as f:
        calibration_cases = json.load(f)
        
    # Create mapping of id -> expected scores
    calibration_map = {c["id"]: c["expected_scores"] for c in calibration_cases}
    
    # Load golden cases matching calibration IDs
    golden_cases = []
    with open(GOLDEN_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                case = json.loads(line)
                if case["id"] in calibration_map:
                    golden_cases.append(case)
                    
    assert len(golden_cases) == len(calibration_cases), f"Loaded {len(golden_cases)} matching cases, expected {len(calibration_cases)}"
    
    agreements = 0
    total_axes_evaluated = 0
    
    for case in golden_cases:
        case_id = case["id"]
        expected = calibration_map[case_id]
        
        # Run pipeline
        pipeline_output = run_pipeline(case["input"], k=3)
        
        # Grade output
        judge_result = grade_output(case, pipeline_output)
        actual = judge_result["scores"]
        
        # Check agreement on each axis (within 1 point on the 1-5 scale)
        case_agreement = True
        for axis in ["faithfulness", "clinical_relevance", "safety", "completeness"]:
            total_axes_evaluated += 1
            diff = abs(actual[axis] - expected[axis])
            if diff > 1:
                case_agreement = False
                print(f"Calibration discrepancy on case {case_id}, axis {axis}: Expected {expected[axis]}, got {actual[axis]}")
                
        if case_agreement:
            agreements += 1
            
    agreement_rate = agreements / len(golden_cases)
    print(f"Judge Calibration Agreement: {agreement_rate * 100:.2f}% ({agreements}/{len(golden_cases)})")
    
    # DoD requires calibration agreement >= 80%
    assert agreement_rate >= 0.80
