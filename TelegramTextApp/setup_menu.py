from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

import json

from .utils.utils import *
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

async def create_keyboard(menu_data, format_data=None, custom_module=None, current_page_index=0): # создание клавиатуры
    builder = InlineKeyboardBuilder()
    return_builder = InlineKeyboardBuilder()

    if "keyboard" in menu_data:
        keyboard_items = list(menu_data["keyboard"].items())
        pagination_limit = menu_data.get("pagination", 10)
        if pagination_limit == None:
            pagination_limit = 1000

        pages = []
        for i in range(0, len(keyboard_items), pagination_limit):
            pages.append(keyboard_items[i:i + pagination_limit])

        page_items = pages[current_page_index]

        rows = []
        current_row = []
        max_in_row = menu_data.get("row", 2)

        if isinstance(menu_data["keyboard"], str):
            return None

        for callback_data, button_text in page_items:
            force_new_line = False
            if button_text.startswith('\\'):
                button_text = button_text[1:]
                force_new_line = True

            button_text = formatting_text(button_text, format_data)
            callback_data = formatting_text(callback_data, format_data)

            if callback_data.startswith("url:"):
                url = callback_data[4:]
                button = InlineKeyboardButton(text=button_text, url=url)
            elif callback_data.startswith("app:"):
                url = callback_data[4:]
                button = InlineKeyboardButton(text=button_text, web_app=WebAppInfo(url=url))
            elif callback_data.startswith("role:"):
                role = callback_data.split("|")[0]
                role = role.split(":")[1]
                callback_data = callback_data.replace(f"role:{role}|", "")

                user_role = await SQL_request_async("SELECT role FROM TTA WHERE id=?", (format_data["id"],))
                user_role = user_role["role"]
                if user_role == role:
                    button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
                else:
                    continue
            else:
                button = InlineKeyboardButton(text=button_text, callback_data=callback_data)

            if len(current_row) >= max_in_row:
                rows.append(current_row)
                current_row = []

            if force_new_line and current_row:
                rows.append(current_row)
                current_row = []

            current_row.append(button)

        if current_row:
            rows.append(current_row)

        for row in rows:
            builder.row(*row)

        # Пагинация с отображением 5-7 страниц
        if len(pages) > 1 and pagination_limit != None:
            nav_row = []
            total_pages = len(pages)
            current_page_num = current_page_index + 1
        
            # Максимум 6 кнопок с номерами страниц
            max_visible_pages = 6
            start_page = 1
            end_page = total_pages
        
            # Если страниц слишком много, ограничиваем диапазон
            if total_pages > max_visible_pages:
                half_window = max_visible_pages // 2  # 3
                start_page = max(1, current_page_num - half_window)
                end_page = start_page + max_visible_pages - 1
                if end_page > total_pages:
                    end_page = total_pages
                    start_page = max(1, end_page - max_visible_pages + 1)
        
            # Кнопка "◀️" (предыдущая страница)
            if current_page_index > 0:
                nav_row.append(InlineKeyboardButton(text=format_data["variables"]["tta_pagination_back"], callback_data=f'pg{current_page_index - 1}|{format_data["menu_name"]}'))
        
            # Кнопки номеров страниц
            for page_num in range(start_page, end_page + 1):
                btn_callback = f'pg{page_num - 1}|{format_data["menu_name"]}'
                btn_text = str(page_num)
                if page_num == current_page_num:
                    btn_text = f"• {btn_text} •"  # Текущая страница
                    nav_row.append(InlineKeyboardButton(text=btn_text, callback_data="placeholder"))
                else:
                    nav_row.append(InlineKeyboardButton(text=btn_text, callback_data=btn_callback))
        
            # Кнопка "▶️" (следующая страница)
            if current_page_index < len(pages) - 1:
                nav_row.append(InlineKeyboardButton(text=format_data["variables"]["tta_pagination_next"], callback_data=f'pg{current_page_index + 1}|{format_data["menu_name"]}'))
        
            builder.row(*nav_row)

    if "return" in menu_data:
        return_builder.button(
            text=format_data["variables"]["tta_return"],
            callback_data=formatting_text(f"return|{menu_data['return']}", format_data)
        )
        builder.row(*return_builder.buttons)

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
    variables = load_json("variables")

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
            text = variables["tta_loading"]
        else:
            text = menu_data["loading"]
        text = markdown(text)
        return {"text":text, "keyboard":None, "loading":True}


    format_data = parse_bot_data(template, menu_name)
    format_data = {**format_data, **(tta_data["user"] or {})}
    format_data["menu_name"] = menu_name
    format_data["variables"] = variables

    if tta_data.get("bot_input"):
        menu_data["bot_input"] = tta_data["bot_input"].get("function")
        bot_input = tta_data["bot_input"]
        format_data[bot_input["data"]] = bot_input.get("input_text", None)
        format_data, menu_data = await process_custom_function("bot_input", format_data, menu_data, custom_module)
    
    
    if menu_data.get("function"):
        format_data, menu_data = await process_custom_function("function", format_data, menu_data, custom_module)
    if menu_data.get("keyboard"):
        format_data, menu_data = await process_custom_function("keyboard", format_data, menu_data, custom_module)


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