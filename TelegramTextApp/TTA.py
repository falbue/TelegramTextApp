from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
from importlib.metadata import version, PackageNotFoundError
import os
import json

from .setup_menu import load_json, get_user, get_menu, create_menu
from . import config

from .utils.logger import setup as logger_setup
from .utils.database import create_tables, get_role_id, update_phone_number
from .update_bot import update_bot_info


logger = logger_setup("TTA")
dp = Dispatcher()

try:
    VERSION = version("TelegramTextApp")
except PackageNotFoundError:
    VERSION = "development"

logger.debug(f"Версия TTA: {VERSION}")

script_dir = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(script_dir, "template_config.json")
if os.path.exists(config.JSON):
    pass
else:
    with open(template_path, "r", encoding="utf-8") as template_file:
        template_data = json.load(template_file)
    with open(config.JSON, "w", encoding="utf-8") as target_file:
        json.dump(template_data, target_file, indent=4, ensure_ascii=False)
    logger.info(f"Файл бота {config.JSON} создан")
if config.TOKEN is None or config.TOKEN == "":
    raise RuntimeError("Укажите TOKEN бота в .env файле")

bot = Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode="MarkdownV2"))


class Form(StatesGroup):
    waiting_for_input = State()


def send_menu(menu_name, ids):
    asyncio.run(send_menu_wrapper(menu_name, ids))


async def send_menu_wrapper(menu_name: str, ids, menu=None):
    """Обёртка: собирает все user_id и отправляет массово."""
    if isinstance(ids, str):
        users = await get_role_id(ids)
        user_ids = [user["telegram_id"] for user in users]
    elif isinstance(ids, list):
        user_ids = ids
    else:
        user_ids = [ids]

    data = {"menu_name": menu_name, "update_message": False}
    menu = await create_menu(data)

    for user_id in user_ids:
        try:
            await send_menu_user(menu_name, user_id, menu)
        except Exception as e:
            logger.error(f"Ошибка при отправке пользователю {user_id}: {e}")


async def send_menu_user(menu_name: str, user_id: int, menu: dict):
    try:
        message = await bot.send_message(
            text=menu["text"],
            chat_id=user_id,
            reply_markup=menu.get("keyboard"),
        )
        message_id = message.message_id

        if menu.get("loading"):
            updated_menu = await create_menu(
                {"menu_name": menu_name, "update_message": False}, loading=True
            )
            try:
                await bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text=updated_menu["text"],
                    reply_markup=updated_menu.get("keyboard"),
                )
            except Exception as e:
                if "message can't be edited" not in str(e):
                    new_msg = await bot.send_message(
                        chat_id=user_id,
                        text=updated_menu["text"],
                        reply_markup=updated_menu.get("keyboard"),
                    )
                    message_id = new_msg.message_id

        if menu.get("send") and isinstance(menu["send"], dict):
            for target_user in menu["send"]["ids"]:
                try:
                    await bot.send_message(
                        chat_id=target_user["telegram_id"],
                        text=menu["send"]["text"],
                        reply_markup=menu["send"].get("keyboard"),
                    )
                except Exception as e:
                    logger.error(f"Ошибка при доп.отправке: {e}")

    except Exception as e:
        logger.error(
            f"Не удалось отправить меню {menu_name} пользователю {user_id}: {e}"
        )
        raise


async def processing_menu(
    menu, callback, state, input_data=None
):  # обработчик сообщений
    await get_user(callback.message, update=True)
    if menu.get("send") and isinstance(menu["send"], bool) and menu["send"] is True:
        await callback.answer()
        await send_menu_user(
            menu_name=callback.data, user_id=callback.message.chat.id, menu=menu
        )
        return
    if menu.get("loading"):
        await callback.message.edit_text(menu["text"], reply_markup=menu["keyboard"])
        if input_data:
            menu = await get_menu(input_data[0], input_data[1], menu_loading=True)
        else:
            menu = await get_menu(callback, menu_loading=True)

    if menu.get("popup"):
        popup = menu.get("popup")
        if isinstance(popup, dict):
            if popup.get("size") == "big":
                show_alert = True
            else:
                show_alert = False
            await callback.answer(popup["text"], show_alert=show_alert)
            if popup.get("blocked") is True:
                return

    if menu.get("input"):
        logger.debug("Ожидание ввода...")
        await state.update_data(
            current_menu=menu, message_id=callback.message.message_id, callback=callback
        )
        await state.set_state(Form.waiting_for_input)

    if menu.get("send") and isinstance(menu["send"], dict):
        for user in menu["send"]["ids"]:
            try:
                await bot.send_message(
                    text=menu["send"]["text"],
                    reply_markup=menu["send"]["keyboard"],
                    chat_id=user,
                )
                logger.debug("Сообщение было отправлено выбранным пользователям")
            except Exception as e:
                logger.error(
                    f"Ошибка при отправке сообщения выбранным пользователям | {user}: {e}"
                )

    try:
        await callback.message.edit_text(menu["text"], reply_markup=menu["keyboard"])
    except Exception as e:
        if str(e) in (
            "Telegram server says - Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message"
        ):
            return
        else:
            logger.error(f"Ошибка при обновлении меню: {e}")
        await callback.message.edit_text(
            menu["text"], reply_markup=menu["keyboard"], parse_mode=None
        )


