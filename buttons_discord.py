# ======== buttons.py (Versión Mejorada) ========
import json
import os
import random
import logging
import discord
from discord.ui import Button, View
from typing import List, Dict, Any, Tuple, Optional, Union
from score_manager import ScoreManager

# Inicializa el score manager
SCORE_MANAGER = ScoreManager()

# ======== Carga de temas desde archivo JSON ========
def load_themes(filename: str = "buttons_discord_THEMES.json") -> Dict[str, List[str]]:
    """Carga los temas de botones desde un archivo JSON"""
    try:
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        
        if not os.path.exists(filepath):
            logging.warning(f"Archivo de temas {filepath} no encontrado. Usando temas por defecto.")
            return {
                "letters": ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
                "uletters": ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
                "numbers": ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
            }
        
        with open(filepath, 'r', encoding='utf-8') as f:
            themes = json.load(f)
            
            # Validar la estructura del archivo
            if not isinstance(themes, dict):
                raise ValueError("El archivo de temas debe ser un diccionario")
                
            for key, value in themes.items():
                if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                    raise ValueError(f"El tema '{key}' debe ser una lista de strings")
            
            return themes
            
    except json.JSONDecodeError:
        logging.error(f"Error al decodificar el archivo de temas {filename}. Usando temas por defecto.")
        return {
            "letters": ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
            "uletters": ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
            "numbers": ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        }
    except Exception as e:
        logging.error(f"Error al cargar temas: {str(e)}. Usando temas por defecto.")
        return {
            "letters": ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'],
            "uletters": ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
            "numbers": ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        }

# Cargamos los temas al inicio
BUTTON_THEMES = load_themes()

