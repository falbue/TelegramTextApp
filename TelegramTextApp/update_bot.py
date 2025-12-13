from aiogram.types import BotCommand
from .utils.logger import setup as logger_setup
from .utils.utils import updated_json

logger = logger_setup("UPDATE")


async def update_bot_info(bot_data, bot):
    data = bot_data["bot"]

    # Обработка текстовых данных (имя, описания)
    try:
        new_name = data.get("name")
        new_short_description = data.get("short_description")
        new_description = data.get("description")

        if any([new_name, new_short_description, new_description]):
            me = await bot.get_me()
            bot_info = await bot.get_my_description()
            full_info = await bot.get_my_short_description()

            changes = {}
            if new_name and new_name != me.full_name:
                changes["name"] = new_name
            if (
                new_short_description
                and new_short_description != full_info.short_description
            ):
                changes["short_description"] = new_short_description
            if new_description and new_description != bot_info.description:
                changes["description"] = new_description

            if changes:
                if "name" in changes:
                    await bot.set_my_name(changes["name"])
                if "short_description" in changes:
                    await bot.set_my_short_description(
                        short_description=changes["short_description"]
                    )
                if "description" in changes:
                    await bot.set_my_description(description=changes["description"])
                logger.info("✅ Текстовые данные бота обновлены")
    except Exception as e:
        logger.error(f"⛔ Ошибка текстовых данных: {e}")

    # Обновление команд
    try:
        if bot_data.get("commands"):
            commands = [
                BotCommand(command=name, description=cmd_data["description"])
                for name, cmd_data in bot_data.get("commands").items()
                if cmd_data.get("visible", True)
            ]
            await bot.set_my_commands(commands=commands)
            logger.info("✅ Команды бота обновлены")
    except Exception as e:
        logger.error(f"⛔ Ошибка обновления команд: {e}")

    update_data = await bot.get_me()
    new_data = {"username": update_data.username, "id": update_data.id}
    await updated_json(data=new_data, level="bot")
