import os
import json
import random
import sys
from utils import Utils

class ContentPicker:
    def __init__(self):
        self.config = Utils.load_config()
        self.MIN_ELEGIBLE = self.config.get("MIN_ELEGIBLE", 50)
        self.MIN_AUXILIAR = self.config.get("MIN_AUXILIAR", 30)
        self.SUFIX_MODULE = self.config.get("SUFIX_CONTENTS_NAME", "")
        self.BASE_PATH = self.config.get("BASE_PATH", "")

    def _load_exceptions(self, module: str = ""):
        """Carga las excepciones desde el archivo JSON."""
        exceptions_path_module = os.path.join(self.BASE_PATH, "DATA", "CONTENTS", f"{module}_exceptions.json")
        exceptions_path_general = os.path.join(self.BASE_PATH, "DATA", "CONTENTS", "CONTENTS_exceptions.json")
        #exceptions_path = os.path.join(os.path.dirname(__file__), "exceptions_CONTENTS.json")

        exceptions_path = exceptions_path_general if not os.path.exists(exceptions_path_module) else exceptions_path_module

        try:
            with open(exceptions_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                #print(f"Exceptions: {content}")
                return content
        except (FileNotFoundError, json.JSONDecodeError):
            return {"excluded_types": [], "excluded_ids": []}

    def is_excluded(self, paragraph):
        """Verifica si un párrafo debe excluirse."""
        return (
            paragraph.get("type", "") in self.exceptions["excluded_types"] or
            paragraph.get("id", "") in self.exceptions["excluded_ids"]
        )

    def get_valid_paragraphs(self, contents, unit_filter=None):
        """Filtra párrafos excluyendo los no deseados."""
        valid_paragraphs = []
        for content in contents["contenidos"]:
            if unit_filter and content["unidad"] != self.normalize_unit_name(unit_filter):
                continue
            
            for section in content["sections"]:
                for subsection in section["subsections"]:
                    if subsection.get("type", "") in self.exceptions["excluded_types"]:
                        continue  # Excluir toda la subsección
                    
                    for idx, paragraph in enumerate(subsection["paragraphs"]):
                        if not self.is_excluded(paragraph):
                            valid_paragraphs.append((content, section, subsection, idx, paragraph))
        return valid_paragraphs

    def normalize_module_name(self, module_name):
        """Añade sufijo al nombre del módulo si no lo tiene"""
        if not module_name.endswith(self.SUFIX_MODULE):
            return f"{module_name}{self.SUFIX_MODULE}"
        return module_name

    def normalize_unit_name(self, unit_name):
        """Añade 'Unidad ' al número si no está presente"""
        if not unit_name.startswith("Unidad "):
            return f"Unidad {unit_name.strip()}"
        return unit_name

    def normalize_paragraph_id(self, paragraph_id):
        """Añade 'P' al ID si no está presente"""
        if isinstance(paragraph_id, int):
            return f"P{paragraph_id}"
        if not paragraph_id.startswith("P"):
            return f"P{paragraph_id.strip()}"
        return paragraph_id

    def load_module_contents(self, module_name):
        """Carga el JSON de contenidos del módulo especificado."""
        normalized_name = self.normalize_module_name(module_name)
        base_path = Utils.get_base_path("CONTENTS")
        json_path = os.path.join(base_path, f"{normalized_name}.json")
        if not os.path.exists(json_path):
            return None
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_random_paragraph(self, contents, unit_filter=None, paragraph_id=None):
        """Selecciona un párrafo aleatorio (con filtros opcionales)."""
        paragraphs = []
        for content in contents["contenidos"]:
            # Si se filtra por unidad, normalizar el nombre
            if unit_filter:
                normalized_unit = self.normalize_unit_name(unit_filter)
                if content["unidad"] != normalized_unit:
                    continue
            
            for section in content["sections"]:
                for subsection in section["subsections"]:
                    for idx, paragraph in enumerate(subsection["paragraphs"]):
                        # Si se busca por ID, normalizarlo
                        if paragraph_id:
                            normalized_id = self.normalize_paragraph_id(paragraph_id)
                            if paragraph["id"] != normalized_id:
                                continue
                        paragraphs.append((content, section, subsection, idx, paragraph))
        
        if not paragraphs:
            return None
        return random.choice(paragraphs)

    def expand_context(self, subsection, current_idx, direction):
        """Versión modificada para saltar párrafos excluidos."""
        context = []
        remaining_chars = self.MIN_AUXILIAR
        step = -1 if direction == "previous" else 1
        idx = current_idx + step
        
        while 0 <= idx < len(subsection["paragraphs"]) and remaining_chars > 0:
            paragraph = subsection["paragraphs"][idx]
            if not self.is_excluded(paragraph):  # <-- Solo añadir si no está excluido
                context.append(paragraph)
                remaining_chars -= len(paragraph["text"])
            idx += step
        
        return context if context else [{"text": "", "links": [], "media": [], "type": "Empty"}]

    def pick_content(self, module="", unit="", paragraph_id=""):
        # 1. Cargar módulo
        if not module:
            modules = [f.split(".")[0] for f in os.listdir(Utils.get_base_path("CONTENTS")) 
                    if f.endswith(f"{self.SUFIX_MODULE}.json")]
            if not modules:
                return {"error": "No hay módulos disponibles"}
            module = random.choice(modules)
        else:
            module = self.normalize_module_name(module)
        
        contents = self.load_module_contents(module)
        self.exceptions = self._load_exceptions(contents['module'])
        if not contents:
            return {"error": "No se pudo cargar el módulo"}
        
        # 2. Parámetros de búsqueda
        use_unit = None if paragraph_id else unit
        use_paragraph_id = self.normalize_paragraph_id(paragraph_id) if paragraph_id else ""
        
        # 3. Selección con reintentos
        max_attempts = 10
        attempts = 0
        
        while attempts < max_attempts:
            if paragraph_id:
                selected = self.get_random_paragraph(contents, use_unit, use_paragraph_id)
                if not selected:
                    return {"error": f"Párrafo {paragraph_id} no encontrado"}
            else:
                valid_paragraphs = self.get_valid_paragraphs(contents, use_unit)
                if not valid_paragraphs:
                    return {"error": "No hay párrafos válidos"}
                selected = random.choice(valid_paragraphs)
            
            content, section, subsection, p_idx, paragraph = selected
            
            if paragraph_id or len(paragraph["text"]) >= self.MIN_ELEGIBLE:
                break
                
            attempts += 1
        else:
            return {"error": "No se encontró párrafo válido"}
        
        # 5. Contexto (ignorando excluidos)
        previous = self.expand_context(subsection, p_idx, "previous")
        next_ = self.expand_context(subsection, p_idx, "next")
        
        return {
            "module": module.replace(self.SUFIX_MODULE, ""),
            "selected_paragraph": {**paragraph, "type": subsection["type"]},
            "previous_paragraph": previous,
            "next_paragraph": next_,
            "metadata": {
                "unidad": content["unidad"],
                "archivo": content["archivo"],
                "section_title": section["title"]
            }
        }

if __name__ == "__main__":
    picker = ContentPicker()
    
    # Procesar argumentos
    args = sys.argv[1:]
    module = args[0] if len(args) > 0 else ""
    unit = args[1] if len(args) > 1 else ""
    paragraph_id = args[2] if len(args) > 2 else ""
    
    content = picker.pick_content(module, unit, paragraph_id)
    print(json.dumps(content, indent=2, ensure_ascii=False))