# ======== Clase InteractiveButton ========
class InteractiveButton:
    def __init__(
        self,
        label: str,
        style: discord.ButtonStyle,
        callback: Optional[callable] = None,
        message: Optional[str] = None,
        direct_message: Optional[str] = None,
        option_reply: str = "",
        prefix_theme: str = ""
    ):
        """
        Crea un botón interactivo con todas las características necesarias.
        
        Args:
            label: Texto visible en el botón
            style: Estilo del botón (discord.ButtonStyle)
            callback: Función a ejecutar al presionar el botón
            message: Mensaje de respuesta en el chat
            direct_message: Mensaje privado al usuario
            option_reply: Respuesta específica de la opción
            prefix_theme: Prefijo temático del botón
        """
        self.label = label
        self.style = style
        self.callback = callback
        self.message = message
        self.direct_message = direct_message
        self.option_reply = option_reply
        self.prefix_theme = prefix_theme

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el botón a diccionario (serializable)"""
        return {
            'label': self.label,
            'style': self.style.value,
            'message': self.message,
            'direct_message': self.direct_message,
            'option_reply': self.option_reply,
            'prefix_theme': self.prefix_theme
        }

# ======== Clase PersistentButtonView ========
class PersistentButtonView(View):
    def __init__(self, message_id: int, buttons: List[InteractiveButton]):
        """
        Vista persistente de botones que sobrevive a reinicios del bot.
        
        Args:
            message_id: ID del mensaje al que están asociados los botones
            buttons: Lista de botones interactivos
        """
        super().__init__(timeout=None)
        self.message_id = message_id
        for btn in buttons:
            self.add_item(self._create_persistent_button(btn))

    def _create_persistent_button(self, button_data: InteractiveButton) -> Button:
        """Crea un botón persistente con su callback"""
        button = Button(
            label=button_data.label,
            style=button_data.style,
            custom_id=f"persist_{self.message_id}_{button_data.label.replace(' ', '_')}"
        )
        
        async def button_callback(interaction: discord.Interaction):
            """Callback base para botones persistentes"""
            try:
                ## Determinar si la respuesta es correcta
                #is_correct = any(
                #    button_data.prefix_theme == symbol 
                #    for symbol in BUTTON_THEMES.get("correct", ["✅", "✓"])
                #)
                
                is_correct = button_data.message.strip().startswith("✅") or button_data.direct_message.strip().startswith("✅")
                #print(f"is_correct:{is_correct}   button_data.message:{button_data.direct_message}")
                

                # Actualizar puntuación
                SCORE_MANAGER.update_score(interaction.user.id, is_correct)
                
                # Obtener estadísticas actualizadas
                scores = SCORE_MANAGER.get_scores(interaction.user.id)
                
                # Reemplazar placeholders en los mensajes
                message_with_scores = button_data.message.replace("{correct_points}", str(scores["correct"])) \
                    .replace("{incorrect_points}", str(scores["incorrect"])) \
                    .replace("{total_points}", str(scores["total"])) \
                    .replace("{average_points}", f"{scores['average']:.1f}%")
                    
                dm_with_scores = button_data.direct_message.replace("{correct_points}", str(scores["correct"])) \
                    .replace("{incorrect_points}", str(scores["incorrect"])) \
                    .replace("{total_points}", str(scores["total"])) \
                    .replace("{average_points}", f"{scores['average']:.1f}%")
                
                # Manejar mensaje directo primero
                if dm_with_scores:
                    try:
                        await interaction.user.send(dm_with_scores)
                    except discord.Forbidden:
                        pass  # No se pueden enviar DMs al usuario
                
                # Manejar respuesta de interacción
                if message_with_scores:
                    await interaction.response.send_message(
                        message_with_scores,
                        ephemeral=True
                    )
                else:
                    await interaction.response.defer(ephemeral=True)
                    
            except Exception as e:
                logging.error(f"Error en button callback: {e}", exc_info=True)
                try:
                    await interaction.response.defer(ephemeral=True)
                except:
                    pass

        button.callback = button_callback
        return button


def pick_theme(
    nombre: Optional[str] = None, 
    solo_booleans: bool = False,
    min_options: int = 2
) -> Tuple[str, List[str]]:
    """
    Selecciona un tema válido según los parámetros dados.
    
    Args:
        nombre: Nombre del tema específico a usar (None para aleatorio)
        solo_booleans: Si True, solo devuelve temas con 2 opciones
        min_options: Mínimo de opciones que debe tener el tema
        
    Returns:
        Tuple con (nombre_tema, lista_de_simbolos)
        
    Raises:
        ValueError: Si no hay temas que cumplan los criterios
    """
    # Si se especificó un tema, verificar que sea válido
    if nombre:
        tema = BUTTON_THEMES.get(nombre)
        if tema:
            if (solo_booleans and len(tema) != 2) or len(tema) < min_options:
                raise ValueError(f"El tema '{nombre}' no cumple con los criterios requeridos")
            return nombre, tema
        else:
            logging.warning(f"Tema '{nombre}' no encontrado. Selección aleatoria.")
    
    # Filtrar temas según criterios
    posibles = {}
    for k, v in BUTTON_THEMES.items():
        if solo_booleans:
            if len(v) == 2:
                posibles[k] = v
        else:
            if len(v) >= min_options:
                posibles[k] = v
    
    if not posibles:
        raise ValueError("No hay temas válidos para los criterios dados.")
    
    nombre_aleatorio = random.choice(list(posibles.keys()))
    return nombre_aleatorio, posibles[nombre_aleatorio]

def get_buttons_filepath(filename: str = "buttons.json") -> str:
    """Obtiene la ruta absoluta del archivo de botones"""
    if os.path.isabs(filename):
        return filename
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, filename)

# ======== Función save_buttons mejorada ========
def save_buttons(
    filename: str, 
    buttons_data: Dict[Union[int, str], List[Union[InteractiveButton, Dict]]],
    merge: bool = True  # Nuevo parámetro para controlar si mezclar con existentes
) -> None:
    """
    Guarda los botones en el archivo, con opción de mezclar con los existentes.
    
    Args:
        filename: Nombre del archivo
        buttons_data: Diccionario con los nuevos botones a guardar
        merge: Si True, mezcla con los botones existentes. Si False, sobrescribe todo.
        
    Raises:
        Exception: Si ocurre un error al guardar
    """
    try:
        filepath = get_buttons_filepath(filename)
        
        # Convertir a formato serializable
        serializable_data = {}
        for msg_id, buttons in buttons_data.items():
            if isinstance(buttons[0], InteractiveButton):
                serializable_data[str(msg_id)] = [btn.to_dict() for btn in buttons]
            else:
                serializable_data[str(msg_id)] = buttons
        
        # Si merge=True, cargar los existentes primero
        if merge:
            existing_data = {}
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    logging.warning("No se pudo cargar el archivo existente, se creará uno nuevo")
            
            # Combinar los datos (los nuevos sobrescriben los existentes si hay conflictos)
            serializable_data = {**existing_data, **serializable_data}
        
        # Guardado atómico
        temp_file = filepath + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        
        if os.path.exists(filepath):
            os.remove(filepath)
        os.rename(temp_file, filepath)
        
        logging.info(f"Botones guardados en {filepath}")
    except Exception as e:
        logging.error(f"Error al guardar botones: {str(e)}", exc_info=True)
        raise
    
def load_buttons(filename: str = "buttons.json") -> Dict[int, List[InteractiveButton]]:
    """
    Carga los botones persistentes desde archivo
    
    Args:
        filename: Nombre del archivo a cargar
        
    Returns:
        Diccionario con los botones cargados
    """
    filepath = get_buttons_filepath(filename)
    
    if not os.path.exists(filepath):
        logging.warning(f"Archivo {filepath} no encontrado. Se creará uno nuevo.")
        return {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        result = {}
        for msg_id, btn_list in data.items():
            buttons = []
            for item in btn_list:
                btn = InteractiveButton(
                    label=item.get('label', ''),
                    style=discord.ButtonStyle(item.get('style', 1)),
                    callback=None,  # Se asignará en PersistentButtonView
                    message=item.get('message'),
                    direct_message=item.get('direct_message'),
                    option_reply=item.get('option_reply', ''),
                    prefix_theme=item.get('prefix_theme', '')
                )
                buttons.append(btn)
            result[int(msg_id)] = buttons
        return result
    
    except json.JSONDecodeError:
        logging.warning(f"Archivo {filepath} corrupto o vacío. Se creará uno nuevo.")
        return {}
    except Exception as e:
        logging.error(f"Error cargando botones: {str(e)}", exc_info=True)
        return {}

def create_theme_message(
    title: str,
    options: List[InteractiveButton],
    theme: str = "letters"
) -> Tuple[discord.Embed, List[InteractiveButton]]:
    """
    Crea un mensaje temático con botones
    
    Args:
        title: Título del mensaje/embed
        options: Lista de opciones/botones
        theme: Tema a usar para los botones
        
    Returns:
        Tuple con (Embed, Lista de botones temáticos)
    """
    # Seleccionar tema adecuado
    if theme == "random":
        try:
            theme, _ = pick_theme(min_options=len(options))
        except ValueError:
            theme = "letters"
    elif theme not in BUTTON_THEMES:
        theme = "letters"

    theme_symbols = BUTTON_THEMES[theme]
    description_lines = [title, ""]
    themed_buttons = []

    for idx, option in enumerate(options):
        symbol = theme_symbols[idx] if idx < len(theme_symbols) else str(idx + 1)
        description_lines.append(f"{symbol} - {option.label}")
        
        themed_buttons.append(InteractiveButton(
            label=symbol,
            style=option.style,
            callback=option.callback,
            message=option.message,
            direct_message=option.direct_message,
            option_reply=option.option_reply,
            prefix_theme=symbol
        ))

    embed = discord.Embed(
        description="\n".join(description_lines),
        color=discord.Color.blue()
    )
    return embed, themed_buttons