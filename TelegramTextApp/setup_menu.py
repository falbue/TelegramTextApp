from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

import json

from .utils.helpers import *
from .utils import logger
from . import config

logger = logger.setup("MENUS")
JSON_PATH = config.JSON

def config_custom_module(user_custom_functions):
    global custom_module
    custom_module = load_custom_functions(user_custom_functions)

async def get_bot_data(callback, bot_input=None):
    user = await get_user(callback)

    tta_data = {}
    if bot_input:
        menu_name = bot_input['menu']
        tta_data['bot_input'] = bot_input
        message = callback

    elif hasattr(callback, 'message'):
        menu_name = callback.data 
        message = callback.message
    else:
        message = callback
        command = message.text
        commands = load_json(level='commands')
        command_data = commands.get(command.replace("/",""))
        if command_data is None:
            return None
        menu_name = command_data.get("menu")

    tta_data["menu_name"] = menu_name
    tta_data["telegram_id"] = message.chat.id
    tta_data['user'] = user
    tta_data['callback'] = callback

    return tta_data

async def create_keyboard(menu_data, format_data=None, custom_module=None): # создание клавиатуры
    builder = InlineKeyboardBuilder()
    return_builder = InlineKeyboardBuilder()
    variable_buttons = load_json("buttons")
    
    if "keyboard" in menu_data:
        rows = []  # Список для готовых строк кнопок
        current_row = []  # Текущая формируемая строка
        max_in_row = menu_data.get("row", 2)  # Максимум кнопок в строке

        if isinstance(menu_data["keyboard"], str):
            return None

        for callback_data, button_text in menu_data["keyboard"].items():
            force_new_line = False
            if button_text.startswith('\\'):
                button_text = button_text[1:]  # Удаляем символ переноса
                force_new_line = True
            
            button_text = formatting_text(button_text, format_data)
            callback_data = formatting_text(callback_data, format_data)
            
            if callback_data.startswith("url:"): # кнопка ссылка
                url = callback_data[4:]
                button = InlineKeyboardButton(text=button_text, url=url)

            elif callback_data.startswith("app:"): # кнопка ссылка
                url = callback_data[4:]
                button = InlineKeyboardButton(text=button_text, web_app=WebAppInfo(url=url))

            else:
                button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
            
            if len(current_row) >= max_in_row: # Проверяем необходимость завершения текущей строки
                rows.append(current_row)
                current_row = []
            
            if force_new_line and current_row: # Обрабатываем принудительный перенос
                rows.append(current_row)
                current_row = []
            
            current_row.append(button)
        
        if current_row: # Добавляем последнюю строку
            rows.append(current_row)

        for row in rows: # Собираем клавиатуру из подготовленных строк
            builder.row(*row)
    
    if "return" in menu_data: # Добавляем кнопку возврата если нужно
        return_builder.button(
            text=variable_buttons['return'],
            callback_data=formatting_text(f"return|{menu_data['return']}", format_data)
        )
        builder.row(*return_builder.buttons)  # Кнопка возврата всегда в новой строке
    
    return builder.as_markup()

def create_text(menu_data, format_data, use_markdown=True): # создание текста
    text = menu_data["text"]
    text = formatting_text(text, format_data)
    if use_markdown:
        text = markdown(text)
    return text

async def get_menu(callback, bot_input=None, menu_loading=False):
    tta_data = await get_bot_data(callback, bot_input)
    return await create_menu(tta_data, menu_loading)


async def create_menu(tta_data, menu_loading=False): # получение нужного меню
    menu_name = tta_data['menu_name']    

    menus = load_json(level='menu')
    if "return|" in menu_name:
        menu_name = menu_name.replace("return|", "")

    menu_data = menus.get(menu_name.split("|")[0])
    template = menu_name

    if "|" in menu_name:
        prefix = menu_name.split("|")[0] + "|"
        
        for key in menus:
            if key.startswith(prefix):
                menu_data = (menus.get(key))
                template = key
                break

    if menu_loading == False:
        logger.debug(f"Открываемое меню: {menu_name}")

    if not menu_data:
        menu_data = menus.get("none_menu")

    if menu_data.get("loading") and menu_loading == False:
        if menu_data["loading"] == True:
            text = "Загрузка..."
        else:
            text = menu_data["loading"]
        text = markdown(text)
        return {"text":text, "keyboard":None, "loading":True}



    if tta_data.get("bot_input"):
        menu_data["bot_input"] = tta_data["bot_input"].get("function")

    format_data = parse_bot_data(template, menu_name)

    if tta_data.get('bot_input'):
        bot_input = tta_data["bot_input"]
        format_data[bot_input["data"]] = bot_input.get("input_text", None)
    format_data = {**format_data, **(tta_data["user"] or {})}
    format_data["menu_name"] = menu_name
    
    if menu_data.get("function"):
        format_data, menu_data = await process_custom_function("function", format_data, menu_data, custom_module)
    if menu_data.get("keyboard"):
        format_data, menu_data = await process_custom_function("keyboard", format_data, menu_data, custom_module)
    if menu_data.get("bot_input"):
        format_data, menu_data = await process_custom_function("bot_input", format_data, menu_data, custom_module)


    if menu_data.get("edit_menu"):
        tta_data["menu_name"] = menu_data["edit_menu"]
        return await create_menu(tta_data, menu_loading)

    if menu_data.get("send_menu"):
        send_menu = menu_data["send_menu"]
        del menu_data["send_menu"]

        tta_data['menu_name'] = send_menu["menu"]
        menu_data["send"] = await create_menu(tta_data)
        ids = send_menu["user"]
        if isinstance(ids, int):
            menu_data["send"]["ids"] = [ids]
        elif isinstance(ids, list):
            menu_data["send"]["ids"] = ids
        elif isinstance(ids, str):
            menu_data["send"]["ids"] = await get_role_id(ids)

    if menu_data.get("popup"):
        popup = {}
        popup = menu_data.get("popup")
        popup['text'] = create_text(popup, format_data, False)
        if popup.get("menu_block"):
            menu_data["text"] = "bla"
    else: popup = None

    if menu_data.get("text"):
        text = create_text(menu_data, format_data)
    else: # попап не может быть применён к сообщению, которое отправляется
        popup = {"text":f"Ошибка!\nУ открываемого меню {menu_name}, отсутсвует текст!", "size":"small", "menu_block":True}
        text = ""
    keyboard = await create_keyboard(menu_data, format_data, custom_module)
    menu_input = menu_data.get("input", None)

    send = menu_data.get("send", False)    
    return {"text":text, "keyboard":keyboard, "input":menu_input, "popup":popup, "send":send}