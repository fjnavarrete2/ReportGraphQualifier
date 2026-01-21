from typing import List
from entities import Atestado

# Función para generar una descripción textual de un atestado
def generar_descripcion(atestado: Atestado) -> str:
    """Devuelve un resumen en lenguaje natural del ``Atestado`` proporcionado."""
    descripcion = []

    descripcion.append(f"El atestado {atestado.atestado_id} documenta un presunto delito contra la propiedad.")

    # Bienes robados
    if atestado.bienes_robados:
        bienes = ", ".join([bien.nombre for bien in atestado.bienes_robados])
        descripcion.append(f"Los bienes sustraídos fueron: {bienes}.")
    else:
        descripcion.append("No se han especificado bienes sustraídos.")

    if atestado.valor_total_robado > 0:
        descripcion.append(f"El valor total estimado de lo robado asciende a {atestado.valor_total_robado:.2f} euros.")

    # Víctimas
    if atestado.victimas:
        victimas = ", ".join([v.id for v in atestado.victimas])
        descripcion.append(f"Las víctimas identificadas son: {victimas}.")
    else:
        descripcion.append("No se ha identificado ninguna víctima.")

    # Autores
    if atestado.autores:
        acusados = []
        for a in atestado.autores:
            partes = [a.id]
            if a.edad:
                partes.append(f"{a.edad} años")
            if a.organizacion_criminal:
                partes.append(f"miembro de la organización '{a.organizacion_criminal}'")
            if a.antecedentes > 0:
                partes.append(f"con {a.antecedentes} antecedentes")
            acusados.append(" ".join(partes))
        descripcion.append(f"Los autores del delito son: {', '.join(acusados)}.")
    else:
        descripcion.append("No se han identificado autores del delito.")

    # Cómplices
    if atestado.complices:
        nombres = ", ".join([c.id for c in atestado.complices])
        descripcion.append(f"Se ha mencionado la participación de cómplices: {nombres}.")

    # Testigos y empresas
    if atestado.testigos:
        descripcion.append(f"Se cuenta con testimonios de los siguientes testigos: {', '.join(atestado.testigos)}.")
    if atestado.empresas:
        descripcion.append(f"Empresas implicadas o afectadas: {', '.join(atestado.empresas)}.")

    # Características del delito
    if atestado.caracteristicas_del_delito:
        descripcion.append(f"Características del delito: {', '.join(atestado.caracteristicas_del_delito)}.")

    # Agravantes y atenuantes
    if atestado.factores_agravantes:
        descripcion.append(f"Factores agravantes: {', '.join(atestado.factores_agravantes)}.")
    if atestado.factores_mitigantes:
        descripcion.append(f"Factores atenuantes: {', '.join(atestado.factores_mitigantes)}.")

    return " ".join(descripcion)
