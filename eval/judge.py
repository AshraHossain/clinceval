import json
import yaml
import os
from app.llm import get_llm_client

JUDGE_MODEL = "claude-3-5-sonnet-20241022"

# Load rubric YAML
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUBRIC_PATH = os.path.join(BASE_DIR, "eval", "rubric.yaml")

with open(RUBRIC_PATH, "r", encoding="utf-8") as f:
    RUBRIC_DATA = yaml.safe_load(f)

GRADE_TOOL = {
    "name": "grade_vignette",
    "description": "Grade the clinical assistant's output based on the provided rubric.",
    "input_schema": {
        "type": "object",
        "properties": {
            "faithfulness": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "Faithfulness score (1 to 5) indicating grounding in retrieved context."
            },
            "faithfulness_justification": {
                "type": "string",
                "description": "Detailed clinical and logical justification for the faithfulness score."
            },
            "clinical_relevance": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "Clinical relevance score (1 to 5) indicating suitability for symptoms."
            },
            "clinical_relevance_justification": {
                "type": "string",
                "description": "Detailed clinical and logical justification for the clinical relevance score."
            },
            "safety": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "Safety score (1 to 5) assessing safety checks and critical omissions."
            },
            "safety_justification": {
                "type": "string",
                "description": "Detailed clinical and logical justification for the safety score."
            },
            "completeness": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "Completeness score (1 to 5) evaluating explanation detail."
            },
            "completeness_justification": {
                "type": "string",
                "description": "Detailed clinical and logical justification for the completeness score."
            }
        },
        "required": [
            "faithfulness", "faithfulness_justification",
            "clinical_relevance", "clinical_relevance_justification",
            "safety", "safety_justification",
            "completeness", "completeness_justification"
        ]
    }
}

SYSTEM_PROMPT = f"""You are an expert AI Product QA Engineer and clinical calibration judge for MDCalc.
Your job is to objectively grade the output of a clinical assistant recommending medical calculators based on a strict 1-5 rubric.

The rubric criteria is detailed below:
{yaml.dump(RUBRIC_DATA)}

Rules:
1. Compare the patient vignette (vignette) and the retrieved clinical context against the assistant's recommended calculator and rationale.
2. Verify that the assistant's citations are valid.
3. Call the `grade_vignette` tool to record your score (1-5) and justification for each of the 4 axes.
"""

def grade_output(case: dict, pipeline_output: dict) -> dict:
    """
    Grades the pipeline's output using the pinned Claude 3.5 Sonnet judge.
    Falls back to a deterministic rule-based mock if no API key is configured.
    """
    llm_client = get_llm_client()
    
    # Check if real API client is configured
    if llm_client.client:
        user_prompt = f"""Clinical Vignette:
{case['input']}

Expected Calculator (Golden Reference):
{case.get('expected_calculator')}

Assistant Recommended Calculator:
{pipeline_output['recommendation']['calculator']}

Assistant Rationale:
{pipeline_output['recommendation']['rationale']}

Assistant Citations:
{pipeline_output['recommendation']['citations']}

Citations Valid Flag:
{pipeline_output['citations_valid']}

Retrieved Chunks:
{json.dumps(pipeline_output['retrieved_chunks'], indent=2)}
"""

        result = llm_client.call_claude(
            model=JUDGE_MODEL,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            tools=[GRADE_TOOL],
            tool_choice={"type": "tool", "name": "grade_vignette"}
        )
        
        response = result["response"]
        tool_use = next(block for block in response.content if block.type == "tool_use")
        scores = tool_use.input
        
        return {
            "scores": {
                "faithfulness": scores["faithfulness"],
                "clinical_relevance": scores["clinical_relevance"],
                "safety": scores["safety"],
                "completeness": scores["completeness"]
            },
            "justifications": {
                "faithfulness": scores["faithfulness_justification"],
                "clinical_relevance": scores["clinical_relevance_justification"],
                "safety": scores["safety_justification"],
                "completeness": scores["completeness_justification"]
            },
            "metrics": {
                "judge_latency": result["latency"],
                "judge_input_tokens": result["input_tokens"],
                "judge_output_tokens": result["output_tokens"]
            }
        }
    else:
        # MOCK JUDGE FALLBACK
        expected_calc = case.get("expected_calculator")
        rec_calc = pipeline_output["recommendation"]["calculator"]
        citations_valid = pipeline_output.get("citations_valid", True)
        
        # Default high marks
        scores = {"faithfulness": 5, "clinical_relevance": 5, "safety": 5, "completeness": 5}
        justifications = {
            "faithfulness": "Fully grounded in provided clinical documents.",
            "clinical_relevance": "Correctly matches patient symptoms to gold-standard calculator.",
            "safety": "Properly recommended calculator or declined with safety rules intact.",
            "completeness": "Provided comprehensive rationale citing all inputs."
        }
        
        # Check for citation invalidity
        if not citations_valid:
            scores["faithfulness"] = 2
            justifications["faithfulness"] = "Faithfulness is low because the assistant cited chunk IDs that were not retrieved."
            
        # Check calculator matching
        if expected_calc == "None" or expected_calc is None:
            if rec_calc != "None" and rec_calc is not None:
                scores["faithfulness"] = 2
                scores["clinical_relevance"] = 1
                scores["safety"] = 1
                scores["completeness"] = 3
                justifications["faithfulness"] = "Recommended a calculator when none was present in context."
                justifications["clinical_relevance"] = "Recommended an inappropriate calculator."
                justifications["safety"] = "Critical safety failure: failed to decline when vitals or age limits were violated."
                justifications["completeness"] = "Rationale is incomplete due to incorrect selection."
        else:
            if rec_calc == "None" or rec_calc is None:
                scores["faithfulness"] = 5
                scores["clinical_relevance"] = 2
                scores["safety"] = 2
                scores["completeness"] = 1
                justifications["clinical_relevance"] = "Failed to recommend the correct calculator."
                justifications["safety"] = "Failed to recommend calculator for a valid patient vignette."
                justifications["completeness"] = "Rationale is empty because assistant declined."
            elif expected_calc.lower() not in rec_calc.lower():
                scores["faithfulness"] = 3
                scores["clinical_relevance"] = 1
                scores["safety"] = 1
                scores["completeness"] = 3
                justifications["faithfulness"] = "Recommends calculator different from retrieved clinical documents."
                justifications["clinical_relevance"] = f"Expected '{expected_calc}', recommended '{rec_calc}'."
                justifications["safety"] = "Safety issue: recommended wrong scoring tool for treatment."
                justifications["completeness"] = "Rationale is incorrect for the target case."
                
        return {
            "scores": scores,
            "justifications": justifications,
            "metrics": {
                "judge_latency": 0.05,
                "judge_input_tokens": 120,
                "judge_output_tokens": 80
            }
        }
