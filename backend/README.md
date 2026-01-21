# Backend

Este directorio contiene el servicio de API y las utilidades de procesamiento semántico.

## Archivos destacados

- `api.py` – API construida con FastAPI para procesar atestados, generar RDF y realizar inferencias.
- `decisionTree.py` – Árbol de decisión que utiliza un modelo LLM para clasificar los delitos.
- `entities.py` – Modelos de datos (bienes, víctimas, acusados, atestados...).
- `atestadoToText.py` – Genera descripciones en lenguaje natural a partir de un `Atestado`.
- `rdfFile.py` – Crea grafos RDF según la ontología definida y permite filtrarlos.
- `documents.py` – Funciones auxiliares para leer archivos PDF y DOCX.
- `reasonerFromFile.py` – Carga un RDF en la ontología `SCPO_Extended_Ontology` y ejecuta el razonador Pellet.
- `SCPO_Extended_Ontology_V01R08_AT08Q.owl` y `catalog-v001.xml` – Ontología utilizada y su catálogo.
- `Dockerfile`, `render-build.sh` y `vercel.json` – Archivos para despliegue.
- `requirements.txt` – Dependencias de Python.

