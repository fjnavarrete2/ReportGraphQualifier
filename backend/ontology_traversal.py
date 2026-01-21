#!/usr/bin/env python3
"""
Script para recorrer una ontología en amplitud (BFS) usando owlready2
"""

from owlready2 import *
from collections import deque
import json
import datetime
import os
from typing import Dict, Any, List, Optional, Union, Tuple
import re

class OntologyTraversal:
    """Clase para realizar recorrido en amplitud de una ontología"""
    
    def __init__(self, ontology_path: str = None):
        """
        Inicializa el traversal con una ontología
        
        Args:
            ontology_path: Ruta al archivo OWL (opcional)
        """
        self.ontology = None
        if ontology_path:
            self.load_ontology(ontology_path)
    
    def load_ontology(self, path: str):
        """Carga una ontología desde un archivo"""
        try:
            self.ontology = get_ontology(path).load()
            print(f"✓ Ontología cargada desde: {path}")
        except Exception as e:
            print(f"✗ Error cargando ontología: {e}")
            raise
    
    def bfs_traversal_subclasses(self, start_class: Union[str, ThingClass], 
                                max_depth: int = None) -> List[tuple]:
        """
        Recorre las subclases en amplitud desde una clase dada
        
        Args:
            start_class: Clase inicial (nombre string o objeto ThingClass)
            max_depth: Profundidad máxima (None = sin límite)
            
        Returns:
            Lista de tuplas (clase, nivel, padre)
        """
        if isinstance(start_class, str):
            # Buscar la clase por nombre
            start_class = getattr(self.ontology, start_class, None)
            if not start_class:
                print(f"✗ Clase '{start_class}' no encontrada")
                return []
            else:
                print(f"✓ Clase '{start_class}' encontrada...")
        
        if not isinstance(start_class, ThingClass):
            print(f"✗ '{start_class}' no es una clase válida")
            return []
        else:
            print(f"✓ Clase '{start_class}' valida...")

        print(f"✓ Max depth: '{max_depth}'")
        
        # Cola para BFS: (clase, nivel, padre)
        queue = deque([(start_class, 0, None)])
        visited = set()
        result = []
        
        print(f"\n🔍 Iniciando recorrido BFS desde: {start_class.name} aaaaaa")
        print("=" * 50)
        
        while queue:
            current_class, level, parent = queue.popleft()
            
            # Verificar profundidad máxima
            if max_depth is not None and level > max_depth:
                continue
            
            # Evitar ciclos
            if current_class in visited:
                continue
            
            visited.add(current_class)
            result.append((current_class, level, parent))
            
            # Mostrar información del nodo actual
            indent = "  " * level
            parent_info = f" (padre: {parent.name})" if parent else " (raíz)"
            print(f"{indent}📁 Nivel {level}: {current_class.name}{parent_info}")
            
            # Mostrar equivalent_to
            self._print_equivalent_classes(current_class, indent)
            
            # Agregar subclases a la cola
            
            subclasses = list(current_class.subclasses())
            print(f"Subclasses of '{current_class.name}': '{subclasses.count(0)}'")
            if subclasses:
                print(f"{indent}   └─ Subclases encontradas: {[sc.name for sc in subclasses]}")
                for subclass in subclasses:
                    if subclass not in visited:
                        queue.append((subclass, level + 1, current_class))
            else: 
                print(f"✗ No existen subclasses de '{current_class.name}'")
        return result
    
    def _print_equivalent_classes(self, current_class: ThingClass, indent: str):
        """
        Imprime las clases equivalentes de una clase dada
        
        Args:
            current_class: La clase a examinar
            indent: Indentación para el formato de salida
        """
        try:
            # Obtener clases equivalentes
            equivalent_classes = list(current_class.equivalent_to)
            
            if equivalent_classes:
                print(f"{indent}   ≡ Equivalentes a:")
                for eq_class in equivalent_classes:
                    # Manejar diferentes tipos de equivalencias
                    if hasattr(eq_class, 'name') and eq_class.name:
                        # Clase nombrada
                        print(f"{indent}     🔗 {eq_class.name}")
                    elif hasattr(eq_class, '__class__'):
                        # Expresión de clase compleja
                        class_expr = self._format_class_expression(eq_class)
                        print(f"{indent}     🔗 {class_expr}")
                    else:
                        # Fallback para otros tipos
                        print(f"{indent}     🔗 {str(eq_class)}")
            else:
                print(f"{indent}   ≡ Sin clases equivalentes")
                
        except Exception as e:
            print(f"{indent}   ≡ Error obteniendo equivalencias: {str(e)}")
    
    def _format_class_expression(self, expression) -> str:
        """
        Formatea expresiones de clases complejas de forma legible
        
        Args:
            expression: Expresión de clase de owlready2
            
        Returns:
            String formateado de la expresión
        """
        try:
            # Verificar si es una intersección (And)
            if hasattr(expression, '__class__') and 'And' in str(type(expression)):
                classes = []
                for item in expression.Classes:
                    if hasattr(item, 'name'):
                        classes.append(item.name)
                    else:
                        classes.append(str(item))
                return f"({' ∩ '.join(classes)})"
            
            # Verificar si es una unión (Or) 
            elif hasattr(expression, '__class__') and 'Or' in str(type(expression)):
                classes = []
                for item in expression.Classes:
                    if hasattr(item, 'name'):
                        classes.append(item.name)
                    else:
                        classes.append(str(item))
                return f"({' ∪ '.join(classes)})"
            
            # Verificar si es una restricción
            elif hasattr(expression, 'property'):
                prop_name = getattr(expression.property, 'name', str(expression.property))
                if hasattr(expression, 'value'):
                    # Restricción de valor
                    value = getattr(expression.value, 'name', str(expression.value))
                    return f"({prop_name} some {value})"
                elif hasattr(expression, 'cardinality'):
                    # Restricción de cardinalidad
                    return f"({prop_name} exactly {expression.cardinality})"
                else:
                    return f"({prop_name} restriction)"
            
            # Verificar si es un complemento (Not)
            elif hasattr(expression, '__class__') and 'Not' in str(type(expression)):
                if hasattr(expression, 'Class'):
                    class_name = getattr(expression.Class, 'name', str(expression.Class))
                    return f"¬{class_name}"
            
            # Para otros tipos de expresiones
            else:
                return str(expression)
                
        except Exception as e:
            return f"Expresión compleja: {str(expression)}"
    
    def export_classes_to_json(self, start_class: Union[str, ThingClass] = None, 
                              output_file: str = None, max_depth: int = None,
                              include_metadata: bool = True, traversal_method: str = "bfs") -> str:
        """
        Exporta las clases y sus equivalent_to a un archivo JSON
        
        Args:
            start_class: Clase inicial (None = todas las clases de la ontología)
            output_file: Nombre del archivo JSON (None = genera automáticamente)
            max_depth: Profundidad máxima para el recorrido
            include_metadata: Incluir metadatos adicionales
            
        Returns:
            Ruta del archivo JSON generado
        """
        # Generar nombre de archivo si no se proporciona
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if start_class:
                start_name = start_class if isinstance(start_class, str) else start_class.name
                output_file = f"ontology_export_{start_name}_{timestamp}.json"
            else:
                output_file = f"ontology_export_all_{timestamp}.json"
        
        # Recopilar datos
        export_data = {
            "metadata": {},
            "classes": {}
        }
        
        # Agregar metadatos si se solicita
        if include_metadata:
            export_data["metadata"] = {
                "export_timestamp": datetime.now().isoformat(),
                "ontology_iri": str(self.ontology.base_iri) if self.ontology else "Unknown",
                "start_class": start_class if isinstance(start_class, str) else (start_class.name if start_class else "All classes"),
                "max_depth": max_depth,
                "total_classes": 0,
                "classes_with_equivalents": 0
            }
        
        # Determinar qué clases procesar
        if start_class:
            # Recorrido BFS o DFS desde una clase específica
            if traversal_method == "dfs":
                traversal_result = self.dfs_equivalent_and_subclasses_instances(start_class, max_depth)
            else:
                traversal_result = self.bfs_traversal_subclasses(start_class, max_depth)
            classes_to_process = [cls for cls, level, parent in traversal_result]
        else:
            # Todas las clases de la ontología
            classes_to_process = list(self.ontology.classes()) if self.ontology else []
        
        
        print(f"🔄 Exportando {len(classes_to_process)} clases a JSON...")
        
        # Procesar cada clase
        classes_with_equivalents = 0
        for class_obj in classes_to_process:
            class_data = self._extract_class_data(class_obj)
            export_data["classes"][class_obj.name] = class_data
            
            if class_data["equivalent_classes"]:
                classes_with_equivalents += 1
        
        # Actualizar metadatos
        if include_metadata:
            export_data["metadata"]["total_classes"] = len(classes_to_process)
            export_data["metadata"]["classes_with_equivalents"] = classes_with_equivalents
        
        # Guardar archivo JSON
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Archivo JSON exportado exitosamente: {output_file}")
            print(f"📊 Estadísticas:")
            print(f"   - Total de clases: {len(classes_to_process)}")
            print(f"   - Clases con equivalencias: {classes_with_equivalents}")
            print(f"   - Tamaño del archivo: {os.path.getsize(output_file)} bytes")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Error al guardar archivo JSON: {e}")
            raise
    
    def _extract_class_data(self, class_obj: ThingClass) -> Dict[str, Any]:
        """
        Extrae datos detallados de una clase para exportación JSON
        
        Args:
            class_obj: Objeto de clase de owlready2
            
        Returns:
            Diccionario con los datos de la clase
        """
        # Extraer comentarios y seeAlso (pueden devolver listas)
        comment_values = getattr(class_obj, "comment", [])
        see_also_values = getattr(class_obj, "seeAlso", [])
        class_data = {
            "name": class_obj.name,
            "iri": str(class_obj.iri) if hasattr(class_obj, 'iri') else None,
            "comments": [str(c) for c in comment_values] if comment_values else [],
            "seeAlso": [str(s) for s in see_also_values] if see_also_values else [],
            "equivalent_classes": [],
            "superclasses": [],
            "subclasses": [],
            "instances_count": 0,
            "properties": {
                "domain": [],
                "range": []
            }
        }
        
        try:
            # Extraer clases equivalentes
            equivalent_classes = list(class_obj.equivalent_to)
            for eq_class in equivalent_classes:
                eq_data = self._format_equivalent_for_json(eq_class)
                class_data["equivalent_classes"].append(eq_data)
            
            # Extraer superclases (padres directos)
            for parent in class_obj.is_a:
                if parent != Thing and hasattr(parent, 'name'):
                    class_data["superclasses"].append({
                        "name": parent.name,
                        "iri": str(parent.iri) if hasattr(parent, 'iri') else None
                    })
            
            # Extraer subclases (hijos directos)
            for child in class_obj.subclasses():
                class_data["subclasses"].append({
                    "name": child.name,
                    "iri": str(child.iri) if hasattr(child, 'iri') else None
                })
            
            # Contar instancias
            class_data["instances_count"] = len(list(class_obj.instances()))
            
            # Extraer propiedades donde esta clase es dominio o rango
            if self.ontology:
                for prop in self.ontology.properties():
                    # Verificar si es dominio
                    if hasattr(prop, 'domain') and class_obj in prop.domain:
                        class_data["properties"]["domain"].append({
                            "name": prop.name,
                            "type": "ObjectProperty" if isinstance(prop, ObjectProperty) else "DataProperty"
                        })
                    
                    # Verificar si es rango
                    if hasattr(prop, 'range') and class_obj in prop.range:
                        class_data["properties"]["range"].append({
                            "name": prop.name,
                            "type": "ObjectProperty" if isinstance(prop, ObjectProperty) else "DataProperty"
                        })
        
        except Exception as e:
            # En caso de error, al menos mantener el nombre
            print(f"⚠️  Error procesando clase {class_obj.name}: {e}")
        
        return class_data
    
    #########################################


    # Se asume que ObjectProperty y otras clases de OWL están disponibles
    # (e.g., importadas desde owlready2, como se infiere del contexto de los archivos).
    # from owlready2 import ObjectProperty, Restriction, And, Or, Not, Some

    def _format_equivalent_for_json(self, equivalent) -> Dict[str, Any]:
        """
        Formatea una clase o expresión equivalente (equivalent_to) para exportación JSON,
        manejando recursivamente operadores lógicos (AND, OR, NOT) y restricciones (some).

        Args:
            equivalent: Clase o expresión equivalente (e.g., owlready2.Class, owlready2.And).

        Returns:
            Diccionario con la estructura JSON completa de la equivalencia.
        """
        # Inicialización del diccionario base
        eq_data = {
            "type": "unknown",
            "description": "",
            "raw": str(equivalent)
        }

        try:
            # 1. CLASE NOMBRADA SIMPLE
            if hasattr(equivalent, 'name') and equivalent.name:
                eq_data.update({
                    "type": "named_class",
                    "name": equivalent.name,
                    "iri": str(equivalent.iri) if hasattr(equivalent, 'iri') else None,
                    "description": f"Clase nombrada: {equivalent.name}"
                })
                
            # 2. OPERADORES LÓGICOS (AND, OR, NOT)

            # Intersección (And)
            elif hasattr(equivalent, '__class__') and 'And' in str(type(equivalent)):
                operands = []
                for item in equivalent.Classes:
                    # Llamada recursiva para procesar cada operando
                    operands.append(self._format_equivalent_for_json(item))
                
                eq_data.update({
                    "type": "intersection",
                    "operands": operands,
                    "description": f"Intersección lógica (AND) de {len(operands)} elementos",
                    "logical_operator": "AND"
                })

            # Unión (Or)
            elif hasattr(equivalent, '__class__') and 'Or' in str(type(equivalent)):
                operands = []
                for item in equivalent.Classes:
                    # Llamada recursiva para procesar cada operando
                    operands.append(self._format_equivalent_for_json(item))
                
                eq_data.update({
                    "type": "union",
                    "operands": operands,
                    "description": f"Unión lógica (OR) de {len(operands)} elementos",
                    "logical_operator": "OR"
                })

            # Complemento (Not)
            elif hasattr(equivalent, '__class__') and 'Not' in str(type(equivalent)):
                if hasattr(equivalent, 'Class'):
                    # Llamada recursiva para el operando negado
                    negated_operand = self._format_equivalent_for_json(equivalent.Class)
                    
                    eq_data.update({
                        "type": "complement",
                        "operand": negated_operand,
                        "description": f"Negación lógica (NOT) de un elemento",
                        "logical_operator": "NOT"
                    })
            
            # 3. RESTRICCIÓN DE PROPIEDAD (Asumiendo que 'equivalent' es una restricción)
            elif hasattr(equivalent, 'property'):
                prop_name = getattr(equivalent.property, 'name', str(equivalent.property))
                prop_iri = str(equivalent.property.iri) if hasattr(equivalent.property, 'iri') else None
                
                restriction_data = {
                    "property": prop_name,
                    "property_iri": prop_iri,
                    # Asumiendo que ObjectProperty está disponible para el chequeo de tipo
                    # "property_type": "ObjectProperty" if isinstance(equivalent.property, ObjectProperty) else "DataProperty"
                }
                
                # Restricción 'some' (Existential Restriction)
                if hasattr(equivalent, 'value') and 'Some' in str(type(equivalent)):
                    # El 'value' en una restricción 'some' (e.g., hasProperty some Class)
                    # es la clase o datatype a la que apunta.
                    target_value = equivalent.value
                    
                    # Llamada recursiva para analizar el valor (puede ser una clase nombrada o una expresión)
                    target_format = self._format_equivalent_for_json(target_value)
                    
                    restriction_data.update({
                        "restriction_type": "some",
                        "target": target_format, # Usar el formato recursivo
                        "description": f"Restricción existencial: {prop_name} some {target_format.get('name', target_format.get('type', 'clase/expresión'))}"
                    })
                
                # Restricción 'only' (Universal Restriction) - Añadida para completitud
                elif hasattr(equivalent, 'value') and 'Only' in str(type(equivalent)):
                    target_value = equivalent.value
                    target_format = self._format_equivalent_for_json(target_value)
                    restriction_data.update({
                        "restriction_type": "only",
                        "target": target_format,
                        "description": f"Restricción universal: {prop_name} only {target_format.get('name', target_format.get('type', 'clase/expresión'))}"
                    })
                
                # Otras restricciones como 'value', 'min', 'max', 'exactly' (cardinalidad)
                # Se mantienen de la función original o se extienden según sea necesario
                elif hasattr(equivalent, 'cardinality'):
                    # Restricción de cardinalidad (e.g., 'exactly', 'min', 'max')
                    cardinality_type = next((attr for attr in ['min_cardinality', 'max_cardinality', 'cardinality'] if hasattr(equivalent, attr)), 'cardinality')
                    cardinality_value = getattr(equivalent, cardinality_type)
                    
                    # Opcional: El valor restringido (si es una QualifiedCardinalityRestriction)
                    if hasattr(equivalent, 'on_class'):
                        target_format = self._format_equivalent_for_json(equivalent.on_class)
                    else:
                        target_format = None
                    
                    restriction_data.update({
                        "restriction_type": "cardinality",
                        "cardinality_type": cardinality_type.replace('_cardinality', ''),
                        "value": cardinality_value,
                        "target": target_format,
                        "description": f"Restricción de cardinalidad: {prop_name} {cardinality_type.replace('_cardinality', '')} {cardinality_value}"
                    })
                # ... Añadir más tipos de restricción si se necesitan (e.g., has_value, exactly)

                else:
                    # Si es una restricción sin un tipo de valor o cardinalidad conocido
                    restriction_data.update({
                        "restriction_type": "unknown",
                        "description": f"Restricción desconocida en propiedad {prop_name}"
                    })

                eq_data.update({
                    "type": "restriction",
                    "restriction_details": restriction_data,
                    "description": restriction_data.get("description", f"Restricción en propiedad {prop_name}")
                })
                
            
            # 4. CLASE ANONIMA (si no es ninguna de las anteriores)
            elif 'Class' in str(type(equivalent)) and not hasattr(equivalent, 'name'):
                # Puede ser una clase anónima, a menudo usada como marcador
                eq_data.update({
                    "type": "anonymous_class",
                    "description": f"Clase anónima",
                })

        except Exception as e:
            eq_data["type"] = "error"
            eq_data["error"] = f"Error procesando equivalencia: {str(e)}"
        
        return eq_data

    #########################################
    
    def _format_equivalent_for_json2(self, equivalent) -> Dict[str, Any]:
        """
        Formatea una clase equivalente para exportación JSON
        
        Args:
            equivalent: Clase o expresión equivalente
            
        Returns:
            Diccionario con información de la equivalencia
        """
        eq_data = {
            "type": "unknown",
            "description": "",
            "raw": str(equivalent)
        }
        
        try:
            # Clase nombrada simple
            if hasattr(equivalent, 'name') and equivalent.name:
                eq_data.update({
                    "type": "named_class",
                    "name": equivalent.name,
                    "iri": str(equivalent.iri) if hasattr(equivalent, 'iri') else None,
                    "description": f"Equivalente a la clase {equivalent.name}"
                })
            
            # Intersección (And)
            elif hasattr(equivalent, '__class__') and 'And' in str(type(equivalent)):
                classes = []
                for item in equivalent.Classes:
                    if hasattr(item, 'name'):
                        classes.append({"name": item.name, "type": "class"})
                    else:
                        classes.append({"name": str(item), "type": "expression"})
                
                eq_data.update({
                    "type": "intersection",
                    "classes": classes,
                    "description": f"Intersección de {len(classes)} clases",
                    "logical_operator": "AND"
                })
            
            # Unión (Or)
            elif hasattr(equivalent, '__class__') and 'Or' in str(type(equivalent)):
                classes = []
                for item in equivalent.Classes:
                    if hasattr(item, 'name'):
                        classes.append({"name": item.name, "type": "class"})
                    else:
                        classes.append({"name": str(item), "type": "expression"})
                
                eq_data.update({
                    "type": "union", 
                    "classes": classes,
                    "description": f"Unión de {len(classes)} clases",
                    "logical_operator": "OR"
                })
            
            # Restricción de propiedad
            elif hasattr(equivalent, 'property'):
                prop_name = getattr(equivalent.property, 'name', str(equivalent.property))
                
                restriction_data = {
                    "property": prop_name,
                    "property_type": "ObjectProperty" if isinstance(equivalent.property, ObjectProperty) else "DataProperty"
                }
                
                if hasattr(equivalent, 'value'):
                    # Restricción existencial o de valor
                    value = getattr(equivalent.value, 'name', str(equivalent.value))
                    restriction_data.update({
                        "restriction_type": "some",
                        "value": value,
                        "description": f"Restricción: {prop_name} some {value}"
                    })
                elif hasattr(equivalent, 'cardinality'):
                    # Restricción de cardinalidad
                    restriction_data.update({
                        "restriction_type": "cardinality",
                        "cardinality": equivalent.cardinality,
                        "description": f"Restricción: {prop_name} exactly {equivalent.cardinality}"
                    })
                
                eq_data.update({
                    "type": "restriction",
                    "restriction": restriction_data,
                    "description": restriction_data.get("description", f"Restricción en propiedad {prop_name}")
                })
            
            # Complemento (Not)
            elif hasattr(equivalent, '__class__') and 'Not' in str(type(equivalent)):
                if hasattr(equivalent, 'Class'):
                    class_name = getattr(equivalent.Class, 'name', str(equivalent.Class))
                    eq_data.update({
                        "type": "complement",
                        "class": class_name,
                        "description": f"Complemento de {class_name}",
                        "logical_operator": "NOT"
                    })
        
        except Exception as e:
            eq_data["error"] = f"Error procesando equivalencia: {str(e)}"
        
        return eq_data
    
    def get_data_property_xsd_range(self, property_name: str) -> Dict[str, Any]:
        """
        Obtiene el rango XSD de una Data Property dada por su nombre, devolviendo 
        las URIs nativas de XML Schema (XSD).
        
        Esta función revierte el mapeo automático de owlready2 (de XSD a Python)
        para asegurar que se devuelva el IRI XSD para la generación de RDF.

        Args:
            property_name (str): El nombre de la Data Property (ej. 'Age', 'ValueCost').

        Returns:
            Dict[str, Any]: Diccionario con el nombre, IRI de la propiedad y lista de rangos XSD.
        """
        if not self.ontology:
            return {"error": "Ontología no cargada"}

        # 1. Buscar la propiedad
        prop = getattr(self.ontology, property_name, None)
    
        if not prop:
            return {"error": f"La propiedad '{property_name}' no existe en la ontología."}

        # 2. Verificar que sea DataProperty
        if not isinstance(prop, DataPropertyClass):
            return {
                "error": f"'{property_name}' no es una DataProperty, es de tipo {type(prop).__name__}.",
            }

        # 3. Mapeo de tipos Python (a los que owlready2 convierte) a URIs XSD estándar
        # Esto es necesario porque prop.range devuelve los tipos de Python
        xsd_uri_map = {
            int: "http://www.w3.org/2001/XMLSchema#integer", # Mejor que 'int' para RDF
            float: "http://www.w3.org/2001/XMLSchema#decimal", # Cubre decimal/double en muchos casos de conversión
            bool: "http://www.w3.org/2001/XMLSchema#boolean",
            str: "http://www.w3.org/2001/XMLSchema#string",
            datetime.date: "http://www.w3.org/2001/XMLSchema#date",
            datetime.datetime: "http://www.w3.org/2001/XMLSchema#dateTime",
            datetime.time: "http://www.w3.org/2001/XMLSchema#time",
        }

        ranges_xsd_uris = []
        
        for r in prop.range:
            # Caso 1: Si owlready2 mantuvo el objeto con IRI (ej. XSD.decimal)
            if hasattr(r, 'iri'):
                ranges_xsd_uris.append(r.iri)
            # Caso 2: Si owlready2 lo convirtió a tipo Python nativo
            elif r in xsd_uri_map:
                ranges_xsd_uris.append(xsd_uri_map[r])
            # Fallback
            else:
                ranges_xsd_uris.append(f"No_Mapeado_{str(r)}")

        return {
            "property_name": property_name,
            "iri": prop.iri,
            "ranges_xsd": ranges_xsd_uris
        }
    
    def load_json_export(self, json_file: str) -> Dict[str, Any]:
        """
        Carga un archivo JSON exportado previamente
        
        Args:
            json_file: Ruta del archivo JSON
            
        Returns:
            Diccionario con los datos cargados
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ Archivo JSON cargado: {json_file}")
            if "metadata" in data:
                print(f"📊 Metadatos:")
                for key, value in data["metadata"].items():
                    print(f"   - {key}: {value}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error cargando archivo JSON: {e}")
            raise


    def dfs_equivalent_and_subclasses_instances(self, 
                                       start_class: Union[str, ThingClass], 
                                       max_depth: Optional[int] = None) -> List[tuple]:
        """
        Recorrido DFS: dada una clase raíz, encuentra:
        - Sus subclases
        - Todas las clases que la referencian en 'equivalent_to'

        Devuelve una lista de tuplas (clase, nivel, padre).
        """

        # Resolver clase inicial
        if isinstance(start_class, str):
            start_class = getattr(self.ontology, start_class, None)
            if not start_class:
                print(f"✗ Clase '{start_class}' no encontrada")
                return []
        if not isinstance(start_class, ThingClass):
            print(f"✗ '{start_class}' no es una clase válida")
            return []

        visited = set()
        result = []
        stack = [(start_class, 0, None)]  # (clase, nivel, padre)

        # Precalcular todas las clases de la ontología
        all_classes = list(self.ontology.classes())

        while stack:
            current_class, depth, parent = stack.pop()

            if max_depth is not None and depth > max_depth:
                continue
            if current_class in visited:
                continue

            visited.add(current_class)
            result.append((current_class, depth, parent))

            # 1. Subclases directas
            for subclass in current_class.subclasses():
                if subclass not in visited:
                    stack.append((subclass, depth + 1, current_class))

            # 2. Dependencias por 'equivalent_to' inverso
            for cls in all_classes:
                for eq in getattr(cls, "equivalent_to", []):
                    if hasattr(eq, "name") and eq.name == current_class.name:
                        if cls not in visited:
                            stack.append((cls, depth + 1, current_class))
                    elif hasattr(eq, "Classes"):
                        for sub_eq in eq.Classes:
                            if hasattr(sub_eq, "name") and sub_eq.name == current_class.name:
                                if cls not in visited:
                                    stack.append((cls, depth + 1, current_class))

        return result

    # Prefijo de la ontología a eliminar
    ONTOLOGY_PREFIX = "SCPO_Extended_Ontology_V01R08_AT08Q."

    def _limpiar_elemento(self, elemento: str) -> str:
        """Elimina el prefijo de la ontología de un string de elemento."""
        return elemento.replace(self.ONTOLOGY_PREFIX, "")
    
    def _extraer_entidad_rango(self, expresion: str) -> Optional[str]:
        """
        Extrae la entidad rango (clase destino) de una expresión de restricción OWL 
        del tipo Propiedad.some(EntidadRango).
        
        Args:
            expresion (str): La expresión de restricción OWL (ej: 'belongsTo.some(Victim)').
            
        Returns:
            Optional[str]: La entidad rango (ej: 'Victim') o None si no se encuentra.
        """
        # Expresión regular para buscar:
        # 1. Cualquier cadena de texto (propiedad).
        # 2. Un punto seguido de un operador de cardinalidad (some, only, min, max, exactly, value).
        # 3. Un paréntesis de apertura.
        # 4. El contenido que queremos capturar (el grupo 1).
        # 5. Un paréntesis de cierre.
        
        # El patrón '(.*)' captura el contenido dentro del paréntesis, que corresponde a la entidad rango.
        patron = r'\s*\w+\.(some|only|value|min|max|exactly)\s*\((.*)\)'
        
        match = re.search(patron, expresion)
        
        if match:
            # El grupo 2 contiene la entidad rango (lo que está dentro de los paréntesis)
            entidad_rango = match.group(2).strip()
            return entidad_rango
        else:
            return None

    def _analizar_restriccion_anidada_dict_v4(self,segmento_restriccion: str, nivel: int, is_subject: bool = True) -> List[Dict[str, Union[str, int]]]:
        """ 
        Función auxiliar para analizar y devolver una lista de diccionarios, 
        eliminando el prefijo de la ontología.
        """
        componentes: List[Dict[str, Union[str, int]]] = []
        contenido_a_analizar = segmento_restriccion.strip()
        nivel_actual_interno = nivel

        # 1. Manejar el operador Not()
        if contenido_a_analizar.startswith("Not("):
            componentes.append({
                "level": nivel, 
                "type": "operador", 
                "element": "Not", 
                "description": "Not", 
                "range": None,
                "cardinality": None
            })
            
            nivel_actual_interno = nivel + 1
            
            # Extracción de contenido de Not()
            parentesis_abiertos = 1
            contenido_not = ""
            for i in range(len("Not("), len(contenido_a_analizar)):
                char = contenido_a_analizar[i]
                if char == '(':
                    parentesis_abiertos += 1
                elif char == ')':
                    parentesis_abiertos -= 1
                    if parentesis_abiertos == 0:
                        break 
                contenido_not += char
            
            # Recursión con el contenido de Not
            componentes.extend(self, contenido_not, nivel_actual_interno, is_subject=False)
            return componentes

        # 2. Análisis de restricciones de propiedad (some, only, etc.)
        match_propiedad_inicial = re.search(r'\.(\w+)\.(some|only|value|min|max|exactly)\(', contenido_a_analizar)
        
        if match_propiedad_inicial:
            
            cuerpo_restriccion = contenido_a_analizar[match_propiedad_inicial.start() + 1:].strip()
            
            # 3. Iterar sobre las restricciones anidadas
            while True:
                # Patrón de restricción: propiedad.cardinalidad(contenido)
                match = re.match(r'(\w+)\.(some|only|value|min|max|exactly)\((.*)\)', cuerpo_restriccion, re.DOTALL)
                
                if match:
                    propiedad = match.group(1)
                    cardinalidad = match.group(2)
                    contenido_con_parentesis = match.group(3)

                    # Encontrar el cierre de paréntesis correcto
                    parentesis_abiertos = 0
                    contenido_real = ""
                    for char in contenido_con_parentesis:
                        if char == '(':
                            parentesis_abiertos += 1
                        elif char == ')':
                            if parentesis_abiertos == 0:
                                break 
                            parentesis_abiertos -= 1
                        contenido_real += char
                    
                    contenido_real = contenido_real.strip()
                    
                    # Añadir la restricción de propiedad (Objeto)
                    # Se limpia el contenido_real solo para mostrarlo, pero se usa el original para la búsqueda anidada
                    contenido_real_limpio = self._limpiar_elemento(contenido_real)
                    
                    if contenido_real_limpio.__contains__("(") and contenido_real_limpio.__contains__(")"):
                        rango = self.get_object_property_detail(propiedad, "range") 
                    else:
                        rango = [contenido_real_limpio]

                    componentes.append({
                        "level": nivel_actual_interno, 
                        "type": "objeto", 
                        "element": propiedad,
                        "description":  f"Propiedad: '{propiedad}' sobre: '{contenido_real_limpio}'",
                        "range": rango,
                        "cardinality": cardinalidad
                    })

                    nivel_siguiente = nivel_actual_interno + 1
                    
                    # Chequear si el contenido anidado empieza con Not() o tiene otra restricción
                    if contenido_real.startswith("Not("):
                        componentes.extend(self._analizar_restriccion_anidada_dict_v4(contenido_real, nivel_siguiente, is_subject=False))
                        break
                        
                    match_next_restriction = re.search(r'\.(\w+)\.(some|only|value|min|max|exactly)\(', contenido_real)
                    
                    if match_next_restriction:
                        # Omitir la entidad del contenido si le sigue otra restricción
                        
                        # Preparar el resto para la próxima iteración (la nueva restricción)
                        cuerpo_restriccion = contenido_real[match_next_restriction.start() + 1:].strip()
                        nivel_actual_interno = nivel_siguiente
                    else:
                        # Es una Entidad simple (Clase/Individuo) al final del anidamiento (ej: SCPO.Accused)

                        componentes.append({
                            "level": nivel_siguiente, 
                            "type": "entidad", 
                            "element": self._limpiar_elemento(contenido_real),
                            "description": contenido_real,
                            "range": None,
                            "cardinality": None 
                        })
                        break 

                else:
                    break 

        else:
            # Es una entidad simple (sin restricciones de propiedad ni Not)
            componentes.append({
                "level": nivel, 
                "type": "entidad", 
                "element": self._limpiar_elemento(contenido_a_analizar), 
                "description": self._limpiar_elemento(contenido_a_analizar), 
                "range": None,
                "cardinality": None
            })

        return componentes
    
    def bfs_traversal_instances(self, start_class: Union[str, ThingClass]) -> List[tuple]:
        """
        Recorre las instancias de una clase en amplitud
        
        Args:
            start_class: Clase inicial
            
        Returns:
            Lista de tuplas (instancia, clase)
        """
        if isinstance(start_class, str):
            start_class = getattr(self.ontology, start_class, None)
            if not start_class:
                return []
        
        result = []
        queue = deque([start_class])
        visited_classes = set()
        
        print(f"\n🎯 Buscando instancias desde: {start_class.name}")
        print("=" * 50)
        
        while queue:
            current_class = queue.popleft()
            
            if current_class in visited_classes:
                continue
            
            visited_classes.add(current_class)
            
            # Obtener instancias de la clase actual
            instances = list(current_class.instances())
            if instances:
                print(f"📋 Clase {current_class.name}:")
                
                # Mostrar equivalent_to de la clase
                self._print_equivalent_classes(current_class, "")
                
                for instance in instances:
                    result.append((instance, current_class))
                    print(f"   └─ 🔸 {instance.name}")
            else:
                # Aún mostrar equivalencias aunque no tenga instancias
                print(f"📋 Clase {current_class.name} (sin instancias):")
                self._print_equivalent_classes(current_class, "")
            
            # Agregar subclases a la cola
            for subclass in current_class.subclasses():
                if subclass not in visited_classes:
                    queue.append(subclass)
        
        return result
    # Se requiere la definición de la función principal para las llamadas recursivas internas
    # (Aquí se simula la llamada a la función principal)
    def analizar_expresion_owl_simplificada_dict_v5__(self, expresion: str, is_internal_call: bool = False, start_level: int = 0) -> List[Dict[str, Union[str, int, Optional[str]]]]:
        """
        Función principal/recursiva para analizar expresiones OWL con AND (&), OR (|) y NOT.
        """
        
        componentes_anidados: List[Dict[str, Union[str, int, Optional[str]]]] = []
        nivel = start_level
        
        # Simplicación: se asume que solo el AND es el operador lógico a nivel de split
        # y que los OR/NOT se manejan dentro de _analizar_restriccion_anidada_dict_v5
        
        operador_logico = "AND"
        separador = r'\s&\s'
        conjuntos = [c.strip() for c in expresion.split('&')]

        for i, conjunto in enumerate(conjuntos):
            
            # Analizar cada conjunto de forma independiente
            # is_subject=True si es el primer elemento del AND global y no es una llamada interna
            is_subject_flag = (i == 0 and not is_internal_call and operador_logico == "AND")
            componentes_anidados.extend(self._analizar_restriccion_anidada_dict_v5(conjunto, nivel, is_subject=is_subject_flag))
                
            # Insertar el operador lógico (si no es el último conjunto)
            if i < len(conjuntos) - 1 and operador_logico:
                componentes_anidados.append({
                    "level": nivel, 
                    "type": "operador", 
                    "element": operador_logico, 
                    "description" : f"{operador_logico}",
                    "range": None,
                    "cardinality": None
                })

        return componentes_anidados
    #############################################
    def _parse_constrained_datatype(self, content: str) -> Dict[str, Any]:
        """
        Método Auxiliar: Parsea una cadena de texto de owlready2 tipo 
        'ConstrainedDatatype(decimal, min_inclusive=400.0)' extrayendo las restricciones.
        """
        try:
            # Limpiar envoltura básica
            inner = content.replace("ConstrainedDatatype(", "").rstrip(")")
            
            # Dividir por comas, pero tener cuidado si hay comas anidadas (aunque en datatypes simples es raro)
            parts = [p.strip() for p in inner.split(",")]
            
            # El primer elemento es el tipo base (ej. decimal, int, float)
            base_type = self._limpiar_elemento(parts[0])
            
            constraints = {}
            # Procesar el resto de argumentos (ej: min_inclusive=400.0)
            for part in parts[1:]:
                if "=" in part:
                    key, val = part.split("=", 1)
                    constraints[key.strip()] = val.strip()
            
            return {
                "base_type": base_type,
                "constraints": constraints,
                "raw": content
            }
        except Exception as e:
            return {"error": f"Error parsing datatype: {e}", "raw": content}

    def analizar_expresion_owl_simplificada_dict_v5(self, expresion: str, is_internal_call: bool = False, start_level: int = 0) -> List[Dict[str, Union[str, int, Optional[str]]]]:
        """
        Función Principal: Analiza expresiones OWL con AND (&), OR (|) y NOT, delegando
        el análisis detallado a la función anidada.
        """
        componentes_anidados: List[Dict[str, Union[str, int, Optional[str]]]] = []
        nivel = start_level
        
        # Separamos por el operador lógico global (Asumimos '&' como intersección principal en equivalent_to)
        # Nota: En expresiones complejas mixtas, esto debería ser un parser recursivo más robusto,
        # pero para la estructura estándar de OWLAPI/Owlready2 esto suele funcionar.
        conjuntos = [c.strip() for c in expresion.split('&')]

        operador_logico = "AND" # Default implícito en listas de intersección

        for i, conjunto in enumerate(conjuntos):
            
            # Analizar cada conjunto de forma independiente
            # is_subject=True si es el primer elemento y no es una llamada recursiva interna
            is_subject_flag = (i == 0 and not is_internal_call)
            
            # Llamada a la función refactorizada de análisis detallado
            resultado_anidado = self._analizar_restriccion_anidada_dict_v5(conjunto, nivel, is_subject=is_subject_flag)
            componentes_anidados.extend(resultado_anidado)
                
            # Insertar el operador lógico visualmente (si no es el último conjunto)
            if i < len(conjuntos) - 1:
                componentes_anidados.append({
                    "level": nivel, 
                    "type": "operator", 
                    "element": "&", 
                    "description" : "AND",
                    "range": None,
                    "cardinality": None
                })

        return componentes_anidados

    #################################

    def _analizar_restriccion_anidada_dict_v5(self, segmento_restriccion: str, nivel: int, is_subject: bool = True) -> List[Dict[str, Union[str, int, Optional[str]]]]:
        """ 
        Función Auxiliar Refactorizada: 
        1. Soporta DataProperties (ValueCost, ConstrainedDatatype).
        2. Prioriza el rango explícito en equivalent_to (belongsTo.some(Victim) -> Range: Victim).
        """
        componentes: List[Dict[str, Union[str, int, Optional[str]]]] = []
        contenido_a_analizar = segmento_restriccion.strip()
        nivel_actual_interno = nivel

        # 1. Manejo del operador Not()
        if contenido_a_analizar.startswith("Not("):
            rango_clean = self._limpiar_elemento(contenido_a_analizar).replace('(', ' ').replace(')', ' ').replace('.', ' ').strip()
            componentes.append({
                "level": nivel, 
                "type": "operator", 
                "element": "Not", 
                "description": "Negación (NOT)", 
                "range": rango_clean,
                "cardinality": None
            })
            nivel_actual_interno = nivel + 1
            parentesis_abiertos = 1
            contenido_not = ""
            for i in range(len("Not("), len(contenido_a_analizar)):
                char = contenido_a_analizar[i]
                if char == '(': parentesis_abiertos += 1
                elif char == ')': parentesis_abiertos -= 1
                if parentesis_abiertos == 0: break 
                contenido_not += char
            componentes.extend(self.analizar_expresion_owl_simplificada_dict_v5(contenido_not, is_internal_call=True, start_level=nivel_actual_interno))
            return componentes

        # 2. Análisis de restricciones (.some, .only, etc.)
        match_propiedad_inicial = re.search(r'\.(\w+)\.(some|only|value|min|max|exactly)\(', contenido_a_analizar)
        if not match_propiedad_inicial:
             match_propiedad_inicial = re.match(r'^(\w+)\.(some|only|value|min|max|exactly)\(', contenido_a_analizar)

        if match_propiedad_inicial:
            start_index = match_propiedad_inicial.start() 
            if contenido_a_analizar[start_index] == '.': start_index += 1 
            cuerpo_restriccion = contenido_a_analizar[start_index:].strip()
            
            while True:
                propiedad, cardinalidad_type, target_content_raw = None, None, None
                match = re.match(r'(\w+)\.(some|only|value|min|max|exactly)\s*\(', cuerpo_restriccion)
                if not match: break 
                    
                propiedad = match.group(1)
                cardinalidad_type = match.group(2)
                
                offset = match.end()
                parentesis_abiertos = 1
                contenido_real = ""
                for i in range(offset, len(cuerpo_restriccion)):
                    char = cuerpo_restriccion[i]
                    if char == '(': parentesis_abiertos += 1
                    elif char == ')': parentesis_abiertos -= 1
                    if parentesis_abiertos == 0: break
                    contenido_real += char
                target_content_raw = contenido_real.strip()
                
                # --- Procesamiento del Target y Cardinalidad ---
                target_content = target_content_raw
                description_suffix = f"{cardinalidad_type}"
                is_datatype = False

                if cardinalidad_type in ["min", "max", "exactly"]:
                    comma_index = -1
                    p_level = 0
                    for i, char in enumerate(target_content_raw):
                        if char == '(': p_level += 1
                        elif char == ')': p_level -= 1
                        elif char == ',' and p_level == 0:
                            comma_index = i; break
                    
                    if comma_index != -1:
                        cardinality_value = target_content_raw[:comma_index].strip()
                        target_content = target_content_raw[comma_index + 1:].strip()
                        description_suffix = f"{cardinalidad_type} {cardinality_value}"
                    else:
                        description_suffix = f"{cardinalidad_type} {target_content_raw}"
                        target_content = None
                        is_datatype = True 

                if target_content:
                    if (target_content.startswith("ConstrainedDatatype") or 
                        target_content in ["int", "integer", "decimal", "float", "string", "boolean"] or
                        cardinalidad_type == "value"):
                        is_datatype = True

                # --- LÓGICA DE RANGO REFACTORIZADA ---
                rango_nombres = []
                
                # A. Prioridad: Rango explícito simple (Lo que pediste)
                # Si target_content es "Victim", queremos "Victim", no "Person"
                use_explicit_target = False
                if target_content and not is_datatype:
                    # Verificamos que sea una clase simple (sin operadores ni restricciones anidadas)
                    if not (re.search(r'\.(some|only|value|min|max|exactly)\(', target_content) or 
                            "Not(" in target_content or 
                            "&" in target_content or 
                            "|" in target_content):
                        use_explicit_target = True
                        rango_nombres = [self._limpiar_elemento(target_content)]

                # B. Fallback: Definición de la ontología
                # Si es una expresión compleja o no pudimos determinar el simple, usamos el genérico
                if not rango_nombres:
                    try:
                        rango_nombres = self.get_object_property_detail(propiedad, "range")
                    except:
                        pass
                # -------------------------------------

                tipo_nodo = "data_property" if is_datatype else "object_property"

                componentes.append({
                    "level": nivel_actual_interno, 
                    "type": tipo_nodo,
                    "element": propiedad,
                    "description":  f"Propiedad: '{propiedad}' ({description_suffix})",
                    "range": rango_nombres, 
                    "cardinality": cardinalidad_type
                })

                nivel_siguiente = nivel_actual_interno + 1
                
                if target_content:
                    # Recursión y manejo de casos (Datatypes, Complejos, Simples)
                    if target_content.startswith("ConstrainedDatatype"):
                        data_info = self._parse_constrained_datatype(target_content)
                        restr_txt = ", ".join([f"{k}={v}" for k,v in data_info.get("constraints", {}).items()])
                        componentes.append({
                            "level": nivel_siguiente,
                            "type": "datatype_restriction",
                            "element": data_info.get("base_type", "datatype"),
                            "description": f"Restricción: {data_info.get('base_type')} [{restr_txt}]",
                            "range": None, "cardinality": None
                        })
                        break 

                    is_nested_complex = target_content.startswith("Not(") or re.search(r'\s+&|\s+\|', target_content)
                    match_next = re.search(r'\.(\w+)\.(some|only|value|min|max|exactly)\(', target_content)
                    
                    if is_nested_complex:
                        componentes.extend(self.analizar_expresion_owl_simplificada_dict_v5(target_content, is_internal_call=True, start_level=nivel_siguiente))
                        break 
                    elif match_next:
                        cuerpo_restriccion = target_content[match_next.start() + 1:].strip()
                        nivel_actual_interno = nivel_siguiente
                    else:
                        elem_clean = self._limpiar_elemento(target_content)
                        node_type = "literal_value" if (is_datatype or target_content[0].isdigit() or target_content.startswith('"')) else "entity_object"
                        componentes.append({
                            "level": nivel_siguiente, 
                            "type": node_type, 
                            "element": elem_clean,
                            "description": target_content,
                            "range": None, "cardinality": None 
                        })
                        break 
                else:
                    break 

        else:
            element_clean = self._limpiar_elemento(contenido_a_analizar)
            componentes.append({
                "level": nivel, 
                "type": "entity_object", 
                "element": element_clean, 
                "description": element_clean, 
                "range": None, "cardinality": None
            })

        return componentes

    ################################

    def _analizar_restriccion_anidada_dict_v5__1(self, segmento_restriccion: str, nivel: int, is_subject: bool = True) -> List[Dict[str, Union[str, int, Optional[str]]]]:
        """ 
        Función Auxiliar: Analiza restricciones anidadas y, CRUCIALMENTE, detecta y parsea
        DataProperties (como ValueCost) y ConstrainedDatatypes.
        """
        componentes: List[Dict[str, Union[str, int, Optional[str]]]] = []
        contenido_a_analizar = segmento_restriccion.strip()
        nivel_actual_interno = nivel

        # ---------------------------------------------------------
        # 1. Manejo del operador Not()
        # ---------------------------------------------------------
        if contenido_a_analizar.startswith("Not("):
            # Extracción visual simple para el nodo actual
            rango_clean = self._limpiar_elemento(contenido_a_analizar).replace('(', ' ').replace(')', ' ').replace('.', ' ').strip()
            
            componentes.append({
                "level": nivel, 
                "type": "operator", 
                "element": "Not", 
                "description": "Negación (NOT)", 
                "range": rango_clean,
                "cardinality": None
            })
            
            nivel_actual_interno = nivel + 1
            
            # Extracción robusta del contenido dentro del paréntesis de Not()
            parentesis_abiertos = 1
            contenido_not = ""
            for i in range(len("Not("), len(contenido_a_analizar)):
                char = contenido_a_analizar[i]
                if char == '(': parentesis_abiertos += 1
                elif char == ')': parentesis_abiertos -= 1
                
                if parentesis_abiertos == 0: break 
                contenido_not += char
            
            # Recursión hacia la función principal para manejar lo que haya dentro del NOT
            componentes.extend(self.analizar_expresion_owl_simplificada_dict_v5(contenido_not, is_internal_call=True, start_level=nivel_actual_interno))
            return componentes

        # ---------------------------------------------------------
        # 2. Análisis de restricciones de propiedad (.some, .only, .min, etc.)
        # ---------------------------------------------------------
        # Buscamos el patrón: .propiedad.operador( o al inicio propiedad.operador(
        match_propiedad_inicial = re.search(r'\.(\w+)\.(some|only|value|min|max|exactly)\(', contenido_a_analizar)
        if not match_propiedad_inicial:
             match_propiedad_inicial = re.match(r'^(\w+)\.(some|only|value|min|max|exactly)\(', contenido_a_analizar)

        if match_propiedad_inicial:
            
            # Determinar punto de inicio del cuerpo de la restricción
            start_index = match_propiedad_inicial.start() 
            if contenido_a_analizar[start_index] == '.':
                start_index += 1 
            
            cuerpo_restriccion = contenido_a_analizar[start_index:].strip()
            
            # Bucle para procesar encadenamientos (aunque owlready suele anidar, no encadenar linealmente)
            while True:
                propiedad = None
                cardinalidad_type = None
                target_content_raw = None
                
                # Match: Propiedad.Cardinalidad(Contenido)
                # Usamos un regex inicial pero luego extraemos manualmente por paréntesis para seguridad
                match = re.match(r'(\w+)\.(some|only|value|min|max|exactly)\s*\(', cuerpo_restriccion)
                
                if not match:
                    break 
                    
                propiedad = match.group(1)
                cardinalidad_type = match.group(2)
                
                # Extraer el contenido dentro de los paréntesis balanceados
                offset = match.end()
                parentesis_abiertos = 1
                contenido_real = ""
                chars_procesados = offset
                
                for i in range(offset, len(cuerpo_restriccion)):
                    char = cuerpo_restriccion[i]
                    chars_procesados += 1
                    if char == '(': parentesis_abiertos += 1
                    elif char == ')': parentesis_abiertos -= 1
                    
                    if parentesis_abiertos == 0: break
                    contenido_real += char
                
                target_content_raw = contenido_real.strip()
                
                # --- LOGICA DE PARSEO DEL TARGET (Aquí solucionamos el problema de ValueCost) ---
                
                target_content = target_content_raw
                description_suffix = f"{cardinalidad_type}"
                is_datatype = False

                # A. Manejo de Cardinalidad Cualificada vs No Cualificada (min/max/exactly)
                if cardinalidad_type in ["min", "max", "exactly"]:
                    # Buscar si hay una coma separando número y clase: min(1, Clase)
                    # Cuidado: ConstrainedDatatype también tiene comas dentro
                    comma_index = -1
                    p_level = 0
                    for i, char in enumerate(target_content_raw):
                        if char == '(': p_level += 1
                        elif char == ')': p_level -= 1
                        elif char == ',' and p_level == 0:
                            comma_index = i
                            break
                    
                    if comma_index != -1:
                        # Es cualificada: min(N, Clase/Datatype)
                        cardinality_value = target_content_raw[:comma_index].strip()
                        target_content = target_content_raw[comma_index + 1:].strip()
                        description_suffix = f"{cardinalidad_type} {cardinality_value}"
                    else:
                        # Es no cualificada o simple: min(N)
                        description_suffix = f"{cardinalidad_type} {target_content_raw}"
                        target_content = None # No hay "destino" que recorrer, es un número
                        is_datatype = True # Técnicamente es un valor literal

                # B. Detección de DataProperty / Datatype
                # Verificamos si el contenido apunta a un tipo de dato restringido o primitivo
                if target_content:
                    if (target_content.startswith("ConstrainedDatatype") or 
                        target_content in ["int", "integer", "decimal", "float", "string", "boolean", "date", "dateTime"] or
                        cardinalidad_type == "value"): # value(400.0)
                        is_datatype = True

                # Intentar obtener el rango real de la ontología si es posible para confirmar tipo
                rango_nombres = []
                try:
                    rango_nombres = self.get_object_property_detail(propiedad, "range")
                except:
                    pass

                tipo_nodo = "data_property" if is_datatype else "object_property"

                # Añadir el nodo de la PROPIEDAD
                componentes.append({
                    "level": nivel_actual_interno, 
                    "type": tipo_nodo,
                    "element": propiedad,
                    "description":  f"Propiedad: '{propiedad}' ({description_suffix})",
                    "range": rango_nombres, 
                    "cardinality": cardinalidad_type
                })
                print(f"_analizar_restriccion_anidada_dict_v5: CASO 1: rango: {rango_nombres} - suffix: {description_suffix}")
                nivel_siguiente = nivel_actual_interno + 1
                
                # --- Proceso Recursivo del TARGET ---
                if target_content:
                    
                    # CASO 1: ConstrainedDatatype (SOLUCIÓN PRINCIPAL)
                    # Ejemplo: ConstrainedDatatype(decimal, min_inclusive=400.0)
                    if target_content.startswith("ConstrainedDatatype"):
                        data_info = self._parse_constrained_datatype(target_content)
                        
                        # Crear descripción legible de las restricciones (ej: min_inclusive: 400.0)
                        restricciones_txt = ", ".join([f"{k}={v}" for k,v in data_info.get("constraints", {}).items()])
                        
                        componentes.append({
                            "level": nivel_siguiente,
                            "type": "datatype_restriction", # Tipo específico para el frontend
                            "element": data_info.get("base_type", "datatype"),
                            "description": f"Restricción de Dato: {data_info.get('base_type')} [{restricciones_txt}]",
                            "range": None,
                            "cardinality": None,
                            "raw_value": data_info # Guardamos toda la info parseada
                        })
                        break # Fin de rama (es una hoja)

                    # CASO 2: Expresiones Lógicas Anidadas (AND, OR, NOT dentro de un some)
                    # Detectamos & o | fuera de paréntesis internos
                    is_complex = False
                    p_level = 0
                    if target_content.startswith("Not("):
                        is_complex = True
                    else:
                        for char in target_content:
                            if char == '(': p_level +=1
                            elif char == ')': p_level -=1
                            elif char in ['&', '|'] and p_level == 0:
                                is_complex = True
                                break
                    
                    # CASO 3: Otra Restricción Anidada (.prop.some(...))
                    match_next = re.search(r'\.(\w+)\.(some|only|value|min|max|exactly)\(', target_content)
                    print(f"_analizar_restriccion_anidada_dict_v5: CASO 3: {target_content} - {is_complex} -{match_next}")
                    if is_complex:
                        # Delegar a la función principal
                        componentes.extend(self.analizar_expresion_owl_simplificada_dict_v5(target_content, is_internal_call=True, start_level=nivel_siguiente))
                        break 
                        
                    elif match_next:
                        # Preparar la siguiente iteración del while con el contenido interno
                        cuerpo_restriccion = target_content[match_next.start() + 1:].strip()
                        nivel_actual_interno = nivel_siguiente
                        # Continue loop
                    
                    else:
                        # CASO 4: Entidad Simple (Clase) o Valor Literal
                        elem_clean = self._limpiar_elemento(target_content)
                        print(f"_analizar_restriccion_anidada_dict_v5: CASO 4: {elem_clean} - {target_content}")
                        
                        # Distinguir valor literal de clase
                        if is_datatype or target_content[0].isdigit() or target_content.startswith('"'):
                            node_type = "literal_value"
                        else:
                            node_type = "entity_object"
                            
                        componentes.append({
                            "level": nivel_siguiente, 
                            "type": node_type, 
                            "element": elem_clean,
                            "description": target_content,
                            "range": None,
                            "cardinality": None 
                        })
                        break 
                else:
                    break # Fin del while

        else:
            # ---------------------------------------------------------
            # 3. Caso Base: Entidad Simple (Clase Raíz sin restricciones)
            # ---------------------------------------------------------
            element_clean = self._limpiar_elemento(contenido_a_analizar)
            componentes.append({
                "level": nivel, 
                "type": "entity_object", 
                "element": element_clean, 
                "description": element_clean, 
                "range": None,
                "cardinality": None
            })

        return componentes
    

    #############################################

    def _analizar_restriccion_anidada_dict_v5__(self, segmento_restriccion: str, nivel: int, is_subject: bool = True) -> List[Dict[str, Union[str, int, Optional[str]]]]:
        """ 
        Función auxiliar generalizada para analizar expresiones complejas.
        """
        componentes: List[Dict[str, Union[str, int, Optional[str]]]] = []
        contenido_a_analizar = segmento_restriccion.strip()
        nivel_actual_interno = nivel

        # 1. Manejar el operador Not()
        if contenido_a_analizar.startswith("Not("):
            rango = self._limpiar_elemento(contenido_a_analizar)
            rango = rango.replace('(', ' ').replace(')', ' ').replace('.', ' ').strip()
            componentes.append({
                "level": nivel, 
                "type": "operador", 
                "element": "Not", 
                "description": "Negación (NOT)", 
                "range": rango,
                "cardinality": None
            })
            
            nivel_actual_interno = nivel + 1
            
            # Extracción robusta del contenido dentro del Not()
            parentesis_abiertos = 1
            contenido_not = ""
            for i in range(len("Not("), len(contenido_a_analizar)):
                char = contenido_a_analizar[i]
                if char == '(':
                    parentesis_abiertos += 1
                elif char == ')':
                    parentesis_abiertos -= 1
                    if parentesis_abiertos == 0:
                        break 
                contenido_not += char
            
            # Llamada recursiva: el contenido de Not debe ser analizado por la función principal
            componentes.extend(self.analizar_expresion_owl_simplificada_dict_v5(contenido_not, is_internal_call=True, start_level=nivel_actual_interno))
            return componentes

        # 2. Análisis de restricciones de propiedad (some, only, min, max, etc.)
        match_propiedad_inicial = re.search(r'\.(\w+)\.(some|only|value|min|max|exactly)\(', contenido_a_analizar)
        
        if match_propiedad_inicial:
            
            # 2a. Tratar la entidad/expresión que PRECEDE la restricción (sujeto)
            # Se omite por ser el prefijo de la ontología (SCPO...) o el sujeto directo de la restricción.
            
            # 2b. Iniciar el cuerpo de la restricción
            cuerpo_restriccion = contenido_a_analizar[match_propiedad_inicial.start() + 1:].strip()
            
            # 3. Iterar sobre las restricciones anidadas
            while True:
                propiedad, cardinalidad_type, target_content = None, None, None
                
                # 3a. Match para Cardinalidad (min, max, exactly) o Existencial/Universal (some, only, value)
                # El patrón simplificado captura Propiedad.CardinalidadType(Contenido)
                match = re.match(r'(\w+)\.(some|only|value|min|max|exactly)\s*\((.*)\)', cuerpo_restriccion, re.DOTALL)
                
                if not match:
                    break # No match, salir del bucle while
                    
                propiedad = match.group(1)
                cardinalidad_type = match.group(2)
                contenido_con_parentesis = match.group(3)
                
                # --- Corrección robusta de paréntesis para obtener el contenido real ---
                parentesis_abiertos = 0
                contenido_real = ""
                for char in contenido_con_parentesis:
                    if char == '(':
                        parentesis_abiertos += 1
                    elif char == ')':
                        if parentesis_abiertos == 0:
                            break 
                        parentesis_abiertos -= 1
                    contenido_real += char
                target_content_raw = contenido_real.strip()
                # ----------------------------------------------------------------------
                
                # 4. Proceso de Target Content (para manejar N, Class/Datatype)
                if cardinalidad_type in ["min", "max", "exactly"]:
                    comma_index = -1
                    parenthesis_level = 0
                    for i, char in enumerate(target_content_raw):
                        if char == '(':
                            parenthesis_level += 1
                        elif char == ')':
                            parenthesis_level -= 1
                        elif char == ',' and parenthesis_level == 0:
                            comma_index = i
                            break
                    
                    if comma_index != -1:
                        # Caso: min(N, Class) -> Qualified Cardinality Restriction
                        cardinality_value = target_content_raw[:comma_index].strip()
                        target_content = target_content_raw[comma_index + 1:].strip()
                        description_target = f"{cardinalidad_type} {cardinality_value}, target: {self._limpiar_elemento(target_content)}"
                    else:
                        # Caso: min(N) -> Unqualified Cardinality Restriction (o error)
                        target_content = target_content_raw
                        description_target = f"{cardinalidad_type} {target_content}"
                else:
                    # Caso: some(Class/Expression)
                    target_content = target_content_raw
                    description_target = f"{cardinalidad_type} {self._limpiar_elemento(target_content)}"
                
                # --- Adición del Elemento de Restricción ---
                if target_content.__contains__("(") and target_content.__contains__(")"):
                        rango = self.get_object_property_detail(propiedad, "range") 
                else:
                    rango = [self._limpiar_elemento(target_content)]
                componentes.append({
                    "level": nivel_actual_interno, 
                    "type": "objeto", 
                    "element": propiedad,
                    "description":  f"Propiedad: '{propiedad}' ({description_target})",
                    "range": rango, 
                    "cardinality": cardinalidad_type
                })

                nivel_siguiente = nivel_actual_interno + 1
                
                # --- Proceso Recursivo/Iterativo del Target ---
                if target_content:
                    
                    # Check for nested logical operators (&, |) or Not()
                    is_nested_complex_expression = target_content.startswith("Not(") or re.search(r'\s+&|\s+\|', target_content)
                    
                    # Check for a nested restriction
                    match_next_restriction = re.search(r'\.(\w+)\.(some|only|value|min|max|exactly)\(', target_content)
                    
                    if is_nested_complex_expression:
                        # Si el target es una expresión compleja (AND/OR/NOT), llamamos a la función principal
                        componentes.extend(self.analizar_expresion_owl_simplificada_dict_v5(target_content, is_internal_call=True, start_level=nivel_siguiente))
                        break # El análisis se transfiere a la función principal
                        
                    elif match_next_restriction:
                        # Si es una restricción anidada, preparamos la siguiente iteración
                        cuerpo_restriccion = target_content[match_next_restriction.start() + 1:].strip()
                        nivel_actual_interno = nivel_siguiente
                    
                    else:
                        # Es una Entidad simple (Clase/Datatype)
                        element_type = "datatype" if target_content.startswith("ConstrainedDatatype") else "entidad"
                            
                        componentes.append({
                            "level": nivel_siguiente, 
                            "type": element_type, 
                            "element": self._limpiar_elemento(target_content),
                            "description": target_content,
                            "range": None,
                            "cardinality": None 
                        })
                        break 
                
                else:
                    break 

        else:
            # Es una entidad simple (sin restricciones ni Not)
            componentes.append({
                "level": nivel, 
                "type": "entidad", 
                "element": self._limpiar_elemento(contenido_a_analizar), 
                "description": self._limpiar_elemento(contenido_a_analizar), 
                "range": None,
                "cardinality": None
            })
        return componentes
    
    def dfs_equivalent_and_subclasses(self, start_class_name: str, max_depth: Optional[int] = None):
        """
        Recorrido DFS: dada una clase raíz, encuentra:
        - Sus subclases
        - Todas las clases que la referencian en 'equivalent_to'
        Recorre en profundidad hacia abajo combinando ambas relaciones.
        """
        visited = set()
        classes = {}
        traversal_path = []
        stack = [(start_class_name, 0, None, "root")]
        max_depth_reached = 0

        # Precalcular todas las clases de la ontología
        all_classes = list(self.ontology.classes())

        while stack:
            current_class_name, depth, parent, relation_type = stack.pop()
            if max_depth is not None and depth > max_depth:
                continue
            if current_class_name in visited:
                continue

            visited.add(current_class_name)
            max_depth_reached = max(max_depth_reached, depth)

            # Obtener el objeto de la clase
            current_class = getattr(self.ontology, current_class_name, None)
            if current_class is None:
                continue

            # Extraer datos de la clase
            class_data = self._extract_class_data(current_class)
            class_data["dfs_extended_info"] = {
                "visit_order": len(visited),
                "depth_level": depth,
                "discovered_via": relation_type,
                "parent": parent if parent else None
            }
            classes[current_class_name] = class_data
            traversal_path.append({
                "class": current_class_name,
                "depth": depth,
                "parent": parent,
                "relation": relation_type,
                "visit_order": len(visited)
            })

            # 1. Subclases directas
            for subclass in current_class.subclasses():
                if subclass.name not in visited:
                    stack.append((subclass.name, depth + 1, current_class_name, "subclass"))

            # 2. Dependencias por 'equivalent_to' inverso
            for cls in all_classes:
                # print(f"✓ Equivalentes de : {cls.name}")
                for eq in getattr(cls, "equivalent_to", []):
                    # print(f"✓ Elemetssssssss de : {eq}")
                    if hasattr(eq, "name") and eq.name == current_class_name:
                        if cls.name not in visited:
                            stack.append((cls.name, depth + 1, current_class_name, "equivalent_to_inverse"))
                    elif hasattr(eq, "Classes"):
                        for sub_eq in eq.Classes:
                            if hasattr(sub_eq, "name") and sub_eq.name == current_class_name:
                                if cls.name not in visited:
                                    stack.append((cls.name, depth + 1, current_class_name, "equivalent_complex_inverse"))

        return {
            "classes": classes,
            "traversal_path": traversal_path,
            "max_depth_reached": max_depth_reached
        }
    

    def dfs_subclasses(self, start_class_name: str, max_depth: Optional[int] = None):
        """
        Recorrido DFS: dada una clase raíz, encuentra:
        - Sus subclases
        - Todas las clases que la referencian en 'equivalent_to'
        Recorre en profundidad hacia abajo combinando ambas relaciones.
        """
        visited = set()
        classes = {}
        traversal_path = []
        stack = [(start_class_name, 0, None, "root")]
        max_depth_reached = 0

        # Precalcular todas las clases de la ontología
        all_classes = list(self.ontology.classes())

        while stack:
            current_class_name, depth, parent, relation_type = stack.pop()
            if max_depth is not None and depth > max_depth:
                continue
            if current_class_name in visited:
                continue

            visited.add(current_class_name)
            max_depth_reached = max(max_depth_reached, depth)

            # Obtener el objeto de la clase
            current_class = getattr(self.ontology, current_class_name, None)
            if current_class is None:
                continue

            # Extraer datos de la clase
            class_data = self._extract_class_data(current_class)
            class_data["dfs_extended_info"] = {
                "visit_order": len(visited),
                "depth_level": depth,
                "discovered_via": relation_type,
                "parent": parent if parent else None
            }
            classes[current_class_name] = class_data
            traversal_path.append({
                "class": current_class_name,
                "depth": depth,
                "parent": parent,
                "relation": relation_type,
                "visit_order": len(visited)
            })

            # 1. Subclases directas
            for subclass in current_class.subclasses():
                if subclass.name not in visited:
                    stack.append((subclass.name, depth + 1, current_class_name, "subclass"))

        return {
            "classes": classes,
            "traversal_path": traversal_path,
            "max_depth_reached": max_depth_reached
        }

    def _extract_restrictions_recursively(self, expression, restriction_list: list):
        """Helper para extraer objetos Restriction de expresiones anidadas (And, Or, Not)."""
        
        # Si la expresión es directamente una restricción, la añadimos y terminamos la rama.
        if isinstance(expression, Restriction):
            restriction_list.append(expression)
            return

        # Si es una intersección (And) o unión (Or), iteramos sobre sus componentes (.Classes)
        if isinstance(expression, (And, Or)) and hasattr(expression, 'Classes'):
            for sub_expression in expression.Classes:
                self._extract_restrictions_recursively(sub_expression, restriction_list)

        # Si es un complemento (Not), examinamos el elemento negado (.Class)
        elif isinstance(expression, Not) and hasattr(expression, 'Class'):
            self._extract_restrictions_recursively(expression.Class, restriction_list)
            
        # Si es una clase nombrada o un tipo simple (ej. Thing), no hacemos nada más.

    # Dentro de la clase OntologyTraversal:

    def get_object_property_detail(self, nombre_del_objeto: str, nombre_de_la_propiedad: str) -> List[str]:
        """
        Extrae el dominio o el rango de una propiedad de objeto en la ontología.

        Args:
            nombre_del_objeto (str): El nombre corto de la propiedad de objeto (e.g., "belongsTo").
            nombre_de_la_propiedad (str): El detalle a extraer: "domain" o "range".

        Returns:
            List[str]: Una lista con los nombres cortos de las clases del dominio/rango.
                    Devuelve una lista vacía si la propiedad o el detalle no existen.
        """
        # 1. Validación de la ontología y del parámetro de propiedad
        if self.ontology is None:
             print("Error: Ontología no cargada en la instancia de OntologyTraversal.")
             return []
             
        prop_key = nombre_de_la_propiedad.lower()
        if prop_key not in ["domain", "range"]:
            print("Error: El parámetro 'nombre_de_la_propiedad' debe ser 'domain' o 'range'.")
            return []

        # 2. Acceso al objeto/propiedad mediante Acceso Directo (Opción 1)
        # owlready2 permite acceder a las entidades por su nombre corto como atributo de la ontología.
        prop_objeto = getattr(self.ontology, nombre_del_objeto, None)

        if prop_objeto is None:
            print(f"Error: No se encontró la entidad '{nombre_del_objeto}' en la ontología.")
            return []

        # 3. Acceder al atributo correspondiente (.domain o .range)
        try:
            # Se usa getattr para acceder dinámicamente al atributo 'domain' o 'range'
            detail_list = getattr(prop_objeto, prop_key)
            
            # 4. Extraer solo el nombre corto (.name) de cada clase en la lista
            result_names = [entity.name for entity in detail_list]
            return result_names
            
        except AttributeError:
            # Esto captura si la entidad encontrada no es una propiedad (ej. es una clase) 
            # y por lo tanto no tiene los atributos .domain o .range.
            print(f"Error: La entidad '{nombre_del_objeto}' no tiene el atributo '{prop_key}' o no es una propiedad.")
            return []

    def analizar_expresion_owl_simplificada_dict(self, expresion: str) -> List[Dict[str, Union[str, int]]]:
        """
        Función principal para analizar la expresión OWL, listar componentes en diccionario,
        mantener el anidamiento y eliminar la referencia a la ontología.
        """
        
        # Separar por el operador lógico global '&' (Nivel 0)
        conjuntos = [c.strip() for c in expresion.split('&')]
        
        componentes_anidados: List[Dict[str, Union[str, int]]] = []
        
        for i, conjunto in enumerate(conjuntos):
            
            # Analizar cada conjunto de forma independiente
            componentes_anidados.extend(self._analizar_restriccion_anidada_dict_v4(conjunto, 0))
                
            # Insertar el operador lógico (si no es el último conjunto)
            if i < len(conjuntos) - 1:
                componentes_anidados.append({
                    "level": 0, 
                    "type": "operador", 
                    "element": "&", 
                    "description" : "AND ('&')",
                    "range": None,
                    "cardinality": None
                })

        return componentes_anidados

    def get_all_restrictions(self) -> List[Restriction]:
        """
        Recupera una lista con todos los objetos Restriction (restricciones existenciales,
        universales, de cardinalidad, etc.) definidos en los axiomas (is_a y equivalent_to)
        de las clases nombradas de la ontología.

        Returns:
            List[Restriction]: Lista de objetos Restriction de owlready2.
        """
        if not self.ontology:
            print("Error: Ontología no cargada.")
            return []
            
        all_restrictions = []
        
        # 1. Iterar sobre todas las clases nombradas en la ontología
        for cls in self.ontology.classes():
            # Concatenar axiomas de superclase y equivalencia
            axioms = list(cls.is_a) + list(getattr(cls, 'equivalent_to', []))

            # 2. Procesar cada axioma para extraer restricciones, incluyendo anidamientos
            for axiom in axioms:
                self._extract_restrictions_recursively(axiom, all_restrictions)
                
        # 3. Eliminar duplicados si las mismas restricciones anónimas se usan en varios axiomas
        # Se usa set() para asegurar que cada objeto Restriction es listado solo una vez.
        unique_restrictions = list(set(all_restrictions))

        # for restriction in unique_restrictions:
        #     propiedad = restriction.property
        #     print(f"Propiedad analizada: {propiedad.name}")
        #     print(f"\n📌 Restriccion: {propiedad.name} (Domain: {propiedad.domain}, Range: {propiedad.range})")
        
        return unique_restrictions
    
  
def print_ontology_structure(self):
    """Muestra la estructura general de la ontología"""
    if not self.ontology:
        print("✗ No hay ontología cargada")
        return
    
    print("\n📊 ESTRUCTURA DE LA ONTOLOGÍA")
    print("=" * 40)
    
    # Clases principales (sin superclases excepto Thing)
    root_classes = [cls for cls in self.ontology.classes() 
                    if cls != Thing and 
                    (not cls.is_a or all(parent == Thing for parent in cls.is_a))]
    
    print(f"🏗️  Clases raíz: {[cls.name for cls in root_classes]}")
    print(f"📦 Total de clases: {len(list(self.ontology.classes()))}")
    print(f"🔸 Total de instancias: {len(list(self.ontology.individuals()))}")
    
    return root_classes


def main():
    """Función principal de demostración"""
    print("🦉 RECORRIDO BFS EN ONTOLOGÍA CON OWLREADY2")
    print("=" * 60)
    
    # Crear el traversal
    traversal = OntologyTraversal()
    
    # Opción 1: Cargar ontología existente (descomenta si tienes un archivo OWL)
    # try:
    #     traversal.load_ontology("ruta/a/tu/ontologia.owl")
    # except:
    #     print("No se pudo cargar la ontología, usando ejemplo...")
    #     traversal.create_sample_ontology()
    
    # Opción 2: Usar ontología de ejemplo
    traversal.create_sample_ontology()
    
    # Agregar algunas equivalencias de ejemplo manualmente para demostración
    try:
        with traversal.ontology:
            # Crear equivalencias de ejemplo usando expresiones lógicas
            Animal = traversal.ontology.Animal
            Bird = traversal.ontology.Bird
            Mammal = traversal.ontology.Mammal
            
            # Ejemplo: crear una clase equivalente simple
            class WingedCreature(Thing): pass
            # En una ontología real, podrías hacer: Bird.equivalent_to = [WingedCreature]
            
        print("✓ Equivalencias de ejemplo añadidas")
    except Exception as e:
        print(f"ℹ️  No se pudieron crear equivalencias de ejemplo: {e}")
    
    # Mostrar estructura
    root_classes = traversal.print_ontology_structure()
    
    # Ejemplo 1: Recorrido BFS de subclases desde Animal
    if hasattr(traversal.ontology, 'Animal'):
        result_classes = traversal.bfs_traversal_subclasses('Animal', max_depth=3)
        
        print(f"\n📈 RESUMEN DEL RECORRIDO")
        print(f"Total de clases visitadas: {len(result_classes)}")
        
        # Mostrar por niveles
        levels = {}
        for cls, level, parent in result_classes:
            if level not in levels:
                levels[level] = []
            levels[level].append(cls.name)
        
        for level in sorted(levels.keys()):
            print(f"  Nivel {level}: {levels[level]}")
    
    # Ejemplo 2: Recorrido de instancias
    if hasattr(traversal.ontology, 'Animal'):
        instances_result = traversal.bfs_traversal_instances('Animal')
        
        if instances_result:
            print(f"\n📋 INSTANCIAS ENCONTRADAS:")
            for instance, cls in instances_result:
                print(f"  🔸 {instance.name} es instancia de {cls.name}")
        else:
            print("\n📋 No se encontraron instancias en la jerarquía")
    
    print(f"\n💡 NOTA: Para ver equivalencias más complejas, carga una ontología")
    print(f"    real que contenga definiciones equivalent_to con expresiones lógicas.")
    
    # Ejemplo 3: Exportar a JSON
    print(f"\n📄 EXPORTANDO DATOS A JSON...")
    
    # Exportar desde la clase Animal
    json_file = traversal.export_classes_to_json(
        start_class='Animal',
        output_file='ejemplo_ontologia_animal.json',
        max_depth=3,
        include_metadata=True
    )
    
    # También puedes exportar toda la ontología
    # json_file_all = traversal.export_classes_to_json(
    #     start_class=None,  # Todas las clases
    #     output_file='ontologia_completa.json'
    # )
    
    # Ejemplo de carga del JSON exportado
    try:
        loaded_data = traversal.load_json_export(json_file)
        print(f"\n🔍 EJEMPLO DE DATOS CARGADOS DEL JSON:")
        
        # Mostrar información de algunas clases
        classes_data = loaded_data.get("classes", {})
        sample_classes = list(classes_data.keys())[:3]  # Primeras 3 clases
        
        for class_name in sample_classes:
            class_info = classes_data[class_name]
            print(f"\n📋 Clase: {class_name}")
            print(f"   - IRI: {class_info.get('iri', 'N/A')}")
            print(f"   - Superclases: {[sc['name'] for sc in class_info.get('superclases', [])]}")
            print(f"   - Subclases: {[sc['name'] for sc in class_info.get('subclases', [])]}")
            print(f"   - Equivalencias: {len(class_info.get('equivalent_classes', []))}")
            
            if class_info.get('equivalent_classes'):
                for eq in class_info['equivalent_classes'][:2]:  # Primeras 2 equivalencias
                    print(f"     • {eq.get('type', 'unknown')}: {eq.get('description', 'N/A')}")
    
    except Exception as e:
        print(f"⚠️  No se pudo cargar el JSON exportado: {e}")

if __name__ == "__main__":
    main()
