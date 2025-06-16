import os
import re

# Directorio donde están los archivos del proyecto
SRC_DIR = "src"

# Archivo donde se guardarán los imports combinados
OUTPUT_FILE = "combined_imports.py"

# Expresión regular para identificar líneas de importación
IMPORT_PATTERN = re.compile(r"^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)")

# Lista para almacenar los imports únicos
imports = set()

# Recorrer los archivos .py dentro de la carpeta src/
for root, _, files in os.walk(SRC_DIR):
    for file in files:
        if file.endswith(".py"):
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                for line in f:
                    match = IMPORT_PATTERN.match(line)
                    if match:
                        imports.add(line.strip())

# Guardar los imports en el archivo de salida
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("# Importaciones extraídas de los módulos\n\n")
    for imp in sorted(imports):
        f.write(imp + "\n")

print(f"Archivo {OUTPUT_FILE} generado con {len(imports)} importaciones únicas.")
