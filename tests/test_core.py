"""Pruebas unitarias sin dependencia de descargas externas."""

import pytest
import math
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from src.evaluation import metrics_at_10
from src.preprocess import preprocess
from src.retrieval import SciFactSearchEngine


CORPUS = [
    {"_id": "doc-A", "title": "Aspirin study", "text": "Aspirin prevents blood clots and heart attacks."},
    {"_id": "doc-B", "title": "Viral infection", "text": "Virus replication depends on host cells."},
    {"_id": "doc-C", "title": "Aspirin treatment", "text": "Aspirin is not effective for all patients."},
]


def test_preprocessing_keeps_negations_and_stems():
    terms = preprocess("Aspirin is NOT preventing viral infections.")
    assert "not" in terms
    assert "aspirin" in terms
    assert "prevent" in terms


def test_metrics_exact():
    m = metrics_at_10(["a", "b", "c"], {"a": 1, "c": 1})
    assert m["precision_at_10"] == pytest.approx(0.2)
    assert m["recall_at_10"] == pytest.approx(1.0)
    assert 0 < m["ndcg_at_10"] <= 1


def test_metrics_cutoff_short_ranking_and_graded_relevance():
    qrels = {"high": 2, "low": 1, "excluded": 0}
    actual = metrics_at_10(["low"], qrels)
    assert actual["precision_at_10"] == pytest.approx(0.1)
    assert actual["recall_at_10"] == pytest.approx(0.5)
    assert actual["ndcg_at_10"] == pytest.approx(1 / (3 + 1 / math.log2(3)))
    assert metrics_at_10([f"irrelevant-{i}" for i in range(10)] + ["high"], qrels) == {
        "precision_at_10": 0, "recall_at_10": 0, "ndcg_at_10": 0,
    }


def test_tfidf_scores_are_cosine_similarity():
    engine = SciFactSearchEngine(CORPUS)
    query = "aspirin heart"
    reference = cosine_similarity(engine.vectorizer.transform([query]), engine.tfidf_matrix)[0]
    assert np.linalg.norm(engine.vectorizer.transform([query]).toarray()) == pytest.approx(1)
    for result in engine.search(query, model="tfidf"):
        index = engine.document_ids.index(result["document_id"])
        assert result["score"] == pytest.approx(reference[index])


@pytest.mark.parametrize("model", ["bm25", "tfidf"])
def test_models_return_original_ids_and_sorted_results(model):
    engine = SciFactSearchEngine(CORPUS)
    assert "aspirin" in engine.vocabulary
    assert set(engine.inverted_index["aspirin"]) == {"doc-A", "doc-C"}
    results = engine.search("Does aspirin prevent heart attacks?", model=model, top_k=2)
    assert 1 <= len(results) <= 2
    assert all(r["document_id"] in {"doc-A", "doc-B", "doc-C"} for r in results)
    assert [r["rank"] for r in results] == list(range(1, len(results) + 1))
    assert [r["score"] for r in results] == sorted((r["score"] for r in results), reverse=True)
    assert len({r["document_id"] for r in results}) == len(results)


@pytest.mark.parametrize("model", ["bm25", "tfidf"])
def test_unknown_terms_return_empty(model):
    engine = SciFactSearchEngine(CORPUS)
    assert engine.search("qzxynotaword", model=model, top_k=10) == []


def test_invalid_inputs():
    engine = SciFactSearchEngine(CORPUS)
    with pytest.raises(ValueError):
        engine.search("test", model="other")
    with pytest.raises(ValueError):
        engine.search("test", top_k=0)
    with pytest.raises(ValueError):
        SciFactSearchEngine(CORPUS + [CORPUS[0]])
