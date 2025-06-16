import json
import os
import logging
from typing import Optional
import random
from pathlib import Path
import discord
from discord.ext import commands

# ======== Clase Utils: Métodos de utilidad para el bot
class Utils:
    # ======== Método: load_config - Lee archivos JSON de configuración
    @staticmethod
    def load_config(nombre_archivo='config.json'):
        """
        Lee un archivo JSON y retorna su contenido como diccionario.
        
        Args:
            nombre_archivo (str): Ruta del archivo JSON (default: 'config.json')
            
        Returns:
            dict: Datos del archivo JSON o None si hay error
        """
        try:
            with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
                return json.load(archivo)
        except Exception as e:
            logging.error(f"Error al leer {nombre_archivo}: {str(e)}")
            return None

    def load_template(filename: str) -> str:
        filepath = os.path.join("TEMPLATES",filename)
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def apply_replacements(template: str, replacements: dict) -> str:
        try:
            for key, value in replacements.items():
                #print(f"key={key}  value={value}")
                template = template.replace(key, value)
        except Exception as e:
            #print("[ERROR apply_replacements] {e}")
            pass

        return template

    def generate_option_replacements(quiz_or_eval: dict, option_index: int, symbol: str = "", is_correct: bool = False) -> dict:
        """
        Genera reemplazos para plantillas de mensaje, compatible con ambos formatos (quiz y eval)
        
        Args:
            quiz_or_eval: Diccionario con datos del quiz o evaluación
            option_index: Índice de la opción actual (0-based)
            symbol: Símbolo visual del botón (A, B, C, etc.)
            is_correct: Indica si la opción es correcta (solo necesario para formato eval)
                
        Returns:
            Diccionario con todos los reemplazos necesarios
        """
        # Determinar si es formato quiz o eval
        is_eval_format = 'question' in quiz_or_eval and isinstance(quiz_or_eval['question'], dict)
        
        if is_eval_format:
            # Formato evaluación (EvalGenerator)
            pregunta = quiz_or_eval.get('question', {})
            opciones = pregunta.get('opciones', [])
            respuestas = pregunta.get('respuestas', [])
            metadata = quiz_or_eval.get("metadata", {})
            
            option_text = opciones[option_index] if option_index < len(opciones) else ""
            
            # Convertir respuestas a índices numéricos
            correct_indices = []
            for r in respuestas:
                try:
                    correct_indices.append(int(r))
                except (ValueError, TypeError):
                    continue
                    
            is_correct = option_index in correct_indices
            
            return {
                # Datos generales
                "{title}": quiz_or_eval.get("title", "Pregunta de evaluación"),
                "{question}": pregunta.get("enunciado", ""),
                "{correct_answer}": ", ".join([str(i+1) for i in correct_indices]),
                
                # Datos específicos de la opción
                "{symbol}": str(symbol),
                "{option_text}": option_text,
                "{option_feedback}": pregunta.get("retroalimentacion", "No hay retroalimentación"),
                "{result}": "✅" if is_correct else "❌",
                
                # Metadatos
                "{section}": metadata.get("section", "Evaluación"),
                "{subsection}": metadata.get("subsection", "Pregunta"),
                "{paragraph_text}": metadata.get("paragraph_text", ""),
                "{paragraph_text_correct}": metadata.get("paragraph_text", "") if is_correct else f'||{metadata.get("paragraph_text", "")}||',
                "{module}": metadata.get("module", "General"),
                
                # Valores por defecto para compatibilidad
                "{quiz_use_count}": "0",
                "{quiz_last_used}": "Nunca",
                "{total_options}": str(len(opciones)),
                "{num_questions}": str(len(opciones))
            }
        else:
            # Formato quiz original (QuizGenerator)
            option = quiz_or_eval["options"][option_index]
            metadata = quiz_or_eval.get("metadata", {})
            
            # Manejo seguro de respuestas correctas (acepta int, str o lista)
            correct_answers = []
            if isinstance(quiz_or_eval.get("correct_answer"), int):
                correct_answers = [quiz_or_eval["correct_answer"]]
            elif isinstance(quiz_or_eval.get("correct_answer"), str):
                try:
                    correct_answers = [int(x.strip()) for x in quiz_or_eval["correct_answer"].split(",")]
                except ValueError:
                    correct_answers = []
            elif isinstance(quiz_or_eval.get("correct_answer"), list):
                correct_answers = [int(x) for x in quiz_or_eval["correct_answer"] if str(x).isdigit()]
            
            is_correct = option_index in correct_answers
            
            return {
                # Datos generales del quiz
                "{title}": str(quiz_or_eval.get("title", "")),
                "{question}": str(quiz_or_eval.get("question", "")),
                "{correct_answer}": ", ".join([str(i+1) for i in correct_answers]),
                
                # Datos específicos de la opción
                "{symbol}": str(symbol),
                "{option_text}": option.get("text", ""),
                "{option_feedback}": option.get("feedback", ""),
                "{result}": "✅" if is_correct else "❌",
                
                # Metadatos
                "{section}": metadata.get("section", ""),
                "{subsection}": metadata.get("subsection", ""),
                "{paragraph_text}": metadata.get("paragraph_text", ""),
                "{paragraph_text_correct}": metadata.get("paragraph_text", "") if is_correct else f'||{metadata.get("paragraph_text", "")}||',
                "{module}": metadata.get("module", ""),
                
                "{quiz_use_count}": str(metadata.get("quiz_use_count", "")),
                "{quiz_last_used}": str(metadata.get("quiz_last_used", "")),
                "{total_options}": str(len(quiz_or_eval.get("options", []))),
                "{num_questions}": str(len(quiz_or_eval.get("options", [])) - 1)
            }

    def get_base_path(dir_path: str = "") -> dict:
        config=Utils.load_config()
        base_path_config = config.get("BASE_PATH",".")
        base_path = os.path.join(base_path_config, "DATA", dir_path)
        #print(f"Base path: {base_path}")
        return base_path

    def get_module_file(type_data: str, module: str, extension: str = "json") -> Optional[str]:
        if not type_data:
            print(f"[ERROR] Se debe indicar el type_data")
            return None
        
        base_path = Utils.get_base_path(type_data)
        if not os.path.exists(base_path):
            print(f"[ERROR] No existe la ruta {base_path}")
            return None

        # Obtener todas las carpetas de módulos dentro de DATA/CONTENTS
        module_dirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
        if not module_dirs:
            print(f"[ERROR] No se encontraron carpetas en {base_path}")
            return None

        # Selección del módulo
        if module:
            chosen_module = next((d for d in module_dirs if d.lower() == module.lower()), None)
            if not chosen_module:
                print(f"[ERROR] No se encontró el módulo '{module}' en {base_path}")
                return None
        else:
            chosen_module = random.choice(module_dirs)

        module_path = os.path.join(base_path, chosen_module)
        json_files = [f for f in os.listdir(module_path) if f.endswith(f".{extension}")]
        if not json_files:
            print(f"[ERROR] No hay archivos {extension}.{extension} en el módulo '{chosen_module}' ({module_path})")
            return None

        chosen_json = json_files[0]  # Por ahora usamos el primero
        full_path = os.path.join(module_path, chosen_json)

        print(f"[INFO] Usando módulo: {chosen_module}, archivo: {chosen_json}")
        return full_path    

