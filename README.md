# QuizBot_Discord
Discrod Bot para generar preguntas a partir de contenidos y evaluaciones de alumnos

# QuizBot

QuizBot es un bot de Discord diseñado para generar preguntas interactivas basadas en contenidos educativos y evaluaciones. Utiliza un modelo de lenguaje (LLM) para generar y reformular preguntas, permitiendo que los usuarios practiquen sus conocimientos en un entorno grupal.

## 🌟 Características principales
- **Generación de preguntas dinámicas** basadas en textos educativos.
- **Autoevaluaciones** mediante extracción de preguntas de tests oficiales.
- **Interacción en Discord** con botones persistentes y comandos intuitivos.
- **Sistema de puntuación** para medir el progreso de los usuarios.
- **Flexibilidad de configuración** mediante archivos JSON estándar.
- **Soporte para imágenes** asociadas a los contenidos.

## 📦 Estructura del Proyecto

Este proyecto consiste en un bot Discord que genera preguntas interactivas sobre contenidos parseados desde ficheros html

El proyecto se divide en varios módulos:
```
QuizBot/
│── src/               # Código fuente del bot
│   │── discordbot_V5.py                             # Programa principal del Bot
│   │── buttons_discord.py                           # Módulo de botones persistentes de discord
│   │── llm_connector.py                             # Módulo con funciones para conectar un LLM (IA) para generar preguntas desde contenidos
│   │── score_manager.py                             # Módulo con funciones para administrar las puntuaciones del usuario.
│   │── utils.py                                     # Utilidades generales
│   │── picker_CONTENTS.py                           # Seleccionador de párrafos de contenidos (CONTENTS) para preparar una pregunta.
│   │── picker_EVALS.py                              # Seleccionador de preguntas de evaluación (EVALS) para volver a preguntar o reformularla con ayuda de IA
│   │── parser_html_CONTENTS.py                      # Parseador HTML para contenidos de módulos/asignaturas
│   │── parser_html_EVALS.py                         # Parseador HTML para contenidos de autoevaluaciones de los alumnos
│   │── quiz_CONTENTS.py                             # Generador de preguntas con IA. En base a la selección de picker_CONTENTS.py
│   │── quiz_EVALS.py                                # Generador de preguntas basadas en la selección de picker_EVALS.py. Puede volver a enviar la misma pregunta o reformularla con ayuda de IA.
│   │── config.json                                  # Configuraciones generales del bot.
│   │── PROMPTS/                                     # Carpeta contenedora de los prompts utilizados.
│   │   │── quiz_prompt_CONTENTS.txt                 # Prompt principal para generar las preguntas a partir de CONTENTS
│   │   │── remix.txt                                # Prompt para reformular preguntas a partir de EVALS
│   │── TEMPLATES/                                   # Plantillas utilizadas para formatear los mensajes de salida.
│   │   │── message_chat_contents_template.txt       # Plantilla para mensaje de respuesta de botón, en el chat principal, para CONTENTS
│   │   │── message_chat_evals_template.txt          # Plantilla para mensaje de respuesta de botón, en el chat principal, para EVALS
│   │   │── message_chat_remix_template.txt          # Plantilla para mensaje de respuesta de botón, en el chat principal, para REMIX
│   │   │── message_dm_contents_template.txt	     # Plantilla para mensaje de respuesta de botón, en el chat privado (Mensaje Directo), para CONTENTS
│   │   │── message_dm_evals_template.txt            # Plantilla para mensaje de respuesta de botón, en el chat privado (Mensaje Directo), para EVALS
│   │   │── message_dm_remix_template.txt            # Plantilla para mensaje de respuesta de botón, en el chat privado (Mensaje Directo), para REMIX
│   │   │── quiz_QUESTION_TEMPLATE.txt               # Plantilla para mostrar la pregunta en el chat.
│   │── user_scores/                                 # Directorio donde se guardan los puntajes de cada usuario.
│   │   │── user_id.json                             # Fichero con puntuación simple de cada usuario.
```

