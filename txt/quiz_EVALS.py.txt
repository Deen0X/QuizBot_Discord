import os
import json
import logging
import sys
from picker_EVALS import EvalPicker
from llm_connector import LLMConnector
from utils import Utils

class QuizGeneratorEVALS:
    def __init__(self):
        self.picker = EvalPicker()
        self.llm = LLMConnector()
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "PROMPTS")
        self.config = Utils.load_config()
        self.base_path = self.config.get("BASE_PATH",".")
        
        # Cargar plantillas de remix
        self.remix_prompts = {
            'remix': self._load_remix_prompt('remix.txt'),
            'remix_bool': self._load_remix_prompt('remix_bool.txt'),
            'remix_single': self._load_remix_prompt('remix_single.txt'),
            'remix_multi': self._load_remix_prompt('remix_multi.txt')
        }

    def load_module_info(self, module="", default_text=""):
        """Carga la información del módulo desde el archivo correspondiente"""
        
        try:
            if not self.base_path:
                return ""
                
            info_path = os.path.join(self.base_path, "DATA", "INFO", f"{module}_Info.txt")
            
            if os.path.exists(info_path):
                with open(info_path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            logging.error(f"Error cargando info del módulo {module}: {str(e)}")
        
        return default_text


    def _load_remix_prompt(self, filename: str) -> str:
        """Carga una plantilla de remix desde el directorio PROMPTS"""
        prompt_path = os.path.join(self.prompts_dir, filename)
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error loading remix prompt {filename}: {str(e)}")
            return ""
        
    def generate_quiz(self, module="", unit="", question_id="", count=1):
        """Convierte preguntas de EVALS al formato estándar de quiz."""
        # 1. Obtener preguntas usando el picker
        eval_data = self.picker.pick_questions(module, unit, question_id, count)
        if "error" in eval_data:
            return eval_data
        
        #print(f"eval_data={eval_data}")
        # 2. Convertir al formato estándar
        quizzes = []
        for question in eval_data["preguntas"]:
            quiz = {
                "title": f"Pregunta {question['numero']}",
                "question": question["enunciado"],
                "options": [{"text": opt, "feedback": ""} for opt in question["opciones"]],
                "correct_answer": [int(r) for r in question["respuestas"]],
                "link_question": None,  # Puedes extraerlos de "origen" si existen
                "media_question": None,  # Igual que arriba
                "module": eval_data["module"],
                "unidad": question["origen"]["unidad"],
                "ID": question["numero"],
                "type_quiz": "multi" if len(question["respuestas"]) > 1 else "single",
                "type_gen": "EVALS",
                "metadata": {
                    "original_data": question  # Conserva todos los datos originales
                }
            }
            quizzes.append(quiz)

        return {
            "quizzes": quizzes,
            "total_quizzes": len(quizzes)
        }

    def remix(self, module="", unit="", question_id="", remix_type="remix", count=1):
            """
            Reformula preguntas usando LLM manteniendo la estructura original
            
            Args:
                module: Nombre del módulo
                unit: Unidad específica
                question_id: ID de pregunta específica
                remix_type: Tipo de remix (remix, remix_bool, remix_single, remix_multi)
                count: Número de preguntas a generar
                
            Returns:
                Mismo formato que generate_quiz pero con preguntas reformuladas
            """
            remix_type = remix_type if remix_type else "remix"
            # 1. Obtener preguntas originales
            original_quiz = self.generate_quiz(module, unit, question_id, count)
            if "error" in original_quiz:
                return original_quiz

            print(f"remix_type={remix_type}") #\nremix_prompts:{self.remix_prompts}")

            # 2. Verificar plantilla de remix
            if remix_type not in self.remix_prompts or not self.remix_prompts[remix_type]:
                return {"error": f"Tipo de remix no válido o plantilla no encontrada: {remix_type}"}

            try:
                aux = original_quiz["quizzes"][0]["module"]
            except:
                aux=""
            
            module_info_text = self.load_module_info(aux, aux)


            # 3. Procesar cada pregunta
            remixed_quizzes = []
            for quiz in original_quiz["quizzes"]:
                # Preparar variables para el prompt
                variables = {
                    "original_question": quiz["question"],
                    "original_options": "\n".join(
                        f"{i+1}. {opt['text']}" 
                        for i, opt in enumerate(quiz["options"])
                    ),
                    "original_corrects_index": ", ".join(
                        str(i) for i in quiz["correct_answer"]
                    ),
                    "original_corrects_answers": "\n".join(
                        quiz["options"][i]["text"] 
                        for i in quiz["correct_answer"]
                    ),
                    "module": quiz.get("module", ""),
                    "unit": quiz.get("unidad", ""),
                    "module_info": module_info_text,
                    "total_options": str(len(quiz["options"])),
                    "total_correct": str(len(quiz["correct_answer"]))
                }

                # Construir prompt final
                prompt = self.remix_prompts[remix_type]
                for ph, val in variables.items():
                    prompt = prompt.replace(f"{{{ph}}}", str(val))

                #print(f"pronpt:\n{prompt}")
                #input("Pause...")

                # 4. Llamar al LLM
                llm_response = self.llm.generate(prompt)
                if not llm_response:
                    remixed_quizzes.append(quiz)  # Mantener original si falla
                    continue

                try:
                    remixed_data = json.loads(llm_response)
                    
                    # Validar estructura básica
                    if not all(k in remixed_data for k in ["question", "options", "correct_answer"]):
                        raise ValueError("Respuesta del LLM incompleta")
                    
                    # 5. Construir respuesta manteniendo estructura original
                    new_quiz = quiz.copy()  # Copiar todos los campos originales
                    
                    # Actualizar solo los campos necesarios
                    new_quiz.update({
                        "question": remixed_data["question"],
                        "options": [
                            {"text": opt["text"], "feedback": opt.get("feedback", "")}
                            for opt in remixed_data["options"]
                        ],
                        "correct_answer": (
                            [remixed_data["correct_answer"] 
                            if isinstance(remixed_data["correct_answer"], int) 
                            else remixed_data["correct_answer"]]
                        ),
                        "type_gen": remix_type,
                        #"metadata": {
                        #    **quiz.get("metadata", {}),  # Mantener metadatos originales
                        #    "remix_type": remix_type,
                        #    #"original_question": quiz["question"],
                        #    #"original_options": [opt["text"] for opt in quiz["options"]],
                        #    #"original_correct": [quiz["options"][i]["text"] for i in quiz["correct_answer"]]
                        #}
                    })
                    
                    remixed_quizzes.append(new_quiz)
                    
                except (json.JSONDecodeError, ValueError) as e:
                    logging.error(f"Error en remix: {str(e)}")
                    remixed_quizzes.append(quiz)

            return {
                "quizzes": remixed_quizzes,
                "total_quizzes": len(remixed_quizzes),
            #    "metadata": {
            #        "remix_type": remix_type,
            #        "source": "EVALS"
            #    }
            }

if __name__ == "__main__":
    generator = QuizGeneratorEVALS()
    
    # Procesar argumentos (mismos que picker_EVALS.py)
    args = sys.argv[1:]
    module = args[0] if len(args) > 0 else ""
    unit = args[1] if len(args) > 1 else ""
    question_id = args[2] if len(args) > 2 else ""
    count = int(args[3]) if len(args) > 3 else 1
    remix_type=""
    #quiz = generator.generate_quiz(module, unit, question_id, count)
    quiz = generator.remix(module, unit, question_id, remix_type, count)
    print(json.dumps(quiz, indent=2, ensure_ascii=False))