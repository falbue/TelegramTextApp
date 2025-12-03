from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .utils.utils import (
    load_custom_functions,
    load_json,
    formatting_text,
    markdown,
    parse_bot_data,
    process_custom_function,
)
from .utils.database import SQL_request_async as SQL, get_user, get_role_id
from .utils.logger import setup as setup_logger


logger = setup_logger("MENUS")


def config_custom_module(user_custom_functions):  # настройка библиотеки пользователя
    global custom_module
    custom_module = load_custom_functions(user_custom_functions)


async def get_bot_data(callback, bot_input=None):  # получение данных от бота
    user = await get_user(callback)

    menu_context = {}
    if bot_input:
        menu_name = bot_input["menu"]
        menu_context["bot_input"] = bot_input
        message = callback

    elif hasattr(callback, "message"):  # кнопка
        menu_name = callback.data
        message = callback.message
    else:  # команда
        message = callback
        command = message.text or ""
        commands = load_json(level="commands") or {}

        if not isinstance(commands, dict):
            try:
                commands = dict(commands)
            except Exception:
                commands = {}

        command_key = command.replace("/", "")
        command_data = commands.get(command_key)
        if command_data is None:
            return None

        if isinstance(command_data, dict):
            menu_name = command_data.get("menu")
        else:
            menu_name = getattr(command_data, "menu", None)

        if menu_name is None:
            return None

    menu_context["menu_name"] = menu_name
    menu_context["telegram_id"] = message.chat.id
    menu_context["user"] = user
    menu_context["callback"] = callback

    return menu_context


async def create_keyboard(
    menu_data, format_data, current_page_index=0
):  # создание клавиатуры
    builder = InlineKeyboardBuilder()
    return_builder = InlineKeyboardBuilder()

    if "keyboard" in menu_data and not (
        isinstance(menu_data["keyboard"], dict) and len(menu_data["keyboard"]) == 0
    ):
        keyboard_items = list(menu_data["keyboard"].items())
        pagination_limit = menu_data.get("pagination", 10)
        if pagination_limit is None:
            pagination_limit = 1000

        pages = []  # получение списка страниц для пагинации
        for i in range(0, len(keyboard_items), pagination_limit):
            pages.append(keyboard_items[i : i + pagination_limit])

        page_items = pages[current_page_index]

        rows = []
        current_row = []
        max_in_row = menu_data.get("row", 2)

        if isinstance(menu_data["keyboard"], str):
            return None

        for callback_data, button_text in page_items:
            if len(callback_data) > 64:
                logger.error(
                    f"Не удалось добавить кнопку '{button_text}'. Название меню слишком длинное: {callback_data}"
                )
                continue
            force_new_line = False
            if button_text.startswith("\\"):
                button_text = button_text[1:]
                force_new_line = True

            button_text = formatting_text(button_text, format_data)
            callback_data = formatting_text(callback_data, format_data)

            if callback_data.startswith("role:"):
                role = callback_data.split("|")[0]
                role = role.split(":")[1]
                callback_data = callback_data.replace(f"role:{role}|", "")

                user_role = await SQL(
                    "SELECT role FROM TTA WHERE id=?", (format_data.get("id"),)
                )
                user_role = user_role.get("role") if user_role else None
                if user_role == role:
                    if callback_data.startswith("url:"):
                        url = callback_data[4:]
                        button = InlineKeyboardButton(text=button_text, url=url)
                    elif callback_data.startswith("app:"):
                        url = callback_data[4:]
                        button = InlineKeyboardButton(
                            text=button_text, web_app=WebAppInfo(url=url)
                        )
                    else:
                        button = InlineKeyboardButton(
                            text=button_text, callback_data=callback_data
                        )

                else:
                    continue

            else:
                button = InlineKeyboardButton(
                    text=button_text, callback_data=callback_data
                )

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

        # Пагинация с отображением 5-6 страниц
        if len(pages) > 1 and pagination_limit is not None:
            nav_row = []
            total_pages = len(pages)
            current_page_num = current_page_index + 1

            max_visible_pages = 6
            start_page = 1
            end_page = total_pages

            if total_pages > max_visible_pages:  # ограничение диапозона
                half_window = max_visible_pages // 2
                start_page = max(1, current_page_num - half_window)
                end_page = start_page + max_visible_pages - 1
                if end_page > total_pages:
                    end_page = total_pages
                    start_page = max(1, end_page - max_visible_pages + 1)

            if current_page_index > 0:  # предыдущая страница
                nav_row.append(
                    InlineKeyboardButton(
                        text=format_data["variables"]["tta_pagination_back"],
                        callback_data=f"pg{current_page_index - 1}|{format_data['menu_name']}",
                    )
                )

            # Кнопки номеров страниц
            for page_num in range(start_page, end_page + 1):
                btn_callback = f"pg{page_num - 1}|{format_data['menu_name']}"
                btn_text = str(page_num)
                if page_num == current_page_num:
                    btn_text = f"• {btn_text} •"  # Текущая страница
                    nav_row.append(
                        InlineKeyboardButton(text=btn_text, callback_data="placeholder")
                    )
                else:
                    nav_row.append(
                        InlineKeyboardButton(text=btn_text, callback_data=btn_callback)
                    )

            if current_page_index < len(pages) - 1:  # следующая страница
                nav_row.append(
                    InlineKeyboardButton(
                        text=format_data["variables"]["tta_pagination_next"],
                        callback_data=f"pg{current_page_index + 1}|{format_data['menu_name']}",
                    )
                )

            builder.row(*nav_row)

    if "return" in menu_data:
        return_builder.button(
            text=format_data["variables"]["tta_return"],
            callback_data=formatting_text(f"return|{menu_data['return']}", format_data),
        )
        builder.row(*return_builder.buttons)

    return builder.as_markup()


