import os
import json
from bs4 import BeautifulSoup
from utils import Utils

def extract_content_data(file_path, paragraph_counter):
    """Extrae el contenido estructurado de un archivo HTML con IDs de párrafos."""
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    result = {
        "title": soup.title.string if soup.title else "Documento",
        "sections": []
    }

    for node in soup.select("article.node"):
        section_title_tag = node.select_one("h1.nodeTitle")
        if not section_title_tag:
            continue
            
        section = {
            "title": section_title_tag.get_text(strip=True),
            "subsections": [],
            "global_links": [],
            "global_media": []
        }

        for device in node.select("article.iDevice_wrapper"):
            subsection_type_tag = device.select_one(".iDeviceTitle")
            subsection_type = subsection_type_tag.get_text(strip=True) if subsection_type_tag else "Contenido"

            subsection = {
                "type": subsection_type,
                "paragraphs": []
            }

            content_block = device.select_one(".iDevice_content")
            if content_block:
                for p in content_block.find_all("p", recursive=True):
                    text = p.get_text(strip=True)
                    if not text:
                        continue

                    paragraph_id = f"P{paragraph_counter}"
                    paragraph_counter += 1

                    subsection["paragraphs"].append({
                        "id": paragraph_id,  # Nuevo campo
                        "text": text,
                        "links": [
                            {"href": a["href"], "text": a.get_text(strip=True)}
                            for a in p.find_all("a", href=True)
                        ],
                        "media": [
                            {
                                "src": img["src"],
                                "alt": img.get("alt", ""),
                                "title": img.get("title", "")
                            }
                            for img in p.find_all("img", src=True)
                        ]
                    })

                # Procesar enlaces y medios globales (sin cambios)
                for a in content_block.find_all("a", href=True):
                    if not any(a in p for p in content_block.find_all("p")):
                        section["global_links"].append({
                            "href": a["href"],
                            "text": a.get_text(strip=True)
                        })

                for img in content_block.find_all("img", src=True):
                    if not any(img in p for p in content_block.find_all("p")):
                        section["global_media"].append({
                            "src": img["src"],
                            "alt": img.get("alt", ""),
                            "title": img.get("title", "")
                        })

            section["subsections"].append(subsection)
        
        result["sections"].append(section)
    
    return result, paragraph_counter  # Devuelve el contador actualizado

def process_module_contents(module_path):
    """Procesa todas las unidades de un módulo con contador de párrafos global."""
    module_name = os.path.basename(module_path)
    contents = []
    paragraph_counter = 1  # Inicia el contador
    
    for unit_name in os.listdir(module_path):
        unit_path = os.path.join(module_path, unit_name)
        if not os.path.isdir(unit_path) or unit_name.endswith("_files"):
            continue
            
        print(f" Procesando unidad: {unit_name}")
        
        for filename in os.listdir(unit_path):
            if not filename.lower().endswith(".html"):
                continue
                
            file_path = os.path.join(unit_path, filename)
            try:
                content_data, paragraph_counter = extract_content_data(file_path, paragraph_counter)
                content_data.update({
                    "unidad": unit_name,
                    "archivo": filename,
                    "ruta_completa": file_path
                })
                contents.append(content_data)
            except Exception as e:
                print(f"Error procesando {file_path}: {str(e)}")
    
    return {
        "module": module_name,
        "total_archivos": len(contents),
        "total_parrafos": paragraph_counter - 1,  # Total de párrafos procesados
        "contenidos": contents
    }

def parse_all_modules_contents():
    """Procesa todos los módulos en CONTENTS y guarda JSON en CONTENTS."""
    base_path = Utils.get_base_path("CONTENTS")
    if not os.path.exists(base_path):
        print(f"Error: Directorio base no encontrado: {base_path}")
        return

    contents_path = Utils.get_base_path("CONTENTS")
    os.makedirs(contents_path, exist_ok=True)

    for module_name in os.listdir(base_path):
        module_path = os.path.join(base_path, module_name)
        if not os.path.isdir(module_path):
            continue
            
        print(f"\nProcesando módulo: {module_name}")
        module_data = process_module_contents(module_path)

        config_file = Utils.load_config()
        sufix_name = config_file.get("SUFIX_CONTENTS_NAME")
        print(f"sufix_name: {sufix_name}")

        output_path = os.path.join(contents_path, f"{module_name}{sufix_name}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(module_data, f, ensure_ascii=False, indent=2)
            
        print(f"[OK] Módulo {module_name} guardado en {output_path}")

if __name__ == "__main__":
    parse_all_modules_contents()