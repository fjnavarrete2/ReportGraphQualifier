import requests
import pytest
from pathlib import Path

BASE_URL = "https://veredictai.onrender.com/"
FILES_DIR = Path(__file__).parent / "files"

def test_procesar_pdf_ok():
    pdf_path = FILES_DIR / "sample.pdf"
    with open(pdf_path, "rb") as f:
        files = {"file": ("sample.pdf", f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/procesar/", files=files)
    
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data, dict)
    assert "descripcion" in json_data or "error" in json_data
