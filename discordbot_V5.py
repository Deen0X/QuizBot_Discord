# ======== discordbot_V5.py ========
import sys
import discord
import logging
import random
import os
from datetime import datetime
from discord.ext import commands
import json
import asyncio
from pathlib import Path
from buttons_discord import (
    InteractiveButton, 
    PersistentButtonView,
    save_buttons,
    load_buttons,
    create_theme_message,
    BUTTON_THEMES
)
from utils import Utils, DirectoryLister
from quiz_EVALS import QuizGeneratorEVALS
from quiz_CONTENTS import QuizGeneratorCONTENTS
from score_manager import ScoreManager

# Inicializa el score manager
SCORE_MANAGER = ScoreManager()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Variable global para vistas persistentes
persistent_views = {}

async def button_callback(interaction: discord.Interaction):
    """Callback base para botones"""
    await interaction.response.send_message(
        "Botón presionado!", 
        ephemeral=True
    )

def generate_random_buttons(count: int, random_id: int) -> list[InteractiveButton]:
    """Genera botones de ejemplo con mensajes aleatorios"""
    buttons = []
    
    for i in range(1, count + 1):
        buttons.append(
            InteractiveButton(
                label=f"Button {i} {random_id}",
                style=discord.ButtonStyle.primary,
                callback=button_callback,
                message=f"Hello from button {i}! {random_id}",
                direct_message=f"Thanks for clicking button {i}! {random_id}",
                option_reply=f"Opción de respuesta {i} {random_id}",
            )
        )
    return buttons

# ======== Función pública: Verificar mensaje existente
async def message_exists(bot: commands.Bot, channel_id: int, message_id: int) -> bool:
    """Verifica si un mensaje existe en un canal"""
    try:
        channel = bot.get_channel(channel_id)
        if channel:
            message = await channel.fetch_message(message_id)
            return message is not None
    except discord.NotFound:
        return False
    except Exception as e:
        logging.error(f"Error verificando mensaje {message_id}: {e}")
        return False
    return False

# -------- Método privado: Limpiar botones inexistentes
async def cleanup_nonexistent_buttons(bot: commands.Bot, all_buttons: dict) -> dict:
    """Elimina botones de mensajes que ya no existen"""
    cleaned_buttons = {}
    for message_id, buttons in all_buttons.items():
        try:
            # Extraer channel_id del primer botón (asumimos mismo canal)
            if buttons and hasattr(buttons[0], 'channel_id'):
                channel_id = buttons[0].channel_id
                exists = await message_exists(bot, channel_id, int(message_id))
                if exists:
                    cleaned_buttons[message_id] = buttons
                else:
                    logging.info(f"Eliminando botones de mensaje inexistente: {message_id}")
            else:
                cleaned_buttons[message_id] = buttons
        except Exception as e:
            logging.error(f"Error limpiando botones {message_id}: {e}")
            continue
    
    return cleaned_buttons

