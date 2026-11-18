"""Evaluación reproducible de ambos modelos sobre la partición TEST."""

import csv
import json
from pathlib import Path

from src.dataset import load_corpus, load_queries, load_test_qrels, prepare_data
from src.evaluation import evaluate_models
from src.retrieval import SciFactSearchEngine


def main():
    prepare_data()
    engine = SciFactSearchEngine(load_corpus())
    queries, qrels = load_queries(), load_test_qrels()
    summary, per_query = evaluate_models(engine, queries, qrels)

    output = Path(__file__).resolve().parents[1] / "results"
    output.mkdir(exist_ok=True)
    (output / "metrics_test.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (output / "metrics_per_query_test.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(per_query[0]))
        writer.writeheader()
        writer.writerows(per_query)

    print(f"Documentos: {len(engine.corpus)} | Vocabulario: {len(engine.vocabulary)} | Consultas test: {len(qrels)}")
    for row in summary:
        print(f"{row['model']:5} | P@10={row['precision_at_10']:.4f} "
              f"R@10={row['recall_at_10']:.4f} NDCG@10={row['ndcg_at_10']:.4f} "
              f"| n={row['queries_evaluated']}")
    print(f"Evidencias escritas en {output}")


if __name__ == "__main__":
    main()