Los datos se obtienen de la siguiente estructura de directorio.
```
BASE_PATH/                                           # Directorio con los datos para que trabaje el bot. Este directorio se configura en el config.json
│── DATA/                                            # Datos de contenidos y evaluaciones
│   │── CONTENTS                                     # Carpeta CONTENTS. 
│   │   │── [Modulo 1]                               # Módulo o Asignatura 1. Utilizar siglas para acortar el nombre
│   │   │   │── Unidad 1                             # Unidad 1 del módulo
│   │   │   │── Unidad 2                             # Unidad 2 del módulo
│   │   │   │── Unidad N                             # Unidad N del módulo
│   │   │── [Modulo 2]                               # Módulo o Asignatura 2.
│   │   │   │── Unidad 1                             # Unidad 1 del módulo
│   │   │   │── Unidad N                             # Unidad N del módulo
│   │   │── [Modulo N]                               # Módulo o Asignatura N.
│   │── EVALS                                        # Carpeta con auto-evaluaciones de los alumnos
│   │   │── [Modulo 1]                               # Módulo o Asignatura 1. Utilizar siglas para acortar el nombre
│   │   │   │── Unidad 1                             # Unidad 1 del módulo
│   │   │   │   │── [User 1 Evals]                   # Carpeta para las evaluaciones del usuario 1
│   │   │   │   |    │── eval_intento1.html          # Fichero intento 1
│   │   │   │   |    │── eval_intento2.html          # Fichero intento 2
│   │   │   │   |    │── eval_intentoN.html          # Fichero intento N
│   │   │   │   │── [User 2 Evals]                   # Carpeta para las evaluaciones del usuario 2
│   │   │   │   |    │── eval_intento1.html          # Fichero intento 1
│   │   │   │   |    │── eval_intentoN.html          # Fichero intento N
│   │   │   │   │── [User N Evals]                   # Carpeta para las evaluaciones del usuario N
│   │   │   │── Unidad 2                             # Unidad 2 del módulo
│   │   │   │   │── [User 1 Evals]                   # Carpeta para las evaluaciones del usuario 1
│   │   │   │   |    │── eval_intento1.html          # Fichero intento 1
│   │   │   │   |    │── eval_intento2.html          # Fichero intento 2
│   │   │   │   |    │── eval_intentoN.html          # Fichero intento N
│   │   │   │   │── [User N Evals]                   # Carpeta para las evaluaciones del usuario N
│   │   │   │── Unidad N                             # Unidad N del módulo
│   │── INFO                                         # Carpeta con ficheros de información de cada módulo utilizado como información adicional para los prompts.
│   │   │── [Modulo 1]_info.txt                      # Información resumida (unos 500 caracteres) sobre el módulo. 1
│   │   │── [Modulo 2]_info.txt                      # Información resumida (unos 500 caracteres) sobre el módulo. 2
│   │   │── [Modulo N]_info.txt                      # Información resumida (unos 500 caracteres) sobre el módulo. N
```

## ⚙️ Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/QuizBot.git
   cd QuizBot

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt

3. Configura config.json con las rutas y parámetros necesarios.

4. Ejecuta el bot:
   python src/discordbot_V5.py

5. Ejecuta el bot:
python src/discordbot_V5.py


## Configuración del Bot

