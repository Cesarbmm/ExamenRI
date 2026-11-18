"""Evita descargas de train y valida también la caché local."""

import json

import pytest

from src.dataset import prepare_data


def test_download_selects_only_allowed_files(monkeypatch, tmp_path):
    calls = []

    def fake_load_dataset(repo, *args, **kwargs):
        calls.append((repo, kwargs))
        return {
            "corpus": [{"_id": "original-01", "title": "Title", "text": "Text"}],
            "queries": [{"_id": "q-01", "text": "Query"}],
            "test": [{"query-id": "q-01", "corpus-id": "original-01", "score": 1}],
        }[kwargs["split"]]

    monkeypatch.setattr("datasets.load_dataset", fake_load_dataset)
    assert prepare_data(tmp_path, force=True) == {"corpus": 1, "queries": 1, "qrels_test": 1}
    assert [(repo, kw["data_files"]) for repo, kw in calls] == [
        ("BeIR/scifact", {"corpus": "corpus/corpus-00000-of-00001.parquet"}),
        ("BeIR/scifact", {"queries": "queries/queries-00000-of-00001.parquet"}),
        ("BeIR/scifact-qrels", {"test": "test.tsv"}),
    ]
    assert all(kw["download_mode"] == "force_redownload" for _, kw in calls)
    assert prepare_data(tmp_path)["corpus"] == 1
    assert len(calls) == 3  # La caché validada no necesita red.
    (tmp_path / "qrels_test.jsonl").write_text(
        json.dumps({"query-id": "q-01", "corpus-id": "missing", "score": 1}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Qrel"):
        prepare_data(tmp_path)
