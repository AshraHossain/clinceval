import pytest
from app.retriever import Retriever, retrieve

@pytest.fixture(scope="module")
def initialized_retriever():
    # Force reindex to ensure we have a clean test database
    return Retriever(force_reindex=True)

def test_basic_retrieval(initialized_retriever):
    results = initialized_retriever.retrieve("stroke risk afib", k=3)
    assert len(results) > 0
    assert any("CHA2DS2-VASc" in chunk["metadata"]["calculator"] for chunk in results)

def test_recall_at_three(initialized_retriever):
    # Test cases: (query, expected_calculator_source_name)
    test_cases = [
        ("stroke risk estimation for a patient with atrial fibrillation", "chads2_vasc.md"),
        ("suspected pulmonary embolism Wells score criteria", "wells_pe.md"),
        ("calf swelling, pain, pitting edema in one leg, DVT risk", "wells_dvt.md"),
        ("3-month mortality risk for liver transplant candidate MELD", "meld.md"),
        ("pneumonia severity score age 65 confusion uremia", "curb_65.md"),
        ("chest pain, emergency department cardiac event risk, HEART score", "heart_score.md"),
        ("neurological eye opening motor verbal assessment, Glasgow coma scale", "gcs.md"),
        ("bleeding risk in patient starting warfarin, HAS-BLED", "has_bled.md"),
        ("rule out PE in a low-risk clinical case using PERC", "perc_rule.md"),
        ("cirrhosis severity Child-Pugh classification and survival", "child_pugh.md"),
        ("sepsis risk assessment qSOFA bedside respiratory rate", "qsofa.md"),
        ("pediatric minor head trauma CT scan criteria PECARN", "pecarn_head_injury.md")
    ]
    
    hits = 0
    total = len(test_cases)
    
    for query, expected_source in test_cases:
        results = initialized_retriever.retrieve(query, k=3)
        retrieved_sources = [chunk["metadata"]["source"] for chunk in results]
        
        if expected_source in retrieved_sources:
            hits += 1
        else:
            print(f"FAIL: Query '{query}' expected '{expected_source}', but got: {retrieved_sources}")
            
    recall_rate = hits / total
    print(f"Recall@3: {recall_rate * 100:.2f}% ({hits}/{total})")
    
    # DoD requires recall@3 >= 90%
    assert recall_rate >= 0.90
