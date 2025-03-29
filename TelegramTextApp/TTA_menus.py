from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot import types
from TelegramTextApp.TTA_scripts import *
import json
import logging
import inspect

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s [%(asctime)s]   %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

LOCALE_PATH = None
TTA_EXPERIENCE = False

def settings_menu(menus, script_path, formating_text, tta_experience):
    global LOCALE_PATH, format_text, TTA_EXPERIENCE
    TTA_EXPERIENCE = tta_experience
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

def processing_text(text, tta_data):
    user_id = user_tg_data(tta_data['telegram_data'])
    text = data_formated(text, user_id)
    if format_text:
        function_format = globals()[format_text]
        text = function_format(tta_data, text, "text")
    text = markdown(text)
    return text


def create_buttons(tta_data):
    locale = get_locale()
    data_menu = tta_data["call_data"]['data'] # значение для навигационных кнопок 
    menu = tta_data["call_data"]["menu"] # название меню, для навигационных кнопок
    page = int(tta_data["call_data"]["page"])
    buttons_data = tta_data["menu_data"].get("buttons")
    if buttons_data is None: buttons_data = {}

    btn_role = 'user'
    user_id = user_tg_data(tta_data["telegram_data"])
    role =  SQL_request("SELECT role FROM TTA WHERE telegram_id = ?", (int(user_id),))

    list_page = (tta_data["menu_data"].get("list_page"))
    if list_page is None: list_page = 20

    width = (tta_data["menu_data"].get("list_page"))
    if width is None: width = 2
    keyboard = InlineKeyboardMarkup(row_width=width)

    buttons = []
    nav_buttons = []
    start_index = int(page) * list_page
    end_index = start_index + list_page
    paginated_data = list(buttons_data.items())[start_index:end_index]
    
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

    if len(buttons_data) > list_page:
        nav_buttons = []
        if int(page) > 0:
            nav_buttons.append(types.InlineKeyboardButton(f'⬅️ {page} ', callback_data=f'{menu}-{page-1}:{data_menu}'))
        if end_index < len(buttons_data):
            nav_buttons.append(types.InlineKeyboardButton(f'{page+1+1} ➡️', callback_data=f'{menu}-{page+1}:{data_menu}'))
        keyboard.add(*nav_buttons)
    
    return keyboard


def menu_layout(data):    
    try:
        if hasattr(data, 'data') and data.data is not None:
            user_id = data.message.chat.id
            menu_base = (data.data).split(":")
            menu_name = menu_base[0].split("-")[0]
            menu_page = menu_base[0].split("-")[1]
            get_data = (data.data).replace(f"{menu_base[0]}:", "")
            if get_data == "": get_data = None

        elif hasattr(data, 'text') and data.text is not None:
            locale = get_locale()
            user_id = data.chat.id
            command = (data.text).replace("/", "")
            menu_name = "error_command"
            if locale["commands"].get(command):
                menu_name = locale["commands"][command]["menu"]
            get_data = None
            if len(menu_name.split(":")) > 1: 
                menu_name = menu_name.split(":")[0]
                get_data = (data.data).replace(f"{menu_name}:", "")
            menu_page = "0"
            if command == "start":
                TTA_scripts.registration(data)
      

        call_data = {"menu":menu_name, "page":menu_page, "data":get_data} 
    except Exception as e:
        logging.error(e)
        call_data = {"menu":"error_command", "page":"0", "data":None}
    return call_data

def open_menu(data, loading=False):
    call_data = menu_layout(data) # данные, передаваемые в меню

    locale = get_locale() # весь json файл
    menus = locale["menus"] # все меню
    menu = menus.get(call_data['menu']) # меню, которое будем обрабатывать
    if menu is None: menu = 'error' # если меню отстутсвует, то обрабатываем меню error

    list_page = 20 # количество кнопок в меню
    kb_width = 2 # ширина клавиатуры
    
    bot_data = {} # контейнер данных, для бота


    if menu.get('loading') is not None and loading == False: # отправляется только текст, что бы потом обработать всё меню
        bot_data["text"] = TTA_scripts.markdown(menu['loading'])
        bot_data['loading'] = True
        return bot_data

    if menu.get('function') is not None: # выполнение указанной функции
        function_name = (menu['function'])
        function = globals()[function_name]
        function_data = function(tta_data)
        try:
            if function_data.get("text"): menu['text'] = function_data.get("text")
            if function_data.get("buttons"): menu['buttons'] = function_data.get("buttons")
        except: pass

    if menu.get('text') is not None:
        text = processing_text(menu['text'], user_id, tta_data)
    else:
        text = None

    bot_data["text"] = text

    if menu.get('error_text'): # добавление ошибочного текста
        menu_data["error_text"] = processing_text(menu.get("error_text"), user_id, tta_data)

    if menu.get('width') is not None: # настройка ширины клавиатуры
        kb_width = int((menu['width']))
    keyboard = InlineKeyboardMarkup(row_width=kb_width)

    if menu.get('list_page') is not None: # сколько кнопок на странице
        list_page = int((menu['list_page']))

    if menu.get('buttons') is not None: # добавление кнопок
        keyboard = create_buttons(menu["buttons"], tta_data, keyboard, list_page, role=role)

    if menu.get('create_buttons') is not None: # добавление кнопок
        function_name = menu['create_buttons']
        function = globals()[function_name]
        function_data = function(tta_data)
        keyboard = create_buttons(function_data, tta_data, keyboard, list_page, role=role)

    if menu.get('return') is not None: # кнопка возврата
        btn_return = InlineKeyboardButton((locale["var_buttons"]['return']), callback_data=f'{locale["menus"][tta_data["menu"]]["return"]}-0:')
        keyboard.add(btn_return)


    if menu.get('handler') is not None: # ожидание ввода
        menu_data["handler"] = menu["handler"]
        function_format = globals()[format_text]
        bot_data["handler"]["menu"] = function_format(tta_data, menu_data["handler"]["menu"]) # 4

    if menu.get('send') is not None: # Отправка сообщения
        if menu['send'].get("text"):
            menu['send']['text'] = processing_text(menu['send']['text'], user_id, tta_data)
        bot_data["send"] = menu["send"] # 3
                                                                                                                                                                     
        if TTA_EXPERIENCE == True and menu.get("text") is None:
            btn_notif = InlineKeyboardButton((locale["var_buttons"]['notification']), callback_data=f'notification')
            keyboard.add(btn_notif)

    if menu.get('query') is not None:
        bot_data['query'] = menu['query'] # 2

    bot_data["keyboard"] = keyboard # 1
    return bot_data