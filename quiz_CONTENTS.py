import os
import json
import re
import sys
from llm_connector import LLMConnector
from picker_CONTENTS import ContentPicker
from utils import Utils

class QuizGeneratorCONTENTS:
    def __init__(self):
        self.picker = ContentPicker()
        self.llm = LLMConnector()
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "PROMPTS")

    def load_prompt_template(self, prompt_name="quiz_prompt_CONTENTS.txt"):
        """Carga la plantilla y la devuelve como texto plano."""
        prompt_path = os.path.join(self.prompts_dir, prompt_name)
        if not os.path.exists(prompt_path):
            return ""
            #raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def load_info(self, module=""):
        """el fichero de info"""
        if module == "":
            return
        config_file = Utils.load_config()

        info_dir = config_file.get("BASE_PATH")
        info_path = os.path.join(info_dir, "DATA", "INFO")

        info_file = module + "_Info.txt"
        info_file_path = os.path.join(info_path, info_file)

        #print(f"load_info   module={module}")
        #print(f"info_file_path={info_file_path}")
        #print(f"info_path={info_path}")


        if not os.path.exists(info_file_path):
            return ""
        with open(info_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            return content

    def replace_variables(self, template, variables):
        """Reemplaza variables en el formato {var} usando un diccionario."""
        for var, value in variables.items():
            template = template.replace(f"{{{var}}}", str(value))
        return template

    def generate_quiz(self, module="", unit="", paragraph_id=""):
        """Genera un quiz a partir de un párrafo y su contexto."""
        # 1. Obtener contenido
        content = self.picker.pick_content(module, unit, paragraph_id)
        if not content:
            return {"error": "No content available"}

        config_file = Utils.load_config()
        total_options = config_file.get("OPTIONS_CONTENTS")
        module_info = self.load_info(content["module"])
        module_prompt = self.load_prompt_template(content["module"] + "_prompt.txt")
        # 2. Definir variables disponibles
        variables = {
            # Metadatos
            "module_info": module_info,
            "module_prompt": module_prompt,
            "module": content["module"],
            "unidad": content["metadata"]["unidad"],
            "section_title": content["metadata"]["section_title"],
            "archivo": content["metadata"]["archivo"],
            
            # Párrafos
            "main_paragraph": content["selected_paragraph"]["text"],
            "main_paragraph_id": content["selected_paragraph"]["id"],
            "previous_paragraph": "\n".join(p["text"] for p in content["previous_paragraph"]),
            "next_paragraph": "\n".join(p["text"] for p in content["next_paragraph"]),
            
            # Configuración
            "total_options": total_options
        }

        # 3. Cargar y personalizar el prompt
        prompt_template = self.load_prompt_template()
        prompt = self.replace_variables(prompt_template, variables)

        # 4. Generar pregunta via LLM
        llm_response = self.llm.generate(prompt)
        if not llm_response:
            return {"error": "LLM failed to generate quiz"}

        try:
            quiz_data = json.loads(llm_response)
            #print(f"quiz_data={quiz_data}")
        except json.JSONDecodeError:
            return {"error": "Invalid LLM response format"}

        previous = '\n'.join(p['text'] for p in content['previous_paragraph'])
        next_ = '\n'.join(p['text'] for p in content['next_paragraph'])

        # 5. Añadir metadatos originales con contexto completo
        #quiz_data.update({
        #    "original_data": {
        #        "paragraph_id": content["selected_paragraph"]["id"],
        #        "question_context": (
        #            f"Párrafo anterior:\n{previous}\n\n"
        #            f"Párrafo principal:\n{content['selected_paragraph']['text']}\n\n"
        #            f"Párrafo siguiente:\n{next_}"
        #        ),
        #        "links": content["selected_paragraph"]["links"],
        #        "media": content["selected_paragraph"]["media"],
        #        "metadata": {
        #            "module": content["module"],
        #            "unidad": content["metadata"]["unidad"],
        #            "section_title": content["metadata"]["section_title"],
        #            "type": content["selected_paragraph"]["type"],  # También añadido en metadata
        #            "type_quiz": "single"
        #        }
        #    }
        #})
        

        return_data = {
            "quizzes": [{
                "title": quiz_data.get("title", ""),
                "question": quiz_data["question"],
                "options": quiz_data["options"],
                "correct_answer": [quiz_data["correct_answer"]] if isinstance(quiz_data["correct_answer"], int) else quiz_data["correct_answer"],
                "link_question": content["selected_paragraph"]["links"],
                "media_question": content["selected_paragraph"]["media"],
                "module": content["module"],
                "unidad": content["metadata"]["unidad"],
                "ID": content["selected_paragraph"]["id"],
                "type_quiz": "multi" if len(str(quiz_data.get("correct_answer", []))) > 1 else "single",
                "type_gen": "CONTENTS",
                "metadata": {
                    "section_title": content["metadata"]["section_title"],
                    "original_text": content["selected_paragraph"]["text"],
                    "type": content["selected_paragraph"]["type"],
                    "context": self._build_context(content)  # Párrafos anterior/siguiente
                }
            }],
            "total_quizzes": 1
        }

        return return_data

    def _build_context(self, content):
        return {
            "previous": [p["text"] for p in content["previous_paragraph"]],
            "next": [p["text"] for p in content["next_paragraph"]]
        }

if __name__ == "__main__":
    generator = QuizGeneratorCONTENTS()
    args = sys.argv[1:]
    module = args[0] if len(args) > 0 else ""
    unit = args[1] if len(args) > 1 else ""
    paragraph_id = args[2] if len(args) > 2 else ""
    
    quiz = generator.generate_quiz(module, unit, paragraph_id)
    print(json.dumps(quiz, indent=2, ensure_ascii=False))