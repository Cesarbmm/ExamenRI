# Verificación de Examen RI — SCIFACT

Verificación completada en `.venv` con Python **3.11.0**. Todos los requisitos
de `requirements.txt` y `requirements-dev.txt` están instalados dentro de sus
rangos; `pip check` no encuentra dependencias incompatibles.

Se descargaron nuevamente y de forma explícita solo los archivos autorizados:

- `BeIR/scifact`: corpus (5.183 documentos) y queries (1.109 consultas).
- `BeIR/scifact-qrels`: `test.tsv` (339 juicios, 300 consultas test).

Los repositorios originales son [BeIR/scifact](https://huggingface.co/datasets/BeIR/scifact)
y [BeIR/scifact-qrels](https://huggingface.co/datasets/BeIR/scifact-qrels).
Las revisiones fijadas y los SHA-256 locales están en `verification.json`.
No se descargaron otros datasets ni qrels de entrenamiento en esta verificación.
Se conservó íntegramente el enunciado original del examen.

## Resultados reales

Promedios macro sobre **todas las 300 consultas test**, con el mismo corpus y
preprocesamiento para ambos modelos. Los qrels se usan únicamente para evaluar.

| Modelo | P@10 | Recall@10 | NDCG@10 |
| --- | ---: | ---: | ---: |
| TF-IDF coseno | 0.083000 | 0.753667 | 0.605102 |
| BM25 | 0.090667 | 0.820167 | 0.684399 |

BM25 obtiene mayores valores en las tres métricas. P@10 usa denominador 10;
Recall@10 usa el total de relevantes de cada consulta. NDCG@10 usa ganancias
`2**rel - 1` y descuentos logarítmicos. No se afirma significancia estadística.

## Verificación ejecutada

- `python -m scripts.prepare_data --force`: descarga permitida e integridad válidas.
- `python -m scripts.evaluate`: evaluación completa, resultados en JSON/CSV.
- `python -m pytest -q`: **21 passed, 1 warning**.
- `notebooks/examen1bim_SCIFACT.ipynb`: 25 celdas, 11 de código, ejecutadas
  consecutivamente con el kernel `scifact-311`, outputs guardados y ningún error.
- TF-IDF contrastado con `cosine_similarity`; BM25 contrastado con su fórmula
  calculada desde las frecuencias y el índice invertido.
- Los 600 rankings test conservan IDs, títulos y snippets originales, ranks
  consecutivos, puntuaciones finitas, orden descendente, desempates deterministas,
  ausencia de duplicados y límite de resultados. Las métricas por consulta se
  contrastaron con un cálculo independiente.
- Uvicorn temporal en localhost: `/health` devuelve HTTP 200 y JSON del corpus;
  `/search` devuelve los mismos 600 rankings que el motor evaluado. Se comprobaron
  ambos modelos, consulta externa, `top_k=1/10/100`, valores predeterminados,
  consulta sin vocabulario y 15 entradas inválidas con HTTP 422. También pasó
  `scripts.smoke_test`. El servidor temporal se cerró al finalizar.
- JSON global, CSV de 600 filas, listado de 300 consultas y hashes de datos
  concordantes. Las versiones completas están en `environment_python311.txt`.

## Correcciones realizadas

| Prioridad | Evidencia | Cambio e impacto |
| --- | --- | --- |
| P1 | `notebooks/examen1bim_SCIFACT.ipynb` solo contenía carga de datos | Se completaron indexación, recuperación, evaluación, interpretación, comprobaciones HTTP y evidencias; se ejecutó y guardó. |
| P1 | `src/dataset.py`, descarga de qrels sin `data_files` | Selección explícita de los tres archivos permitidos y revisiones fijadas; evita preparar otros splits. |
| P1 | `src/dataset.py`, caché sin validar | Se comprueba unicidad e integridad referencial también al reutilizar datos locales. |
| P2 | `app/main.py`, coerción de `top_k` | Se rechazan booleanos, cadenas y flotantes; solo se aceptan enteros de 1 a 100. |
| P2 | `README.md`, nombre de notebook inexistente | Se corrigió la ruta y se documentó la ejecución completa con Python 3.11. |

## Servicio público

Servicio en Render: https://examenri-14iv.onrender.com.
`GET /health` devuelve HTTP 200 y confirma los 5.183 documentos SCIFACT.
`POST /search` funciona con BM25 y TF-IDF: IDs originales, puntuaciones finitas,
orden descendente, sin duplicados y límites `top_k=1/5/10` comprobados.
Las entradas inválidas devuelven 422 y `scripts.smoke_test` pasa contra esa URL.

**Aviso no bloqueante:** Starlette anuncia la deprecación de `httpx` para su
`TestClient`. Las 21 pruebas pasan y el servicio HTTP real funciona. Se conserva
el aviso en `verification.json`; no se alteraron las dependencias del examen.

No quedan fallos de ejecución, de recuperación ni de contrato JSON observados.
