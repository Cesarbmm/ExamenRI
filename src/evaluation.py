"""Métricas de recuperación sobre consultas con qrels de la partición TEST."""

import math
from statistics import mean


def metrics_at_10(ranked_ids: list[str], graded_qrels: dict[str, int]) -> dict[str, float]:
    relevance = {doc_id: int(score) for doc_id, score in graded_qrels.items() if score > 0}
    if not relevance:
        raise ValueError("La consulta no posee documentos relevantes evaluables")

    top10 = ranked_ids[:10]
    hits = sum(document_id in relevance for document_id in top10)
    dcg = sum((2 ** relevance.get(document_id, 0) - 1) / math.log2(i + 2)
              for i, document_id in enumerate(top10))
    ideal = sorted(relevance.values(), reverse=True)[:10]
    idcg = sum((2 ** score - 1) / math.log2(i + 2) for i, score in enumerate(ideal))

    return {
        "precision_at_10": hits / 10,
        "recall_at_10": hits / len(relevance),
        "ndcg_at_10": dcg / idcg if idcg else 0.0,
    }


def evaluate_models(engine, queries: dict[str, str], test_qrels: dict[str, dict[str, int]]):
    """Evalúa todas las consultas test con qrels positivos y promedia por consulta."""
    query_ids = sorted(qid for qid, rels in test_qrels.items() if any(v > 0 for v in rels.values()))
    missing = set(query_ids) - set(queries)
    if missing:
        raise ValueError(f"Hay {len(missing)} consultas de TEST sin texto: {sorted(missing)[:5]}")

    per_query = []
    for qid in query_ids:
        for model in ("tfidf", "bm25"):
            ranked_ids = [r["document_id"] for r in engine.search(queries[qid], model=model, top_k=10)]
            per_query.append({"query_id": qid, "model": model,
                              **metrics_at_10(ranked_ids, test_qrels[qid])})

    summary = []
    for model in ("tfidf", "bm25"):
        model_rows = [row for row in per_query if row["model"] == model]
        summary.append({
            "model": model,
            "queries_evaluated": len(model_rows),
            **{metric: mean(row[metric] for row in model_rows)
               for metric in ("precision_at_10", "recall_at_10", "ndcg_at_10")},
        })
    return summary, per_query
