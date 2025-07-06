from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiogram.types import BotCommand
import aiohttp
from .logging_config import setup_logging


async def update_bot_info(bot_token, bot_data, debug):
    logger = setup_logging(debug)
    bot = Bot(token=bot_token)
    
    data = bot_data['bot']
    
    # Вспомогательная функция для скачивания изображений
    async def download_image(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()  # Проверка на ошибки HTTP
                image_data = await response.read()
                return BufferedInputFile(image_data, filename="image.jpg")

    # Обработка текстовых данных (имя, описания)
    try:
        new_name = data.get('name')
        new_short_description = data.get("short_description")
        new_description = data.get("description")
        
        if any([new_name, new_short_description, new_description]):
            me = await bot.get_me()
            bot_info = await bot.get_my_description()
            full_info = await bot.get_my_short_description()
            
            changes = {}
            if new_name and new_name != me.full_name:
                changes["name"] = new_name
            if new_short_description and new_short_description != full_info.short_description:
                changes["short_description"] = new_short_description
            if new_description and new_description != bot_info.description:
                changes["description"] = new_description
            
            if changes:
                if "name" in changes:
                    await bot.set_my_name(changes["name"])
                if "short_description" in changes:
                    await bot.set_my_short_description(short_description=changes["short_description"])
                if "description" in changes:
                    await bot.set_my_description(description=changes["description"])
                logger.info("✅ Текстовые данные бота обновлены")
    except Exception as e:
        logger.error(f"⛔ Ошибка текстовых данных: {e}")

    # Обновление команд
    try:
        if bot_data.get('commands'):
            commands = [BotCommand(command=name, description=cmd_data["description"])for name, cmd_data in bot_data.get('commands').items()]
            await bot.set_my_commands(commands=commands)
            logger.info("✅ Команды бота обновлены")
    except Exception as e:
        logger.error(f"⛔ Ошибка обновления команд: {e}")
        
    finally:
        await bot.session.close()