from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import json

from utils import *

from scripts import *


def load_bot(level=None): # загрузка меню
    filename="bot.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        if level:
            data = data[level]
        return data

async def get_bot_data(callback, bot_input=None):
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
        commands = load_bot(level='commands')
        command_data = commands.get(command.replace("/",""))
        if command_data is None:
            return None
        menu_name = command_data.get("menu")

    tta_data["menu_name"] = menu_name
    tta_data["telegram_id"] = message.chat.id

    user = await get_user(tta_data['telegram_id'])
    if not user:
        result = await create_user(message)
        if not result:
            logger.error(f"Не удалось зарегестировать пользователя {tta_data['telegram_id']}")
        else:
            user = await get_user(tta_data['telegram_id'])
            logger.info(f"Зарегестирован новый пользователь: {tta_data['telegram_id']}")

    tta_data['user'] = user
    return tta_data

def create_keyboard(menu_data, format_data=None): # создание клавиатуры
    builder = InlineKeyboardBuilder()
    return_builder = InlineKeyboardBuilder()
    variable_buttons = load_bot("buttons")
    
    if "keyboard" in menu_data:
        rows = []  # Список для готовых строк кнопок
        current_row = []  # Текущая формируемая строка
        max_in_row = menu_data.get("row", 2)  # Максимум кнопок в строке
        
        for callback_data, button_text in menu_data["keyboard"].items():
            force_new_line = False
            if button_text.startswith('\\'):
                button_text = button_text[1:]  # Удаляем символ переноса
                force_new_line = True
            
            button_text = formatting_text(button_text, format_data)
            callback_data = formatting_text(callback_data, format_data)
            
            if callback_data.startswith("url:"): # Создаем кнопку
                url = callback_data[4:]
                button = InlineKeyboardButton(text=button_text, url=url)
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

def create_text(menu_data, format_data): # создание текста
    text = menu_data["text"]
    text = formatting_text(text, format_data)
    text = markdown(text)
    return text

async def get_menu(callback, bot_input=None):
    tta_data = await get_bot_data(callback, bot_input) 
    return await create_menu(tta_data)

async def get_mini_menu(callback):
    tta_data = await get_bot_data(callback)
    menu_name = tta_data['menu_name'].replace("mini|","")
    menus = load_bot(level='mini_menu')

    text = menus.get(menu_name.split("|")[0])
    template = menu_name

    if "|" in menu_name:
        prefix = menu_name.split("|")[0] + "|"
        
        for key in menus:
            if key.startswith(prefix):
                text = (menus.get(key))
                template = key
                break

    format_data = parse_bot_data(template, menu_name)
    format_data = {**format_data, **(tta_data["user"] or {})}
    format_data["menu_name"] = menu_name

    if not text:
        text = ""

    text = formatting_text(text, format_data)
    return text


async def create_menu(tta_data): # получение нужного меню
    menu_name = tta_data['menu_name']
    menus = load_bot(level='menu')
    if "return|" in menu_name:
        menu_name = menu_name.replace("return|", "")
    menu_data = menus.get(menu_name.split("|")[0])
    template = menu_name
    logger.debug(f"Открываемое меню: {menu_name}")

    if "|" in menu_name:
        prefix = menu_name.split("|")[0] + "|"
        
        for key in menus:
            if key.startswith(prefix):
                menu_data = (menus.get(key))
                template = key
                break

    if not menu_data:
        menu_data = menus.get("none_menu")

    format_data = parse_bot_data(template, menu_name)
    if tta_data.get('bot_input'):
        bot_input = tta_data["bot_input"]
        format_data[bot_input["data"]] = bot_input.get("input_text", None)
    format_data = {**format_data, **(tta_data["user"] or {})}
    format_data["menu_name"] = menu_name


    if tta_data.get('bot_input'):
        if tta_data['bot_input'].get("function"):
            bot_input = tta_data["bot_input"]
            custom_function = globals().get(bot_input.get('function'))
            if custom_function and callable(custom_function):
                if asyncio.iscoroutinefunction(custom_function):
                    custom_format = await custom_function(format_data)
                else:
                    custom_format = custom_function(format_data)
                if isinstance(custom_format, dict):
                    format_data = {**format_data, **(custom_format or {})}

    if menu_data.get("function"):
        custom_function = globals().get(menu_data["function"])
        if custom_function and callable(custom_function):
            if asyncio.iscoroutinefunction(custom_function):
                custom_format = await custom_function(format_data)
            else:
                custom_format = custom_function(format_data)
            
            if isinstance(custom_format, dict):
                format_data = {**format_data, **(custom_format or {})}

    if menu_data.get("keyboard"):
        if isinstance(menu_data["keyboard"], str):
            buttons_func = globals().get(menu_data["keyboard"])
            if buttons_func and callable(buttons_func):
                if asyncio.iscoroutinefunction(buttons_func):
                    buttons_data = await buttons_func(format_data)
                else:
                    buttons_data = buttons_func(format_data)
                
                if isinstance(buttons_data, dict):
                    menu_data["keyboard"] = buttons_data


    text = create_text(menu_data, format_data)
    keyboard = create_keyboard(menu_data, format_data)
    menu_input = menu_data.get("input", None)
    
    return {"text":text, "keyboard":keyboard, "input":menu_input}