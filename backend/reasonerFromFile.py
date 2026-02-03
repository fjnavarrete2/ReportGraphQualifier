from decimal import Decimal
from urllib.parse import urlparse
from rdflib import RDF, BNode, Graph, Literal
from owlready2 import get_ontology, sync_reasoner_pellet, ObjectPropertyClass, FunctionalProperty, World, sync_reasoner_hermit
from rdflib.namespace import RDF, OWL
from owlready2 import ThingClass, ObjectPropertyClass, FunctionalProperty, OwlReadyInconsistentOntologyError, Not
from owlready2 import *
from entities import AnalisisAtestado
# Renombramos el Namespace de rdflib para evitar el error de base_iri
from rdflib import Graph, URIRef, RDF, Literal, Namespace as RDFNamespace, RDFS





# from articles import ARTICULOS_EXPLICACION

NS_URI = os.getenv("NS_URI")
ONTOLOGY = os.getenv("ONTOLOGY")

def extract_local_name(iri):
    """Return the local fragment of an IRI."""
    if '#' in iri:
        return iri.split('#')[-1]
    else:
        path = urlparse(iri).path
        return path.split('/')[-1]


def import_rdf_individuals(rdf_graph, onto):
    """Importa individuos y relaciones de un grafo RDF a una ontología."""

    existing_individuals = {ind.name for ind in onto.individuals()}
    individual_map = {}  
    count_created = 0
    count_relations = 0

    # 1. CREAR INDIVIDUOS A PARTIR DE rdf:type
    for s, p, o in rdf_graph.triples((None, RDF.type, None)):
        subject_iri = str(s)
        class_iri = str(o)

        if any(ns in class_iri for ns in [
            "owl#", "rdf#", "rdfs#", "xsd#", "shacl#"
        ]):
            continue

        ind_name = extract_local_name(subject_iri)
        class_name = extract_local_name(class_iri)

        print(f"import_rdf_individuals ind_name: {ind_name} -- class_name: { class_name}")

        if ind_name in existing_individuals:
            continue

        cls = onto.search_one(iri=class_iri) or onto.search_one(iri="*#" + class_name)
        if cls is None:
            continue

        with onto:
            ind = cls(ind_name)
            individual_map[subject_iri] = ind
            existing_individuals.add(ind_name)
            count_created += 1
            print(f"  [+] Creado individuo: {ind_name} de tipo {cls.name}")

    print(f"✅ Total de individuos creados: {count_created}")

    for s, p, o in rdf_graph.triples((None, None, None)):
        if p == RDF.type:
            continue

        subject_iri = str(s)
        predicate_iri = str(p)
        object_iri = str(o)

        subj_ind = individual_map.get(subject_iri)
        if subj_ind is None:
            continue

        pred_name = extract_local_name(predicate_iri)
        prop = onto.search_one(iri=predicate_iri) or onto.search_one(iri="*#" + pred_name)

        if prop is None:
            continue

        if isinstance(o, Literal):

            value = o.toPython()

            if isinstance(value,Decimal):
                value=float(value)
                
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                value = float(value)
            elif hasattr(value, "value"):
                value = value.value

            current_value = getattr(subj_ind, prop.name)
                
            if isinstance(current_value, list):
                current_value.append(value)
            else:
                setattr(subj_ind, prop.name, value)

        else:

            obj_ind = individual_map.get(object_iri)
            if obj_ind is None:
                continue 

            if isinstance(prop, ObjectPropertyClass):
                if isinstance(prop, FunctionalProperty):
                    setattr(subj_ind, prop.name, obj_ind)
                else:
                    current = getattr(subj_ind, prop.name, [])
                    if isinstance(current, list):
                        current.append(obj_ind)
                    else:
                        setattr(subj_ind, prop.name, obj_ind)

                count_relations += 1
                print(f"  [+] Relación: {subj_ind.name} --{prop.name}--> {obj_ind.name}")

    print(f"Pero cuantos días de vigencia le damos a las alegaciones Total de relaciones/properties importadas: {count_relations}")



