import sys

print(sys.path)

import pytest
from atestadoToText import generar_descripcion
from entities import Atestado, Bien, Acusado, Victima

def test_descripcion_minima():
    atestado = Atestado(
        atestado_id="A001",
        bienes_robados=[],
        valor_total_robado=0.0,
        victimas=[],
        autores=[],
        complices=[],
        testigos=[],
        empresas=[],
        caracteristicas_del_delito=[],
        factores_agravantes=[],
        factores_mitigantes=[]
    )
    descripcion = generar_descripcion(atestado)
    assert "El atestado A001 documenta un presunto delito contra la propiedad." in descripcion
    assert "No se han especificado bienes sustraídos." in descripcion
    assert "No se ha identificado ninguna víctima." in descripcion
    assert "No se han identificado autores del delito." in descripcion

def test_descripcion_con_bienes_y_victimas():
    atestado = Atestado(
        atestado_id="A002",
        bienes_robados=[Bien(nombre="Teléfono", caracteristicas=[], propietario="V1", usuario="V1")],
        valor_total_robado=500.0,
        victimas=[Victima(id="V1", efectos_del_delito=[])],
        autores=[],
        complices=[],
        testigos=[],
        empresas=[],
        caracteristicas_del_delito=[],
        factores_agravantes=[],
        factores_mitigantes=[]
    )
    descripcion = generar_descripcion(atestado)
    assert "Los bienes sustraídos fueron: Teléfono." in descripcion
    assert "El valor total estimado de lo robado asciende a 500.00 euros." in descripcion
    assert "Las víctimas identificadas son: V1." in descripcion

def test_descripcion_completa():
    atestado = Atestado(
        atestado_id="A003",
        bienes_robados=[Bien(nombre="Ordenador", caracteristicas=[], propietario="V2", usuario="V2")],
        valor_total_robado=1000.0,
        victimas=[Victima(id="V2", efectos_del_delito=["estrés"])],
        autores=[
            Acusado(id="A1", edad=30, organizacion_criminal="Los Gatos", antecedentes=2, caracteristicas=[])
        ],
        complices=[Acusado(id="C1", edad=0, organizacion_criminal="", antecedentes=0, caracteristicas=[])],
        testigos=["T1", "T2"],
        empresas=["EmpresaX"],
        caracteristicas_del_delito=["Forzamiento de cerradura"],
        factores_agravantes=["Violencia"],
        factores_mitigantes=["Colaboración con la justicia"]
    )
    descripcion = generar_descripcion(atestado)
    assert "Ordenador" in descripcion
    assert "1000.00 euros" in descripcion
    assert "V2" in descripcion
    assert "A1 30 años miembro de la organización 'Los Gatos' con 2 antecedentes" in descripcion
    assert "C1" in descripcion
    assert "T1, T2" in descripcion
    assert "EmpresaX" in descripcion
    assert "Forzamiento de cerradura" in descripcion
    assert "Factores agravantes: Violencia." in descripcion
    assert "Factores atenuantes: Colaboración con la justicia." in descripcion
