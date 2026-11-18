"""Servicio REST. Sin interfaz gráfica; API disponible para Postman/curl."""

from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field, field_validator

from src.dataset import DEFAULT_DATA_DIR, load_corpus
from src.retrieval import SciFactSearchEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    path = DEFAULT_DATA_DIR / "corpus.jsonl"
    if not path.is_file():
        raise RuntimeError("Falta el corpus. Ejecuta: python -m scripts.prepare_data")
    app.state.engine = SciFactSearchEngine(load_corpus(DEFAULT_DATA_DIR))
    yield


app = FastAPI(title="Examen RI - SciFact", docs_url=None, redoc_url=None, lifespan=lifespan)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    model: Literal["bm25", "tfidf"] = "bm25"
    top_k: int = Field(default=10, ge=1, le=100, strict=True)

    @field_validator("query")
    @classmethod
    def check_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query no puede contener únicamente espacios")
        return value


class SearchResult(BaseModel):
    rank: int
    document_id: str
    score: float
    title: str
    snippet: str


class SearchResponse(BaseModel):
    model: Literal["bm25", "tfidf"]
    results: list[SearchResult]


@app.get("/health")
def health(request: Request):
    return {
        "status": "ok",
        "dataset": "BeIR/scifact",
        "documents": len(request.app.state.engine.document_ids),
        "models": ["bm25", "tfidf"],
    }


@app.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, request: Request):
    results = request.app.state.engine.search(payload.query, model=payload.model, top_k=payload.top_k)
    return SearchResponse(model=payload.model, results=results)
