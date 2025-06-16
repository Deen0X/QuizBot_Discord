# ======== buttons.py (Versión Corregida) ========
import json
import os
import random
import logging
import discord
from discord.ui import Button, View
from typing import List, Dict, Any, Tuple, Optional, Union
from typing import List, Optional, Tuple
import discord

# ======== Clase InteractiveButton ========
class InteractiveButton:
    def __init__(
        self,
        label: str,
        style: discord.ButtonStyle,
        callback=None,  # Cambiado a valor por defecto None
        message: Optional[str] = None,
        direct_message: Optional[str] = None,
        option_reply: str = "",
        prefix_theme: str = "",
        row: int = 0,
        action: Optional[callable] = None,
        custom_id: Optional[str] = None
    ):
        self.label = label
        self.style = style
        self.callback = callback
        self.message = message
        self.direct_message = direct_message
        self.option_reply = option_reply
        self.prefix_theme = prefix_theme
        self.row = row
        self.action = action
        self.custom_id = custom_id

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el botón a diccionario (serializable)"""
        return {
            'label': self.label,
            'style': self.style.value,
            'message': self.message,
            'direct_message': self.direct_message,
            'option_reply': self.option_reply,
            'prefix_theme': self.prefix_theme,
            'row': self.row,
            'custom_id': self.custom_id
            # No serializamos callback ni action
        }

# ======== Diccionarios de formatos predefinidos ========
def load_button_themes(filename: str = "buttons_discord_THEMES.json") -> Dict[str, List[str]]:
    """Carga los temas de botones desde un archivo JSON"""
    #filepath = get_buttons_filepath(filename)
    filepath = filename
    if not os.path.exists(filepath):
        logging.warning(f"Archivo {filepath} no encontrado. Se usará un diccionario vacío.")
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error al cargar temas de botones: {e}")
        return {}

BUTTON_THEMES = load_button_themes()


# ======== Clase PersistentButtonView ========
class PersistentButtonView(View):
    def __init__(self, message_id: int, buttons: List[InteractiveButton]):
        super().__init__(timeout=None)
        self.message_id = message_id
        
        # Organizar por filas primero
        buttons_by_row = {}
        for btn in buttons:
            if btn.row not in buttons_by_row:
                buttons_by_row[btn.row] = []
            buttons_by_row[btn.row].append(btn)
        
        # Añadir botones en orden de fila
        for row in sorted(buttons_by_row.keys()):
            for btn in buttons_by_row[row]:
                discord_btn = Button(
                    label=btn.label,
                    style=btn.style,
                    custom_id=btn.custom_id or f"persist_{message_id}_{btn.label.replace(' ', '_')}",
                    row=row
                )
                
                # Asignar callback dinámico
                discord_btn.callback = self.create_callback(btn)
                self.add_item(discord_btn)
    
    def create_callback(self, button_data: InteractiveButton):
        """Crea un callback personalizado para cada botón"""
        async def button_callback(interaction: discord.Interaction):
            try:
                # Ejecutar acción personalizada si existe
                if button_data.action:
                    await button_data.action(interaction, button_data)
                
                # Comportamiento base (mensajes)
                if button_data.direct_message:
                    try:
                        await interaction.user.send(button_data.direct_message)
                    except discord.Forbidden:
                        pass
                
                if button_data.message:
                    await interaction.response.send_message(
                        button_data.message,
                        ephemeral=True
                    )
                elif not button_data.action:  # Solo deferir si no hay acción personalizada
                    await interaction.response.defer(ephemeral=True)
            
            except Exception as e:
                logging.error(f"Error en callback: {e}")
                await interaction.response.defer(ephemeral=True)
        
        return button_callback



def pick_theme(nombre: Optional[str] = None, solo_booleans: bool = False) -> Tuple[str, List[str]]:
    """Selecciona un tema válido según los parámetros dados."""
    if nombre:
        tema = BUTTON_THEMES.get(nombre)
        if tema:
            return nombre, tema
        else:
            logging.warning(f"Tema '{nombre}' no encontrado. Selección aleatoria.")
    
    if solo_booleans:
        posibles = {k: v for k, v in BUTTON_THEMES.items() if len(v) == 2}
    else:
        posibles = {k: v for k, v in BUTTON_THEMES.items() if len(v) > 2}
    
    if not posibles:
        raise ValueError("No hay temas válidos para los criterios dados.")
    
    nombre_aleatorio = random.choice(list(posibles.keys()))
    return nombre_aleatorio, posibles[nombre_aleatorio]

def build_message_chat(
    texto: str,
    lista_opciones: List[Union[str, Tuple[str, callable]]],  # Ahora acepta tuplas (texto, acción)
    submensaje: Optional[str] = None,
    imagen_o_enlace: Optional[str] = None,
    subopciones: Optional[List[Union[str, Tuple[str, callable]]]] = None,
    tema: Optional[str] = None,
) -> Tuple[str, discord.Embed, List[InteractiveButton]]:
    """Versión que soporta acciones personalizadas por botón"""
    nombre_tema, simbolos = pick_theme(tema, solo_booleans=(len(lista_opciones) == 2))
    
    partes = [texto.strip()]
    botones = []
    
    # Procesar opciones principales
    for i, opcion in enumerate(lista_opciones):
        opcion_texto, *accion = (opcion if isinstance(opcion, tuple) else (opcion, None))
        simbolo = simbolos[i] if i < len(simbolos) else str(i + 1)
        partes.append(f"{simbolo} - {opcion_texto}")
        
        botones.append(InteractiveButton(
            label=simbolo,
            style=discord.ButtonStyle.primary,
            message=f"Selección: {opcion_texto}",
            option_reply=opcion_texto,
            prefix_theme=simbolo,
            row=0,
            action=accion[0] if accion else None
        ))
    
    if submensaje:
        partes.append(submensaje.strip())
    
    mensaje_final = "\n".join(partes)
    
    # Crear embed si hay imagen
    embed = None
    if imagen_o_enlace:
        embed = discord.Embed(description=mensaje_final, color=discord.Color.blue())
        if imagen_o_enlace.startswith(("http://", "https://")):
            embed.set_image(url=imagen_o_enlace)
    
    # Procesar subopciones
    if subopciones:
        for sub in subopciones:
            sub_texto, *accion = (sub if isinstance(sub, tuple) else (sub, None))
            botones.append(InteractiveButton(
                label=sub_texto,
                style=discord.ButtonStyle.secondary,
                message=f"Acción: {sub_texto}",
                option_reply=sub_texto,
                prefix_theme="",
                row=1,
                action=accion[0] if accion else None
            ))
    
    return mensaje_final, embed, botones


# ======== Funciones de persistencia ========
def get_buttons_filepath(filename: str = "buttons.json") -> str:
    """Obtiene la ruta absoluta del archivo de botones"""
    # Si la ruta ya es absoluta, usarla directamente
    if os.path.isabs(filename):
        return filename
    
    # Si no, crear el archivo en el directorio del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, filename)

#======== Función pública: Guardar todos los botones
def save_buttons(filename: str, buttons_data: dict) -> None:
    """Guarda todos los botones en el archivo (sobrescribe)"""
    try:
        filepath = get_buttons_filepath(filename)
        
        # Convertir solo los datos necesarios
        serializable_data = {}
        for msg_id, buttons in buttons_data.items():
            if isinstance(buttons[0], InteractiveButton):  # Si son objetos InteractiveButton
                serializable_data[str(msg_id)] = [btn.to_dict() for btn in buttons]
            else:  # Si ya están en formato diccionario
                serializable_data[str(msg_id)] = buttons
        
        # Guardado atómico
        temp_file = filepath + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        
        if os.path.exists(filepath):
            os.remove(filepath)
        os.rename(temp_file, filepath)
        
        logging.info(f"Botones actualizados en {filepath}")
    except Exception as e:
        logging.error(f"Error al guardar botones: {str(e)}")
        raise


# ======== Funciones de persistencia ========
def load_buttons(filename: str = "buttons.json") -> Dict[int, List[InteractiveButton]]:
    """Carga los botones persistentes desde archivo"""
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
                # Crear botón con todos los atributos
                btn = InteractiveButton(
                    label=item.get('label', ''),
                    style=discord.ButtonStyle(item.get('style', 1)),
                    callback=None,
                    message=item.get('message', ''),
                    direct_message=item.get('direct_message', ''),
                    option_reply=item.get('option_reply', ''),
                    prefix_theme=item.get('prefix_theme', ''),
                    row=item.get('row', 0),  # Añadido
                    custom_id=item.get('custom_id', None)  # Añadido
                )
                buttons.append(btn)
            result[int(msg_id)] = buttons
        return result
    
    except json.JSONDecodeError:
        logging.warning(f"Archivo {filepath} corrupto o vacío. Se creará uno nuevo.")
        return {}
    except Exception as e:
        logging.error(f"Error cargando botones: {str(e)}")
        return {}


# ======== Función create_theme_message ========
def create_theme_message(
    title: str,
    options: List[InteractiveButton],
    theme: str = "letters"
) -> Tuple[discord.Embed, List[InteractiveButton]]:
    """Crea un mensaje temático con botones"""
    if theme == "random":
        theme = random.choice(list(BUTTON_THEMES.keys()))
        while theme.startswith("bool") and len(options)>2:
            theme = random.choice(list(BUTTON_THEMES.keys()))
    if theme not in BUTTON_THEMES:
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

## Callback por defecto para botones persistentes
#async def button_callback(interaction: discord.Interaction):
#    """Callback base para botones persistentes"""
#    await interaction.response.send_message(
#        "Botón persistente presionado!", 
#        ephemeral=True
#    )