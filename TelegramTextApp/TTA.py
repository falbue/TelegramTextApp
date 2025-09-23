from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import asyncio

from importlib.metadata import version, PackageNotFoundError

from .setup_menu import *
from . import update_bot
from . import config
from .utils import logger

logger = logger.setup("TTA")

try:
    VERSION = version("TelegramTextApp")
except PackageNotFoundError:
    VERSION = "development"

script_dir = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(script_dir, "template_config.json")

logger.info(f"Версия TTA: {VERSION}")

if os.path.exists(config.JSON):
    pass
else:
    with open(template_path, 'r', encoding='utf-8') as template_file:
        template_data = json.load(template_file)
    
    with open("bot.json", 'w', encoding='utf-8') as target_file:
        json.dump(template_data, target_file, indent=4, ensure_ascii=False)
    
    logger.info(f"Файл бота 'bot.json' успешно создан")

asyncio.run(create_tables())

config_custom_module(get_caller_file_path())

asyncio.run(update_bot.update_bot_info(load_json()))

bot = Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode="MarkdownV2"))
dp = Dispatcher()

class Form(StatesGroup):
    waiting_for_input = State()

async def processing_menu(menu, callback, state, input_data=None):
    if menu.get("loading"):
        await callback.message.edit_text(menu["text"], reply_markup=menu["keyboard"])
        if input_data:
            menu = await get_menu(input_data[0], input_data[1], menu_loading=True)
        else:
            menu = await get_menu(callback, menu_loading=True)

    if menu.get("popup"):
        popup = menu.get("popup")
        if popup.get("size") == "big":
            show_alert = True
        else: 
            show_alert = False
        await callback.answer(popup["text"], show_alert=show_alert)
        if popup.get("menu_block"):
            return

    if menu.get("input"):
        logger.debug("Ожидание ввода...")
        await state.update_data(
            current_menu=menu,
            message_id=callback.message.message_id,
            callback=callback
        )
        await state.set_state(Form.waiting_for_input)
    try:
        await callback.message.edit_text(menu["text"], reply_markup=menu["keyboard"])
    except:
        await callback.message.edit_text(menu["text"], reply_markup=menu["keyboard"],parse_mode=None )


# Обработчик команд
@dp.message(lambda message: message.text and message.text.startswith('/'))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.chat.id
    try: # если пользователь есть, удалим старое сообщение
        message_id = await get_user(message, False)
        message_id = message_id["message_id"]
        if message.text == "/start":
            await bot.delete_message(chat_id=user_id, message_id=message_id)
    except:
        message_id = 0


    logger.debug(f"id: {user_id} | Команда: {message.text}")
    menu = await get_menu(message)


    if menu:
        print(menu)
        try:
            await bot.edit_message_text(menu["text"], reply_markup=menu["keyboard"], chat_id=user_id, message_id=message_id)
            await message.delete()
            if menu.get("loading"):
                menu = await get_menu(message, menu_loading=True)
                await bot.edit_message_text(menu["text"], reply_markup=menu["keyboard"], chat_id=user_id, message_id=message_id)
        except Exception as e:
            if "message is not modified" in str(e) and message.text != "/start":
                # Это именно та ошибка, которую мы ожидаем
                logger.debug("Сообщение не было изменено (контент и разметка идентичны)")
                await message.delete()
            else:
                # Это какая-то другая ошибка
                logger.error(f"Не удалось изменить сообщение: {e}") 
                await message.answer(menu["text"], reply_markup=menu["keyboard"])
                await message.delete()
                if menu.get("loading"):
                    message_id = await get_user(message, False)
                    message_id = message_id["message_id"]
                    menu = await get_menu(message, menu_loading=True)
                    await bot.edit_message_text(menu["text"], reply_markup=menu["keyboard"], chat_id=user_id, message_id=message_id)

# Обработчики нажатий на кнопки
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    data = callback.data
    user_id = callback.message.chat.id
    logger.debug(f"id: {user_id} | Кнопка: {data}")

    if data == 'notification':
        await callback.message.delete()
        return

    menu = await get_menu(callback)
    await processing_menu(menu, callback, state)

    

@dp.message(Form.waiting_for_input)
async def handle_text_input(message: types.Message, state: FSMContext):
    await message.delete()

    data = await state.get_data()
    await state.clear()
    menu = data.get("current_menu")
    callback = data.get('callback')

    input_data = menu['input']
    input_data['input_text'] = message.text

    menu = await get_menu(message, input_data)
    await processing_menu(menu, callback, state, [message, input_data])
    
    
def start():
    # Запуск бота
    async def main():
        await dp.start_polling(bot)
    
    logger.info("Бот запущен")
    asyncio.run(main())