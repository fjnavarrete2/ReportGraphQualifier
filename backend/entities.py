from pydantic import BaseModel, Field
from decimal import Decimal, InvalidOperation
import re
from typing import List, Any, Optional, Union, Dict


class ContextoElementoClase(BaseModel):
    tipo_elemeto: str
    nombre_elemento: str
    domain: List[str]
    elemento_dominio: str
    range: List[str]
    prompt: str
    respuesta: Optional[Union[List[str], Dict[str, Any], str, int, float]] = None # respuesta: List[str]
    positivo: bool

    # def __eq__(self, other):
    #     if not isinstance(other, ContextoElementoClase):
    #         return NotImplemented
    #     return sorted(self.prompts) == sorted(other.prompts) and \
    #         sorted(self.respuestas) == sorted(other.respuestas) and \
    #         self.positivo == other.positivo

class PropiedadEntidad(BaseModel):
    nombre: str
    valor:  Union[str, float, int]
    rango: list[str]

    # def __eq__(self, other):
    #     if not isinstance(other, PropiedadEntidad):
    #         return NotImplemented
    #     return self.nombre == other.nombre and self.valor == other.valor

class EntidadClase(BaseModel):
    nombre: str
    repetido: bool = False
    dominios: List[str]
    dominios_negativos: List[str]
    propiedades: List[PropiedadEntidad]

    # def __eq__(self, other):
    #     if not isinstance(other, EntidadClase):
    #         return NotImplemented
    #     return sorted(self.dominios) == sorted(other.dominios) and \
    #         sorted(self.propiedades) == sorted(other.propiedades) and \
    #         self.nombre == other.nombre

class ObjetoClase(BaseModel):
    nombre: str
    repetido: bool = False
    dominios: List[str]
    entidad_dominio: str
    rangos: List[str]
    entidad_rango: str
    referencia: str
    clase_origen: Optional[str] = None

    # def __eq__(self, other):
    #     if not isinstance(other, ObjetoClase):
    #         return NotImplemented
    #     return sorted(self.dominios) == sorted(other.dominios) and \
    #         sorted(self.rangos) == sorted(other.rangos) and \
    #         self.nombre == other.nombre and \
    #         self.nombre_entidad_dominio == other.nombre_entidad_dominio and \
    #         self.entidad_rango == other.entidad_rango

class AnalisisClase(BaseModel):
    nombre: str 
    existe: bool = False
    excluido: bool = False
    contexto: List[ContextoElementoClase] #= Field(default_factory=list)
    objetos: List[ObjetoClase] #= Field(default_factory=list)
    entidades: List[EntidadClase] #= Field(default_factory=list)
    profundidad: int
    orden: int

    # def __eq__(self, other):
    #     if not isinstance(other, AnalisisClase):
    #         return NotImplemented
    #     return sorted(self.objetos) == sorted(other.objetos) and \
    #         sorted(self.entidades) == sorted(other.entidades) and \
    #         sorted(self.contexto) == sorted(other.contexto) and \
    #         self.nombre == other.nombre and \
    #         self.existe == other.existe and \
    #         self.excluido == other.excluido and \
    #         self.profundidad == other.profundidad and \
    #         self.orden == other.orden

class AnalisisAtestado(BaseModel):
    ley: str 
    llm_model : str
    contexto_positivo: List[ContextoElementoClase]
    contexto_negativo: List[ContextoElementoClase]
    objetos: List[ObjetoClase]
    entidades: List[EntidadClase]
    analisis: List[AnalisisClase]

class ListaAnalisis(BaseModel):
    nombre_grafo: str
    respuestas: List[AnalisisAtestado]


# resultado_extraido = {
#             "class": clase_nombre,
#             "existe": True,
#             "content": {
#                 "tipo_elemeto": "objeto",
#                 "nombre_elemento": elemento_nombre,
#                 "domain": dominio,
#                 "range": rango,
#                 "prompt": extraccion_prompt,
#                 "respuesta": resultados_extraccion
#             }
#         }



##########################################################3
class Bien(BaseModel):
    nombre: str
    caracteristicas_especiales: List[str] = []
    propietario: str = ""
    usuario: str = ""

class Acusado(BaseModel):
    id: str
    edad: int = 0
    organizacion_criminal: str = ""
    antecedentes: int = 0
    caracteristicas_acusado: List[str] = []

class Victima(BaseModel):
    id: str
    efectos_del_delito: List[str] = []

class Atestado(BaseModel):
    atestado_id: str
    victimas: List[Victima]
    autores: List[Acusado]
    complices: List[Acusado] = []
    testigos: List[str] = []
    empresas: List[str] = []
    bienes_robados: List[Bien]
    valor_total_robado: float = 0.0
    caracteristicas_del_delito: List[str] = []
    factores_agravantes: List[str] = []
    factores_mitigantes: List[str] = []

def initBienes(nombres: List[str]) -> List[Bien]:
    """Crea objetos ``Bien`` a partir de una lista de nombres."""
    return [Bien(nombre=nombre) for nombre in nombres]

def initAcusados(ids: List[str]) -> List[Acusado]:
    """Inicializa instancias de ``Acusado`` para los identificadores dados."""
    return [Acusado(id=id) for id in ids]

def initVictimas(ids: List[str]) -> List[Victima]:
    """Devuelve una lista de ``Victima`` basándose en sus identificadores."""
    return [Victima(id=id) for id in ids]

def initAtestado(atestado_id: str, bienes: List[Bien], victimas: List[Victima], autores: List[Acusado]) -> Atestado:
    """Construye un objeto ``Atestado`` con sus elementos principales."""
    return Atestado(
        atestado_id=atestado_id,
        bienes_robados=bienes,
        victimas=victimas,
        autores=autores
    )

import re

def filtrar_bienes(lista):
    """Elimina partes que representan exclusivamente dinero de descripciones de bienes."""
    # Patrón para encontrar menciones monetarias como '70 euros', 'monedas', 'billetes'
    patron_dinero = re.compile(r'(con\s*)?(?:[0-9]+ ?euros?|billetes?\w*|monedas?\w*)', re.IGNORECASE)
    
    resultado = []
    for item in lista:
        # Elimina las partes que coinciden con el patrón de dinero
        bien_filtrado = patron_dinero.sub('', item).strip(",;:.- ").strip()
        # Solo se guarda si queda algo significativo
        if bien_filtrado:
            resultado.append(bien_filtrado)
    return resultado
