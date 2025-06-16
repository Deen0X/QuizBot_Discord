import os
import json
import random
import sys
from utils import Utils

class EvalPicker:
    def __init__(self):
        self.config = Utils.load_config()
        self.SUFIX_MODULE = self.config.get("SUFIX_EVALS_NAME", "")
        self.SUFIX_AVAILABLE = "_disponibles"

    def normalize_module_name(self, module_name):
        """Añade sufijo al nombre del módulo si no lo tiene"""
        if not module_name.endswith(self.SUFIX_MODULE):
            return f"{module_name}{self.SUFIX_MODULE}"
        return module_name

    def normalize_unit_name(self, unit_name):
        """Añade 'Unidad ' al número si no está presente"""
        if unit_name and not unit_name.startswith("Unidad "):
            return f"Unidad {unit_name.strip()}"
        return unit_name

    def load_module_questions(self, module_name):
        """Carga el JSON de preguntas del módulo especificado."""
        normalized_name = self.normalize_module_name(module_name)
        base_path = Utils.get_base_path("EVALS")
        json_path = os.path.join(base_path, f"{normalized_name}.json")
        if not os.path.exists(json_path):
            return None
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def find_question_by_id(self, questions_data, question_id):
        """Busca una pregunta específica por ID en todo el módulo"""
        q_num = str(question_id)
        for q in questions_data["preguntas"]:
            if q["numero"] == q_num:
                return q
        return None
    
    def pick_questions(self, module="", unit="", question_id="", count=1):
        """Selecciona preguntas según los filtros."""
        # 1. Determinar módulo
        if not module:
            modules = [f.replace(self.SUFIX_MODULE, "").replace(".json", "") 
                      for f in os.listdir(Utils.get_base_path("EVALS")) 
                      if f.endswith(f"{self.SUFIX_MODULE}.json")]
            if not modules:
                return {"error": "No modules found"}
            module = random.choice(modules)
        
        normalized_module = self.normalize_module_name(module)
        
        # 2. Cargar preguntas
        questions_data = self.load_module_questions(normalized_module)
        if not questions_data:
            return {"error": "Module not found"}
        
        # 3. Caso especial: búsqueda directa por ID (ignora disponibilidad)
        if question_id:
            question = self.find_question_by_id(questions_data, question_id)
            if not question:
                return {"error": f"Question ID {question_id} not found"}
            return {
                "module": module,
                "preguntas": [question],
                "total_preguntas": 1,
                "note": "Question fetched directly (ignored availability)"
            }
        
        # 4. Proceso normal con sistema de disponibilidad
        normalized_unit = self.normalize_unit_name(unit) if unit else ""
        available = self.load_availability_file(normalized_module)
        if not available:
            available = self.reset_availability(normalized_module)
        
        # Filtrar por unidad si se especifica
        filtered = []
        for q_id in available:
            q_unit, q_num = q_id.split("-")
            
            if normalized_unit and q_unit != normalized_unit:
                continue
            
            filtered.append((q_unit, q_num))
        
        # Seleccionar preguntas aleatorias
        if not filtered:
            if normalized_unit:  # Resetear solo esta unidad
                self.reset_availability(normalized_module)
                return self.pick_questions(module, unit, question_id, count)
            return {"error": "No questions available"}
        
        random.shuffle(filtered)
        selected_ids = filtered[:count]
        
        # Preparar resultado
        result = {
            "module": module,
            "preguntas": [],
            "total_preguntas": 0
        }
        
        for q_unit, q_num in selected_ids:
            q_id = f"{q_unit}-{q_num}"
            available.remove(q_id)
            
            # Buscar la pregunta completa
            for q in questions_data["preguntas"]:
                if (q["numero"] == q_num and 
                    self.normalize_unit_name(q["origen"]["unidad"]) == q_unit):
                    result["preguntas"].append(q)
                    result["total_preguntas"] += 1
                    break
        
        # Guardar disponibilidad actualizada
        self.save_availability(normalized_module, available)
        
        return result
    
    def load_availability_file(self, module_name):
        """Carga el archivo de disponibilidad"""
        base_path = Utils.get_base_path("EVALS")
        availability_file = os.path.join(base_path, f"{module_name}{self.SUFIX_AVAILABLE}.json")
        if not os.path.exists(availability_file):
            return None
        with open(availability_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_availability(self, module_name, available_list):
        """Guarda el archivo de disponibilidad"""
        base_path = Utils.get_base_path("EVALS")
        availability_file = os.path.join(base_path, f"{module_name}{self.SUFIX_AVAILABLE}.json")
        with open(availability_file, "w", encoding="utf-8") as f:
            json.dump(available_list, f, indent=2)
    
    def reset_availability(self, module_name):
        """Reinicia las preguntas disponibles para un módulo."""
        questions_data = self.load_module_questions(module_name)
        if not questions_data:
            return []
        
        available = []
        for q in questions_data["preguntas"]:
            unit = self.normalize_unit_name(q["origen"]["unidad"])
            num = q["numero"]
            available.append(f"{unit}-{num}")
        
        self.save_availability(module_name, available)
        return available

if __name__ == "__main__":
    picker = EvalPicker()
    
    # Procesar argumentos
    args = sys.argv[1:]
    module = args[0] if len(args) > 0 else ""
    unit = args[1] if len(args) > 1 else ""
    question_id = args[2] if len(args) > 2 else ""
    count = int(args[3]) if len(args) > 3 else 1
    
    questions = picker.pick_questions(module, unit, question_id, count)
    print(json.dumps(questions, indent=2, ensure_ascii=False))