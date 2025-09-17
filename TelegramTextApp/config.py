import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Создаем шаблонный .env файл
    env_template = """TOKEN=
DB_PATH=data/database.db
LOG_PATH=data
BOT_JSON=bot.json
DEBUG=True
"""
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_template)
    
    raise RuntimeError(
        "Файл .env не найден и был создан автоматически.\n"
        "Пожалуйста, настройте его перед запуском:\n"
        "1. Добавьте ваш TOKEN в файл .env\n"
        "2. Настройте другие параметры при необходимости\n"
        "3. Перезапустите приложение\n"
        f"Файл создан по пути: {env_path.absolute()}"
    )

TOKEN = os.getenv("TOKEN")

if TOKEN is None or TOKEN == "":
    raise RuntimeError("Укажите TOKEN бота в .env файле")

DB_PATH = os.getenv("DB_PATH")
LOG_PATH = os.getenv("LOG_PATH")
DEBUG = os.getenv("DEBUG", "False").lower() in ["true", "1"]
JSON = os.getenv("BOT_JSON")