import json
from datetime import datetime
import pytz
import sqlite3
import os
import re
import inspect
from TTA_use_db import *

def get_settings():
    path = "local.json"
    with open(path, 'r', encoding='utf-8') as file:
        locale = json.load(file)
    return locale["settings"]

config = get_settings()
DB_NAME = f'{config["database"]}.db'
DB_PATH = config["database_path"]
if DB_PATH == "": DB_PATH = DB_NAME
SAVE_FOLDER = config["save_folder"]
use_db_settings(DB_PATH)
if not os.path.exists(DB_PATH):
    create_TTA()


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

def update_user(call):
    user_id = call.message.chat.id
    username = call.from_user.username
    menu_id = call.message.message_id
    user = SQL_request("SELECT * FROM TTA WHERE telegram_id = ?", (int(user_id),))
    SQL_request("UPDATE TTA SET username = ? WHERE telegram_id = ?", (username, user_id))
    print(f"{user_id}: {call.data}")
    return user_id, menu_id

def registration(message, call):
    if message: user_id = message.chat.id
    if call: user_id = call.message.chat.id
    date, time  = now_time()
    user = SQL_request("SELECT * FROM TTA WHERE telegram_id = ?", (user_id,))
    if user is None:
        SQL_request("INSERT INTO TTA (telegram_id, time_registration) VALUES (?, ?)", (user_id, f"{date} {time}"))
        print(f"Зарегистрирован новый пользователь")