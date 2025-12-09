from aiogram.types import InlineKeyboardButton, WebAppInfo, CopyTextButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .utils.utils import (
    load_json,
    formatting_text,
    markdown,
    function,
    get_params,
)
from .utils.database import SQL_request_async as SQL, get_user, get_role_id
from .utils.logger import setup as setup_logger


logger = setup_logger("MENUS")


async def create_context(callback, user_input=None):
    # создание контекста, для настройки меню
    context = {}
    if user_input:  # обработка ввода пользователя
        menu_name = user_input["menu"]
        context["user_input"] = user_input
        context["params"] = user_input.get("params", {})
        message = callback

    elif hasattr(callback, "message"):  # кнопка
        menu_name = callback.data
        message = callback.message
    else:  # команда
        message = callback
        command = message.text.split("@")[0] or ""
        commands = await load_json(level="commands") or {}

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
            delete_command = command_data.get("delete", True)
            update_message = command_data.get("update", True)
            context["delete_command"] = delete_command
            context["update_message"] = update_message
        else:
            menu_name = getattr(command_data, "menu", None)

        if menu_name is None:
            return None

    context["menu_name"] = menu_name
    context["user"] = await get_user(callback)

    return context


async def create_keyboard(
    menu_data, format_data, current_page_index=0
):  # создание клавиатуры
    builder = InlineKeyboardBuilder()
    return_builder = InlineKeyboardBuilder()

    if menu_data.get("keyboard"):
        if isinstance(menu_data["keyboard"], str):
            func_data = await function(menu_data["keyboard"], format_data)
            if isinstance(func_data, dict):
                menu_data["keyboard"] = func_data.get("keyboard", {})

    if "keyboard" in menu_data and not (
        isinstance(menu_data["keyboard"], dict) and len(menu_data["keyboard"]) == 0
    ):
        keyboard_items = list(menu_data["keyboard"].items())
        pagination_limit = menu_data.get("pagination", 10)
        if pagination_limit is None:
            pagination_limit = 50

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

            button_text = await formatting_text(button_text, format_data)
            callback_data = await formatting_text(callback_data, format_data)

            if callback_data.startswith("role:"):
                button_role = callback_data.split("|")[0]
                button_role = button_role.split(":")[1]
                callback_data = callback_data.replace(f"role:{button_role}|", "")

                user_role = await SQL(
                    "SELECT role FROM TTA WHERE id=?", (format_data.get("id"),)
                )
                user_role = user_role.get("role") if user_role else None
            else:
                user_role = None
                button_role = None

            if callback_data.startswith("url:"):
                url = callback_data[4:]
                button = InlineKeyboardButton(text=button_text, url=url)
            elif callback_data.startswith("app:"):
                url = callback_data[4:]
                button = InlineKeyboardButton(
                    text=button_text, web_app=WebAppInfo(url=url)
                )
            elif callback_data.startswith("copy:"):
                print(callback_data)
                copy = callback_data[5:]
                copy_data = CopyTextButton(text=copy)
                button = InlineKeyboardButton(text=button_text, copy_text=copy_data)
                print("Србатывает")

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

            if button_role is None or button_role == user_role:
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
            callback_data=await formatting_text(
                f"return|{menu_data['return']}", format_data
            ),
        )
        builder.row(*return_builder.buttons)

    return builder.as_markup()


async def create_text(
    text, format_data=None, use_markdown=True
) -> str:  # создание текста
    if format_data:
        text = await formatting_text(text, format_data)
    if use_markdown:
        text = await markdown(text)
    return text


async def get_menu(callback, user_input=None, menu_loading=False, error={}):
    menu_context = await create_context(callback, user_input)
    return await create_menu(menu_context, menu_loading, error)


async def create_raw_menu(name) -> dict:
    if "return|" in name:
        name = name.replace("return|", "")
    if name.startswith("pg"):
        page = name.split("|")[0]
        name = name.replace(f"{page}|", "")
        page = int(page.replace("pg", ""))
    else:
        page = 0
    return {"name": name, "page": page}


async def get_parameters(name) -> tuple[dict, str]:
    menus = await load_json(level="menu")
    data = menus.get(name.split("|")[0])
    template = ""
    if "|" in name:
        prefix = name.split("|")[0] + "|"
        for key in menus:
            if key.startswith(prefix):
                data = menus.get(key)
                template = key
                break
    if data:
        return data, template
    else:
        return {}, ""


