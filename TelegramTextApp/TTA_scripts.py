import json
from datetime import datetime
import pytz
import sqlite3
import os
import re
import inspect
from TelegramTextApp import TTA_use_db
from TelegramTextApp.TTA_use_db import SQL_request

def create_file_menus(menu_path):
    if not os.path.isfile(menu_path):
        data = {
            "menus": {
                "error": {
                    "text": "Это меню ещё не создано",
                    "buttons": {},
                    "return": "main"
                },

                "main": {
                    "text": "Привет я запущен на [TTA](https://github.com/falpin/TelegramTextApp)"
                }
            },

            "commands": {
                "start": {
                    "menu": "main",
                    "text": "Перезапуск бота"
                }
            },

            "general_buttons": {
                "return": "< Назад",
                "admin": "Администратор",
                "notification": "Прочитано"
            }
        }
        
        with open(menu_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print("Файл Для работы с меню бота создан!")

def get_config(DB_PATH="database.db", save_folder="SAVE_FOLDER"):
    global SAVE_FOLDER
    SAVE_FOLDER = save_folder
    TTA_use_db.use_db_settings(DB_PATH)
    TTA_use_db.create_TTA()


def now_time():  # Получение текущего времени по МСК
    now = datetime.now()
    tz = pytz.timezone('Europe/Moscow')
    now_moscow = now.astimezone(tz)
    current_time = now_moscow.strftime("%H:%M:%S")
    current_date = now_moscow.strftime("%Y.%m.%d")
    return current_date, current_time


def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def save_file(document, bot):
    create_folder(SAVE_FOLDER)
    file_info = bot.get_file(document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    unique_file_name = get_unique_filename(SAVE_FOLDER, document.file_name)
    save_path = os.path.join(SAVE_FOLDER, unique_file_name)
    
    with open(save_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    return unique_file_name

def get_unique_filename(base_path, filename):
    name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(base_path, new_filename)):
        new_filename = f"{name}_{counter}{ext}"
        counter += 1
    return new_filename

def markdown(text, full=False):  # экранирование
    if full == True: special_characters = r'*|~[]()>#+-=|{}._!'
    else: special_characters = r'>#+-={}.!'
    escaped_text = ''
    for char in text:
        if char in special_characters:
            escaped_text += f'\\{char}'
        else:
            escaped_text += char
    return escaped_text

def data_formated(text, data=None): # форматирование текста
    user_data = [None] * 4
    if data is None:
        data = {}

    if data.get("user"):
        user_data = SQL_request("SELECT * FROM users WHERE telegram_id = ?", (int(data["user"]),))

    if data != {}:
        text = text.format(
            user_id=user_data[1],
            user_link=user_data[2],
            user_balance=user_data[3],
        )
    return text

def update_user(message=None, call=None):
    if message is not None: 
        user_id = message.chat.id
        menu_id = message.message_id
    elif call is not None: 
        user_id = call.message.chat.id
        menu_id = call.message.message_id

    date, time = now_time()
    date = f"{date} {time}"

    if call:
        username = call.from_user.username
        SQL_request("UPDATE TTA SET username = ? WHERE telegram_id = ?", (username, user_id))
    
    SQL_request("UPDATE TTA SET menu_id = ?, use_time = ? WHERE telegram_id = ?", (menu_id, date, user_id))
    return user_id, menu_id

def registration(message, call):
    if message: user_id = message.chat.id
    if call: user_id = call.message.chat.id
    date, time  = now_time()
    user = SQL_request("SELECT * FROM TTA WHERE telegram_id = ?", (user_id,))
    if user is None:
        SQL_request("INSERT INTO TTA (telegram_id, time_registration) VALUES (?, ?)", (user_id, f"{date} {time}"))
        print(f"Зарегистрирован новый пользователь")