def start_bot():
    """Inicia y configura el bot de Discord"""
    config = Utils.load_config()
    if not config:
        print("No se pudo cargar el archivo config.json")
        return

    token = config.get("TOKEN")
    command_prefix = config.get("COMMAND_PREFIX", "!")

    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True
    intents.guilds = True

    bot = commands.Bot(
        command_prefix=command_prefix,
        intents=intents,
        help_command=None
    )

    @bot.event
    async def on_ready():
        """Evento cuando el bot está listo"""
        print(f"***********************\nBot conectado como {bot.user} (ID: {bot.user.id})\n***********************")

        # Cargar y limpiar botones persistentes
        all_buttons = load_buttons()
        cleaned_buttons = await cleanup_nonexistent_buttons(bot, all_buttons)
        
        # Guardar cambios si hubo limpieza
        if len(cleaned_buttons) != len(all_buttons):
            save_buttons("buttons.json", cleaned_buttons)
        
        loaded_count = 0
        loaded_views = 0

        # Cargar botones persistentes
        all_buttons = load_buttons()
        for message_id, buttons in all_buttons.items():
            try:
                view = PersistentButtonView(int(message_id), buttons)
                bot.add_view(view)
                persistent_views[int(message_id)] = view
                loaded_count += len(buttons)
                loaded_views += 1
            except Exception as e:
                logging.error(f"Error cargando vista {message_id}: {e}")

        # Mostrar resumen de carga
        if loaded_count > 0:
            logging.info(f"Se han cargado {loaded_count} botones persistentes")
            print(f"✅ Se han cargado {loaded_count} botones persistentes")
        else:
            logging.info("No se encontraron botones persistentes para cargar")
            print("ℹ️ No se encontraron botones persistentes para cargar")            

        if loaded_views > 0:
            logging.info(f"Se han cargado {loaded_views} vistas persistentes")
            print(f"✅ Se han cargado {loaded_views} vistas persistentes")
        else:
            logging.info("No se encontraron vistas persistentes para cargar")
            print("ℹ️ No se encontraron vistas persistentes para cargar")       

        print("\n\nBot inicializado!")

    @bot.event
    async def on_command_error(ctx, error):
        """Manejo de errores de comandos"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Comando no encontrado. Usa !help para ver los comandos disponibles.")
        else:
            logging.error(f"Error en comando: {error}")

    # ======== COMANDO: button (botón único) ========
    @bot.command(name="button")
    async def show_button(ctx):
        """Muestra un solo botón interactivo"""
        button = InteractiveButton(
            label="Click Me",
            style=discord.ButtonStyle.primary,
            callback=button_callback,
            message="Hello from single button!",
            direct_message="Thanks for clicking the single button!"
        )

        view = PersistentButtonView(ctx.message.id, [button])
        bot.add_view(view)
        
        # Corregido: Ahora pasamos un diccionario con el message_id como clave
        buttons_data = {str(ctx.message.id): [button]}
        save_buttons("buttons.json", buttons_data)
        
        await ctx.send("Single button:", view=view)

    # ======== COMANDO: buttons (múltiples botones) ========
    @bot.command(name="buttons")
    async def show_multiple_buttons(ctx):
        """Muestra múltiples botones aleatorios"""
        random_id = random.randint(10000, 99999)
        num_buttons = random.randint(3, 6)
        buttons = generate_random_buttons(num_buttons, random_id)

        view = PersistentButtonView(ctx.message.id, buttons)
        bot.add_view(view)
        
        # Corregido: Ahora pasamos un diccionario con el message_id como clave
        buttons_data = {str(ctx.message.id): buttons}
        save_buttons("buttons.json", buttons_data)
        
        await ctx.send(f"Here are {num_buttons} buttons:", view=view)

    # ======== COMANDO: theme (botones temáticos) ========
    @bot.command(name="theme")
    async def show_theme_buttons(ctx, theme: str = "random"):
        """Muestra botones con temas visuales"""
        num_buttons = random.randint(3, 6)
        random_id = random.randint(10000, 99999)
        options = generate_random_buttons(num_buttons, random_id)
        if theme.startswith("bool"):
            options = options[:2]  # Limitar a 2 opciones para temas booleanos
        
        embed, themed_buttons = create_theme_message(
            f"**Encuesta de ejemplo {random_id}**",
            options,
            theme
        )
        
        view = PersistentButtonView(ctx.message.id, themed_buttons)
        bot.add_view(view)
        
        # Corregido: Ahora pasamos un diccionario con el message_id como clave
        buttons_data = {str(ctx.message.id): themed_buttons}
        save_buttons("buttons.json", buttons_data)
        
        await ctx.send(embed=embed, view=view)

    # ======== COMANDO: Clean ==========
    @bot.command(name='clean')
    @commands.has_permissions(manage_messages=True)
    async def clean(ctx):
        """Limpia el canal actual y elimina solo sus botones persistentes"""
        try:
            # 1. Obtener todos los IDs de mensajes del canal actual
            channel_message_ids = {str(msg.id) async for msg in ctx.channel.history(limit=None)}
            
            # 2. Cargar todos los botones existentes
            all_buttons = load_buttons()
            
            # 3. Eliminar solo los botones del canal actual
            buttons_to_keep = {
                msg_id: buttons for msg_id, buttons in all_buttons.items() 
                if msg_id not in channel_message_ids
            }
            
            # 4. Guardar solo si hubo cambios
            if len(buttons_to_keep) != len(all_buttons):
                save_buttons("buttons.json", buttons_to_keep)
                logging.info(f"Eliminados {len(all_buttons)-len(buttons_to_keep)} botones del canal {ctx.channel.id}")
            
            # 5. Limpiar el canal
            await ctx.channel.purge()
            await ctx.send("✅ Canal limpiado y botones persistentes actualizados.", delete_after=3)
            
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para borrar mensajes.")
        except Exception as e:
            logging.error(f"Error en comando limpiar: {e}")
            await ctx.send(f"❌ Error al limpiar: {e}")

    # ======== COMANDO: limpiar ========
    @bot.command(name='limpiar')
    @commands.has_permissions(manage_messages=True)
    async def limpiar(ctx):
        """Limpia el canal actual y elimina sus botones persistentes"""
        try:
            # 1. Obtener todos los IDs de mensajes del canal actual como strings
            channel_messages = [str(msg.id) async for msg in ctx.channel.history(limit=None)]
            channel_message_ids = set(channel_messages)
            
            # Debug: Mostrar los primeros 5 IDs del canal
            logging.info(f"IDs de mensajes en el canal (primeros 5): {list(channel_message_ids)[:5]}")
            
            # 2. Cargar todos los botones existentes
            all_buttons = load_buttons()
            
            # Debug: Mostrar los primeros 5 IDs de botones persistentes
            logging.info(f"IDs de botones persistentes (primeros 5): {list(all_buttons.keys())[:5]}")
            
            # 3. Filtrar botones que pertenecen a este canal
            buttons_to_keep = {}
            removed_count = 0
            
            for msg_id, buttons in all_buttons.items():
                # Asegurarnos que el msg_id es string (por si acaso)
                str_msg_id = str(msg_id)
                if str_msg_id in channel_message_ids:
                    removed_count += 1
                    logging.info(f"Eliminando botones del mensaje: {str_msg_id}")
                else:
                    buttons_to_keep[str_msg_id] = buttons
            
            # Debug: Mostrar intersección
            common_ids = set(all_buttons.keys()) & channel_message_ids
            logging.info(f"Mensajes con botones persistentes encontrados: {len(common_ids)}")
            
            # 4. Eliminar físicamente los mensajes del canal
            await ctx.channel.purge()
            
            # 5. Actualizar el archivo de botones si hubo cambios
            if removed_count > 0:
                # Forzar guardado completo (no merge)
                save_buttons("buttons.json", buttons_to_keep, merge=False)
                msg = f"✅ Canal limpiado y {removed_count} botones persistentes eliminados."
                logging.info(msg)
                # Verificar que el archivo se actualizó
                post_clean_buttons = load_buttons()
                logging.info(f"Botones restantes después de limpiar: {len(post_clean_buttons)}")
                await ctx.send(msg, delete_after=5)
            else:
                msg = "✅ Canal limpiado (no había botones persistentes)."
                await ctx.send(msg, delete_after=3)
                
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para borrar mensajes.")
        except Exception as e:
            logging.error(f"Error en comando limpiar: {e}", exc_info=True)
            await ctx.send(f"❌ Error al limpiar: {str(e)}")


    #Este comando limpia todos los botones del bot en todas las salas. cuidado!
    @bot.command(name='limpiartodo')
    @commands.has_permissions(manage_messages=True)
    async def limpiartodo(ctx):
        """Limpia TODO el canal y elimina TODOS los botones persistentes asociados a mensajes de este canal"""
        try:
            deleted_ids = set()
            last_message = None

            while True:
                deleted_batch = await ctx.channel.purge(limit=100, before=last_message)
                if not deleted_batch:
                    break
                deleted_ids.update(str(msg.id) for msg in deleted_batch)
                last_message = deleted_batch[-1]
                await asyncio.sleep(2)  # prevenir rate limits

            all_buttons = load_buttons()
            new_buttons = {
                msg_id: buttons for msg_id, buttons in all_buttons.items()
                if msg_id not in deleted_ids
            }

            removed_count = len(all_buttons) - len(new_buttons)
            if removed_count > 0:
                save_buttons("buttons.json", new_buttons, merge=False)
                await ctx.send(f"✅ Canal limpiado y {removed_count} botones persistentes eliminados.", delete_after=5)
            else:
                await ctx.send("✅ Canal limpiado (no había botones persistentes).", delete_after=3)

        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para borrar mensajes.")
        except Exception as e:
            logging.error(f"Error en comando limpiartodo: {e}", exc_info=True)
            await ctx.send(f"❌ Error al limpiar: {str(e)}")


    # ======== COMANDO: exam (genera múltiples preguntas de contents) ========
    @bot.command(name="exams", aliases=["examen"])
    async def generate_exams(ctx, *args):
        """Genera un examen con múltiples preguntas de CONTENTS con delay entre ellas"""
        config = Utils.load_config()
        total_quizzes = config.get("TOTAL_QUIZZES", 5)
        quiz_delay = config.get("QUIZ_DELAY_SECONDS", 3)
        
        # Mensaje inicial
        status_msg = await ctx.send(f"📝 Preparando examen de {total_quizzes} preguntas... (CONTENTS)")

        channel_name = ctx.channel.name if hasattr(ctx.channel, "name") else ""
        module_name = channel_name[len("quizbot_"):] if channel_name.startswith("quizbot_") else ""

        if module_name:
            unit_name = args[0] if len(args) >= 1 else ""
        else:
            module_name = args[0] if len(args) >= 1 else ""
            unit_name = args[1] if len(args) >= 2 else ""

        args = [module_name, unit_name,""]

        try:
            for i in range(1, total_quizzes + 1):
                # Actualizar estado
                status_msg_quiz = await ctx.send(content=f"📝 Generando pregunta {i}/{total_quizzes}... (CONTENTS)")
                
                # Generar y enviar pregunta
                await show_question(ctx, *args, source="contents")
                
                await status_msg_quiz.delete()
                # Esperar el delay (excepto después de la última pregunta)
                if i < total_quizzes:
                    status_msg_quiz = await ctx.send(content=f"⏳...aplicando pausa para la siguiente pregunta...")
                    await asyncio.sleep(quiz_delay)
                    await status_msg_quiz.delete()

            # Mensaje final
            #await status_msg.edit(content=f"✅ Examen completado! {total_quizzes} preguntas generadas.")
            await ctx.send(content=f"✅ Examen completado! {total_quizzes} preguntas generadas.")
            
        except Exception as e:
            #await status_msg.edit(content=f"❌ Error generando examen: {str(e)}")
            await ctx.send(content=f"❌ Error generando examen: {str(e)}")

    # ======== COMANDO: exam (genera múltiples preguntas de contents) ========
    @bot.command(name="remixes", aliases=["megamix"])
    async def generate_remixes(ctx, *args):
        """Genera un examen con múltiples preguntas de CONTENTS con delay entre ellas"""
        config = Utils.load_config()
        total_quizzes = config.get("TOTAL_REMIX", 5)
        quiz_delay = config.get("REMIX_DELAY_SECONDS", 3)
        
        # Mensaje inicial
        status_msg = await ctx.send(f"📝 Preparando examen de {total_quizzes} preguntas... (REMIX)")

        channel_name = ctx.channel.name if hasattr(ctx.channel, "name") else ""
        module_name = channel_name[len("quizbot_"):] if channel_name.startswith("quizbot_") else ""

        if module_name:
            unit_name = args[0] if len(args) >= 1 else ""
        else:
            module_name = args[0] if len(args) >= 1 else ""
            unit_name = args[1] if len(args) >= 2 else ""

        args = [module_name, unit_name,""]

        try:
            for i in range(1, total_quizzes + 1):
                # Actualizar estado
                status_msg_quiz = await ctx.send(content=f"📝 Generando pregunta {i}/{total_quizzes}... (CONTENTS)")
                
                # Generar y enviar pregunta
                await show_question(ctx, *args, source="remix")
                
                await status_msg_quiz.delete()
                # Esperar el delay (excepto después de la última pregunta)
                if i < total_quizzes:
                    status_msg_quiz = await ctx.send(content=f"⏳...aplicando pausa para la siguiente pregunta...")
                    await asyncio.sleep(quiz_delay)
                    await status_msg_quiz.delete()

            # Mensaje final
            #await status_msg.edit(content=f"✅ Examen completado! {total_quizzes} preguntas generadas.")
            await ctx.send(content=f"✅ Examen completado! {total_quizzes} preguntas remixeadas.")
            
        except Exception as e:
            #await status_msg.edit(content=f"❌ Error generando examen: {str(e)}")
            await ctx.send(content=f"❌ Error generando examen: {str(e)}")

    # ======== COMANDO: evals (genera múltiples preguntas de evals) ========
    @bot.command(name="evals", aliases=["evaluaciones", "autoevaluaciones"])
    async def generate_evals(ctx, *args):
        """Genera múltiples preguntas de EVALS de una sola vez"""
        config = Utils.load_config()
        total_evals = config.get("TOTAL_EVALS", 5)
        
        # Mensaje inicial
        status_msg = await ctx.send(f"🧠 Generando {total_evals} preguntas de autoevaluación...")
        

        channel_name = ctx.channel.name if hasattr(ctx.channel, "name") else ""
        module_name = channel_name[len("quizbot_"):] if channel_name.startswith("quizbot_") else ""

        if module_name:
            unit_name = args[0] if len(args) >= 1 else ""
        else:
            aux = args[0] if len(args) >= 1 else ""
            if aux.isdigit():
                module_name = ""
                unit_name = aux
            else:
                module_name = args[0] if len(args) >= 1 else ""
                unit_name = args[1] if len(args) >= 2 else ""

        args = [module_name, unit_name,""]
        print(f"args={args}")
        try:
            # Generar todas las preguntas de una vez (el count lo maneja show_question internamente)
            await show_question(ctx, *args, source="evals", count=total_evals)
            
            # Mensaje final
            #await status_msg.edit(content=f"✅ {total_evals} preguntas de autoevaluación generadas!")
            await ctx.send(content=f"✅ {total_evals} preguntas de autoevaluación generadas!")
            #await asyncio.sleep(3)
            #await status_msg.delete()
            
        except Exception as e:
            #await status_msg.edit(content=f"❌ Error generando autoevaluaciones: {str(e)}")
            await ctx.send(content=f"❌ Error generando autoevaluaciones: {str(e)}")
            #await asyncio.sleep(5)
            #await status_msg.delete()

    # ======== COMANDO: quiz (renombrado de content) ========
    @bot.command(name="exam", aliases=["q", "pregunta", "quiz"])
    async def show_single_quiz(ctx, *args):
        """Muestra una sola pregunta de CONTENTS (antiguo comando 'content')"""

        channel_name = ctx.channel.name if hasattr(ctx.channel, "name") else ""
        module_name = channel_name[len("quizbot_"):] if channel_name.startswith("quizbot_") else ""

        if module_name:
            unit_name = args[0] if len(args) >= 1 else ""
        else:
            module_name = args[0] if len(args) >= 1 else ""
            unit_name = args[1] if len(args) >= 2 else ""

        args = [module_name, unit_name,""]
        await show_question(ctx, *args, source="contents")

    # ======== COMANDO: eval (mantenemos el individual) ========
    @bot.command(name="eval", aliases=["e", "autoeval"])
    async def show_single_eval(ctx, *args):
        """Muestra una sola pregunta de EVALS"""
        channel_name = ctx.channel.name if hasattr(ctx.channel, "name") else ""
        module_name = channel_name[len("quizbot_"):] if channel_name.startswith("quizbot_") else ""

        if module_name:
            unit_name = args[0] if len(args) >= 1 else ""
        else:
            module_name = args[0] if len(args) >= 1 else ""
            unit_name = args[1] if len(args) >= 2 else ""

        args = [module_name, unit_name,""]
        await show_question(ctx, *args, source="evals")

    # ======== COMANDO: eval (mantenemos el individual) ========
    @bot.command(name="remix", aliases=["r"])
    async def show_single_remix(ctx, *args):
        """Muestra una sola pregunta de EVALS"""
        channel_name = ctx.channel.name if hasattr(ctx.channel, "name") else ""
        module_name = channel_name[len("quizbot_"):] if channel_name.startswith("quizbot_") else ""

        if module_name:
            unit_name = args[0] if len(args) >= 1 else ""
        else:
            module_name = args[0] if len(args) >= 1 else ""
            unit_name = args[1] if len(args) >= 2 else ""

        args = [module_name, unit_name,""]
        await show_question(ctx, *args, source="remix")


    #======================================================================================================================
    async def show_question(ctx, *args, theme: str = "random", source="evals", count : int =1):
        """Muestra una pregunta de evaluación con botones temáticos interactivos"""
        if not ctx.guild:
            return await ctx.send("Utiliza este comando en una sala...")
        
        status_msg = await ctx.send(f"🧠 Generando pregunta... {source}")

        try:
            # Procesamiento de parámetros
            module_name = args[0] if len(args) >= 1 else ""
            unit = args[1] if len(args) >= 2 else ""
            question_id = args[2] if len(args) >= 3 else ""

            # Obtener module_name del canal si no se especificó
            if not module_name:
                channel_name = ctx.channel.name if hasattr(ctx.channel, "name") else ""
                module_name = channel_name[len("quizbot_"):] if channel_name.startswith("quizbot_") else ""

            # Generar la pregunta
            if source == "evals":
                generator = QuizGeneratorEVALS()
                eval_data = generator.generate_quiz(module=module_name, unit=unit, question_id=question_id, count=count)
            elif source == "remix":
                generator = QuizGeneratorEVALS()
                eval_data = generator.remix(module=module_name, unit=unit, question_id=question_id, count=1)
            elif source == "contents":
                generator = QuizGeneratorCONTENTS()
                eval_data = generator.generate_quiz(module=module_name, unit=unit, paragraph_id=question_id)
            else:
                return await ctx.send(f"❌ No se pudo generar la pregunta de tipo {source}")

            #print(f"source={source}\neval_data:\n{json.dumps(eval_data, indent=4)}")
            #input("Pause...")
            if not eval_data or not eval_data.get('quizzes'):
                return await ctx.send("❌ No se pudo generar la pregunta de evaluación.")

            # Procesar cada quiz en la respuesta
            for quiz in eval_data['quizzes']:
                # Obtener opciones directamente del quiz (no de metadata)
                options = quiz.get('options', [])
                # Convertir opciones a formato estándar si son strings
                processed_options = []
                for i, opt in enumerate(options):
                    if isinstance(opt, str):
                        processed_options.append({'text': opt, 'feedback': f"Feedback para opción {i+1}"})
                    elif isinstance(opt, dict):
                        processed_options.append({
                            'text': opt.get('text', f"Opción {i+1}"),
                            'feedback': opt.get('feedback', f"Feedback para opción {i+1}")
                        })
                    else:
                        processed_options.append({'text': f"Opción {i+1}", 'feedback': f"Feedback para opción {i+1}"})

                # Si no hay opciones, usar unas por defecto
                if not processed_options:
                    processed_options = [
                        {'text': "Opción 1", 'feedback': "Feedback para opción 1"},
                        {'text': "Opción 2", 'feedback': "Feedback para opción 2"},
                        {'text': "Opción 3", 'feedback': "Feedback para opción 3"},
                        {'text': "Opción 4", 'feedback': "Feedback para opción 4"}
                    ]

                options = processed_options

                # Obtener respuestas correctas
                correct_answers = []
                correct_answer = quiz.get('correct_answer', [])
                if isinstance(correct_answer, int):
                    correct_answers = [correct_answer]
                elif isinstance(correct_answer, (list, str)):
                    try:
                        correct_answers = [int(x) for x in (correct_answer if isinstance(correct_answer, list) else correct_answer.split(','))]
                    except (ValueError, TypeError):
                        correct_answers = []

                # Extraer otros datos
                question_text = quiz.get('question', 'Pregunta sin texto')
                metadata = quiz.get('metadata', {})
                feedback = metadata.get('original_text', "No hay feedback")  #para los CONENTS
                
                if metadata.get('original_data'):  #para las EVALS
                    original_data = metadata.get('original_data', {})
                    feedback = original_data['retroalimentacion']

                # Obtener configuracion para rutas de imágenes
                config = Utils.load_config()
                base_path = config.get("BASE_PATH", "")
                
                # Procesar imágenes si existen
                image_files = []
                media_list = quiz.get('media_question', [])
                if not media_list and metadata.get('original_data', {}).get('media'):
                    media_list = metadata['original_data']['media']
                
                if media_list:
                    for media in media_list:
                        if media and media.get('src'):
                            # Construir ruta completa
                            if source == "contents":
                                media_path = os.path.join(base_path, "DATA", "CONTENTS", quiz['module'], quiz['unidad'], media['src'])
                            else:  # source == "evals"
                                media_path = os.path.join(base_path, "DATA", "EVALS", quiz['module'], quiz['unidad'], metadata['original_data']['origen']['usuario'], media['src'])
                            
                            if os.path.exists(media_path):
                                image_files.append(discord.File(media_path))
                            else:
                                logging.warning(f"No se encontró el archivo de imagen: {media_path}")

                # Seleccionar tema de botones
                if theme == "random":
                    theme = random.choice([t for t in BUTTON_THEMES if not t.startswith("bool") or len(options) <= 2])
                symbols = BUTTON_THEMES.get(theme, BUTTON_THEMES["letters"])

                # Cargar templates
                question_template = Utils.load_template("quiz_QUESTION_TEMPLATE.txt") or (
                    "> 🧠 **Tipo:** Evaluación obtenida de Autoevaluación {source_icon}\n"
                    "> 📚 **Módulo:** {module}\n"
                    "> 📝 **{unit} - Pregunta {question_id}**\n"
                    "> 🔍 **Fuente:** {title}\n"
                    "> ❓ **Pregunta:**\n"
                    "> ```ini\n> [{question_text}]\n> ```\n"
                    "> 📋 **Selecciona la respuesta correcta:**\n> \n"
                    "{options}"
                    "\n> ℹ️ *Esta es una pregunta de opción {question_type}.*"
                )

                #source_aux = "evals" if source == "remix" else source
                source_aux = source
                message_template = Utils.load_template(f"message_chat_{source_aux}_template.txt")
                dm_template = Utils.load_template(f"message_dm_{source_aux}_template.txt")

                # Construir opciones formateadas
                formatted_options = "\n".join(
                    f"> {symbols[i] if i < len(symbols) else str(i + 1)} - {option['text']}"
                    for i, option in enumerate(quiz["options"])
                )

                #print (f'quiz={json.dumps(quiz["metadata"]["original_data"],indent=4)}')
                #print (f'quiz["metadata"]["original_data"]["options"]={quiz["metadata"]["original_data"]["opciones"]}')

                if source == "remix":
                    original_question = quiz["metadata"]["original_data"]["enunciado"]
                    # Construir opciones formateadas originales
                    formatted_original_options = "\n".join(
                        f"· {text}"
                        for i, text in enumerate(quiz["metadata"]["original_data"]["opciones"])
                    )
                    original_feedback = quiz["metadata"]["original_data"]["retroalimentacion"]
                    original_question_full = "Pregunta original: " + original_question + "\nOpciones Originales:\n" + formatted_original_options + "\nRetroalimentación Original: " + original_feedback
                else:
                    original_question_full = ""

                #input(f"original_question={original_question_full}")
                # Reemplazos comunes
                replacements_generales = {
                    "{source}": source,
                    "{SOURCE}": source.upper(),
                    "{source_icon}": "👤" if source == "evals" else "🤖",
                    "{module}": quiz.get('module', 'General'),
                    "{MODULE}": quiz.get('module', 'General').upper(),
                    "{unit}": quiz.get('unidad', 'Unidad'),
                    "{UNIT}": quiz.get('unidad', 'Unidad').upper(),
                    "{question_id}": quiz.get('ID', ''),
                    "{title}": quiz.get('title', 'Pregunta de evaluación'),
                    "{TITLE}": quiz.get('title', 'Pregunta de evaluación').upper(),
                    "{question_text}": question_text,
                    "{QUESTION_TEXT}": question_text.upper(),
                    #"{options}": "\n".join(f"{symbols[i] if i < len(symbols) else str(i+1)} - {str(opt.get('text'))}" for i, opt in enumerate(options)),
                    "{options}": "\n".join(f"{symbols[i] if i < len(symbols) else str(i+1)} - {opt['text']}" for i, opt in enumerate(options)),
                    "{options}": "\n".join(f"{symbols[i] if i < len(symbols) else str(i+1)} - {opt['text'].upper()}" for i, opt in enumerate(options)),
                    "{formatted_options}": formatted_options,
                    "{FORMATTED_OPTIONS}": formatted_options.upper(),
                    "{question_type}": 'múltiple' if len(correct_answers) > 1 else 'simple',
                    "{QUESTION_TYPE}": 'MÚLTIPLE' if len(correct_answers) > 1 else 'SIMPLE',
                    "{section}": quiz.get('unidad', 'Unidad'),
                    "{subsection}": f"Pregunta {quiz.get('ID', '')}",
                    "{paragraph_text}": question_text,
                    "{correct_answer}": ", ".join([str(i+1) for i in correct_answers]),
                    "{message_id}": str(ctx.message.id),
                    "{message_link}": f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}",
                    "{feedback}": feedback,
                    "{original_question}": original_question_full
                }

                # Aplicar reemplazos al template de pregunta
                formatted_question = question_template
                for ph, val in replacements_generales.items():
                    formatted_question = formatted_question.replace(ph, str(val))

                # Crear botones para cada opción
                themed_buttons = []
                for idx, option in enumerate(options[:len(symbols)]):
                    is_correct = idx in correct_answers
                    symbol = symbols[idx]

                    replacements_boton = replacements_generales.copy()
                    result_icon="✅" if is_correct else "❌"
                    replacements_boton.update({
                        "{result_icon}": result_icon,
                        "{symbol}": symbol,
                        "{option_text}": option['text'],
                        "{option_feedback}": option['feedback'],
                        "{result}": "Correcto!" if is_correct else "Incorrecto",
                        "{paragraph_text_correct}": question_text if is_correct else f'||{question_text}||',
                        "{incorrect}": "" if is_correct else "||"
                    })
                    # Es necesario que el mensaje del botón comience con un estado correcto o incorrecto.
                    #message_template=f"{result_icon}{message_template}" if message_template else ""
                    #dm_template=f"{result_icon}{dm_template}" if dm_template else ""
                    themed_buttons.append(
                        InteractiveButton(
                            label=symbol,
                            style=discord.ButtonStyle.secondary,
                            callback=button_callback,
                            message=Utils.apply_replacements((result_icon if message_template else "") + message_template, replacements_boton),
                            direct_message=Utils.apply_replacements((result_icon if dm_template else "") + dm_template, replacements_boton),
                            option_reply=option,
                            prefix_theme=symbol
                        )
                    )

                # Enviar cada pregunta con imágenes si existen
                if themed_buttons:
                    view = PersistentButtonView(ctx.message.id, themed_buttons)
                    bot.add_view(view)
                    save_buttons("buttons.json", {str(ctx.message.id): themed_buttons})
                    
                    if image_files:
                        # Si hay imágenes, enviar primero el mensaje con las imágenes
                        await ctx.send(formatted_question, files=image_files, view=view)
                    else:
                        await ctx.send(formatted_question, view=view)
                else:
                    if image_files:
                        await ctx.send(formatted_question, files=image_files)
                    else:
                        await ctx.send(formatted_question)

            await status_msg.delete()

        except Exception as e:
            # Asegurarse de eliminar el mensaje de estado incluso si hay un error
            try:
                await status_msg.delete()
            except:
                pass
            logging.error(f"Error en comando pregunta: {str(e)}", exc_info=True)
            await ctx.send(f"❌ Error al generar pregunta: {str(e)}")
    
    # ======== COMANDO: reset (resetea la puntuación del usuario) ========
    @bot.command(name='reset')
    async def reset_scores(ctx):
        """Reinicia las puntuaciones del usuario"""
        try:
            SCORE_MANAGER.reset_scores(ctx.author.id)
            msg = await ctx.send("✅ Puntajes reseteados a cero!", delete_after=3)
            await asyncio.sleep(3)
            await ctx.message.delete()
        except Exception as e:
            await ctx.send(f"❌ Error al resetear puntajes: {str(e)}", delete_after=5)

    # ======== COMANDO: dir (listado unificado de módulos) ========
    @bot.command(name="dir", aliases=["list"])
    async def list_modules(ctx):
        """Lista unificada de módulos y unidades (contenido y evaluación)"""
        try:
            config = Utils.load_config()
            base_path = config.get("BASE_PATH", ".")
            contents_suffix = config.get("CONTENTS_SUFFIX", "_contents_v5.json")
            evals_suffix = config.get("EVALS_SUFFIX", "_evals_v5.json")

            # Obtener listados de contenidos y evaluaciones
            contents_data = DirectoryLister.get_modules_list(base_path, "CONTENTS", contents_suffix)
            evals_data = DirectoryLister.get_modules_list(base_path, "EVALS", evals_suffix)

            # Generar embed con los datos
            embed = DirectoryLister.generate_embed(contents_data, evals_data)
            await ctx.send(embed=embed)

        except Exception as e:
            logging.error(f"Error en comando dir: {str(e)}", exc_info=True)
            await ctx.send("❌ Error al listar los módulos.")

    @bot.command(name="help")
    async def show_help(ctx):
        """Muestra la ayuda desde bot_help.txt"""
        try:
            with open("bot_help.txt", "r", encoding="utf-8") as f:
                help_text = f.read()
            
            if not help_text.strip():
                await ctx.send("⚠️ El archivo de ayuda está vacío.")
            else:
                # Si el texto es muy largo, dividirlo
                for chunk in [help_text[i:i+1900] for i in range(0, len(help_text), 1900)]:
                    await ctx.send(f"```{chunk}```")
        
        except FileNotFoundError:
            await ctx.send("❌ No se encontró el archivo `bot_help.txt` en el directorio actual.", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ Error al leer el archivo de ayuda: {e}")

    # ======== INICIAR BOT ========
    try:
        bot.run(token)
    except discord.LoginError:
        logging.error("Token de bot inválido")
    except Exception as e:
        logging.error(f"Error al iniciar bot: {e}")



if __name__ == "__main__":
    start_bot()