from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot import types
import TTA_scripts
import json

def get_locale(menus, script_path):
    global locale
    locale = menus
    import sys
    from importlib.util import spec_from_file_location, module_from_spec
    sys.path.append("scripts.py")
    module = module_from_spec(spec_from_file_location("scripts", script_path))
    module.__spec__.loader.exec_module(module)
    globals().update(vars(module))

def menu_layout(call=None, message=None, user_id=None):
    if call:
        menu_base = (call.data).split(":")
        get_data = menu_base[1]
        if get_data == "": get_data = None
        menu_name = menu_base[0].split("-")[0]
        menu_page = menu_base[0].split("-")[1]
    elif message:
        command = (message.text).replace("/", "")
        menu_name = locale["commands"][command]["menu"]
        get_data = None
        if len(menu_name.split(":")) > 1: 
            get_data = menu_name.split(":")[1]
            menu_name = menu_name.split(":")[0]
        menu_page = "0"
        if command == "start":
            TTA_scripts.registration(message, call)
    return {"name":menu_name, "page":menu_page, "data":get_data, "call":call, "message":message, "user_id": user_id}


def create_buttons(data, page=0, prefix="", list_page=20, menu=None):
    page = int(page)
    buttons = []
    nav_buttons = []
    start_index = int(page) * list_page
    end_index = start_index + list_page
    paginated_data = list(data.items())[start_index:end_index]
    
    for callback, text in paginated_data:
        if len(callback.split(":")) > 1:
            data_button = callback.split(":")[1]
            callback = callback.split(":")[0]
        if callback == "url":
            button = types.InlineKeyboardButton(text, url=data_button)
        else:
            button = types.InlineKeyboardButton(text, callback_data=f'{callback}-{page}:{data_button}')
        buttons.append(button)
    
    if len(data) > list_page:
        nav_buttons = []
        if int(page) > 0:
            nav_buttons.append(types.InlineKeyboardButton('⬅️', callback_data=f'{menu}-{page-1}:{prefix}'))
        nav_buttons.append(types.InlineKeyboardButton(f"• {page+1} •", callback_data=f'none'))
        if end_index < len(data):
            nav_buttons.append(types.InlineKeyboardButton('➡️', callback_data=f'{menu}-{page+1}:{prefix}'))
    
    return buttons, nav_buttons


def open_menu(call=None, message=None, loading=False):
    if message is not None: user_id = message.chat.id
    elif call is not None: user_id = call.message.chat.id
    menu_data = menu_layout(call, message, user_id)
    formatting_data = None
    function_data = {}


    find_menu = locale["menus"].get(menu_data['name'])
    if find_menu is None: menu_data['name'] = "none_menu"

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
    else:
        text = function_data
        if text is None: text = "Укажите текст настройках меню!"
    text = TTA_scripts.data_formated(text, formatting_data)
    text = TTA_scripts.markdown(text)
    return_data["text"] = text

    if locale["menus"][menu_data['name']].get('width') is not None: # настройка ширины клавиатуры
        kb_width = int((locale["menus"][menu_data['name']]['width']))
    keyboard = InlineKeyboardMarkup(row_width=kb_width)

    if locale["menus"][menu_data['name']].get('buttons') is not None: # добавление кнопок
        buttons, nav_buttons = create_buttons(locale["menus"][menu_data['name']]['buttons'], menu_data['page'], menu=menu_data["name"], prefix=menu_data['data'])
        keyboard.add(*buttons)
        keyboard.add(*nav_buttons)

    if locale["menus"][menu_data['name']].get('create_buttons') is not None: # добавление кнопок
        function_name = locale["menus"][menu_data['name']]['create_buttons']
        function = globals()[function_name]
        function_data = function(menu_data)
        buttons, nav_buttons = create_buttons(function_data, page=menu_data['page'], menu=menu_data["name"], prefix=menu_data['data'])
        keyboard.add(*buttons)
        keyboard.add(*nav_buttons)



    if locale["menus"][menu_data['name']].get('return') is not None: # кнопка возврата
        btn_return = InlineKeyboardButton((locale["general_buttons"]['return']), callback_data=f'{locale["menus"][menu_data["name"]]["return"]}-0:')
        keyboard.add(btn_return)
    return_data["keyboard"] = keyboard

    if locale["menus"][menu_data['name']].get('handler') is not None: # ожидание ввода
        return_data["handler"] = locale["menus"][menu_data['name']]["handler"]

    return_data["call"] = call
    return_data["message"] = message
    return return_data