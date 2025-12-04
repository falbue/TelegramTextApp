import os
from dotenv import load_dotenv
from pathlib import Path
from dotenv import dotenv_values

env_path = Path(".") / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    env_template = """TOKEN=
DB_PATH=data/database.db
LOG_PATH=data
JSON=bot.json
DEBUG=True
"""

    with open(env_path, "w", encoding="utf-8") as f:
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
DB_PATH: str = os.getenv("DB_PATH", "data/database.db")
LOG_PATH: str = os.getenv("LOG_PATH", "data")
DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
JSON: str = os.getenv("JSON", "bot.json")

ENV = {
    "TOKEN": TOKEN,
    "DB_PATH": DB_PATH,
    "LOG_PATH": LOG_PATH,
    "DEBUG": DEBUG,
    "JSON": JSON,
}

for key, value in dotenv_values(env_path).items():
    if not key:
        continue
    if key not in ENV:
        ENV[key] = value
