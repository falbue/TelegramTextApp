import aiosqlite
import json
import sqlite3
import asyncio
from logging_config import logger

DB_PATH = "database.db"

async def SQL_request(query, params=(), fetch=None, jsonify_result=False):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.cursor() as cursor:
            try:
                await cursor.execute(query, params)
                
                if fetch == 'all':
                    rows = await cursor.fetchall()
                    if rows:
                        columns = [desc[0] for desc in cursor.description]
                        result = []
                        for row in rows:
                            processed_row = {}
                            for i, col in enumerate(columns):
                                if isinstance(row[i], str) and row[i].startswith('{'):
                                    try:
                                        processed_row[col] = json.loads(row[i])
                                    except json.JSONDecodeError:
                                        processed_row[col] = row[i]
                                else:
                                    processed_row[col] = row[i]
                            result.append(processed_row)
                    else:
                        result = []
                
                elif fetch == 'one':
                    row = await cursor.fetchone()
                    if row:
                        columns = [desc[0] for desc in cursor.description]
                        result = {}
                        for i, col in enumerate(columns):
                            if isinstance(row[i], str) and row[i].startswith('{'):
                                try:
                                    result[col] = json.loads(row[i])
                                except json.JSONDecodeError:
                                    result[col] = row[i]
                            else:
                                result[col] = row[i]
                    else:
                        result = None
                
                else:  # Для запросов без выборки (INSERT/UPDATE/DELETE)
                    await db.commit()
                    result = None
                    
            except sqlite3.Error as e:
                await db.rollback()
                logger.error(f"Ошибка SQL: {e}")
                raise

    # Преобразование в JSON при необходимости
    if jsonify_result and result is not None:
        return json.dumps(result, ensure_ascii=False, indent=2)
    return result


async def create_tables():
    # Пользователи
    await SQL_request('''
    CREATE TABLE IF NOT EXISTS TTA (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL,
        first_name TEXT,
        last_name TEXT,
        username TEXT,
        message_id INTEGER,
        message_type TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_approved BOOLEAN DEFAULT 1,
        role TEXT DEFAULT 'user'
    )''')

asyncio.run(create_tables())


async def create_user(bot_data):
    try: bot_data = bot_data.message
    except: pass

    try:
        telegram_id = bot_data.chat.id
        first_name = bot_data.chat.first_name
        last_name = bot_data.chat.last_name
        username = bot_data.chat.username
        message_id = bot_data.message_id
    
        await SQL_request('''
        INSERT INTO TTA (
            telegram_id, 
            first_name, 
            last_name, 
            username, 
            message_id
        ) VALUES (?, ?, ?, ?, ?)
        ''', (telegram_id, first_name, last_name, username, message_id))

        return True
    except Exception as e:
        logger.error(f"Ошибка SQL при регистрации: {e}")
        return False

async def get_user(telegram_id):
    user = await SQL_request('SELECT * FROM TTA WHERE telegram_id=?', (telegram_id,), "one")
    return user
