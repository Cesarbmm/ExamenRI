"""Comprueba un servicio publicado y valida el contrato esperado por el docente."""

import argparse

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", help="Ejemplo: https://mi-servicio.onrender.com")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    with httpx.Client(timeout=120) as client:
        health = client.get(base + "/health")
        health.raise_for_status()
        assert health.json()["status"] == "ok", health.json()
        print("GET /health:", health.json())

        for model in ("bm25", "tfidf"):
            payload = {"query": "Aspirin reduces the risk of cardiovascular disease", "model": model, "top_k": 5}
            response = client.post(base + "/search", json=payload)
            response.raise_for_status()
            body = response.json()
            assert body["model"] == model
            assert len(body["results"]) <= 5
            ids = [item["document_id"] for item in body["results"]]
            assert len(ids) == len(set(ids)), "Documentos duplicados"
            assert [item["rank"] for item in body["results"]] == list(range(1, len(ids) + 1))
            assert all(body["results"][i]["score"] >= body["results"][i + 1]["score"]
                       for i in range(len(ids) - 1))
            assert all(set(item) == {"rank", "document_id", "score", "title", "snippet"}
                       for item in body["results"])
            print(f"POST /search ({model}) OK | recuperados: {len(ids)} | IDs: {ids}")

        invalid = client.post(base + "/search", json={"query": "test", "model": "invalido", "top_k": 10})
        assert invalid.status_code == 422
        print("Validación de modelo inválido: 422 OK")


if __name__ == "__main__":
    main()
