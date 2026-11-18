"""Verifica el contrato HTTP del examen usando un corpus mínimo sintético."""

from fastapi.testclient import TestClient
import pytest

from app.main import app
from src.retrieval import SciFactSearchEngine
from tests.test_core import CORPUS


@pytest.fixture
def client(monkeypatch):
    # Se inserta motor de prueba para no descargar SCIFACT.
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def test_lifespan(api):
        api.state.engine = SciFactSearchEngine(CORPUS)
        yield

    monkeypatch.setattr(app.router, "lifespan_context", test_lifespan)
    with TestClient(app) as test_client:
        yield test_client


def test_http_contract(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.headers["content-type"] == "application/json"
    assert health.json() == {"status": "ok", "dataset": "BeIR/scifact",
                             "documents": 3, "models": ["bm25", "tfidf"]}
    for model in ("bm25", "tfidf"):
        response = client.post("/search", json={"query": "aspirin heart", "model": model, "top_k": 2})
        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"model", "results"}
        assert body["model"] == model
        assert len(body["results"]) == 2
        assert all(set(result) == {"rank", "document_id", "score", "title", "snippet"}
                   for result in body["results"])
    invalid = client.post("/search", json={"query": "hello", "model": "other"})
    assert invalid.status_code == 422
    blank = client.post("/search", json={"query": "   "})
    assert blank.status_code == 422
    huge_k = client.post("/search", json={"query": "hello", "top_k": 999})
    assert huge_k.status_code == 422


@pytest.mark.parametrize("top_k", [True, False, "10", 10.0, 1.5, None, 0, -1, 101])
def test_top_k_requires_integer_in_range(client, top_k):
    response = client.post("/search", json={"query": "aspirin", "top_k": top_k})
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)


def test_defaults_unknown_terms_and_missing_query(client):
    response = client.post("/search", json={"query": "aspirin"})
    assert response.status_code == 200
    assert response.json()["model"] == "bm25"
    for model in ("bm25", "tfidf"):
        response = client.post("/search", json={"query": "qzxynotaword", "model": model})
        assert response.json() == {"model": model, "results": []}
    assert client.post("/search", json={}).status_code == 422