def aplicar_not_sobre_hasOffenceCharacteristic_si_es_nothing(rdf_graph, onto):
    """Añade inferencias negativas cuando la propiedad está restringida a Nothing."""

    for subj in rdf_graph.subjects(RDF.type, None):
        # print(f"❕ aplicar_not subj: {subj}")
        # Para cada tipo que sea un BNode (clase anónima)
        for _, _, class_bnode in rdf_graph.triples((subj, RDF.type, None)):
            if isinstance(class_bnode, BNode):
                print(f"❕ aplicar_not class_bnode: {class_bnode}")
                # Buscar intersectionOf
                intersection = rdf_graph.value(class_bnode, OWL.intersectionOf)
                if intersection:
                    print(f" ❗ aplicar_not intersection: {intersection}")
                    # Recorrer la lista RDF (puede usar rdflib.collection.Collection)
                    from rdflib.collection import Collection
                    items = list(Collection(rdf_graph, intersection))
                    for item in items:
                        # Buscar Restriction con owl:allValuesFrom owl:Nothing
                        if (item, RDF.type, OWL.Restriction) in rdf_graph:
                            prop = rdf_graph.value(item, OWL.onProperty)
                            all_val = rdf_graph.value(item, OWL.allValuesFrom)
                            if all_val == OWL.Nothing:
                                # Encontrado, buscar individuo y propiedad en la ontología
                                subject_iri = str(subj)
                                prop_iri = str(prop)
                                subj_ind = next((ind for ind in onto.individuals() if ind.iri == subject_iri), None)
                                owl_prop = onto.search_one(iri=prop_iri)
                                if subj_ind and owl_prop:
                                    from owlready2 import Not
                                    expr = Not(owl_prop.some(onto.RobberyCharacteristic))
                                    if expr not in subj_ind.is_a:
                                        subj_ind.is_a.append(expr)
                                        print(f"  🔁 Añadida inferencia negativa: {subj_ind.name} → NOT {owl_prop.name}.some(RobberyCharacteristic)")

    print("✅ Aplicación de NOT finalizada.\n")


def reasoner_v1(ruta_grafo):
    """Carga un RDF, importa sus individuos y ejecuta el razonador Pellet."""
    print(f"📄 Cargando archivo RDF desde: {ruta_grafo}")

    onto = get_ontology(ONTOLOGY).load(reload=True)

    grafo = Graph()
    grafo.parse(ruta_grafo, format="xml")

    print("--- Importando individuos y relaciones desde RDF ---")
    import_rdf_individuals(grafo, onto)
    aplicar_not_sobre_hasOffenceCharacteristic_si_es_nothing(grafo, onto)

    print("--- Ejecutando razonador Pellet ---")
    with onto:
        sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)

    # Buscar clase base Report
    report_class = onto.search_one(iri="*#Report")
    if not report_class:
        return []

    report_classes = set(report_class.subclasses()) | {report_class}

    clases_inferidas = set()

    for ind in onto.individuals():
        all_types = set(ind.INDIRECT_is_a)
        if report_classes & all_types:
            declared_classes = set(ind.is_a)
            for cls in declared_classes:
                if hasattr(cls, "name"):
                    clases_inferidas.add(cls.name)
                    print(f"  [+] Inferida clase: {cls.name} para individuo {ind.name}")

    return sorted(clases_inferidas)

def construir_articulos_inferidos_v1(lista_clases: list[str]) -> list[str]:
    """Convierte las clases inferidas en referencias legislativas."""
    res = [ARTICULOS_EXPLICACION[c] for c in lista_clases if c in ARTICULOS_EXPLICACION]
    print(res)
    return res

def reasoner(tmp_path):
    world = World()
    try:
        # Cargar ontología base e individuos
        base_onto = world.get_ontology(ONTOLOGY).load()
        user_data = world.get_ontology(f"file://{tmp_path}").load()
        
        # Ejecutar razonador
        with base_onto:
            sync_reasoner_pellet(world, infer_property_values=True, infer_data_property_values=True)
        
        # Guardar el RDF generado con las inferencias en un nuevo archivo temporal
        output_path = tmp_path.replace(".rdf", "_inferido.rdf")
        world.save(file=output_path, format="rdfxml")
        
        return world, output_path
    except Exception as e:
        print(f"Error en el razonamiento: {e}")
        return None, None

def construir_articulos_inferidos(world):
    if world is None: return []
    articulos_encontrados = []
    for i in world.individuals():
        clases = [c.name for c in i.is_a if isinstance(c, ThingClass) and c.name != "Thing"]
        if clases:
            articulos_encontrados.append({"id": i.name, "clases": clases})
    return articulos_encontrados

