VERSION="0.6.3"
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import asyncio
import uuid

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
    
    
    @dp.inline_query()
    async def inline_query_handler(inline_query: types.InlineQuery):
        logger.debug(f"inline: {inline_query}")

        def get_keyboard():
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text="Кнопка",
                url="https://example.com"
            ))
            builder.add(types.InlineKeyboardButton(
                text="Действие",
                callback_data="action"
            ))
            return builder.as_markup()
        
        results = [
            # 1. Текстовый результат (Article)
            types.InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="📝 Текстовый результат",
                input_message_content=types.InputTextMessageContent(
                    message_text="<b>Основной текст</b> с HTML-разметкой",
                    parse_mode="HTML"
                ),
                description="Результат с форматированием и миниатюрой",
                thumb_url="https://via.placeholder.com/100",
                reply_markup=get_keyboard()
            ),
            
            # # 2. Фото по URL
            # types.InlineQueryResultPhoto(
            #     id=str(uuid.uuid4()),
            #     photo_url="https://picsum.photos/600/400",
            #     thumb_url="https://picsum.photos/100/100",
            #     title="🖼 Фото из интернета",
            #     description="Загружено по прямой ссылке",
            #     caption="Фото с подписью",
            #     reply_markup=get_keyboard()
            # ),
            
            # # 3. Видео
            # types.InlineQueryResultVideo(
            #     id=str(uuid.uuid4()),
            #     video_url="https://example.com/sample.mp4",
            #     mime_type="video/mp4",
            #     thumb_url="https://via.placeholder.com/100",
            #     title="🎬 Видео-результат",
            #     description="Видео с платформы",
            #     caption="Пример видео"
            # ),
            
            # # 4. GIF-анимация
            # types.InlineQueryResultGif(
            #     id=str(uuid.uuid4()),
            #     gif_url="https://media.giphy.com/media/3o7TKwxYkeW0ZvTqsU/giphy.gif",
            #     thumb_url="https://media.giphy.com/media/3o7TKwxYkeW0ZvTqsU/giphy.gif",
            #     title="🎞 GIF-анимация",
            #     caption="Гифка с подписью"
            # ),
            
            # # 5. Аудио файл
            # types.InlineQueryResultAudio(
            #     id=str(uuid.uuid4()),
            #     audio_url="https://example.com/sample.mp3",
            #     title="🎵 Аудио трек",
            #     performer="Исполнитель",
            #     caption="Описание трека"
            # ),
            
            # # 6. Голосовое сообщение
            # types.InlineQueryResultVoice(
            #     id=str(uuid.uuid4()),
            #     voice_url="https://example.com/voice.ogg",
            #     title="🎤 Голосовое сообщение",
            #     caption="Voice message"
            # ),
            
            # # 7. Документ (PDF и др.)
            # types.InlineQueryResultDocument(
            #     id=str(uuid.uuid4()),
            #     document_url="https://example.com/document.pdf",
            #     mime_type="application/pdf",
            #     title="📄 PDF документ",
            #     caption="Важный документ",
            #     thumb_url="https://via.placeholder.com/100"
            # ),
            
            # 8. Местоположение
            types.InlineQueryResultLocation(
                id=str(uuid.uuid4()),
                latitude=55.755826,
                longitude=37.617300,
                title="📍 Красная площадь",
                address="Москва, Россия",
                horizontal_accuracy=50
            ),
            
            # 9. Контакт
            types.InlineQueryResultContact(
                id=str(uuid.uuid4()),
                phone_number="+71234567890",
                first_name="Иван",
                last_name="Иванов",
                thumb_url="https://via.placeholder.com/100"
            ),
            
            # # 10. Кэшированное фото (требует file_id)
            # types.InlineQueryResultCachedPhoto(
            #     id=str(uuid.uuid4()),
            #     photo_file_id="AgACAgIAAxkBAAIB...",  # Замените реальным file_id
            #     caption="Кэшированное фото",
            #     reply_markup=get_keyboard()
            # ),
            
            # # 11. Кэшированный стикер
            # types.InlineQueryResultCachedSticker(
            #     id=str(uuid.uuid4()),
            #     sticker_file_id="CAACAgIAAxkBAAIB..."  # Замените реальным file_id
            # )
        ]
        await inline_query.answer(results)
    

    # Запуск бота
    async def main():
        await dp.start_polling(bot)
    
    logger.info("Бот запущен")
    asyncio.run(main())