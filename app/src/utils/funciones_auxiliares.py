import os
import json

RUBRICA_CRITICO_EVALUADOR_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "Rubricas", "rubrica_errores.json")
RUBRICA_DEMOSTRADOR_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "Ejemplos", "ejemplos_ejercicios.json")

def cargar_rubrica_demostrador():
    try:
        with open(RUBRICA_DEMOSTRADOR_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar la rúbrica del Agente Demostrador: {e}")
        return {}
    
def cargar_rubrica_critico_evaluador():
    try:
        with open(RUBRICA_CRITICO_EVALUADOR_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar la rúbrica del Agente Crítico/Evaluador: {e}")
        return {}
    
def limpiar_rubrica(ejemplos):
    rubrica_limpia = {}
    for key, data in ejemplos.items():
        rubrica_limpia[key] = {
            "titulo": data.get("titulo", ""),
            "descripcion":[],
            "reglas_de_penalizacion":[]
        }
        for ej in data.get("ejemplos", []):
            rubrica_limpia[key]["descripcion"].append(
                ej.get("problema", "") 
            )
            rubrica_limpia[key]["reglas_de_penalizacion"].append(
                ej.get("explicacion", "") 
            )
    return rubrica_limpia