def clean_uri(text):
    """Limpia el texto para convertirlo en una URI válida."""
    if not text: return "unknown"
    # text = text.lower()
    text = re.sub(r'\s+', '_', text)
    #text = re.sub(r'[^a-zA-Z0-9_]', '', text)
    #text = regex.sub(r'[^\p{L}\p{N}_]', '', text)
    text = re.sub(r'[^a-zA-Z0-9_À-ÿ]', '', text)
    return text


def reasoner_ttls(tmp_path,  data: list[AnalisisAtestado]):
    world = World()
    # Aumentar memoria para procesos de materialización pesados
    owlready2.reasoning.JAVA_MAX_MEM = "4000M" 
    
    try:
        NS = RDFNamespace(NS_URI)
        base_path = os.path.abspath(ONTOLOGY)
        base_onto = world.get_ontology(f"file://{base_path}").load()

        # 1. Carga de datos de usuario
        user_onto = world.get_ontology("http://temp.org/user_data")
        with user_onto:
            # Cargamos el RDF directamente al grafo del world
            world.as_rdflib_graph().parse(tmp_path, format="xml")
        
        user_onto.imported_ontologies.append(base_onto)

        # --- ESTADO 1.1: World con individuos ANTES de razonar ---
        pre_reasoning_path = tmp_path.replace(".rdf", "_PRE_RAZONADO.owl")
        pre_reasoning_path = pre_reasoning_path.replace("/tmp/", "/app/import/")
        print(f"[1] Guardado pre-razonamiento: {pre_reasoning_path}")
        world.save(file=pre_reasoning_path, format="rdfxml")
        

        # 2. Razonamiento (Pellet es necesario para SWRL e INDIRECT_is_a complejos)
        with base_onto:
            #sync_reasoner_pellet(world, infer_property_values=True, infer_data_property_values=True)
            sync_reasoner_hermit(world, infer_property_values=True)

        # --- BLOQUE DE MATERIALIZACIÓN: FORZAR INDIRECT_IS_A ---
        # --- BLOQUE DE MATERIALIZACIÓN DEFINITIVO ---
        # --- BLOQUE DE MATERIALIZACIÓN ROBUSTO ---
        print("🛠️ Iniciando materialización de superclases inferidas...")
        
        # 1. Obtenemos todos los sujetos del grafo de rdflib que pertenecen a tu namespace
        # Esto es más seguro que world.individuals()
        graph = world.as_rdflib_graph()
        sujetos_iris = {str(s) for s, p, o in graph if NS_URI in str(s) and isinstance(s, URIRef)}
        
        for iri_ind in sujetos_iris:
            # 2. Intentamos obtener el objeto
            instancia = world[iri_ind]
            
            # 3. Verificamos que sea un individuo y no una clase o propiedad
            # En Owlready2, los individuos son instancias de 'Thing'
            if instancia and hasattr(instancia, "is_a"):
                try:
                    # 4. Obtenemos lo que el razonador calculó
                    inferidos = instancia.INDIRECT_is_a
                    
                    for cls in inferidos:
                        # REGLA DE FILTRADO:
                        # - Debe ser una clase (ThingClass)
                        # - Debe tener nombre (no ser una restricción anónima o intersección)
                        # - No debe ser 'Thing' (para no ensuciar el grafo)
                        if isinstance(cls, ThingClass) and hasattr(cls, "name") and cls.name != "Thing":
                            if cls not in instancia.is_a:
                                # Usamos una asignación limpia en lugar de append directo si da problemas
                                instancia.is_a = instancia.is_a + [cls]
                                
                    print(f"\t✅ {instancia.name} actualizado con sus superclases inferidas.")
                except Exception as e:
                    # Si falla un individuo, continuamos con el siguiente
                    # print(f"\t⚠️ Error en individuo {iri_ind}: {e}")
                    pass
            else:
                # Si no tiene is_a, es probable que el IRI sea de una Clase o Propiedad, no de un Individuo
                continue

        # 3. EXTRACCIÓN QUIRÚRGICA (Filtro A-Box)
        # output_graph = Graph()
        # output_graph.bind("ns0", RDFNamespace(NS_URI))
        
        # Ahora el full_graph contiene las inferencias "materializadas" en el is_a
        full_graph = world.as_rdflib_graph()

        # Listas negras (se mantienen igual que en tu código)
        predicados_prohibidos = {RDFS.comment, RDFS.seeAlso, RDFS.label, RDFS.domain, RDFS.range, 
                                 RDFS.subPropertyOf, RDFS.subClassOf, OWL.disjointWith, 
                                 OWL.propertyDisjointWith, OWL.inverseOf, OWL.equivalentClass}
        
        tipos_prohibidos = {OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.FunctionalProperty,
                            OWL.SymmetricProperty, OWL.AsymmetricProperty, OWL.TransitiveProperty,
                            OWL.Restriction, URIRef("http://www.w3.org/2003/11/swrl#Variable")}

        # Acumuladores
        triples = []              # Triplas A-Box normales
        triple_annotations = {}   # RDF-star: comentarios sobre relaciones
        encontrados = 0
        for s, p, o in full_graph:
            s_str = str(s)
            if NS_URI in s_str:
                if p in predicados_prohibidos: continue
                if p == RDF.type and o in tipos_prohibidos: continue
                if isinstance(s, BNode) or isinstance(o, BNode): continue

                triples.append((str(s), str(p), o))
                
                referencias = []
                suj = s.replace(NS_URI, "")
                pred = p.replace(NS_URI, "")
                obje = o.replace(NS_URI, "")
                referencias = []
                for elemento in data:       
                    referencias.extend([obj.get("referencia") for obj in elemento.get("objetos", []) if clean_uri(obj.get("nombre")) == pred 
                                        and clean_uri(obj.get("entidad_dominio")) == suj and clean_uri(obj.get("entidad_rango")) == obje])
                    
                if referencias:
                    print(f"\t📌referencias {len(referencias)}: {referencias[0]}  de {suj} - {pred} - {obje}")
                    key = (str(s), str(p), o)
                    triple_annotations.setdefault(key, [])

                    for ref in referencias:
                        triple_annotations[key].append((str(NS.referencia), ref))

                encontrados += 1

        # # 4. Guardado de los dos archivos finales
        # # El .rdf incluirá el world con las inferencias materializadas en RDF/XML
        # output_path_rdf = tmp_path.replace(".rdf", "_inferido.rdf")
        # world.save(file=output_path_rdf, format="rdfxml")

        # El .ttls incluirá solo los individuos limpios
        output_path_ttl = tmp_path.replace(".rdf", "_solo_datos.ttls")
        write_turtle_star(output_path_ttl, triples, triple_annotations)
        
        print(f"✅ Proceso completado. Triplas en A-Box: {encontrados}")
        return world, output_path_ttl

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, None
    