class DirectoryLister:
    @staticmethod
    def get_modules_list(base_path: str, data_type: str, suffix: str) -> dict:
        """
        Obtiene el listado de módulos y unidades para un tipo de datos (CONTENTS o EVALS)
        
        Args:
            base_path: Ruta base del proyecto
            data_type: "CONTENTS" o "EVALS"
            suffix: Sufijo de los archivos (ej: "_contents_v5.json")
            
        Returns:
            Diccionario con {nombre_modulo: cantidad_unidades}
        """
        modules_data = {}
        data_dir = Path(base_path) / "DATA" / data_type
        
        # Buscar archivos de módulo (ej: AEI_contents_v5.json)
        for module_file in data_dir.glob(f"*{suffix}"):
            module_name = module_file.name.replace(suffix, "")
            units_dir = data_dir / module_name
            
            # Contar unidades (subdirectorios)
            unit_count = 0
            if units_dir.exists():
                unit_count = len([d for d in units_dir.iterdir() if d.is_dir()])
            
            modules_data[module_name] = unit_count
        
        return modules_data

    @staticmethod
    def generate_embed(contents_data: dict, evals_data: dict) -> discord.Embed:
        """
        Genera un Embed de Discord con el listado unificado
        
        Args:
            contents_data: Datos de contenidos {modulo: unidades}
            evals_data: Datos de evaluaciones {modulo: unidades}
            
        Returns:
            Embed de Discord listo para enviar
        """
        all_modules = set(contents_data.keys()).union(set(evals_data.keys()))
        
        embed = discord.Embed(
            title="📂 Listado de Módulos y Unidades",
            description="Lista unificada de todos los módulos con sus unidades\n",
            color=discord.Color.blue()
        )

        lines = []
        for module in sorted(all_modules):
            content_units = contents_data.get(module, 0)
            eval_units = evals_data.get(module, 0)
            status_emoji = "✅" if content_units == eval_units else "⚠️"
            lines.append(f"{status_emoji} **{module}**: 📚 {content_units} / 📝 {eval_units}")

        embed.description += "\n".join(lines)
        embed.set_footer(text=" 📚 = Contenido  📝 = Evaluación\n ✅ = Coinciden  ⚠️ = Diferencia")
        #await ctx.send(embed=embed)
        return embed


# Ejemplo de uso:
if __name__ == "__main__":
    config = Utils.load_config()
    if config:
        print("Configuración cargada:", config)
    dir = DirectoryLister.get_modules_list()
    print(f"dir:\n{dir}")
