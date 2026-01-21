import rdflib
import re
from rdflib import XSD, BNode, Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, OWL, RDFS
from entities import Atestado, Bien, Acusado, Victima, AnalisisAtestado
import os
from platformdirs import user_downloads_path
from dotenv import load_dotenv

load_dotenv()

# Definir el espacio de nombres para la ontología proporcionada
DELPATRIMONIO = Namespace(os.getenv("NS_URI"))
EX = Namespace(os.getenv("NS_URI"))

## ---- Función para iniciar un grafo RDF -----
def instanciar_grafo(data: any):
    """Crea un grafo RDF inicializado con los prefijos de la ontología."""
    g = rdflib.Graph()
    g.bind("delpatrimonio", DELPATRIMONIO)
    g.bind("owl", OWL)
    g.bind("xsd", XSD)

    print(f"\n📌iniciar_grafoG - bind")
    # Conjuntos para evitar declarar la misma propiedad varias veces
    props_declaradas = set()
    for elemento in data:
        # ---------------------------------------------------------
        # FASE 1: DECLARACIÓN DEL ESQUEMA (Propiedades y Clases)
        # ---------------------------------------------------------

        # 1.1 Declarar ObjectProperties (Relaciones del array "objetos")
        for objeto in elemento.get("objetos", []):
            pred_name = objeto.get("nombre")
            if pred_name not in props_declaradas:
                uri_prop = EX[clean_uri(pred_name)]
                # Aquí definimos que es una propiedad de objeto
                g.add((uri_prop, RDF.type, OWL.ObjectProperty))
                g.add((uri_prop, RDFS.label, Literal(pred_name))) # Opcional: etiqueta legible
                props_declaradas.add(pred_name)
                # print(f"📌iniciar_grafoG - object {uri_prop}")

        # 1.2 Declarar DatatypeProperties (Del array "entidades" -> "propiedades")
        for entidad in elemento.get("entidades", []):
            # Opcional: Declarar que la clase existe (ej: StolenGoods a owl:Class)
            for dominio in entidad.get("dominios", []):
                uri_class = EX[clean_uri(dominio)]
                g.add((uri_class, RDF.type, OWL.Class))
                # print(f"📌iniciar_grafoG - class {uri_class}")

            # Declarar las propiedades de datos
            for prop_dict in entidad.get("propiedades", []):
                for key in prop_dict.keys():
                    if key not in props_declaradas:
                        uri_prop = EX[clean_uri(key)]
                        # Aquí definimos que es una propiedad de datos
                        g.add((uri_prop, RDF.type, OWL.DatatypeProperty))
                        g.add((uri_prop, RDFS.label, Literal(key)))
                        props_declaradas.add(key)
                        # print(f"📌iniciar_grafoG - prop {uri_prop}")
    return g

## ---- Función para iniciar un grafo RDF -----
def poblar_grafo(data: any, g: Graph):
    
    for elemento in data:
        # ---------------------------------------------------------
        # FASE 2: POBLAR LOS DATOS (Instancias)
        # ---------------------------------------------------------
        
        # 2.1 Crear Entidades y asignar sus valores (Literales)
        for entidad in elemento.get("entidades", []):
            uri_entidad = EX[clean_uri(entidad.get("nombre"))]
            
            # 2.1.1 Tipos positivos (dominios)
            for dominio in entidad.get("dominios", []):
                g.add((uri_entidad, RDF.type, EX[clean_uri(dominio)]))

            # 2.1.2 Tipos negativos (dominios_negativos) -> CLASES ANÓNIMAS
            for dom_neg in entidad.get("dominios_negativos", []):
                # Generamos la estructura compleja
                bnode_clase = procesar_expresion_negativa(g, dom_neg, EX)
                print(f"📌poblar_grafo - dom_neg {bnode_clase}")
                if bnode_clase:
                    # Asignamos la entidad como instancia de esa estructura negativa
                    g.add((uri_entidad, RDF.type, bnode_clase))
            
            # 2.1.3 Propiedades de datos (Datatype Properties)
            for prop_dict in entidad.get("propiedades", []):
                # nom = entidad.get("nombre", "")
                # print(f"📌poblar_grafo - props {nom}: {prop_dict}")
                uri_prop = EX[clean_uri(prop_dict.get("nombre"))]
                # Rdflib infiere el XSD type, pero puedes forzarlo si quieres
                # g.add((uri_entidad, uri_prop, Literal(value)))
                g.add((uri_entidad, uri_prop, Literal(prop_dict.get("valor"), datatype = prop_dict.get("rango")[0])))

        # 2.2 Relacionar Entidades (Object Properties)
        for objeto in elemento.get("objetos", []):
            sujeto = EX[clean_uri(objeto.get("entidad_dominio"))]
            predicado = EX[clean_uri(objeto.get("nombre"))]
            rango = EX[clean_uri(objeto.get("entidad_rango"))]
            
            g.add((sujeto, predicado, rango))  
        
    return g

