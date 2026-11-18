"""Índice invertido, TF-IDF coseno y BM25 para documentos completos."""

import re
from collections import defaultdict

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer

from src.preprocess import preprocess


class SciFactSearchEngine:
    def __init__(self, corpus: list[dict]):
        if not corpus:
            raise ValueError("No se puede construir el índice de un corpus vacío")

        self.corpus = [
            {
                "_id": str(document["_id"]),
                "title": str(document.get("title") or ""),
                "text": str(document.get("text") or ""),
            }
            for document in corpus
        ]
        self.document_ids = [document["_id"] for document in self.corpus]
        if len(self.document_ids) != len(set(self.document_ids)):
            raise ValueError("Los identificadores de documentos deben ser únicos")

        full_texts = [f'{doc["title"]} {doc["text"]}' for doc in self.corpus]
        self.tokenized_documents = [preprocess(text) for text in full_texts]

        postings: dict[str, list[str]] = defaultdict(list)
        for document_id, tokens in zip(self.document_ids, self.tokenized_documents):
            for term in set(tokens):
                postings[term].append(document_id)
        self.inverted_index = dict(sorted(postings.items()))
        self.vocabulary = frozenset(self.inverted_index)

        # Preprocesamiento de consulta idéntico al de documentos.
        self.vectorizer = TfidfVectorizer(analyzer=preprocess, norm="l2", smooth_idf=True)
        self.tfidf_matrix = self.vectorizer.fit_transform(full_texts)
        self.bm25 = BM25Okapi(self.tokenized_documents, k1=1.5, b=0.75)

    def search(self, query: str, model: str = "bm25", top_k: int = 10) -> list[dict]:
        if model not in {"bm25", "tfidf"}:
            raise ValueError("model debe ser 'bm25' o 'tfidf'")
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
            raise ValueError("top_k debe ser un entero positivo")
        if not isinstance(query, str):
            raise ValueError("query debe ser texto")

        tokens = preprocess(query)
        if not tokens or not self.vocabulary.intersection(tokens):
            return []

        if model == "bm25":
            scores = np.asarray(self.bm25.get_scores(tokens), dtype=np.float64)
        else:
            query_vector = self.vectorizer.transform([query])
            scores = (self.tfidf_matrix @ query_vector.T).toarray().reshape(-1)

        matching_indices = np.flatnonzero(np.isfinite(scores) & (scores > 0))
        # Desempates consistentes por ID original, para reproducibilidad.
        ordered = sorted(matching_indices, key=lambda i: (-float(scores[i]), self.document_ids[i]))[:top_k]

        results = []
        for rank, i in enumerate(ordered, start=1):
            document = self.corpus[i]
            snippet = re.sub(r"\s+", " ", document["text"]).strip()[:250]
            results.append(
                {
                    "rank": rank,
                    "document_id": document["_id"],
                    "score": float(scores[i]),
                    "title": document["title"],
                    "snippet": snippet,
                }
            )
        return results
