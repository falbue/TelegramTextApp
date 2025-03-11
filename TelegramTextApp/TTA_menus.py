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

def create_buttons(buttons_data, tta_data, keyboard, list_page, role=None):
    locale = get_locale()
    data = buttons_data
    prefix= tta_data['data']
    page = int(tta_data["page"])
    btn_role = 'user'

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
                data_button = function_format(tta_data, data_button)

        var_button = locale["var_buttons"].get(callback)
        if var_button:
            callback_button = text
            if isinstance(var_button, dict):
                text = var_button["text"]
                btn_role = var_button["role"]
            else:
                text = locale["var_buttons"][callback]
            callback = callback_button

        if btn_role == "user" or btn_role == role:
            if callback == "url":
                button = types.InlineKeyboardButton(text, url=data_button)
            elif callback == "app":
                button = types.InlineKeyboardButton(text, web_app=types.WebAppInfo(url=data_button))
            else:
                button = types.InlineKeyboardButton(text, callback_data=f'{callback}-{page}:{data_button}')
        else:
            continue
    
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


def menu_layout(call=None, message=None, user_id=None):
    locale = get_locale()

    try:
        if call:
            menu_base = (call.data).split(":")
            menu_name = menu_base[0].split("-")[0]
            menu_page = menu_base[0].split("-")[1]
            get_data = (call.data).replace(f"{menu_base[0]}:", "")
            if get_data == "": get_data = None
        elif message:
            command = (message.text).replace("/", "")
            menu_name = "error_command"
            if locale["commands"].get(command):
                menu_name = locale["commands"][command]["menu"]
            get_data = None
            if len(menu_name.split(":")) > 1: 
                menu_name = menu_name.split(":")[0]
                get_data = (call.data).replace(f"{menu_name}:", "")
            menu_page = "0"
            if command == "start":
                TTA_scripts.registration(message, call)
      

        tta_data = {"menu":menu_name, "page":menu_page, "data":get_data, "call":call, "message":message} 
        return tta_data
    except Exception as e:
        print(e)
        return {"menu":"error_command", "page":"0", "data":None, "call":call, "message":message}


def open_menu(call=None, message=None, loading=False, menu=None, input_text=None):
    locale = get_locale()

    if message is not None: user_id = message.chat.id
    elif call is not None: user_id = call.message.chat.id

    tta_data = menu_layout(call, message, user_id)
    tta_data["user_id"] = user_id
    if menu:
        tta_data['menu'] = menu
    if input_text:
        tta_data["input_text"] = input_text

    user = TTA_scripts.SQL_request("SELECT * FROM TTA WHERE telegram_id = ?", (user_id,))
    if user is None:
        TTA_scripts.registration(message, call)
        role = "user"
    else:
        role = user[6]
    formatting_data = None
    function_data = {}
    list_page = 20

    find_menu = locale["menus"].get(tta_data['menu'])
    if find_menu is None: tta_data['menu'] = "error"

    kb_width=2
    menu_data = {}
    formatting = {}

    if locale["menus"][tta_data['menu']].get('loading') is not None and loading == False:
        menu_data["text"] = TTA_scripts.markdown(locale["menus"][tta_data['menu']]['loading'])
        menu_data['loading'] = True
        return menu_data

    if locale["menus"][tta_data['menu']].get('function') is not None: # выполнение указанной функции
        function_name = (locale["menus"][tta_data['menu']]['function'])
        function = globals()[function_name]
        function_data = function(tta_data)

    if locale["menus"][tta_data['menu']].get('text') is not None:
        text = locale["menus"][tta_data['menu']]['text']
        text = TTA_scripts.data_formated(text, user_id)
        if format_text:
            function_format = globals()[format_text]
            text = function_format(tta_data, text)
        text = TTA_scripts.markdown(text)
    else:
        text = function_data
        if text is None: text = "Укажите текст настройках меню\!"

    menu_data["text"] = text

    if locale["menus"][tta_data['menu']].get('width') is not None: # настройка ширины клавиатуры
        kb_width = int((locale["menus"][tta_data['menu']]['width']))
    keyboard = InlineKeyboardMarkup(row_width=kb_width)

    if locale["menus"][tta_data['menu']].get('list_page') is not None: # сколько кнопок на странице
        list_page = int((locale["menus"][tta_data['menu']]['list_page']))

    if locale["menus"][tta_data['menu']].get('buttons') is not None: # добавление кнопок
        keyboard = create_buttons(locale["menus"][tta_data['menu']]["buttons"], tta_data, keyboard, list_page, role=role)

    if locale["menus"][tta_data['menu']].get('create_buttons') is not None: # добавление кнопок
        function_name = locale["menus"][tta_data['menu']]['create_buttons']
        function = globals()[function_name]
        function_data = function(tta_data)
        keyboard = create_buttons(function_data, tta_data, keyboard, list_page, role=role)

    if locale["menus"][tta_data['menu']].get('return') is not None: # кнопка возврата
        btn_return = InlineKeyboardButton((locale["var_buttons"]['return']), callback_data=f'{locale["menus"][tta_data["menu"]]["return"]}-0:')
        keyboard.add(btn_return)

    menu_data["keyboard"] = keyboard

    if locale["menus"][tta_data['menu']].get('handler') is not None: # ожидание ввода
        menu_data["handler"] = locale["menus"][tta_data['menu']]["handler"]

    if locale["menus"][tta_data['menu']].get('send') is not None: # Отправка сообщения
        menu_data["send"] = locale["menus"][tta_data['menu']]["send"]

    menu_data["call"] = call
    menu_data["message"] = message
    return menu_data