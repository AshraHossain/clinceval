"""API surface: FastAPI endpoint behavior (complements the Playwright E2E suite)."""
import pytest
from fastapi.testclient import TestClient

from app.server import app


@pytest.fixture(scope="module")
def client():
    # test_retriever's force_reindex drops the Chroma collection out from under
    # the module-global retriever; reset so warmup builds a fresh handle
    from app import retriever as retriever_module
    retriever_module._global_retriever = None
    with TestClient(app) as test_client:  # context manager runs lifespan warmup
        yield test_client


def test_recommend_returns_structured_result(client):
    resp = client.post("/api/recommend", json={
        "query": "A 75-year-old female with atrial fibrillation and hypertension needs stroke risk assessment."
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "CHA2DS2" in body["recommendation"]["calculator"]
    assert body["recommendation"]["citations"]
    assert body["citations_valid"] is True


def test_blank_query_rejected(client):
    resp = client.post("/api/recommend", json={"query": "   "})
    assert resp.status_code == 400


def test_missing_field_rejected(client):
    resp = client.post("/api/recommend", json={})
    assert resp.status_code == 422


def test_serves_chat_ui(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "ClinCalc-Eval" in resp.text
