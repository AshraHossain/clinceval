"""Unit coverage for triage heuristics and the mock judge's scoring branches."""
from eval.judge import grade_output
from eval.regression_runner import (
    PASS_THRESHOLD,
    infer_triage_tag,
    is_generation_successful,
    is_retrieval_successful,
)


def _pipeline_result(calculator, citations_valid=True, chunks=("chads2_vasc_chunk_0",), error=None):
    result = {
        "recommendation": {"calculator": calculator, "rationale": "r", "citations": []},
        "citations_valid": citations_valid,
        "retrieved_chunks": [{"id": c} for c in chunks],
    }
    if error:
        result["error"] = error
    return result


def _judge_result(**scores):
    base = {"faithfulness": 5, "clinical_relevance": 5, "safety": 5, "completeness": 5}
    base.update(scores)
    return {"scores": base}


CASE = {"expected_calculator": "CHA2DS2-VASc Score", "must_cite": ["chads2_vasc"]}


# --- triage ---

def test_triage_integration_on_error():
    assert infer_triage_tag(CASE, _pipeline_result(None, error="timeout"), _judge_result()) == "INTEGRATION"


def test_triage_retrieval_when_required_chunk_missing():
    result = _pipeline_result("CHA2DS2-VASc Score", chunks=("wells_pe_chunk_0",))
    assert infer_triage_tag(CASE, result, _judge_result()) == "RETRIEVAL"


def test_triage_generation_when_wrong_calculator():
    assert infer_triage_tag(CASE, _pipeline_result("MELD Score"), _judge_result()) == "GENERATION"


def test_triage_judge_when_scores_below_threshold():
    result = _pipeline_result("CHA2DS2-VASc Score")
    assert infer_triage_tag(CASE, result, _judge_result(safety=PASS_THRESHOLD - 1)) == "JUDGE"


def test_triage_pass_when_everything_ok():
    assert infer_triage_tag(CASE, _pipeline_result("CHA2DS2-VASc Score"), _judge_result()) == "PASS"


def test_retrieval_check_is_case_insensitive():
    assert is_retrieval_successful(CASE, ["CHADS2_VASC_CHUNK_1"])


def test_generation_check_none_expected():
    case = {"expected_calculator": "None"}
    assert is_generation_successful(case, _pipeline_result("None"))
    assert not is_generation_successful(case, _pipeline_result("MELD Score"))


# --- mock judge scoring branches ---

def test_mock_judge_penalizes_invalid_citations():
    scores = grade_output(CASE, _pipeline_result("CHA2DS2-VASc Score", citations_valid=False))["scores"]
    assert scores["faithfulness"] < PASS_THRESHOLD


def test_mock_judge_penalizes_hallucinated_recommendation():
    case = {"expected_calculator": "None"}
    scores = grade_output(case, _pipeline_result("MELD Score"))["scores"]
    assert scores["safety"] == 1 and scores["clinical_relevance"] == 1


def test_mock_judge_penalizes_wrongful_decline():
    scores = grade_output(CASE, _pipeline_result("None"))["scores"]
    assert scores["clinical_relevance"] < PASS_THRESHOLD


def test_mock_judge_penalizes_wrong_calculator():
    scores = grade_output(CASE, _pipeline_result("MELD Score"))["scores"]
    assert scores["clinical_relevance"] == 1 and scores["safety"] == 1


def test_mock_judge_full_marks_on_correct_answer():
    scores = grade_output(CASE, _pipeline_result("CHA2DS2-VASc Score"))["scores"]
    assert all(v == 5 for v in scores.values())
