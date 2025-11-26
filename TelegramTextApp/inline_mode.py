import uuid
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from . import setup_menu
from .utils.utils import load_json
from .utils import logger

logger = logger.setup("INLINE")
# https://docs.aiogram.dev/en/v3.22.0/api/types/inline_query_result.html#module-aiogram.types.inline_query_result


async def get_inline_result(inline_query):
    query = inline_query.query
    if query == "":
        query = "default"
    inline = load_json(level="inline")

    menus = inline.get(query)
    if menus:
        switch_pm_text = menus.get("tta_button")
        switch_pm_parameter = menus.get("tta_link")
        results = []

        for menu in menus:
            if menu == "tta_button" or menu == "tta_link":
                continue
            menu = menus[menu]
            if isinstance(menu, dict):
                if menu.get("keyboard"):
                    keyboard = None
                    pass
                else:
                    keyboard = None
                result = InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=menu.get("title", "Нужно указать title"),
                    description=menu.get("description", "Нужно указать описание"),
                    input_message_content=InputTextMessageContent(
                        message_text=setup_menu.create_text(
                            menu.get("text", "Нужно указать текст")
                        ),
                        parse_mode="MarkdownV2",
                    ),
                    thumbnail_url=menu.get("thumbnail", None),
                    reply_markup=keyboard,
                )
                results.append(result)
        return results, switch_pm_text, switch_pm_parameter
    else:
        return [], "Меню не найдено", "start"
