# Examen ICCD753 — Recuperación de Información (SCIFACT)

Servicio web **sin interfaz gráfica**, que recupera documentos completos de `BeIR/scifact`
utilizando **TF-IDF + coseno** y **BM25**, con IDs originales y evaluación en `test`.

## Qué entrega el examen

1. **URL pública**: endpoints `GET /health` y `POST /search`.
2. **Notebook ejecutado**: `notebooks/examen1bim_SCIFACT.ipynb` (con el enunciado original), con resultados y tabla
   de `Precision@10`, `Recall@10`, `NDCG@10` para ambos modelos sobre los qrels de `test`.

El código está preparado para descargar el corpus original, NO NFCorpus ni FiQA.
No se entrenan modelos con los qrels y no se trocean los documentos.

## Requisitos previos (Windows 11 + Python 3.11)

Desde PowerShell, en la carpeta raíz del repositorio:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m scripts.prepare_data
python -m scripts.evaluate
pytest -q
```

Para abrir el Notebook:

```powershell
jupyter lab
```

Abre `notebooks/examen1bim_SCIFACT.ipynb`, selecciona el kernel de Python 3.11 de `.venv` y
**ejecuta todas las celdas** (`Run All`). Luego **guarda el notebook** para
entregarlo con los resultados calculados realmente en tu equipo.

También puedes ejecutarlo y guardarlo desde PowerShell con el entorno activo:

```powershell
python -m ipykernel install --sys-prefix --name scifact-311 --display-name "Python 3.11 (Examen RI)"
python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=scifact-311 --ExecutePreprocessor.timeout=600 notebooks/examen1bim_SCIFACT.ipynb
```

El notebook comprueba los 600 rankings de test, contrasta las fórmulas de ambos
modelos y las métricas por consulta, inicia y cierra Uvicorn en localhost para
verificar el contrato HTTP y ejecuta `pip check` y `pytest`. Guarda las evidencias
en `results/verification.json` y las versiones exactas en `results/environment_python311.txt`.
La descarga selecciona explícitamente corpus, queries y `test.tsv` en revisiones
fijadas de SCIFACT. Para repetirla: `python -m scripts.prepare_data --force`.

Recomendación: asegúrate de que haya conexión a Hugging Face durante
`prepare_data`. Después, dataset, API y evaluación funcionan sin conexión.

## Arrancar el web service localmente

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```powershell
python -m scripts.smoke_test http://127.0.0.1:8000
```

Peticiones manuales (PowerShell):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health

$payload = @{query='Aspirin reduces the risk of cardiovascular disease'; model='bm25'; top_k=10} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/search -ContentType 'application/json' -Body $payload
```

Usa `model='tfidf'` para el otro ranking. La API valida `query`, `model`
y `top_k` (de 1 a 100); entradas inválidas devuelven HTTP 422.
Si la consulta no contiene términos del vocabulario, devuelve `results: []`.

## Publicar en Render

El destino es el **Web Service existente `examenri`**, con URL asignada
`https://examenri-14iv.onrender.com`, y el repositorio
`https://github.com/Cesarbmm/ExamenRI`. **No crear otro servicio ni un Blueprint.**
`render.yaml` documenta la configuración; su presencia en el repositorio no
actualiza por sí sola un servicio creado manualmente.

En Settings del servicio existente, comprobar su ID, nombre y URL antes de aplicar:

| Ajuste | Valor |
| --- | --- |
| Repository | `https://github.com/Cesarbmm/ExamenRI` |
| Branch | `main` |
| Root Directory | vacío: el proyecto está en la raíz del repositorio |
| Runtime / Plan | Python / Free |
| `PYTHON_VERSION` | `3.11.11` |
| Build Command | `python -m pip install -r requirements.txt && python -m scripts.prepare_data` |
| Start Command | `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1` |
| Health Check Path | `/health` |
| Auto Deploy | activado para `main` |

