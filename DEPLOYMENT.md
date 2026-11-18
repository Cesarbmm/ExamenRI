# Estado del despliegue en Render

El c?digo completo est? publicado en https://github.com/Cesarbmm/ExamenRI,
rama `main`. Commit de c?digo probado: `f3394b97ab9debbf7dd6c756a033da639db7fec3`.

Destino obligatorio: servicio existente **examenri**, URL asignada
https://examenri.onrender.com, health https://examenri.onrender.com/health.
No se cre? ning?n servicio ni Blueprint y no se cambi? la URL.

## Verificaci?n completada

- 21 pruebas pytest aprobadas; `pip check` sin incompatibilidades.
- Clon nuevo desde GitHub, entorno virtual Python 3.11.0 nuevo e instalaci?n
  ?nicamente de `requirements.txt`.
- Descarga en una cach? nueva: 5.183 documentos, 1.109 consultas y 339 qrels
  test de SCIFACT. Los archivos obtenidos coinciden con los datos originales.
- API iniciada y reiniciada desde ese clon: dos rondas de 12 comprobaciones
  HTTP reales. Ambos modelos, IDs originales, orden, ausencia de duplicados,
  t?tulos, snippets y top_k=1/5/10 correctos. Modelo inv?lido, consulta vac?a
  y JSON incorrecto devuelven 422.
- Arranques locales de 13.27 y 13.25 segundos; memoria RSS del ?rbol de
  procesos de 313.69 y 314.83 MiB en Windows. La memoria real de Render queda
  pendiente de observaci?n; estas mediciones locales no sustituyen sus logs.
- Evaluaci?n sobre las 300 consultas test desde el clon limpio: las seis
  m?tricas coinciden exactamente con los resultados originales.
- Notebook ejecutado, recuperaci?n, preprocesamiento, evaluaci?n y m?tricas
  originales sin cambios, comprobados mediante SHA-256.

## Cambios de infraestructura publicados

- `render.yaml` apunta a examenri, rama main y plan Free; es una referencia
  que **no debe aplicarse para crear un Blueprint**.
- Build: `python -m pip install -r requirements.txt && python -m scripts.prepare_data`.
- Start: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`.
- Health `/health`, Python 3.11.11 y Auto Deploy documentados en README.
- `.gitignore` excluye entornos, temporales, cach?s y credenciales; conserva
  las evidencias de evaluaci?n que se deben entregar.

## Bloqueo pendiente

La integraci?n Render figura instalada tras la conexi?n indicada por el usuario,
pero ninguna herramienta de Render est? disponible en esta ejecuci?n. Tampoco
hay CLI autenticado, clave API ni navegador autenticado accesible como alternativa.
No fue posible consultar el ID del servicio, actualizar su configuraci?n,
activar un deploy ni consultar logs. No hay commit desplegado confirmado.

Las solicitudes HTTPS a `/health` agotaron el tiempo de espera. Las pruebas
p?blicas de b?squeda, l?mites, entradas inv?lidas, smoke test y arranque en fr?o
quedan pendientes de un despliegue confirmado. No se acredita HTTP 200 p?blico.
Swagger est? deshabilitado en la API existente (`/docs` devuelve 404 localmente).

Paso m?nimo para continuar: enviar un nuevo mensaje con la integraci?n Render
seleccionada para disponer de sus herramientas. La instalaci?n ya est? hecha.

El detalle de esta comprobaci?n est? en `results/deployment_public.json`.
