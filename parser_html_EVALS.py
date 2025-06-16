import os
import json
import re
from bs4 import BeautifulSoup
from utils import Utils

question_counter = 1


def parse_all_evaluations():
    global question_counter
    base_path = Utils.get_base_path("EVALS")
    if not os.path.exists(base_path):
        print(f"Error: Directorio base no encontrado: {base_path}")
        return

    modules = [m for m in os.listdir(base_path) 
               if os.path.isdir(os.path.join(base_path, m)) and not m.endswith("_files")]
    
    for module_name in modules:
        module_path = os.path.join(base_path, module_name)
        module_questions = []
        question_counter = 1
        
        # Procesar todas las unidades del módulo
        for unit_name in os.listdir(module_path):
            unit_path = os.path.join(module_path, unit_name)
            if not os.path.isdir(unit_path) or unit_name.endswith("_files"):
                continue
            
            # Procesar todos los usuarios de la unidad
            for user_name in os.listdir(unit_path):
                user_path = os.path.join(unit_path, user_name)
                if not os.path.isdir(user_path):
                    continue
                
                # Procesar todos los archivos HTML del usuario
                for file_name in os.listdir(user_path):
                    if not file_name.lower().endswith(".html"):
                        continue
                    
                    file_path = os.path.join(user_path, file_name)
                    questions = parse_evaluation_file(file_path, module_name, unit_name, user_name, file_name)
                    
                    # Añadir preguntas únicas al módulo
                    for q in questions:
                        if not any(q['enunciado'] == existing['enunciado'] for existing in module_questions):
                            q['numero'] = str(question_counter)
                            module_questions.append(q)
                            question_counter += 1
        
        # Guardar todas las preguntas del módulo
        save_module_evaluations(module_path, module_name, module_questions)

def process_evaluation_module(module_path, module_name):
    global question_counter
    unique_questions = []
    
    for root, dirs, files in os.walk(module_path):
        if root.endswith("_files"):
            continue
            
        for file_name in files:
            if not file_name.lower().endswith(".html"):
                continue
                
            file_path = os.path.join(root, file_name)
            questions = parse_evaluation_file(file_path)
            
            for q in questions:
                if not any(q['enunciado'] == existing['enunciado'] for existing in unique_questions):
                    q['numero'] = str(question_counter)
                    unique_questions.append(q)
                    question_counter += 1
    
    save_module_evaluations(module_path, module_name, unique_questions)

def parse_evaluation_file(file_path, module_name, unit_name, user_name, file_name):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    questions = []
    question_divs = soup.find_all('div', class_='que')

    for div in question_divs:
        options = get_question_options(div)
        feedback = get_question_feedback(div)
        correct_indices = get_correct_answer_indices_from_feedback(options, feedback)
        quiz_type = determine_quiz_type(div, options)
        
        question = {
            'numero': len(questions) + 1,
            'enunciado': get_question_text(div),
            'opciones': options,
            'respuestas': correct_indices,
            'retroalimentacion': feedback,
            'type_quiz': quiz_type,
            'media': get_question_media(div),
            'links': get_question_links(div),
            'origen': {
                'modulo': module_name,
                'unidad': unit_name,
                'usuario': user_name,
                'archivo': file_name
            }
        }
        
        # Handle combo questions (matching type)
        if quiz_type == "combo":
            question['combo_options'] = get_combo_options(div)
        
        questions.append(question)
    
    return questions

def get_question_number(div):
    number_tag = div.find('span', class_='qno')
    return number_tag.text.strip() if number_tag else "N/A"

def get_question_text(div):
    qtext_div = div.find('div', class_='qtext')
    if not qtext_div:
        return "N/A"
    
    text = ' '.join([clean_special_characters(p.get_text(' ', strip=True)) 
                   for p in qtext_div.find_all(['p', 'br']) 
                   if p.get_text(strip=True)])
    return text if text else clean_special_characters(qtext_div.get_text(' ', strip=True))

def get_question_options(div):
    options = []
    answer_div = div.find('div', class_='answer')
    
    if answer_div:
        for option in answer_div.find_all('div', class_=['r0', 'r1']):
            text_div = option.find('div', class_='flex-fill') or \
                      option.find('div', {'data-region': 'answer-label'})
            
            if text_div:
                raw_text = text_div.get_text(' ', strip=True)
                clean_text = clean_special_characters(raw_text)
                options.append(clean_text)
    
    if not options and is_boolean_feedback(get_question_feedback(div)):
        return ['Verdadero', 'Falso']
    
    return options


def normalize_special_spaces(text):
    """Reemplaza caracteres especiales de espacio por espacios normales"""
    if not isinstance(text, str):
        return text
    
    # Diccionario mínimo de reemplazos (solo caracteres problemáticos conocidos)
    SPECIAL_SPACES = {
        '\xa0': ' ',   # No-break space
        '\u202f': ' ', # Narrow no-break space
        '\u200b': '',  # Zero-width space
    }
    
    for bad_char, good_char in SPECIAL_SPACES.items():
        text = text.replace(bad_char, good_char)
    return text

