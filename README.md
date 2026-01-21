# 🏺 ReportGraphQualifier

**ReportGraphQualifier** es un ecosistema desarrollado para **Atenea Research Group** enfocado en la gestión y calificación de grafos de conocimiento (Knowledge Graphs). El sistema permite la ingesta de datos semánticos, su almacenamiento en grafos y una interfaz visual para su análisis.

## 🏗️ Arquitectura del Sistema

El proyecto está completamente dockerizado y se compone de:
* **Neo4j 5.x:** Base de datos de grafos con soporte RDF mediante `n10s` (neosemantics).
* **FastAPI:** Backend en Python para la lógica de negocio y procesamiento de datos.
* **React + Vite:** Frontend interactivo con Hot Reload configurado para entornos Docker.

---

## 📥 Instalación y Despliegue (Máquina Limpia)

Sigue estos pasos para desplegar el entorno desde cero:

### 1. Requisitos previos
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y en ejecución.
* [Git](https://git-scm.com/) instalado.

### 2. Clonar el repositorio
```bash
git clone https://github.com/fjnavarrete2/ReportGraphQualifier.git
cd ReportGraphQualifier