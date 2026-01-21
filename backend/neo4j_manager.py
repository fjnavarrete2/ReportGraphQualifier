import os
from neo4j import GraphDatabase
from fastapi import HTTPException

# Configuración de conexión (Ajustar según entorno)
NEO4J_URI=os.getenv("NEO4J_URI")
NEO4J_USER=os.getenv("NEO4J_USER")
NEO4J_PASSWORD=os.getenv("NEO4J_PASSWORD")

# Namespace de tu ontología
NS_URI = os.getenv("NS_URI")
PREFIX = os.getenv("PREFIX")

ROOT_CLASS = os.getenv("ROOT_CLASS")
label_root_class = f"ns0__{ROOT_CLASS}"

class Neo4jManager:
    _initialized = False

    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            encrypted=False  # Añade esto para evitar errores de certificados en local
        )

    def close(self):
        self.driver.close()

   
    def import_turtle(self, turtle_file_path, llm_type, root_name: str):
        """Importa el fichero .ttl usando el plugin n10s."""
        # FORZAMOS el reseteo antes de importar
        self.ensure_initialized(root_name, force_reset=True)

        print(f"✔ Inicializado import_turtle... file_uri:{turtle_file_path} ")
        if not os.path.exists(turtle_file_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Fichero no encontrado en la ruta: {turtle_file_path}"
            )
        
        file_uri = turtle_file_path
        # Si la ruta empieza por /home, es de WSL. 
        # La traducimos para que el Neo4j de Windows la encuentre
        if turtle_file_path.startswith("/app/"): #Viene del docker
            # Reemplaza 'Ubuntu' por el nombre exacto de tu distro si no es esa
            win_path = turtle_file_path.replace("/app/import", "/import")
            file_uri = f"file://{win_path.replace(os.sep, '/')}"
        elif turtle_file_path.startswith("/home/"):
            # Reemplaza 'Ubuntu' por el nombre exacto de tu distro si no es esa
            win_path = turtle_file_path.replace("/home/", "//wsl.localhost/Ubuntu/home/")
            file_uri = f"file:///{win_path.replace(os.sep, '/')}"
        elif turtle_file_path.startswith("/mnt/"):
            # Reemplaza 'Ubuntu' por el nombre exacto de tu distro si no es esa
            win_path = turtle_file_path.replace("/mnt/", "//wsl.localhost/Ubuntu/mnt/")
            file_uri = f"file:///{win_path.replace(os.sep, '/')}"
        elif turtle_file_path.startswith("/tmp/"):
            # Reemplaza 'Ubuntu' por el nombre exacto de tu distro si no es esa
            win_path = turtle_file_path.replace("/tmp/", "//wsl.localhost/Ubuntu/tmp/")
            file_uri = f"file:///{win_path.replace(os.sep, '/')}"
        else:
            abs_path = os.path.abspath(turtle_file_path)
            file_uri = f"file://{abs_path.replace(os.sep, '/')}"

        print(f"✔ Arrancando import_turtle... file_uri:{file_uri} ")

        with self.driver.session() as session:
            if llm_type == "ttl":
                query = f"""
                CALL n10s.rdf.import.fetch("{file_uri}", "Turtle")
                YIELD terminationStatus, triplesLoaded, triplesParsed
                RETURN terminationStatus, triplesLoaded, triplesParsed
                """
            else:
                query = f"""
                CALL n10s.rdf.import.fetch("{file_uri}", "Turtle-star")
                YIELD terminationStatus, triplesLoaded, triplesParsed
                RETURN terminationStatus, triplesLoaded, triplesParsed
                """

            # result = session.run(query, path=file_uri)
            print(f"{query}")
            result = session.run(query)
            return result.single()

    def ensure_initialized(self, root_name: str, force_reset=False):
        """
        Controla el estado de Neosemantics.
        - Si force_reset=True: Borra todo (datos y config) y re-inicializa.
        - Si force_reset=False: Solo inicializa si nunca se ha hecho en esta sesión.
        """
        
        # Escenario: ¿Debemos ejecutar la limpieza? 
        # Entramos si se pide fuerza o si es la primera vez (self._initialized es False)
        if force_reset or not self._initialized:
            print(f"🔄 {'[RE-INICIALIZANDO]' if force_reset else '[PRIMERA INICIALIZACIÓN]'} Preparando Neo4j...")
            
            with self.driver.session() as session:
                # 1. BORRADO DE DATOS CON COMMIT
                # Usamos execute_write para asegurar que Neo4j confirme la eliminación de nodos
                def clear_data(tx):
                    # print("  🗑️ 1/5: Borrando datos existentes (DETACH DELETE)...")
                    # tx.run("MATCH (n) DETACH DELETE n")

                    print(f"  🗑️ 1/5: Borrando datos existentes de grafos denominados: {root_name} (DETACH DELETE)...")
                    query = f"""
                    MATCH (rootA:{label_root_class} {{name: '{root_name}'}})
                    CALL apoc.path.subgraphNodes(rootA, {{}})
                    YIELD node
                    DETACH DELETE node
                    return count(node)
                    """
                    res = tx.run(query). single()
                    print(f"  \t🗑️ 1/5: Borrados: {res} nodos...")
                
                session.execute_write(clear_data)
                
                # 2. SABER DE LA EXISTENCIA DE N10S 
                # Este paso es vital para que el siguiente 'init' no de error de "non-empty"
                try:
                    result = session.run("MATCH (gc:_GraphConfig) return count(gc) as gc_number").single()
                    gc_number = result["gc_number"]
                    print(f"  🧹 2/5: Configuración Neosemantics MATCH (gc:_GraphConfig) return count(gc)... {gc_number}")
                except Exception:
                    pass

                if gc_number != 1:
                    # 3. CREAR RESTRICCIÓN
                    print("  ✅ 3/5: Asegurando restricción de URI única...")
                    session.run("CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS FOR (r:Resource) REQUIRE r.uri IS UNIQUE")

                    # 4. INICIALIZACIÓN DE N10S (GraphConfig)
                    # Ahora que el grafo está vacío y no hay config, esto funcionará siempre.
                    print("  ⚙️ 4/5: Ejecutando n10s.graphconfig.init...")
                    session.run("CALL n10s.graphconfig.init({n10s_graph_import_rdfstar_enabled: true, handleVocabUris: 'SHORTEN' })") #
                    
                    # 5. REGISTRAR NAMESPACE
                    print(f"  🔗 5/5: Registrando prefijo '{PREFIX}' {NS_URI}...")
                    session.run("CALL n10s.nsprefixes.add($prefix, $uri)", prefix=PREFIX, uri=NS_URI)
                    print("✅ Neo4j está limpio y configurado.")
                else: 
                    print("  ✅ 3/5: Asegurando restricción de URI única... ya realizado.")
                    print("  ⚙️ 4/5: Ejecutando n10s.graphconfig.init... ya realizado.")
                    print(f"  🔗 5/5: Registrando prefijo '{PREFIX}' {NS_URI}... ya realizado.")
                    print(f"✅ Neo4j ha actualizado por los grafos denominados '{root_name}'.")
                
            self._initialized = True
        else:
            print("ℹ️ Neosemantics ya estaba inicializado en esta sesión. Saltando configuración.")


    def curar_datos(self, root_name: str):
        """
        Ejecuta las consultas de curación para simplificar nombres 
        y eliminar las URIs largas de los nodos.
        """
        self.ensure_initialized(root_name)
        
        # Consulta 1: Extraer el nombre corto de la URI
        query1 = f"""
        MATCH (n)
        WHERE n.uri IS NOT NULL
        SET n.name = replace(n.uri, "{NS_URI}", "")
        RETURN count(n) as procesados
        """
        
        # Consulta 2: Eliminar la propiedad uri
        query2 = """
        MATCH (n) 
        WHERE n.uri IS NOT NULL 
        SET n.uri = null 
        RETURN count(n) as limpiados
        """

        # Consulta 23: Eliminar la propiedad uri
        query3 = """
        MATCH (n: ns0__Report)-[r:rdf__type]->(p) DELETE r 
        RETURN count(r) as r_limpiados
        """

        # Consulta 4: Eliminar la propiedad uri
        query4 = """
        MATCH ()-[r:ns0__referencedIn | ns0__appliedIn | ns0__isThiefOf | ns0__isOwnerOf]-() DELETE r
        RETURN count(r) as r_limpiados
        """
        
        with self.driver.session() as session:
            res1 = session.run(query1).single()
            res2 = session.run(query2).single()
            res3 = session.run(query3).single()
            res4 = session.run(query4).single()
            return {
                "nombres_simplificados": res1["procesados"],
                "uris_eliminadas": res2["limpiados"],
                "types_eliminadas": res3["r_limpiados"],
                "types_eliminadas2": res4["r_limpiados"]
            }
    
    def generate_root(self, root_name: str, articles_list: list):
        """
        Clona el nodo raíz para cada artículo de la lista proporcionada.
        """
        self.ensure_initialized(root_name)

        print(f"✔ Inicializado generate_root... name:{root_name}")
        print(f"✔ Inicializado generate_root... articles_list:{articles_list}")

        query = f"""
        MATCH (rootA:{label_root_class} {{name: '{root_name}'}})
        WHERE rootA.article IS NULL
        AND NOT EXISTS {{
            MATCH (rootB:{label_root_class})
            WHERE rootB.article IS NOT NULL AND rootA.name = rootB.name
        }}
        WITH DISTINCT rootA.name AS name_to_clone
        UNWIND $laws_list AS law_name
        MATCH (original:{label_root_class})
        WHERE original.name = name_to_clone AND original.article IS NULL
        CALL apoc.refactor.cloneNodes([original], false) YIELD output
        SET output.article = 'ns0__' + law_name
        RETURN count(output) as total_clonados
        """
        
        with self.driver.session() as session:
            try:
                result = session.run(
                    query,  
                    laws_list=articles_list
                )
                record = result.single()
                return record["total_clonados"] if record else 0
            except Exception as e:
                print(f"❌ Error en Cypher generate_root: {e}")
                raise e
    
    def generate_subgraphs(self, root_name: str, articles_list: list):
        """
        Replica el grafo completo para cada artículo, conectándolo a su respectivo clon raíz.
        """
        self.ensure_initialized(root_name)

        query = f"""
        MATCH (n:{label_root_class} {{name: '{root_name}'}})
        WHERE n.article IS NOT NULL 
        AND NOT (n)--()
        WITH DISTINCT n.name AS name_to_clone
        UNWIND $laws_list AS law_name
        MATCH (rootA:{label_root_class} {{name: name_to_clone}}),
              (rootB:{label_root_class} {{name: name_to_clone, article: 'ns0__' + law_name}})
        WHERE rootA.article IS NULL
        
        // 2. Obtener todos los nodos y relaciones conectados al original
        CALL apoc.path.subgraphAll(rootA, {{relationshipFilter: '<|>'}})
        YIELD nodes, relationships
        
        // 3. Clonar el subgrafo y re-vincularlo al nuevo rootB
        CALL apoc.refactor.cloneSubgraph(
            nodes,
            relationships,
            {{standinNodes: [[rootA, rootB]]}}
        )
        YIELD input, output, error
        RETURN count(output) as elementos_clonados
        """
        
        with self.driver.session() as session:
            try:
                result = session.run(
                    query, 
                    laws_list=articles_list
                )
                record = result.single()
                return record["elementos_clonados"] if record else 0
            except Exception as e:
                print(f"❌ Error en Cypher generate_subgraphs: {e}")
                raise e
    
    def decorate_probabilities(self, root_name: str, articles_list: list):
        """
        Calcula y añade la probabilidad a priori para cada artículo en su respectivo subgrafo.
        """
        self.ensure_initialized(root_name)

        query = f"""
        MATCH (n:{label_root_class} {{name: '{root_name}'}})-[r]-()
        WHERE n.article IS NOT NULL 
        AND r.typeReportRelation is null
        WITH DISTINCT n.name AS name_to_decorate
        UNWIND $laws_list AS law_name
        MATCH (rootA:{label_root_class} {{name: name_to_decorate, article: 'ns0__' + law_name}})
        CALL ontology.util.addArticlePriorProbability(rootA, law_name)
        YIELD relations
        RETURN count(relations) as total_relaciones_prob
        """ 
        with self.driver.session() as session:
            try:
                result = session.run(
                    query,  
                    laws_list=articles_list
                )
                record = result.single()
                return record["total_relaciones_prob"] if record else 0
            except Exception as e:
                print(f"❌ Error en Cypher decorate_probabilities: {e}")
                raise e

    def recuperar_referencias(self, root_name: str) -> list[tuple]:
        """Recupera relaciones y las devuelve como una lista de tuplas."""
        
        # print(f"✔ Recuperando información del artículo: {article}")
        print(f"✔ Recuperando información del grafo '{root_name}'")

        query = f"""
        MATCH (rootA {{name:'{root_name}'}})
        WHERE rootA.article IS NULL
        CALL apoc.path.subgraphAll(rootA, {{relationshipFilter:'<|>'}})
        YIELD relationships
        UNWIND relationships AS rel
        WITH rel, startNode(rel) AS inicio, endNode(rel) AS fin
        WHERE rel.ns0__referencia IS NOT NULL
        RETURN 
        inicio.name AS nombre_origen,
        type(rel) AS tipo_relacion,  
        fin.name AS nombre_destino, 
        rel.ns0__referencia AS referencia
        ORDER BY nombre_origen, tipo_relacion, nombre_destino;
        """

        with self.driver.session() as session:
            result = session.run(query)
            # Convertimos cada registro en una tupla y los metemos en una lista
            lista_tuplas = [
                (record["nombre_origen"], 
                 record["tipo_relacion"], 
                 record["nombre_destino"], 
                 record["referencia"]) 
                for record in result
            ]
            return lista_tuplas  

    def recuperar_resultados(self, name: str) -> list[tuple]:
        """Recupera relaciones y las devuelve como una lista de tuplas."""
        
        print(f"\t✔ Recuperando probabilidadesde aplicación de los artículos")

        query = f"""
        MATCH (rootA:ns0__Report {{name: '{name}'}})
        WHERE rootA.article IS NOT NULL
        CALL apoc.path.subgraphAll(rootA, {{relationshipFilter:'<|>'}})
        YIELD relationships

        WITH rootA.article AS article, 
            ontology.util.subGraphSubjetiveProbability(relationships,'AV') AS s_prob

        // 1. Extraemos los campos fijos por posición
        WITH article,
            s_prob[0] AS total_prob,
            s_prob[1] AS uncertainty,
            s_prob[2] AS subjetive_prob,
            // 2. Tomamos el resto de la lista (de la posición 3 en adelante)
            s_prob[3..] AS propiedades_raw

        // 3. Transformamos dinámicamente la lista de strings "Clave: Valor" en un Mapa
        WITH article, total_prob, uncertainty, subjetive_prob,
            apoc.map.fromPairs([p IN propiedades_raw WHERE p CONTAINS ": " | [
                split(p, ": ")[0], // Parte izquierda -> Clave
                split(p, ": ")[1]  // Parte derecha -> Valor
            ]]) AS dynamic_prop

        // 4. Retornamos los fijos y el mapa con el resto
        RETURN 
            article,
            total_prob,
            uncertainty,
            subjetive_prob,
            dynamic_prop
        ORDER BY total_prob DESC, uncertainty ASC
        """

        with self.driver.session() as session:
            print(f"\t✔ query: {query}")
            result = session.run(query)
            # Convertimos cada registro en una tupla y los metemos en una lista
            lista_tuplas = [
                (record["article"],
                record["total_prob"], 
                record["uncertainty"], 
                record["subjetive_prob"],
                record["dynamic_prop"]) 
                for record in result
            ]

            return lista_tuplas  
    
    def recuperar_relaciones(self, name: str, article: str | None) -> list[tuple]:
        """Recupera relaciones y las devuelve como una lista de tuplas."""
        
        print(f"\t✔ Recuperando relaciones del artículo: {article}")

        if article:
            query = f"""
            MATCH (rootA {{name: '{name}', article: 'ns0__{article}'}})
            CALL apoc.path.subgraphAll(rootA, {{relationshipFilter:'<|>'}})
            YIELD relationships

            // 1. Extraemos los datos y mantenemos el ID de la relación para asegurar unicidad
            UNWIND relationships AS rel
            WITH 
                startNode(rel).name AS nombre_origen,
                type(rel) AS tipo_relacion,
                endNode(rel).name AS nombre_destino,
                rel.typeReportRelation AS tipo,
                rel.ns0__referencia AS texto_referencia,
                id(rel) AS rel_id
            ORDER BY nombre_origen, tipo_relacion, nombre_destino

            // 2. Agrupamos toda la lista ya ordenada
            WITH collect({{
                origen: nombre_origen, 
                rel: tipo_relacion, 
                destino: nombre_destino, 
                tipo: tipo,
                texto_referencia: texto_referencia,
                rel_id: rel_id
            }}) AS listaOrdenada

            // 3. Creamos una sub-lista que SOLO contiene los elementos con texto_referencia
            WITH listaOrdenada, 
                [x IN listaOrdenada WHERE x.texto_referencia IS NOT NULL] AS listaSoloConTexto

            // 4. Desenrollamos la lista completa y calculamos el índice condicionalmente
            UNWIND listaOrdenada AS fila
            RETURN 
                CASE 
                    WHEN fila.texto_referencia IS NOT NULL 
                    THEN apoc.coll.indexOf(listaSoloConTexto, fila) + 1 
                    ELSE null 
                END AS referencia,
                fila.origen AS origen,
                fila.rel AS relacion,
                fila.destino AS destino,
                fila.tipo AS tipo,
                fila.texto_referencia AS texto_referencia
            """
        else:
            query = f"""
            MATCH (rootA {{name: '{name}'}})
            WHERE rootA.article IS NULL
            CALL apoc.path.subgraphAll(rootA, {{relationshipFilter:'<|>'}})
            YIELD relationships

            // 1. Extraemos los datos y mantenemos el ID de la relación para asegurar unicidad
            UNWIND relationships AS rel
            WITH 
                startNode(rel).name AS nombre_origen,
                type(rel) AS tipo_relacion,
                endNode(rel).name AS nombre_destino,
                rel.typeReportRelation AS tipo,
                rel.ns0__referencia AS texto_referencia,
                id(rel) AS rel_id
            ORDER BY nombre_origen, tipo_relacion, nombre_destino

            // 2. Agrupamos toda la lista ya ordenada
            WITH collect({{
                origen: nombre_origen, 
                rel: tipo_relacion, 
                destino: nombre_destino, 
                tipo: tipo,
                texto_referencia: texto_referencia,
                rel_id: rel_id
            }}) AS listaOrdenada

            // 3. Creamos una sub-lista que SOLO contiene los elementos con texto_referencia
            WITH listaOrdenada, 
                [x IN listaOrdenada WHERE x.texto_referencia IS NOT NULL] AS listaSoloConTexto

            // 4. Desenrollamos la lista completa y calculamos el índice condicionalmente
            UNWIND listaOrdenada AS fila
            RETURN 
                CASE 
                    WHEN fila.texto_referencia IS NOT NULL 
                    THEN apoc.coll.indexOf(listaSoloConTexto, fila) + 1 
                    ELSE null 
                END AS referencia,
                fila.origen AS origen,
                fila.rel AS relacion,
                fila.destino AS destino,
                fila.tipo AS tipo,
                fila.texto_referencia AS texto_referencia
            """

        with self.driver.session() as session:
            print(f"\t✔ query: {query}")
            result = session.run(query)
            # Convertimos cada registro en una tupla y los metemos en una lista
            if article:
                lista_tuplas = [
                    (record["referencia"],
                    record["origen"], 
                    record["relacion"], 
                    record["destino"], 
                    record["tipo"],
                    record["texto_referencia"]) 
                    for record in result
                ]
            else:
                lista_tuplas = [
                    (record["referencia"],
                    record["origen"], 
                    record["relacion"], 
                    record["destino"],
                    record["texto_referencia"]) 
                    for record in result
                ]

            return lista_tuplas        

    def recuperar_nodos(self, name: str, article: str | None) -> list[tuple]:
        """Recupera nodos y las devuelve como una lista de tuplas."""    
        print(f"\t✔ Recuperando nodos del artículo: {article}")

        if article:
            query = f"""
            MATCH (rootA {{name: '{name}', article: 'ns0__{article}'}})
            CALL apoc.path.subgraphAll(rootA, {{relationshipFilter:'<|>'}})
            YIELD nodes
            UNWIND nodes AS n
            // 1. Limpiamos los prefijos de todas las etiquetas primero
            WITH n, [l IN labels(n) | replace(l, 'ns0__', '')] AS etiquetasLimpias
            // 2. Definimos la lista negra (ya sin prefijos)
            WITH n, etiquetasLimpias, 
                ['Resource', 'OffenceElement', 'OffenceThing', 'TypeOfOffence', 'OffenceActor'] AS ignorar
            // 3. Filtramos las etiquetas que están en la lista negra
            WITH n, [l IN etiquetasLimpias WHERE NOT l IN ignorar] AS etiquetasFinales
            RETURN 
                n.name AS elemento,
                apoc.text.join(etiquetasFinales, ", ") AS tipos,
                apoc.text.join([k IN keys(n) WHERE k <> 'name' | 
                    replace(k, 'ns0__', '') + ": " + toString(n[k])
                ], " | ") AS propiedades
            """
        else:
            query = f"""
            MATCH (rootA {{name: '{name}'}})
            WHERE rootA.article IS NULL
            CALL apoc.path.subgraphAll(rootA, {{relationshipFilter:'<|>'}})
            YIELD nodes
            UNWIND nodes AS n
            // 1. Limpiamos los prefijos de todas las etiquetas primero
            WITH n, [l IN labels(n) | replace(l, 'ns0__', '')] AS etiquetasLimpias
            // 2. Definimos la lista negra (ya sin prefijos)
            WITH n, etiquetasLimpias, 
                ['Resource', 'OffenceElement', 'OffenceThing', 'TypeOfOffence', 'OffenceActor'] AS ignorar
            // 3. Filtramos las etiquetas que están en la lista negra
            WITH n, [l IN etiquetasLimpias WHERE NOT l IN ignorar] AS etiquetasFinales
            RETURN 
                n.name AS elemento,
                apoc.text.join(etiquetasFinales, ", ") AS tipos,
                apoc.text.join([k IN keys(n) WHERE k <> 'name' | 
                    replace(k, 'ns0__', '') + ": " + toString(n[k])
                ], " | ") AS propiedades
            """

        with self.driver.session() as session:
            print(f"\t✔ query: {query}")
            result = session.run(query)

            # Convertimos cada registro en una tupla y los metemos en una lista 
            lista_tuplas = [
                (record["elemento"], 
                record["tipos"], 
                record["propiedades"]) 
                for record in result
            ]

            return lista_tuplas  

# Instancia única para ser importada
neo4j_client = Neo4jManager()