@dp.message(
    lambda message: message.text and message.text.startswith("/")
)  # Обработчик команд
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.chat.id
    message_id = await get_user(message)
    if message_id is not None:
        message_id = message_id["message_id"]

    logger.debug(f"id: {user_id} | Команда: {message.text}")
    menu = await get_menu(message)

    try:
        if menu.get("update_message", True) is True:
            await bot.edit_message_text(
                menu["text"],
                reply_markup=menu["keyboard"],
                chat_id=user_id,
                message_id=message_id,
            )
        else:
            await bot.send_message(
                text=menu["text"], reply_markup=menu["keyboard"], chat_id=user_id
            )
    except Exception as e:
        if str(e) in ("Telegram server says - Bad Request: message to edit not found"):
            await bot.send_message(
                text=menu["text"], reply_markup=menu["keyboard"], chat_id=user_id
            )
            message_id = await get_user(message, update=True)
            if message_id is not None:
                message_id = message_id["message_id"]
            logger.error(f"Обработанная ошибка: {e}")
        elif str(e) in (
            "Telegram server says - Bad Request: message can't be edited",
            "Telegram server says - Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message",
        ):
            pass
        else:
            logger.error(f"Ошибка при обработке команды: {e}")
    finally:
        if menu.get("loading"):
            menu = await get_menu(message, menu_loading=True)
            try:
                await bot.edit_message_text(
                    menu["text"],
                    reply_markup=menu["keyboard"],
                    chat_id=user_id,
                    message_id=message_id,
                )
            except Exception as e:
                if str(e) in (
                    "Telegram server says - Bad Request: message can't be edited"
                ):
                    pass
                else:
                    await bot.send_message(
                        text=menu["text"],
                        reply_markup=menu["keyboard"],
                        chat_id=user_id,
                    )
                    message_id = await get_user(message, update=True)
                    if message_id is not None:
                        message_id = message_id["message_id"]
                    logger.error(f"{e}")

        if menu.get("send"):
            logger.debug("Сообщение было отправлено выбранным пользователям")
            for user in menu["send"]["ids"]:
                await bot.send_message(
                    text=menu["send"]["text"],
                    reply_markup=menu["send"]["keyboard"],
                    chat_id=user["telegram_id"],
                )
        if menu.get("delete_command") is True:
            await message.delete()


@dp.callback_query()  # Обработчики нажатий на кнопки
async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    data = callback.data
    user_id = (
        callback.message.chat.id
        if callback.message and callback.message.chat
        else callback.from_user.id
    )
    logger.debug(f"id: {user_id} | Кнопка: {data}")

    if data == "notification":
        if callback.message:
            await callback.message.delete()  # type: ignore
        return
    if data == "placeholder":
        await callback.answer("")
        return

    menu = await get_menu(callback)
    await processing_menu(menu, callback, state)


@dp.message(Form.waiting_for_input)  # обработчик введённого текста
async def handle_text_input(message: types.Message, state: FSMContext):
    await message.delete()

    data = await state.get_data()
    await state.clear()
    menu = data.get("current_menu")
    callback = data.get("callback")

    if message.contact:
        await update_phone_number(message.chat.id, message.contact.phone_number)

    if isinstance(menu, dict):
        if menu.get("input"):
            input_data = menu["input"]
            input_data["input_text"] = message.text
            menu = await get_menu(message, user_input=input_data)
            if menu.get("error"):
                await state.set_state(Form.waiting_for_input)
                menu = await get_menu(callback, error=menu.get("error"))
                del menu["error"]
                await state.update_data(
                    current_menu=menu,
                    message_id=message,
                    callback=callback,
                )
            await processing_menu(menu, callback, state, [message, input_data])
        else:
            logger.error("Меню ввода не найдено или оно некорректно")
    else:
        logger.error("Текущего меню не найдено или оно некорректно")


def start() -> None:
    async def main():
        await create_tables()
        await update_bot_info(await load_json(), bot)
        await dp.start_polling(bot)

    logger.info("Бот запущен")
    asyncio.run(main())
