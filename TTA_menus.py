from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot import types
import TTA_scripts
import json

import sys
from importlib.util import spec_from_file_location, module_from_spec
sys.path.append("scripts.py")
module = module_from_spec(spec_from_file_location("scripts", "scripts.py"))
module.__spec__.loader.exec_module(module)
globals().update(vars(module))

def get_locale():
    path = "local.json"
    with open(path, 'r', encoding='utf-8') as file:
        locale = json.load(file)

    return locale

locale = get_locale()

def menu_layout(call=None, message=None):
    if call:
        menu_base = (call.data).split(":")
        get_data = menu_base[1]
        menu_name = menu_base[0].split("-")[0]
        menu_page = menu_base[0].split("-")[1]
    elif message:
        menu_name = (message.text).replace("/", "")
        get_data = ""
        menu_page = "0"
    if menu_name == "start":
        menu_name = 'main'
    return {"name":menu_name, "page":menu_page, "data":get_data}


def create_buttons(data, page, prefix, list_page=10, menu=None):
    buttons = []
    start_index = int(page) * list_page
    end_index = start_index + list_page
    paginated_data = list(data.items())[start_index:end_index]
    
    for callback, text in paginated_data:
        button = types.InlineKeyboardButton(text, callback_data=f'{callback}-{page}:{prefix}')
        buttons.append(button)
    
    if menu is not None:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton('⬅️', callback_data=f'{menu}-{page-1}:{prefix}'))
        nav_buttons.append(types.InlineKeyboardButton(f"• {page+1} •", callback_data=f'none'))
        if end_index < len(data):
            nav_buttons.append(types.InlineKeyboardButton('➡️', callback_data=f'{menu}-{page+1}:{prefix}'))
    
        return buttons, nav_buttons
    return buttons


def open_menu(call=None, message=None):
    menu_data = menu_layout(call, message)
    formatting_data = None


    find_menu = locale["menus"].get(menu_data['name'])
    if find_menu is None: menu_data['name'] = "none_menu"

    if menu_data['name'] == "main":
            TTA_scripts.registration(message, call)

    if message is not None: user_id = message.chat.id
    elif call is not None: user_id = call.message.chat.id
    if user_id: user = TTA_scripts.SQL_request("SELECT * FROM TTA WHERE telegram_id = ?", (int(user_id),))

    kb_width=2
    return_data = {}
    formatting = {}

    if locale["menus"][menu_data['name']].get('function') is not None: # выполнение указанной функции
        function_name = (locale["menus"][menu_data['name']]['function'])
        function = globals()[function_name]
        function_data = function(call, message, menu_data["data"])

    if locale["menus"][menu_data['name']].get('text') is not None:
        text = locale["menus"][menu_data['name']]['text']
    else:
        text = function_data
    text = TTA_scripts.data_formated(text, formatting_data)
    text = TTA_scripts.markdown(text, True)
    return_data["text"] = text

    if locale["menus"][menu_data['name']].get('width') is not None: # настройка ширины клавиатуры
        kb_width = int((locale["menus"][menu_data['name']]['width']))
    keyboard = InlineKeyboardMarkup(row_width=kb_width)

    if locale["menus"][menu_data['name']].get('buttons') is not None: # добавление кнопок
        buttons = create_buttons(locale["menus"][menu_data['name']]['buttons'], menu_data['page'], menu_data['data'])
        if menu_data['name'] == "main" and user[4] == "admin": # добавление админки
            buttons.append(InlineKeyboardButton((locale["general_buttons"]['admin']), callback_data=f'admin'))
        keyboard.add(*buttons)

    if locale["menus"][menu_data['name']].get('return') is not None: # кнопка возврата
        btn_return = InlineKeyboardButton((locale["general_buttons"]['return']), callback_data=f'{locale["menus"][menu_data["name"]]["return"]}-0:{menu_data["data"]}')
        keyboard.add(btn_return)
    return_data["keyboard"] = keyboard

    if locale["menus"][menu_data['name']].get('handler') is not None: # ожидание ввода
        return_data["handler"] = locale["menus"][menu_data['name']]["handler"]

    return_data["call"] = call
    return_data["message"] = message
    return return_data