import aiosqlite
import json
import sqlite3
import asyncio
from .logging_config import setup_logging


def config_db(path="database.db", debug=False):
    global DB_PATH, logger
    logger = setup_logging(debug)
    DB_PATH = path

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

async def extract_user_data(bot_data, update=True):  # Извлекает данные пользователя из объекта бота/сообщения
    if hasattr(bot_data, 'message'):
        message = bot_data.message
        message_id = message.message_id
    else:
        message = bot_data
        try:
            if update and message.text == "/start":
                message_id = message.message_id+1
            else:
                user = await SQL_request('SELECT * FROM TTA WHERE telegram_id = ?', (message.chat.id,), "one")
                message_id = user["message_id"]
        except:
            message_id = message.message_id
    
    return {
        'telegram_id': message.chat.id,
        'first_name': message.chat.first_name,
        'last_name': message.chat.last_name,
        'username': message.chat.username,
        'message_id': message_id,
        'message_text': message.text
    }

async def create_user(bot_data):
    """Создает нового пользователя в базе данных."""
    user_data = await extract_user_data(bot_data)
    try:
        await SQL_request(
            '''
            INSERT INTO TTA (
                telegram_id, 
                first_name, 
                last_name, 
                username, 
                message_id
            ) VALUES (?, ?, ?, ?, ?)
            ''',
            (
        user_data['telegram_id'],
        user_data['first_name'],
        user_data['last_name'],
        user_data['username'],
        user_data['message_id']
            )
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка SQL при регистрации: {e}")
        return False

async def update_user_data(bot_data, update=True):
    """Обновляет данные пользователя в базе данных."""
    user_data = await extract_user_data(bot_data, update)
    try:
        await SQL_request(
            '''
            UPDATE TTA 
            SET 
                first_name = ?, 
                last_name = ?, 
                username = ?, 
                message_id = ? 
            WHERE telegram_id = ?
            ''',
            (
                user_data['first_name'],
                user_data['last_name'],
                user_data['username'],
                user_data['message_id'],
                user_data['telegram_id'],
            )
        )
    except Exception as e:
        logger.error(f"Не удалось обновить данные пользователя: {e}")

async def get_user(bot_data, update=True):
    """Возвращает пользователя, создает нового при отсутствии."""
    user_data = await extract_user_data(bot_data)
    telegram_id = user_data['telegram_id']
    user = await SQL_request('SELECT * FROM TTA WHERE telegram_id = ?', (telegram_id,), "one")
    
    if user:
        await update_user_data(bot_data, update)
        return await SQL_request('SELECT * FROM TTA WHERE telegram_id = ?', (telegram_id,), "one")
    else:
        if await create_user(bot_data):
            logger.info(f"Зарегистрирован новый пользователь: {telegram_id}")
            return await SQL_request(
                'SELECT * FROM TTA WHERE telegram_id = ?', 
                (telegram_id,), 
                "one"
            )
        else:
            logger.error(f"Не удалось зарегистрировать пользователя {telegram_id}")
            return None