def procesar_expresion_negativa(g, expresion, namespace):
    """
    Parsea una expresión simple tipo 'not (propiedad some clase)'
    y devuelve el BNode (Clase Anónima) correspondiente.
    """
    EX = namespace
    
    # Patrón regex para: not (propiedad some clase)
    # Grupo 1: Propiedad
    # Grupo 2: Cuantificador (some/only)
    # Grupo 3: Clase Rango
    patron = r"not\s*\(\s*(\w+)\s+(some|only)\s+(\w+)\s*\)"
    match = re.search(patron, expresion, re.IGNORECASE)
    
    if match:
        prop_str, cuantificador, clase_str = match.groups()
        
        uri_propiedad = EX[clean_uri(prop_str)]
        uri_clase_rango = EX[clean_uri(clase_str)]
        
        # 1. Crear el Nodo Anónimo para la Restricción (lo que está dentro del paréntesis)
        restriccion_bnode = BNode()
        g.add((restriccion_bnode, RDF.type, OWL.Restriction))
        g.add((restriccion_bnode, OWL.onProperty, uri_propiedad))
        
        if cuantificador.lower() == 'some':
            g.add((restriccion_bnode, OWL.someValuesFrom, uri_clase_rango))
        elif cuantificador.lower() == 'only':
            g.add((restriccion_bnode, OWL.allValuesFrom, uri_clase_rango))
            
        # 2. Crear el Nodo Anónimo para la Negación (el "not")
        clase_anonima_negativa = BNode()
        g.add((clase_anonima_negativa, RDF.type, OWL.Class))
        g.add((clase_anonima_negativa, OWL.complementOf, restriccion_bnode))
        
        return clase_anonima_negativa
    
    else:
        print(f"Advertencia: No se pudo parsear la expresión compleja: {expresion}")
        return None

def clean_uri(text):
    """Limpia el texto para convertirlo en una URI válida."""
    if not text: return "unknown"
    # text = text.lower()
    text = re.sub(r'\s+', '_', text)
    #text = re.sub(r'[^a-zA-Z0-9_]', '', text)
    #text = regex.sub(r'[^\p{L}\p{N}_]', '', text)
    text = re.sub(r'[^a-zA-Z0-9_À-ÿ]', '', text)
    return text

def uriSegura(text: str) -> str:
    """Devuelve una representación segura para usar en URIs."""
    text = text.strip().replace("/", "_")
    return text.strip().replace(" ", "_")


## ---- Añadir el atestado completo -----
def generarGrafo(data: list[AnalisisAtestado], nombre_grafo):

    """Construye el RDF de un atestado de hurto o robo, creando restricciones
    cuando no hay características del delito."""

    print(f"\t📌generarGrafo - instanciar")
    g = instanciar_grafo(data)
    print(f"\t📌generarGrafo - poblar")
    g = poblar_grafo(data, g)
    print(f"\t📌generarGrafo - poblado")
    nombre_archivo = f"{uriSegura(nombre_grafo)}"  
    return g, nombre_archivo

def crear_rdf2(data: list[AnalisisAtestado], nombre_grafo: str):
    """Crea el archivo RDF correspondiente a un ``Atestado``."""
    print(f"\t📌crear_rdf2: {nombre_grafo}")
    grafo, nombre_archivo = generarGrafo(data, nombre_grafo)

    print(f"\t📌crear_rdf2: grafo generado")
    ruta_descargas = user_downloads_path()
    os.makedirs(ruta_descargas, exist_ok=True)

    print(f"\t📌crear_rdf2: rutas generadas")
    ruta_salida = os.path.join(ruta_descargas, f"{nombre_archivo}.rdf")

    print(f"\t📌crear_rdf2: ruta_salida: {ruta_salida}")
    grafo.serialize(destination=ruta_salida, format="xml")
    
    print(f"\n📌RDF creado guardado en {ruta_salida}")

    return f"{nombre_archivo}.rdf"



    
