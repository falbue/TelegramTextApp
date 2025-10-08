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
logger.info(f"Версия TTA: {VERSION}")

script_dir = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(script_dir, "template_config.json")


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


async def processing_menu(menu, callback, state, input_data=None): # обработчик сообщений
    message_id = await get_user(callback.message, update=True)
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

    if menu.get("send"):
        logger.debug(f"Сообщение было отправлено выбранным пользователям")
        for user in menu["send"]['ids']:
            await bot.send_message(text=menu["send"]["text"], reply_markup=menu["send"]["keyboard"], chat_id=user["telegram_id"])
    try:
        await callback.message.edit_text(menu["text"], reply_markup=menu["keyboard"])
    except:
        await callback.message.edit_text(menu["text"], reply_markup=menu["keyboard"],parse_mode=None)



@dp.message(lambda message: message.text and message.text.startswith('/')) # Обработчик команд
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.chat.id
    message_id = await get_user(message)
    message_id = message_id["message_id"]

    logger.debug(f"id: {user_id} | Команда: {message.text}")
    menu = await get_menu(message)

    try:
        await bot.edit_message_text(menu["text"], reply_markup=menu["keyboard"], chat_id=user_id, message_id=message_id)
    except Exception as e:
        if str(e) in ("Telegram server says - Bad Request: message to edit not found"):
            await bot.send_message(text=menu["text"], reply_markup=menu["keyboard"], chat_id=user_id)
            message_id = await get_user(message, update=True)
            message_id = message_id["message_id"]
            logger.error(f"Обработанная ошибка: {e}")
        elif str(e) in ("Telegram server says - Bad Request: message can't be edited", "Telegram server says - Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message"):
            pass
        else:
            logger.error(f"Ошибка: {e}")
    finally:
        if menu.get("loading"):
            menu = await get_menu(message, menu_loading=True)
            try:
                await bot.edit_message_text(menu["text"], reply_markup=menu["keyboard"], chat_id=user_id, message_id=message_id)
            except Exception as e:
                if str(e) in ("Telegram server says - Bad Request: message can't be edited"):
                    pass
                else:
                    await bot.send_message(text=menu["text"], reply_markup=menu["keyboard"], chat_id=user_id)
                    message_id = await get_user(message, update=True)
                    message_id = message_id["message_id"]
                    logger.error(f"{e}")

        if menu.get("send"):
            logger.debug(f"Сообщение было отправлено выбранным пользователям")
            for user in menu["send"]['ids']:
                await bot.send_message(text=menu["send"]["text"], reply_markup=menu["send"]["keyboard"], chat_id=user["telegram_id"])

        await message.delete()
            


@dp.callback_query() # Обработчики нажатий на кнопки
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

    

@dp.message(Form.waiting_for_input) # обработчик введённого текста
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