Para poder ejecutar el bot, necesitas crear una cuenta de desarrollador en el [Portal de Desarrollador de Discord](https://discord.com/developers/applications)

## ✨ Uso del Bot

El bot funciona dentro de Discord y los usuarios pueden interactuar mediante comandos o botones persistentes. Existen dos tipos principales de preguntas:

**CONTENTS**: Basadas en materiales educativos de módulos.

**EVALS**: Preguntas tomadas de autoevaluaciones realizadas por los alumnos.


## 📌 Comandos principales

Los usuarios pueden pedir preguntas mediante los siguientes comandos:

**!help**
  Muestra este archivo de ayuda.

**!dir**  (alias: !list)
  Lista todos los módulos disponibles y muestra cuántas unidades de contenido y evaluación tiene cada uno.
  Ejemplo de salida:
    ✅ POKE: 📚 4 / 📝 4
    
    ⚠️ PCMT: 📚 6 / 📝 5

## 🧩 QUIZ COMMANDS

- `!exam` [modulo] [unidad]
  Muestra una sola pregunta del módulo/unidad indicado (basada en CONTENIDOS).
  !exam - si no se indican parámetros y estamos en una sala común de estudio (no es temática), se seleccionará un módulo y unidad al azar
  !exam [modulo] si se indica el módulo, se seleccionará una  unidad al azar
  !exam [modulo] [unidad] si se especifica módulo y unidad, se hará una pregunta de ese módulo y unidad.

- `!exams` [modulo] [unidad]
  Genera varias preguntas de examen del módulo/unidad indicado.
  Los parámetros funcionan igual que en !exam

- `!eval` [modulo] [unidad]
  Muestra una sola pregunta de autoevaluación (basada en EVALS).
  Los parámetros funcionan igual que en !exam

- `!evals` [modulo] [unidad]
  Genera múltiples preguntas de autoevaluación.
  Los parámetros funcionan igual que en !exam

- `!remix` [modulo] [unidad]
  Muestra una pregunta reformulada automáticamente a partir de las EVALS originales.
  Los parámetros funcionan igual que en !exam

- `!remixes` [modulo] [unidad]
  Genera varias preguntas remix.
  Los parámetros funcionan igual que en !exam

si se ejecuta uno de los QUIZ COMMANDS en una sala que empiece con el nombre "quizbot_" tomará el texto que viene a continuación como tema de la sala
en estos casos no es necesario lanzar el comando indicando el nombre del módulo.

por ejemplo:

quizbot_biologia    sera un canal temático de biología, y el boto solo mostrará resultados de biología.

en estos canales se puede indicar directamente la unidad.

!exam 3    lanzará preguntas de biologia (que es el canal temático) de la unidad 3


!reset
  Este comando sirve para resetear el contador personal de correctas/incorrectas.


## 💬 Formato de los mensajes interactivos

Las respuestas se envían por mensaje privado. Esto se ha hecho así para que los tests sean reutilizables por muchos usuarios.

Además, el bot cuenta con un sistema que asegura que se agotan todas las preguntas existentes en EVALS, antes de volver a repetir las preguntas.

En CONTENTS, ya que las preguntas son generadas por IA, es mas difícil que se repitan preguntas por que incluso el mismo contenido puede generar diferente preguntas y respuestas.

## 📂 Formato JSON de Preguntas y Evaluaciones

Actualmente, el proyecto cuenta con un parseador HTML para CONTENTS y para EVALS. estos html son los contenidos de cada módulo y pueden variar de centro en centro, por lo que si necestias ajustar para que el bot funcione con los contenidos de algún centro específico, tendrás que generar un nuevo parseador.

Puedes ayudarte de IA para generarlo. le tienes que indicar el fichero fuente (HTML con el contenido), y especificar que debe sacar el siguiente formato para que sea usable por el bot:

```
Ejemplo de CONTENTS
{
  "module": "Historia Pokémon",
  "total_archivos": 3,
  "total_parrafos": 250,
  "contenidos": [
    {
      "title": "Unidad 1 - Origen de los Pokémon",
      "sections": [
        {
          "title": "Primeros descubrimientos",
          "subsections": [
            {
              "type": "Caso práctico",
              "paragraphs": [
                {
                  "id": "P1",
                  "text": "El profesor Oak descubrió que los Pokémon se organizan en especies con habilidades únicas.",
                  "links": [],
                  "media": []
                }
              ]
            }
          ],
          "global_media": [
            {
              "src": "unidad1_files/pikachu.png",
              "alt": "Imagen de Pikachu",
              "title": "Pikachu en su hábitat natural"
            }
          ]
        }
      ]
    }
  ]
}
```

El parser lo que hace es analizar el fichero HTML, obtener párrafos y organizarlos en el json con la estructura anterior.


Para el caso de las autoevaluaciones, sigue un esquema parecido, aunque los HTML de autoevaluaciones tienen una estructura diferente, pero el objetivo es generar un json de salida normalizado.

La diferencia con respecto a los contenidos, es que los tests de autoevaluación, normalmente son generados por algún programa que obtiene preguntas y respuestas y las muestra en un formato de X preguntas por examen.

El parseador analiza los ficheros HTML, extrae las preguntas y luego verifica en el fichero json si existen dichas preguntas. si no existe, la agrega. Con esto se puede recrear la base de datos de preguntas originales que tiene el programa.

El formato de salida de EVALS es el siguiente
```
{
  "module": "Combates Pokémon",
  "total_preguntas": 50,
  "preguntas": [
    {
      "numero": "1",
      "enunciado": "¿Qué tipo de ataque es más efectivo contra un Pokémon de tipo Agua?",
      "opciones": [
        "Ataques de tipo fuego",
        "Ataques de tipo eléctrico",
        "Ataques de tipo normal",
        "Ataques de tipo veneno"
      ],
      "respuestas": ["1"],
      "retroalimentacion": "Los ataques de tipo eléctrico son más efectivos contra Pokémon de tipo Agua.",
      "type_quiz": "single",
      "media": [],
      "origen": {
        "modulo": "Combates Pokémon",
        "unidad": "Unidad 2",
        "usuario": "Anonimo",
        "archivo": "test_pokemon.html"
      }
    }
  ]
}
```

Cada módulo mantiene su propio fichero de parseo, tanto para CONTENTS como para EVALS.

esto asegura que el bot puede funcionar sin necesidad de realizar modificaciones, añadiendo simplemente los módulos nuevos, y luego parseando con su respectivo parser.

## 📋 Sistema de Templates para mensajes y prompts

En la carpeta TEMPLATES y PROMPTS existen ficheros txt que son plantillas para presentar mensajes de preguntas, respuestas y de la generación de prompts para generar las pregunas con LLM (IA)

Estos templates contienen una serie de placeholders que se actualizan dinámicamente en el bot. 

A continuación está un alista de los placeholders existentes hasta ahora, y su ámbito de uso:

📌 Lista de Placeholders en los Mensajes del Bot
Estos placeholders se utilizan dentro de los archivos de templates para mensajes en chat y mensajes en DM, reemplazando los valores con información generada dinámicamente.

🔹 Datos del usuario

- `{username}` → Nombre de usuario en Discord.
- `{user_id}` → ID del usuario en Discord.
- `{user_score}` → Puntuación acumulada del usuario.
- `{correct_answers}` → Número total de respuestas correctas del usuario.
- `{incorrect_answers}` → Número total de respuestas incorrectas del usuario.

🔹 Datos de la pregunta

- `{question_text}` → Enunciado de la pregunta generada.
- `{module_name}` → Nombre del módulo al que pertenece la pregunta.
- `{unit_name}` → Nombre de la unidad dentro del módulo.
- `{question_id}` → ID único de la pregunta en la base de datos.
- `{question_source}` → Indica si la pregunta fue generada por contenido (CONTENTS) o por evaluación (EVALS).
- `{question_type}` → Tipo de pregunta (single, multiple, true/false).

🔹 Opciones de respuesta

- `{options_list}` → Lista de opciones de respuesta.
- `{correct_option}` → Respuesta correcta esperada.
- `{user_response}` → Respuesta ingresada por el usuario.

🔹 Feedback y retroalimentación

- `{feedback_text}` → Mensaje de retroalimentación sobre la respuesta dada por el usuario.
- `{hint_text}` → Sugerencia o pista adicional sobre la pregunta.

🔹 Referencias y recursos

- `{related_link}` → Enlace a material de referencia.
- `{image_path}` → Ruta de la imagen asociada a la pregunta.
- `{image_alt_text}` → Descripción alternativa de la imagen.

🔹 Datos de mensajes en Discord

- `{channel_name}` → Nombre del canal de Discord donde se generó la pregunta.
- `{bot_mention}` → Mención al bot dentro del mensaje (@QuizBot).
- `{timestamp}` → Hora en la que se generó el mensaje.


### 🎯 Placeholders Generales (Mensajes y Preguntas)

Estos reemplazos se utilizan en la función show_question para generar mensajes dinámicos en Discord.

- `{source}` → Indica el origen de la pregunta (`evals` o `contents`).
- `{SOURCE}` → Igual que `{source}`, pero en mayúsculas.
- `{source_icon}` → Ícono visual del origen (`👤` evaluación, `🤖` bot).
- `{module}` → Nombre del módulo de la pregunta (Ej. "Matemáticas").
- `{MODULE}` → Igual que `{module}`, pero en mayúsculas.
- `{unit}` → Nombre de la unidad dentro del módulo.
- `{UNIT}` → Igual que `{unit}`, pero en mayúsculas.
- `{question_id}` → ID único de la pregunta.
- `{title}` → Título de la pregunta.
- `{TITLE}` → Igual que `{title}`, pero en mayúsculas.
- `{question_text}` → Texto completo de la pregunta.
- `{QUESTION_TEXT}` → Igual que `{question_text}`, pero en mayúsculas.
- `{options}` → Lista de opciones formateadas con símbolos.
- `{formatted_options}` → Versión estructurada de `{options}`.
- `{FORMATTED_OPTIONS}` → Igual que `{formatted_options}`, pero en mayúsculas.
- `{question_type}` → Tipo de pregunta (`múltiple` o `simple`).
- `{QUESTION_TYPE}` → Igual que `{question_type}`, pero en mayúsculas.
- `{section}` → Nombre de la unidad de la pregunta.
- `{subsection}` → Identificación específica dentro de la unidad.
- `{paragraph_text}` → Texto largo de la pregunta.
- `{correct_answer}` → Respuestas correctas en formato numérico.
- `{message_id}` → ID del mensaje en Discord.
- `{message_link}` → URL del mensaje en Discord.
- `{feedback}` → Texto con retroalimentación sobre la respuesta.
- `{original_question}` → Pregunta original antes de ser procesada.

### 🖱️ Placeholders para Botones (Respuestas en Chat y DM)

Se usan en los botones interactivos con respuestas y validaciones.

- `{result_icon}` → Ícono visual según si es correcto o incorrecto.
- `{symbol}` → Símbolo de la opción (`🔹`, `✅`, etc.).
- `{option_text}` → Texto de la opción elegida por el usuario.
- `{option_feedback}` → Retroalimentación asociada a la opción.
- `{result}` → Indica si la respuesta es `Correcto!` o `Incorrecto`.
- `{paragraph_text_correct}` → Texto de la pregunta con formato especial si es incorrecto.
- `{incorrect}` → Se aplica efecto visual (`||texto oculto||`) en respuestas incorrectas.

🎯 Metadatos
- `{module_info}` → Información detallada del módulo obtenida desde el directorio INFO ([modulo]_Info.json).
- `{module_prompt}` → Prompt específico del módulo, cargado desde el directorio del TEMPLATE ([modulo]_prompt.txt).
- `{module}` → Nombre del módulo relacionado con el contenido.
- `{unidad}` → Nombre de la unidad dentro del módulo.
- `{section_title}` → Título de la sección actual en el contenido.
- `{archivo}` → Nombre del archivo fuente del contenido.

📜 Párrafos
- `{main_paragraph}` → Párrafo principal seleccionado del contenido.
- `{main_paragraph_id}` → ID único del párrafo principal seleccionado.
- `{previous_paragraph}` → Texto combinado de los párrafos previos.
- `{next_paragraph}` → Texto combinado de los párrafos siguientes.

⚙️ Configuración
- `{total_options}` → Número total de opciones disponibles en la pregunta.


## 🛠 Mantenimiento y Expansión
El bot está diseñado para ser modular. Para agregar soporte a nuevas instituciones educativas o plataformas, es necesario crear un nuevo parseador que genere archivos JSON en el formato estándar mostrado anteriormente.

## 📝 Licencia

Este proyecto está protegido bajo la licencia **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.

📌 **Términos principales**:
- Puedes **usar, modificar y distribuir** el contenido de este proyecto.
- **No está permitido el uso comercial** sin autorización.
- Siempre debes **mencionar la autoría** (DNX) en cualquier adaptación o distribución.

📄 Para más información sobre la licencia, visita:  
🔗 [Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)


## 🤖 Información extra
Este bot ha sido desarrollado como una herramienta de aprendizaje comunitario, escalable y que se puede adaptar a múltiples formatos de contenidos. Espero que sea una herramienta útil.

## Algunas capturas

Las siguientes son capturas utilizando contenido generado como ejemplo.

### Comando !dir

![image](https://github.com/user-attachments/assets/15e4ba77-a49d-4841-8e8c-080ef1672e39)

NOTA: Los contenidos son generados para la demo.

### Comando !exam

![image](https://github.com/user-attachments/assets/86e29fbd-c52c-4fe0-b07e-b5115fd090fb)

![image](https://github.com/user-attachments/assets/470b306a-bff0-4398-b734-9fa504ba1c32)

### Comando !eval

![image](https://github.com/user-attachments/assets/e6950b70-c475-449b-962e-a029b63a95cd)

![image](https://github.com/user-attachments/assets/8d62b5eb-6bea-434b-b55b-180155ea436d)


### Ejemplo de mensaje popup de Discord con información de la opción seleccionada

![image](https://github.com/user-attachments/assets/932f4e3e-5ee9-4f88-8aa6-3747b0a869c4)

![image](https://github.com/user-attachments/assets/d03e0a06-655e-40ec-b3cd-58808d908ebf)

### Mensaje Directo enviado por el bot con la opción seleccionada

![image](https://github.com/user-attachments/assets/2caaedf7-ef9f-4a57-a777-60adb580e49d)

![image](https://github.com/user-attachments/assets/4d0f0cad-8fd4-498f-ac82-3c1231159fa4)

Cuando la respuesta es incorrecta, la retroalimentación, en el caso de ser una evaluación, muestra en spoiler la respuesta, para que el usuario pueda probar nuevamente sin ver la respuesta directamente.

En el caso de Exam, si es correcta, muestra el párrafo seleccionado para generar la pregunta y sus opciones de respuestas.

![image](https://github.com/user-attachments/assets/a09e35cb-9f6e-4b9d-ab05-e5cbee997196)

En este ejemplo, la pregunta es de selección múltiple por lo que había que responder correctamente a todos los botones.

Cuando el usuario falla en una pregunta de !exam, se muestra regroalimentación sobre la opción seleccionada, informando por que no es correcta.

por ejemplo en esta pregunta:

![image](https://github.com/user-attachments/assets/db99ce32-c383-4d00-b3f3-6ba01be0b31c)

La primera opción no es la correcta, por lo que se muestra el popup

![image](https://github.com/user-attachments/assets/a47666d1-6dcd-4dd0-aa6e-16e520cc8623)

y el mensaje directo que envía el bot contiene esta información:

![image](https://github.com/user-attachments/assets/088540e3-b853-4721-bcdd-536bf75fc903)

Donde se puede apreciar que al comienzo se ha indicado por que es incorrecta la selección.

Y para el caso de responder correctamente:

![image](https://github.com/user-attachments/assets/502c3789-7a1d-4235-ba80-d199b5124522)

Se muestra completamente el texto de retroalimentación, sin spoilers.

![image](https://github.com/user-attachments/assets/7df3b3cf-b4d2-4f4d-b9f6-e963aca31720)


¡Feliz aprendizaje con QuizBot! 🚀

Project Coded By:
DNX Projects