def get_correct_answer_indices_from_feedback(options, feedback):
    """Versión definitiva con comparación directa en texto completo"""
    if feedback == "N/A":
        return []

    # Manejo Verdadero/Falso
    boolean_match = re.match(r"La respuesta correcta es '(Verdadero|Falso)'", feedback)
    if boolean_match:
        return ['0'] if boolean_match.group(1) == 'Verdadero' else ['1']

    if not options:
        return []

    # Normalización completa del feedback (sin split)
    normalized_feedback = normalize_for_comparison(feedback.split(": ", 1)[-1]) #+ ","
    
    # Buscar cada opción en el feedback completo
    correct_indices = []
    remaining_feedback = normalized_feedback
    
    for idx, option in enumerate(options):
        search_pattern = normalize_for_comparison(option).strip() #+ ","
        
        if search_pattern in remaining_feedback:
            correct_indices.append(str(idx))
            # Eliminar la opción encontrada para evitar duplicados
            remaining_feedback = remaining_feedback.replace(search_pattern, "", 1)
    
    # Debugging para casos no encontrados
    if not correct_indices:
        print("\n[DEBUG] No se encontraron coincidencias:")
        print(f"Feedback normalizado: {normalized_feedback}")
        print("Opciones normalizadas:")
        for i, opt in enumerate(options):
            print(f"{i}. {normalize_for_comparison(opt)}")
        print("__________Para para análisis__________")
    
    return correct_indices


def get_question_feedback(div):
    feedback_div = div.find('div', class_='rightanswer')
    if not feedback_div:
        return "N/A"
    
    # Extraemos el texto conservando TODOS los caracteres originales
    raw_text = feedback_div.get_text(' ', strip=True)
    
    # Solo limpiamos los artefactos de BeautifulSoup
    return clean_artifacts(raw_text)

def determine_quiz_type(div, options):
    """Determina el tipo de pregunta basado en su estructura HTML
    NOTA: en algunos casos puede estar mal configurado el HTML (o puede haberse creado asi a conciencia), 
          puesto que se han encontrado pregunas tipo multiple (checkbox) pero que solo tienen una opción marcada.
          la varible type_quiz guarda el valor del tipo de dato registrado en el html, pero para mostrar correctametne
          las opciones en pantalla, hay que contar cuantas respuestas vienen en la lista de respuestas.

    """
    if div.find('input', {'type': 'radio'}):
        # Verificar si es pregunta V/F
        feedback = get_question_feedback(div)
        if is_boolean_feedback(feedback) or (len(options) == 2 and is_boolean_question(options)):
            return "boolean"
        return "single"
    elif div.find('input', {'type': 'checkbox'}):
        return "multiple"
    elif div.find('input', {'type': 'text'}):
        return "text"
    elif div.find('select'):
        return "combo"
    
    question_text = get_question_text(div).lower()
    if "relacionar" in question_text or "emparejar" in question_text:
        return "combo"
    
    return "unknown"


def is_boolean_feedback(feedback):
    """Determina si el feedback es de una pregunta Verdadero/Falso"""
    return bool(re.match(r"La respuesta correcta es '(Verdadero|Falso)'", feedback))

def is_boolean_question(options):
    bool_options = {'verdadero', 'falso', 'true', 'false', 'si', 'no'}
    return all(any(op in opt.lower() for op in bool_options) for opt in options)

def get_combo_options(div):
    """Obtiene opciones de combos para preguntas de matching"""
    select = div.find('select')
    if not select:
        return []
    
    return [option.get_text(strip=True) for option in select.find_all('option') if option.get_text(strip=True)]

def get_question_media(div):
    qtext_div = div.find('div', class_='qtext')
    if not qtext_div:
        return []
    
    media = []
    for img in qtext_div.find_all('img', src=True):
        media.append({
            'src': img['src'],
            'alt': img.get('alt', ''),
            'title': img.get('title', '')
        })
    return media

def get_question_links(div):
    qtext_div = div.find('div', class_='qtext')
    if not qtext_div:
        return []
    
    links = []
    for a in qtext_div.find_all('a', href=True):
        links.append({
            'href': a['href'],
            'text': a.get_text(strip=True)
        })
    return links

def save_module_evaluations(module_path, module_name, questions):
    output = {
        "module": module_name,
        "total_preguntas": len(questions),
        "preguntas": questions
    }
    
    # El archivo JSON se guarda en el directorio del módulo con el nombre del módulo + _evals.json
    config_file = Utils.load_config()
    sufix_name=config_file.get("SUFIX_EVALS_NAME")
    #print (f"sufix_name:",sufix_name)
    
    base_path = Utils.get_base_path("EVALS")
    #output_path = os.path.join(module_path, f"{module_name}{sufix_name}.json")
    output_path = os.path.join(base_path, f"{module_name}{sufix_name}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[OK] Evaluaciones de {module_name} guardadas en {output_path}. Total Preguntas:{len(questions)}")

def clean_quotes(text):
    """Elimina comillas simples que BeautifulSoup puede añadir alrededor de textos con comas"""
    return text.replace("', '", ", ").replace("'", "").strip()

def clean_artifacts(text):
    """Elimina solo las comillas simples artificiales que BeautifulSoup añade"""
    if "', '" in text:
        return text.replace("', '", ", ")
    return text

def clean_special_characters(text):
    """Normaliza caracteres problemáticos en el texto original"""
    if not text or not isinstance(text, str):
        return text
    
    replacements = {
        '\xa0': ' ',    # No-break space
        '\u202f': ' ',  # Narrow no-break space
        '\u200b': '',   # Zero-width space
        '\r\n': ' ',    # Saltos de línea
        '\n': ' ',      # Saltos de línea
    }
    
    for bad_char, good_char in replacements.items():
        text = text.replace(bad_char, good_char)
    return text.strip()

def normalize_for_comparison(text):
    """Aplica TODAS las normalizaciones necesarias para comparar textos"""
    if not text:
        return text
    
    # 1. Reemplazar caracteres especiales de espacio
    text = text.replace('\xa0', ' ').replace('\u202f', ' ').replace('\u200b', '')
    
    # 2. Eliminar comillas simples artificiales de BeautifulSoup
    text = text.replace("', '", ", ").replace("'", "")
    
    # 3. Normalizar espacios múltiples y trim
    text = ' '.join(text.split()).strip()
    
    return text


if __name__ == "__main__":
    parse_all_evaluations()
