VERSION="0.6.4"
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import asyncio

from .setup_menu import *
from . import update_bot


def start(token, json_file, database, debug=False):
    logger = setup_logging(debug)
    logger.debug("Логгирование подключено")

    TOKEN = os.getenv("BOT_TOKEN")
    logger.debug("Токен получен")

    config_db(database, debug)
    asyncio.run(create_tables())
    logger.debug("База настроена")

    utils_config(debug)
    logger.debug("Утилиты подключены")

    config_json(json_file, debug, get_caller_file_path())
    logger.debug("Бот получен")

    asyncio.run(update_bot.update_bot_info(token, load_bot(), debug))
    
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode="MarkdownV2"))
    dp = Dispatcher()
    
    class Form(StatesGroup):
        waiting_for_input = State()
    
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
                else:
                    # Это какая-то другая ошибка
                    logger.error(f"Не удалось изменить сообщение: {e}") 
                    await message.answer(menu["text"], reply_markup=menu["keyboard"])
                await message.delete()
    
    # Обработчики нажатий на кнопки
    @dp.callback_query()
    async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
        await state.clear()
        data = callback.data
        user_id = callback.message.chat.id
        logger.debug(f"id: {user_id} | Кнопка: {data}")
        
        if data.split("|")[0] == "mini":
            text = await get_mini_menu(callback)
            await callback.answer(text, show_alert=True)
            return
    
        if data == 'notification':
            await callback.message.delete()
            return
    
        menu = await get_menu(callback)
    
        if menu.get("input"):
            logger.debug("Ожидание ввода...")
            await state.update_data(
                current_menu=menu,
                message_id=callback.message.message_id,
                callback=callback
            )
            await state.set_state(Form.waiting_for_input)
        
        await callback.message.edit_text(menu["text"], reply_markup=menu["keyboard"])

        if menu.get("loading"):
            menu = await get_menu(callback, menu_loading=True)
            await callback.message.edit_text(menu["text"], reply_markup=menu["keyboard"])
    
    
    @dp.message(Form.waiting_for_input)
    async def handle_text_input(message: types.Message, state: FSMContext):
        await message.delete()
    
        data = await state.get_data()
        menu = data.get("current_menu")
        callback = data.get('callback')
    
        input_data = menu['input']
        input_data['input_text'] = message.text
    
        menu = await get_menu(message, input_data)
        if not menu:
            logger.debug("Пока никак")
            return
    
        await state.clear()
        await callback.message.edit_text(menu["text"], reply_markup=menu["keyboard"])
    
    
    # Запуск бота
    async def main():
        await dp.start_polling(bot)
    
    logger.info("Бот запущен")
    asyncio.run(main())