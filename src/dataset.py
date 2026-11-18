"""Lectura, descarga y validación de SCIFACT de Hugging Face."""

import json
from collections import defaultdict
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
# Revisiones originales comprobadas; solo se solicitan los tres archivos permitidos.
SCIFACT_REVISION = "b3b5335604bf5ee3c4447671af975ea25143d4f5"
QRELS_REVISION = "2938d17dc3b09882fdb8c12bbbe2e2dc0e75a029"


def _read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def _write_jsonl(path: Path, records) -> None:
    with path.open("w", encoding="utf-8") as target:
        for record in records:
            target.write(json.dumps(record, ensure_ascii=False) + "\n")


def prepare_data(data_dir: Path = DEFAULT_DATA_DIR, force: bool = False) -> dict[str, int]:
    """Descarga corpus, consultas y qrels de TEST sin alterar identificadores."""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    paths = {name: data_dir / f"{name}.jsonl" for name in ("corpus", "queries", "qrels_test")}
    if not force and all(path.is_file() for path in paths.values()):
        records = {key: _read_jsonl(path) for key, path in paths.items()}
        _validate(records["corpus"], records["queries"], records["qrels_test"])
        return {key: len(rows) for key, rows in records.items()}

    from datasets import load_dataset

    download_mode = "force_redownload" if force else "reuse_dataset_if_exists"
    corpus_ds = load_dataset(
        "BeIR/scifact", "corpus", split="corpus", revision=SCIFACT_REVISION,
        data_files={"corpus": "corpus/corpus-00000-of-00001.parquet"},
        download_mode=download_mode,
    )
    queries_ds = load_dataset(
        "BeIR/scifact", "queries", split="queries", revision=SCIFACT_REVISION,
        data_files={"queries": "queries/queries-00000-of-00001.parquet"},
        download_mode=download_mode,
    )
    # split="test" por sí solo no impide preparar otros splits del repositorio.
    qrels_ds = load_dataset(
        "BeIR/scifact-qrels", split="test", revision=QRELS_REVISION,
        data_files={"test": "test.tsv"}, download_mode=download_mode,
    )

    corpus = [
        {"_id": str(row["_id"]), "title": str(row.get("title") or ""), "text": str(row.get("text") or "")}
        for row in corpus_ds
    ]
    queries = [
        {"_id": str(row["_id"]), "text": str(row.get("text") or "")}
        for row in queries_ds
    ]
    qrels = [
        {
            "query-id": str(row["query-id"]),
            "corpus-id": str(row["corpus-id"]),
            "score": int(row["score"]),
        }
        for row in qrels_ds
    ]

    _validate(corpus, queries, qrels)
    for key, records in (("corpus", corpus), ("queries", queries), ("qrels_test", qrels)):
        temp_path = paths[key].with_suffix(".jsonl.tmp")
        _write_jsonl(temp_path, records)
        temp_path.replace(paths[key])
    return {"corpus": len(corpus), "queries": len(queries), "qrels_test": len(qrels)}


def _validate(corpus: list[dict], queries: list[dict], qrels: list[dict]) -> None:
    doc_ids = [row["_id"] for row in corpus]
    query_ids = [row["_id"] for row in queries]
    if not doc_ids or not query_ids or not qrels:
        raise ValueError("SCIFACT no puede tener corpus, consultas o qrels vacíos")
    if len(doc_ids) != len(set(doc_ids)) or len(query_ids) != len(set(query_ids)):
        raise ValueError("El dataset contiene IDs duplicados")
    docs, qs = set(doc_ids), set(query_ids)
    for row in qrels:
        if row["query-id"] not in qs or row["corpus-id"] not in docs:
            raise ValueError(f"Qrel sin referencia válida: {row}")


def load_corpus(data_dir: Path = DEFAULT_DATA_DIR) -> list[dict]:
    return _read_jsonl(Path(data_dir) / "corpus.jsonl")


def load_queries(data_dir: Path = DEFAULT_DATA_DIR) -> dict[str, str]:
    return {row["_id"]: row["text"] for row in _read_jsonl(Path(data_dir) / "queries.jsonl")}


def load_test_qrels(data_dir: Path = DEFAULT_DATA_DIR) -> dict[str, dict[str, int]]:
    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    for row in _read_jsonl(Path(data_dir) / "qrels_test.jsonl"):
        query_id, document_id, score = row["query-id"], row["corpus-id"], int(row["score"])
        qrels[query_id][document_id] = max(score, qrels[query_id].get(document_id, 0))
    return dict(qrels)
