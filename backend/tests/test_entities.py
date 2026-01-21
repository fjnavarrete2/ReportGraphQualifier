import pytest
from entities import (
    Bien, Acusado, Victima, Atestado,
    initBienes, initAcusados, initVictimas,
    initAtestado, filtrar_bienes
)

# ------------------ TESTS DE MODELOS ------------------

def test_bien_modelo():
    bien = Bien(nombre="Ordenador", caracteristicas_especiales=["MacBook"], propietario="Alice", usuario="Bob")
    assert bien.nombre == "Ordenador"
    assert bien.caracteristicas_especiales == ["MacBook"]
    assert bien.propietario == "Alice"
    assert bien.usuario == "Bob"

def test_acusado_modelo_con_datos():
    acusado = Acusado(id="123", edad=30, organizacion_criminal="Mafia", antecedentes=2)
    assert acusado.id == "123"
    assert acusado.edad == 30
    assert acusado.organizacion_criminal == "Mafia"
    assert acusado.antecedentes == 2

def test_victima_modelo_por_defecto():
    victima = Victima(id="v1")
    assert victima.id == "v1"
    assert victima.efectos_del_delito == []

# ------------------ TESTS DE FUNCIONES init* ------------------

def test_initBienes():
    nombres = ["Televisor", "Cámara"]
    bienes = initBienes(nombres)
    assert len(bienes) == 2
    assert all(isinstance(b, Bien) for b in bienes)
    assert bienes[0].nombre == "Televisor"

def test_initAcusados():
    acusados = initAcusados(["a1", "a2"])
    assert len(acusados) == 2
    assert all(isinstance(a, Acusado) for a in acusados)
    assert acusados[1].id == "a2"

def test_initVictimas():
    victimas = initVictimas(["v1", "v2"])
    assert len(victimas) == 2
    assert all(isinstance(v, Victima) for v in victimas)
    assert victimas[0].id == "v1"

def test_initAtestado_minimo():
    bienes = initBienes(["Libro"])
    autores = initAcusados(["acusado1"])
    victimas = initVictimas(["victima1"])
    atestado = initAtestado("A001", bienes, victimas, autores)

    assert isinstance(atestado, Atestado)
    assert atestado.atestado_id == "A001"
    assert len(atestado.bienes_robados) == 1
    assert atestado.bienes_robados[0].nombre == "Libro"
    assert atestado.victimas[0].id == "victima1"

# ------------------ TEST filtrar_bienes ------------------

def test_filtrar_bienes_descarta_dinero():
    entrada = ["ordenador", "billetes de euro", "monedas", "teléfono"]
    salida = filtrar_bienes(entrada)
    assert salida == ["ordenador", "teléfono"]

def test_filtrar_bienes_sin_dinero():
    entrada = ["libro", "mochila"]
    salida = filtrar_bienes(entrada)
    assert salida == ["libro", "mochila"]

def test_filtrar_bienes_mayusculas_minusculas():
    entrada = ["Billete falso", "EUROS falsos", "televisor"]
    salida = filtrar_bienes(entrada)
    assert salida == ["televisor"]
