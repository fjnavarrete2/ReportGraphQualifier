import requests
import pytest
from pathlib import Path


BASE_URL = "https://veredictai.onrender.com/"
FILES_DIR = Path(__file__).parent / "files"


atestado_ejemplo = {
  "atestado_id": "Atestado123",
  "victimas": [
    {
      "id": "victima1",
      "efectos_del_delito": []
    }
  ],
  "autores": [
    {
      "id": "acusado1",
      "edad": 28,
      "organizacion_criminal": "Ninguna",
      "antecedentes": 2,
      "caracteristicas_acusado": ["Más de 3 condenas previas"]
    }
  ],
  "complices": [],
  "testigos": [],
  "empresas": ["Supermercado Central"],
  "bienes_robados": [
    {
      "nombre": "iPhone12",
      "caracteristicas_especiales": [],
      "propietario": "victima1",
      "usuario": "victima1"
    }
  ],
  "valor_total_robado": 599.99,
  "caracteristicas_del_delito": ["Violencia o Intimidación"],
  "factores_agravantes": ["Uso de armas"],
  "factores_mitigantes": []
}


def test_generar_rdf_ok():
    response = requests.post(f"{BASE_URL}/generar_rdf/", json=atestado_ejemplo)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"

def test_ver_grafo_ok():
    rdf_path = FILES_DIR / "sample.rdf"
    assert rdf_path.exists(), f"El archivo {rdf_path} no existe"

    with open(rdf_path, "r", encoding="utf-8") as f:
        rdf_content = f.read()

    data = {"rdf": rdf_content, "formato": "xml"}
    response = requests.post(f"{BASE_URL}/ver_grafo/", data=data)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
