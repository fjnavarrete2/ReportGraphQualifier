import os
import tempfile
import pytest
from docx import Document
import fitz

from documents import leer_pdf, leer_docx

# ------------------------- FUNCIONES AUXILIARES -------------------------

def crear_docx_temporal(texto: str = "") -> str:
    """Crea un archivo DOCX temporal con el texto indicado."""
    ruta = tempfile.mktemp(suffix=".docx")
    doc = Document()
    if texto:
        doc.add_paragraph(texto)
    doc.save(ruta)
    return ruta

def crear_pdf_temporal(texto: str = "") -> str:
    """Crea un archivo PDF temporal con el texto indicado."""
    ruta = tempfile.mktemp(suffix=".pdf")
    doc = fitz.open()
    pagina = doc.new_page()
    if texto:
        pagina.insert_text((72, 72), texto)  # Posición estándar
    doc.save(ruta)
    doc.close()
    return ruta

# ------------------------- TESTS DOCX -------------------------

def test_leer_docx_valido():
    texto = "Esto es un documento DOCX de prueba."
    ruta = crear_docx_temporal(texto)
    resultado = leer_docx(ruta)
    assert texto in resultado
    os.remove(ruta)

def test_leer_docx_vacio():
    ruta = crear_docx_temporal("")
    resultado = leer_docx(ruta)
    assert resultado == "El DOCX no contiene texto."
    os.remove(ruta)

def test_leer_docx_no_existente():
    resultado = leer_docx("archivo_inexistente.docx")
    assert resultado == "Archivo no encontrado."

def test_leer_docx_con_error():
    resultado = leer_docx("/dev/null")
    assert resultado.startswith("Error al leer el archivo DOCX:")

# ------------------------- TESTS PDF --------------------------

def test_leer_pdf_valido():
    texto = "Texto de prueba en PDF."
    ruta = crear_pdf_temporal(texto)
    resultado = leer_pdf(ruta)
    assert texto in resultado
    os.remove(ruta)

def test_leer_pdf_vacio():
    ruta = crear_pdf_temporal("")
    resultado = leer_pdf(ruta)
    assert resultado == "El PDF no contiene texto."
    os.remove(ruta)

def test_leer_pdf_no_existente():
    resultado = leer_pdf("archivo_inexistente.pdf")
    assert resultado == "Archivo no encontrado."

def test_leer_pdf_con_error():
    resultado = leer_pdf("/dev/null")
    assert resultado.startswith("Error al leer el archivo PDF:")