def create_text(text, format_data=None, use_markdown=True) -> str:  # создание текста
    if format_data:
        text = formatting_text(text, format_data)
    if use_markdown:
        text = markdown(text)
    return text


async def get_menu(callback, bot_input=None, menu_loading=False):
    menu_context = await get_bot_data(callback, bot_input)
    return await create_menu(menu_context, menu_loading)


async def create_menu(menu_context, menu_loading=False):
    menu_name = menu_context["menu_name"]
    variables = load_json("variables")

    menus = load_json(level="menu")
    if "return|" in menu_name:
        menu_name = menu_name.replace("return|", "")

    if menu_name.startswith("pg"):
        page = menu_name.split("|")[0]
        menu_name = menu_name.replace(f"{page}|", "")
        page = int(page.replace("pg", ""))
    else:
        page = 0

    menu_data = menus.get(menu_name.split("|")[0])
    template = menu_name

    if "|" in menu_name:
        prefix = menu_name.split("|")[0] + "|"
        for key in menus:
            if key.startswith(prefix):
                menu_data = menus.get(key)
                template = key
                break

    if menu_loading is False:
        logger.debug(f"Открываемое меню: {menu_name}")

    if not menu_data:
        menu_data = menus.get("none_menu")

    if menu_data is None:
        raise Exception(f"Меню {menu_name} не найдено в файле меню!")

    if menu_data.get("loading") and menu_loading is False:
        if menu_data["loading"] is True:
            text = variables["tta_loading"]
        else:
            text = menu_data["loading"]
        text = markdown(str(text))
        return {"text": text, "keyboard": None, "loading": True}

    format_data = dict(parse_bot_data(template, menu_name) or {})
    user_data = menu_context.get("user") or {}
    format_data.update(user_data)
    format_data["menu_name"] = menu_name
    format_data["variables"] = variables

    if menu_data.get("input"):
        input_data = menu_data.get("input")
        if isinstance(input_data, dict):
            if input_data.get("menu"):
                menu_data["input"]["menu"] = formatting_text(  # type: ignore
                    input_data.get("menu"), format_data
                )

    if menu_context.get("bot_input"):
        menu_data["bot_input"] = menu_context["bot_input"].get("function")
        bot_input = menu_context["bot_input"]
        format_data[bot_input["data"]] = bot_input.get("input_text", None)
        format_data, menu_data = await process_custom_function(
            "bot_input", format_data, menu_data, custom_module
        )

    if menu_data.get("function"):
        format_data, menu_data = await process_custom_function(
            "function", format_data, menu_data, custom_module
        )
    if menu_data.get("keyboard"):
        format_data, menu_data = await process_custom_function(
            "keyboard", format_data, menu_data, custom_module
        )

    if menu_data.get("edit_menu"):
        menu_context["menu_name"] = menu_data["edit_menu"]
        return await create_menu(menu_context, menu_loading)

    if menu_data.get("send_menu"):
        send_menu = menu_data["send_menu"]
        del menu_data["send_menu"]

        if isinstance(menu_data, dict):
            if isinstance(send_menu, dict):
                menu_context["menu_name"] = send_menu.get("menu")
                menu_context["menu_name"] = formatting_text(
                    menu_context["menu_name"], format_data
                )
                raw_menu_data = await create_menu(menu_context, menu_loading)
                menu_data["send"] = raw_menu_data  # type: ignore
                ids = send_menu.get("id")
                if isinstance(ids, int):
                    menu_data["send"]["ids"] = [ids]
                elif isinstance(ids, list):
                    menu_data["send"]["ids"] = ids
                elif isinstance(ids, str):
                    if ids.startswith("{"):
                        ids = formatting_text(ids, format_data)
                        menu_data["send"]["ids"] = [ids]
                    else:
                        menu_data["send"]["ids"] = await get_role_id(ids)
            else:
                raise Exception("send_menu должен быть словарём!")
        else:
            raise Exception("Меню для отправки должно быть словарём!")

    if menu_data.get("popup"):
        popup = menu_data.get("popup")
        if isinstance(popup, dict):
            popup["text"] = create_text(popup.get("text"), format_data, False)
            if popup.get("blocked") is True:
                menu_data["text"] = "None"  # type: ignore
    else:
        popup = None

    if menu_data.get("text"):
        text = create_text(menu_data["text"], format_data)
    else:  # попап не может быть применён к сообщению, которое отправляется
        popup = {
            "text": f"Ошибка!\nУ открываемого меню {menu_name}, отсутсвует текст!",
            "size": "small",
            "menu_block": True,
        }
        text = ""
    if menu_data.get("keyboard") or menu_data.get("return"):
        keyboard = await create_keyboard(menu_data, format_data, page)
    else:
        keyboard = None
    menu_input = menu_data.get("input", None)

    send = menu_data.get("send", False)
    return {
        "text": text,
        "keyboard": keyboard,
        "input": menu_input,
        "popup": popup,
        "send": send,
    }
