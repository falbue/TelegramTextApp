import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


TOKEN = os.getenv("TOKEN")
DB_PATH = os.getenv("DB_PATH")
LOG_PATH = os.getenv("LOG_PATH")
DEBUG = os.getenv("DEBUG", "False").lower() in ["true", "1"]
JSON = os.getenv("BOT_JSON")