async def create_menu(context, loading=False, error={}) -> dict:
    menu_name = context["menu_name"]
    variables = await load_json("variables")
    raw_menu = await create_raw_menu(menu_name)
    parameters, template = await get_parameters(raw_menu["name"])
    logger.debug(f"Создание меню: {raw_menu['name']}")

    if not parameters:
        return {
            "popup": {
                "text": f"Меню {menu_name} не найдено!",
                "size": "big",
                "blocked": True,
            }
        }

    if parameters.get("loading") and loading is False:
        if parameters["loading"] is True:
            raw_menu["text"] = variables.get("loading", "Loading...")
        elif isinstance(parameters["loading"], str):
            raw_menu["text"] = parameters["loading"]
        return {
            "text": await create_text(raw_menu["text"], False),
            "keyboard": None,
            "loading": True,
        }

    format_data = {}
    format_data["params"] = context.get("params", {})
    format_data["params"].update(await get_params(template, raw_menu["name"]) or {})
    format_data["user"] = context.get("user") or {}
    format_data["menu_name"] = raw_menu["name"]
    format_data["bot"] = await load_json(level="bot")
    format_data["variables"] = variables
    format_data["error"] = error

    async def call_function(func_name: str, format_data: dict):
        func_data = await function(func_name, format_data)
        if isinstance(func_data, dict):
            if func_data.get("error"):
                format_data["error"].update(func_data["error"])
                del func_data["error"]
                return False
            else:
                format_data["params"].update(func_data)

    if context.get("user_input"):  # обработка ввода пользователя
        input_param = context["user_input"].get("data", "input_text")
        format_data["params"][input_param] = context["user_input"].get("input_text", "")
        if context["user_input"].get("function"):
            logger.debug("Вызов функции после ввода пользователя")
            result = await call_function(context["user_input"]["function"], format_data)
            if result is False:
                return {"error": format_data["error"]}
            del context["user_input"]

    if parameters.get("function"):
        logger.debug(f"Вызов функции меню: {menu_name}")
        await call_function(parameters["function"], format_data)

    send = {}
    if parameters.get("send"):
        send_menu = parameters["send"]

        if isinstance(send_menu, dict):
            if send_menu.get("text"):
                send["send"] = {
                    "text": await formatting_text(send_menu["text"], format_data),
                    "keyboard": await create_keyboard(
                        {"keyboard": {"notification": "{variables.tta_notification}"}},
                        format_data,
                    ),
                }
            else:
                context["menu_name"] = await formatting_text(
                    send_menu["menu"], format_data
                )
                send["send"] = await create_menu(
                    context, loading, format_data.get("error", {})
                )
            ids = send_menu.get("id")
            if isinstance(ids, int):
                send["send"]["ids"] = [ids]  # type: ignore
            elif isinstance(ids, list):
                raw_ids = []
                for uid in ids:
                    raw_ids.append(await formatting_text(uid, format_data))
                ids = raw_ids
                send["send"]["ids"] = ids  # type: ignore
            elif isinstance(ids, str):
                if ids.startswith("{"):
                    ids = await formatting_text(ids, format_data)
                    send["send"]["ids"] = [ids]  # type: ignore
                else:
                    send["send"]["ids"] = await get_role_id(ids)  # type: ignore
        else:
            raise Exception("send должен быть словарём!")

    if parameters.get("text"):
        raw_menu["text"] = parameters["text"]
        font_style = format_data.get("bot", {}).get("font_style", "").lower()
        if font_style == "bold":
            raw_menu["text"] = f"*{raw_menu['text']}*"
    else:
        parameters["popup"] = {
            "text": f"Ошибка!\nУ открываемого меню {menu_name}, отсутсвует текст!",
            "size": "big",
            "blocked": True,
        }
        raw_menu["text"] = ""

    async def create_popup(
        popup: dict | str, blocked: bool = False, size: str = "small"
    ):
        if isinstance(popup, dict):
            popup["text"] = await create_text(popup.get("text"), format_data, False)
            if popup.get("blocked") is True:
                raw_menu["text"] = ""
        elif isinstance(popup, str):
            popup = {"text": await create_text(popup, format_data, False)}

    popup = parameters.get("popup", None)
    if popup:
        popup = await create_popup(parameters["popup"])

    if parameters.get("keyboard") or parameters.get("return"):
        keyboard = await create_keyboard(parameters, format_data, raw_menu["page"])
    else:
        keyboard = None

    menu_input = parameters.get("input", None)
    if menu_input and isinstance(menu_input, dict):
        menu_input["params"] = format_data["params"]

    return {
        "text": await create_text(raw_menu["text"], format_data),
        "keyboard": keyboard,
        "input": menu_input,
        "popup": popup,
        "send": send.get("send", None),
        "error": format_data.get("error"),
        "delete_command": context.get("delete_command", True),
        "update_message": context.get("update_message", True),
    }