from rdflib import Literal
from rdflib.namespace import XSD

PREFIXES = f"""@prefix ns0: <{NS_URI}> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""

def write_turtle_star(path, triples, triple_annotations):
    """
    triples:
        list of tuples -> (s, p, o)
    triple_annotations:
        dict keyed by (s, p, o) -> list of (annotation_predicate, annotation_value)
    """

    with open(path, "w", encoding="utf-8") as f:
        f.write(PREFIXES + "\n")

        # 1. Triplas normales (asserted triples)
        for s, p, o in triples:
            s_t = f"<{s}>"
            p_t = f"<{p}>"

            if isinstance(o, Literal):
                o_t = o.n3()
            else:
                o_t = f"<{o}>"

            f.write(f"{s_t} {p_t} {o_t} .\n")

        f.write("\n")

        # 2. Anotaciones RDF-star
        for (s, p, o), annos in triple_annotations.items():
            s_t = f"<{s}>"
            p_t = f"<{p}>"

            if isinstance(o, Literal):
                o_t = o.n3()
            else:
                o_t = f"<{o}>"

            quoted = f"<< {s_t} {p_t} {o_t} >>"

            for apred, aval in annos:
                aval_t = Literal(aval).n3()
                f.write(f"{quoted} <{apred}> {aval_t} .\n")

def reasoner_ttl(tmp_path):
    world = World()
    # Aumentar memoria para procesos de materialización pesados
    owlready2.reasoning.JAVA_MAX_MEM = "4000M" 
    
    try:
        base_path = os.path.abspath(ONTOLOGY)
        base_onto = world.get_ontology(f"file://{base_path}").load()

        # 1. Carga de datos de usuario
        user_onto = world.get_ontology("http://temp.org/user_data")
        with user_onto:
            # Cargamos el RDF directamente al grafo del world
            world.as_rdflib_graph().parse(tmp_path, format="xml")
        
        user_onto.imported_ontologies.append(base_onto)

        # --- ESTADO 1.1: World con individuos ANTES de razonar ---
        pre_reasoning_path = tmp_path.replace(".rdf", "_PRE_RAZONADO.owl")
        world.save(file=pre_reasoning_path, format="rdfxml")
        print(f"[1] Guardado pre-razonamiento: {pre_reasoning_path}")

        # 2. Razonamiento (Pellet es necesario para SWRL e INDIRECT_is_a complejos)
        with base_onto:
            #sync_reasoner_pellet(world, infer_property_values=True, infer_data_property_values=True)
            sync_reasoner_hermit(world, infer_property_values=True)

        # --- BLOQUE DE MATERIALIZACIÓN: FORZAR INDIRECT_IS_A ---
        # --- BLOQUE DE MATERIALIZACIÓN DEFINITIVO ---
        # --- BLOQUE DE MATERIALIZACIÓN ROBUSTO ---
        print("🛠️ Iniciando materialización de superclases inferidas...")
        
        # 1. Obtenemos todos los sujetos del grafo de rdflib que pertenecen a tu namespace
        # Esto es más seguro que world.individuals()
        graph = world.as_rdflib_graph()
        sujetos_iris = {str(s) for s, p, o in graph if NS_URI in str(s) and isinstance(s, URIRef)}
        
        for iri_ind in sujetos_iris:
            # 2. Intentamos obtener el objeto
            instancia = world[iri_ind]
            
            # 3. Verificamos que sea un individuo y no una clase o propiedad
            # En Owlready2, los individuos son instancias de 'Thing'
            if instancia and hasattr(instancia, "is_a"):
                try:
                    # 4. Obtenemos lo que el razonador calculó
                    inferidos = instancia.INDIRECT_is_a
                    
                    for cls in inferidos:
                        # REGLA DE FILTRADO:
                        # - Debe ser una clase (ThingClass)
                        # - Debe tener nombre (no ser una restricción anónima o intersección)
                        # - No debe ser 'Thing' (para no ensuciar el grafo)
                        if isinstance(cls, ThingClass) and hasattr(cls, "name") and cls.name != "Thing":
                            if cls not in instancia.is_a:
                                # Usamos una asignación limpia en lugar de append directo si da problemas
                                instancia.is_a = instancia.is_a + [cls]
                                
                    print(f"\t✅ {instancia.name} actualizado con sus superclases inferidas.")
                except Exception as e:
                    # Si falla un individuo, continuamos con el siguiente
                    # print(f"\t⚠️ Error en individuo {iri_ind}: {e}")
                    pass
            else:
                # Si no tiene is_a, es probable que el IRI sea de una Clase o Propiedad, no de un Individuo
                continue

        # 3. EXTRACCIÓN QUIRÚRGICA (Filtro A-Box)
        output_graph = Graph()
        output_graph.bind("ns0", RDFNamespace(NS_URI))
        
        # Ahora el full_graph contiene las inferencias "materializadas" en el is_a
        full_graph = world.as_rdflib_graph()

        # Listas negras (se mantienen igual que en tu código)
        predicados_prohibidos = {RDFS.comment, RDFS.seeAlso, RDFS.label, RDFS.domain, RDFS.range, 
                                 RDFS.subPropertyOf, RDFS.subClassOf, OWL.disjointWith, 
                                 OWL.propertyDisjointWith, OWL.inverseOf, OWL.equivalentClass}
        
        tipos_prohibidos = {OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.FunctionalProperty,
                            OWL.SymmetricProperty, OWL.AsymmetricProperty, OWL.TransitiveProperty,
                            OWL.Restriction, URIRef("http://www.w3.org/2003/11/swrl#Variable")}

        encontrados = 0
        for s, p, o in full_graph:
            s_str = str(s)
            if NS_URI in s_str:
                if p in predicados_prohibidos: continue
                if p == RDF.type and o in tipos_prohibidos: continue
                if isinstance(s, BNode) or isinstance(o, BNode): continue

                output_graph.add((s, p, o))
                encontrados += 1

        # 4. Guardado de los dos archivos finales
        # El .rdf incluirá el world con las inferencias materializadas en RDF/XML
        output_path_rdf = tmp_path.replace(".rdf", "_inferido.rdf")
        world.save(file=output_path_rdf, format="rdfxml")

        # El .ttl incluirá solo los individuos limpios
        output_path_ttl = tmp_path.replace(".rdf", "_solo_datos.ttl")
        output_graph.serialize(destination=output_path_ttl, format="turtle")
        
        print(f"✅ Proceso completado. Triplas en A-Box: {encontrados}")
        return world, output_path_ttl

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, None