El build descarga los tres archivos permitidos y crea `data/*.jsonl` dentro del
artefacto desplegado. No se requieren archivos de la computadora del estudiante.
Cada inicio reconstruye los índices desde el corpus incluido en ese artefacto;
FastAPI completa esa carga antes de aceptar solicitudes. No se necesita disco
persistente, GPU ni un servicio adicional. Los qrels no se cargan en el servidor.
Las dependencias de Jupyter y pytest solo se instalan para desarrollo.

Verificar build y runtime en los logs de Render y comprobar la URL real:

   ```powershell
   python -m scripts.smoke_test https://examenri-14iv.onrender.com
   ```

Los servicios gratuitos de Render entran en reposo tras 15 minutos sin tráfico;
el primer acceso puede tardar mientras se reconstruyen los índices. Véase la
[documentación oficial del plan Free](https://render.com/docs/free).
El servicio conserva los endpoints `GET /health` y `POST /search`; Swagger
`/docs` está deshabilitado en esta API. El endpoint raíz `/` no es una interfaz.
La URL asignada solo se considera operativa después de pasar las pruebas HTTP.

## Estrategia de recuperación

- **Colección**: documentos completos (`title + text`) sin fragmentación.
- **Normalización**: Unicode NFKC y minúsculas.
- **Tokenización**: expresiones regulares para letras inglesas y dígitos.
- **Stopwords**: lista en inglés de scikit-learn, exceptuando negaciones
  `no`, `not`, `nor`, `without` por su importancia en afirmaciones científicas.
- **Stemming**: PorterStemmer (`nltk`), sin descargas adicionales.
- **Índice invertido**: `término -> lista de document_id originales`.
- **TF-IDF**: vocabulario del corpus + pesos IDF suavizados + vectores L2.
  La multiplicación `documentos_normalizados @ consulta_normalizada.T` calcula coseno.
- **BM25**: `rank_bm25.BM25Okapi`, `k1=1.5`, `b=0.75`.
- **Rankings**: puntuación descendente, desempate determinista por ID,
  sin documentos duplicados y hasta `top_k`. Se omiten puntuaciones cero.

## Evaluación correcta

- Se usa `BeIR/scifact-qrels`, **partición `test` exclusivamente**.
- Solo se evalúan consultas con al menos un qrel de relevancia positiva.
- `P@10`: relevantes recuperados en los primeros 10 / 10.
- `Recall@10`: relevantes recuperados / total relevante en qrels de esa consulta.
- `NDCG@10`: DCG de relevancias graduadas con ganancia `2**rel - 1`,
  normalizado por el DCG ideal de la consulta.
- Todas las métricas son **macro promedio por consulta**.
- Los qrels se usan solo para evaluación; no se alteran rankings con su contenido.

## Estructura

```text
app/main.py                  API FastAPI (/health, /search)
src/preprocess.py            Normalización, stopwords y stemming
src/dataset.py               Carga BeIR + validación y caché JSONL
src/retrieval.py             Índice invertido + TF-IDF + BM25
src/evaluation.py            P@10, Recall@10, NDCG@10
scripts/prepare_data.py      Descarga y validación
scripts/evaluate.py          Evaluación test y exportación de CSV/JSON
scripts/smoke_test.py        Smoke test HTTP para URL local o pública
tests/                       Pruebas unitarias y contrato HTTP
notebooks/examen1bim_SCIFACT.ipynb Entregable conservando enunciado
notebooks/Examen_SCIFACT.ipynb Versión compacta ejecutable
render.yaml                  Configuración de despliegue
requirements*.txt            Dependencias de servidor y desarrollo
```

## Verificación final de entrega

- [ ] `pytest -q` termina sin errores.
- [ ] El notebook se ejecutó íntegramente **con outputs reales y guardados**.
- [ ] Aparecen las métricas de **ambos modelos y todas las consultas test**.
- [ ] `GET /health` responde 200 en la **URL pública**.
- [ ] `POST /search` responde con ambos modelos para consultas nuevas.
- [ ] Se verificó que los IDs pertenecen al corpus y los resultados están ordenados.
- [ ] La URL sigue pública durante todo el período de evaluación docente.
