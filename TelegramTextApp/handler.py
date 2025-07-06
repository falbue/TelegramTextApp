from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import asyncio

from setup_menu import *
import update_bot

TOKEN = os.getenv("BOT_TOKEN")
asyncio.run(update_bot.update_bot_info(TOKEN, load_bot()))


bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="MarkdownV2"))
dp = Dispatcher()

class Form(StatesGroup):
    waiting_for_input = State()

# Обработчик команд
@dp.message(lambda message: message.text and message.text.startswith('/'))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.chat.id
    logger.debug(f"id: {user_id} | Команда: {message.text}")
    menu = await get_menu(message)
    if menu is None:
        await message.delete()
    else:
        await message.answer(menu["text"], reply_markup=menu["keyboard"])

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

if __name__ == "__main__":
    logger.info("Бот запущен")
    asyncio.run(main())