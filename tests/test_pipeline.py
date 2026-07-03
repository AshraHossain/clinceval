import pytest
from app.pipeline import run_pipeline

def test_pipeline_e2e():
    query = "I have an 78-year-old male patient with history of atrial fibrillation, diabetes, and prior stroke. I need to calculate his stroke risk."
    
    result = run_pipeline(query, k=3)
    
    assert "query" in result
    assert "retrieved_chunks" in result
    assert "recommendation" in result
    
    recommendation = result["recommendation"]
    assert recommendation["calculator"] is not None
    assert "CHA2DS2-VASc" in recommendation["calculator"]
    assert recommendation["confidence"] > 0.5
    assert len(recommendation["citations"]) > 0
    
    # Assert citation validation ran and passed
    assert "citations_valid" in result
    assert result["citations_valid"] is True
    assert len(result["invalid_citations"]) == 0
    
    # Check metrics are tracked
    assert "metrics" in result
    metrics = result["metrics"]
    assert metrics["retrieval_count"] == 3
    assert metrics["generation_latency"] > 0
    assert metrics["pipeline_latency"] > 0
    assert metrics["input_tokens"] > 0
    assert metrics["output_tokens"] > 0
