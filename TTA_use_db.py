import sqlite3
import os

def use_db_settings(path):
    global DB_PATH
    DB_PATH = path

def SQL_request(request, params=(), all_data=None):  # Выполнение SQL-запросов
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()
    if request.strip().lower().startswith('select'):
        cursor.execute(request, params)
        if all_data == None: result = cursor.fetchone()
        else: result = cursor.fetchall()
        connect.close()
        return result
    else:
        cursor.execute(request, params)
        connect.commit()
        connect.close()



def create_TTA():
    SQL_request("""CREATE TABLE IF NOT EXISTS TTA (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id TEXT,
        menu_id TEXT,
        username TEXT,
        use_time TEXT,
        time_registration TEXT,
        role TEXT DEFAULT "user"
    )""")