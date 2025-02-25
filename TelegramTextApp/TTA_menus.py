from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot import types
from TelegramTextApp import TTA_scripts
import json

LOCALE_PATH = None

def settings_menu(menus, script_path, formating_text):
    global LOCALE_PATH, format_text
    LOCALE_PATH = menus
    format_text = formating_text
    import sys
    from importlib.util import spec_from_file_location, module_from_spec
    sys.path.append("scripts.py")
    module = module_from_spec(spec_from_file_location("scripts", script_path))
    module.__spec__.loader.exec_module(module)
    globals().update(vars(module))

    with open(LOCALE_PATH, 'r', encoding='utf-8') as file:
        commands = json.load(file)
    return commands

def get_locale():
    with open(LOCALE_PATH, 'r', encoding='utf-8') as file:
        locale = json.load(file)
        return locale

def menu_layout(call=None, message=None, user_id=None):
    locale = get_locale()

    try:
        if call:
            menu_base = (call.data).split(":")
            get_data = menu_base[1]
            if get_data == "": get_data = None
            menu_name = menu_base[0].split("-")[0]
            menu_page = menu_base[0].split("-")[1]
        elif message:
            command = (message.text).replace("/", "")
            menu_name = "error_command"
            if locale["commands"].get(command):
                menu_name = locale["commands"][command]["menu"]
            get_data = None
            if len(menu_name.split(":")) > 1: 
                get_data = menu_name.split(":")[1]
                menu_name = menu_name.split(":")[0]
            menu_page = "0"
            if command == "start":
                TTA_scripts.registration(message, call)
        return {"name":menu_name, "page":menu_page, "data":get_data, "call":call, "message":message, "user_id": user_id}
    except:
        return {"name":"error_command", "page":"0", "data":None, "call":call, "message":message, "user_id": user_id}


def create_buttons(buttons_data, menu_data, keyboard, list_page):
    locale = get_locale()
    data = buttons_data
    prefix= menu_data['data']
    page = int(menu_data["page"])

    buttons = []
    nav_buttons = []
    start_index = int(page) * list_page
    end_index = start_index + list_page
    paginated_data = list(data.items())[start_index:end_index]
    
    for data, text in paginated_data:
        slash  = text
        callback = data
        data_button = ""
        text = text.replace("\\","")
        if len(data.split(":")) > 1:
            callback = data.split(":")[0]
            data_button = data.replace(f"{callback}:", "")
            if format_text:
                function_format = globals()[format_text]
                data_button = function_format(menu_data, data_button)

        var_buttons = locale["var_buttons"].get(callback)
        if var_buttons:
            return_btn = text
            text = locale["var_buttons"][callback]
            callback = return_btn

        if callback == "url":
            button = types.InlineKeyboardButton(text, url=data_button)
        elif callback == "app":
            button = types.InlineKeyboardButton(text, web_app=types.WebAppInfo(url=data_button))
        else:
            button = types.InlineKeyboardButton(text, callback_data=f'{callback}-{page}:{data_button}')

        if slash[0] == "\\":
            if buttons:
                keyboard.add(*buttons)
                buttons = []
                buttons.append(button)
        else:
            buttons.append(button)
    if buttons:
        keyboard.add(*buttons)

    
    if len(paginated_data) > list_page:
        nav_buttons = []
        if int(page) > 0:
            nav_buttons.append(types.InlineKeyboardButton('⬅️', callback_data=f'{menu}-{page-1}:{prefix}'))
        nav_buttons.append(types.InlineKeyboardButton(f"• {page+1} •", callback_data=f'none'))
        if end_index < len(data):
            nav_buttons.append(types.InlineKeyboardButton('➡️', callback_data=f'{menu}-{page+1}:{prefix}'))
        keyboard.add(*nav_buttons)
    
    return keyboard


def open_menu(call=None, message=None, loading=False):
    locale = get_locale()
    if message is not None: user_id = message.chat.id
    elif call is not None: user_id = call.message.chat.id
    menu_data = menu_layout(call, message, user_id)
    user = TTA_scripts.SQL_request("SELECT * FROM TTA WHERE id = ?", (user_id,))
    if user is None:
        TTA_scripts.registration(message, call)
    formatting_data = None
    function_data = {}
    list_page = 20


    find_menu = locale["menus"].get(menu_data['name'])
    if find_menu is None: menu_data['name'] = "error"


    if user_id: user = TTA_scripts.SQL_request("SELECT * FROM TTA WHERE telegram_id = ?", (int(user_id),))

    kb_width=2
    return_data = {}
    formatting = {}

    if locale["menus"][menu_data['name']].get('loading') is not None and loading == False:
        return_data["text"] = TTA_scripts.markdown(locale["menus"][menu_data['name']]['loading'])
        return_data['loading'] = True
        return return_data

    if locale["menus"][menu_data['name']].get('function') is not None: # выполнение указанной функции
        function_name = (locale["menus"][menu_data['name']]['function'])
        function = globals()[function_name]
        function_data = function(menu_data)

    if locale["menus"][menu_data['name']].get('text') is not None:
        text = locale["menus"][menu_data['name']]['text']
        if format_text:
            function_format = globals()[format_text]
            text = function_format(menu_data, text)
        text = TTA_scripts.markdown(text)
    else:
        text = function_data
        if text is None: text = "Укажите текст настройках меню!"

    text = TTA_scripts.data_formated(text, formatting_data)
    return_data["text"] = text

    if locale["menus"][menu_data['name']].get('width') is not None: # настройка ширины клавиатуры
        kb_width = int((locale["menus"][menu_data['name']]['width']))
    keyboard = InlineKeyboardMarkup(row_width=kb_width)

    if locale["menus"][menu_data['name']].get('list_page') is not None: # настройка ширины клавиатуры
        list_page = int((locale["menus"][menu_data['name']]['list_page']))

    if locale["menus"][menu_data['name']].get('buttons') is not None: # добавление кнопок
        keyboard = create_buttons(locale["menus"][menu_data['name']]["buttons"], menu_data, keyboard, list_page)

    if locale["menus"][menu_data['name']].get('create_buttons') is not None: # добавление кнопок
        function_name = locale["menus"][menu_data['name']]['create_buttons']
        function = globals()[function_name]
        function_data = function(menu_data)
        keyboard = create_buttons(function_data, menu_data, keyboard, list_page)

    return_data["keyboard"] = keyboard

    if locale["menus"][menu_data['name']].get('handler') is not None: # ожидание ввода
        return_data["handler"] = locale["menus"][menu_data['name']]["handler"]

    return_data["call"] = call
    return_data["message"] = message
    return return_data