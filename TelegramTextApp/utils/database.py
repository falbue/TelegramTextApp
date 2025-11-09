import aiosqlite
import json
import sqlite3
from typing import overload, Literal, Any

import os
from .utils import logger
from .. import config

logger = logger.setup("DATABASE")  # type: ignore

DB_PATH = config.DB_PATH
db_dir = os.path.dirname(DB_PATH)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)


@overload
async def SQL_request_async(
    query: str, params: tuple = ..., fetch: Literal["one"] = ...
) -> dict[str, Any] | None: ...
@overload
async def SQL_request_async(
    query: str, params: tuple = ..., fetch: Literal["all"] = ...
) -> list[dict[str, Any]]: ...
@overload
async def SQL_request_async(
    query: str, params: tuple = ..., fetch: str = ...
) -> None: ...


async def SQL_request_async(
    query, params=(), fetch="one"
) -> dict[str, str] | list[dict[str, str]] | None:
    def _parse_json_if_needed(value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith(("{", "[")):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    pass
        return value

    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        try:
            await cursor.execute(query, params)

            if fetch == "all":
                rows = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                result = [
                    {
                        col: _parse_json_if_needed(row[i])
                        for i, col in enumerate(columns)
                    }
                    for row in rows
                ]

            elif fetch == "one":
                row = await cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    result = {
                        col: _parse_json_if_needed(row[i])
                        for i, col in enumerate(columns)
                    }
                else:
                    result = None
            else:
                await conn.commit()
                result = None

        except Exception as e:
            print(f"Ошибка SQL: {e}")
            raise

    return result


def SQL_request(
    query, params=(), fetch="one"
) -> dict[str, Any] | list[dict[str, Any]] | None:
    def _parse_json_if_needed(value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith(("{", "[")):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    pass
        return value

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)

            if fetch == "all":
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                result = [
                    {
                        col: _parse_json_if_needed(row[i])
                        for i, col in enumerate(columns)
                    }
                    for row in rows
                ]

            elif fetch == "one":
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    result = {
                        col: _parse_json_if_needed(row[i])
                        for i, col in enumerate(columns)
                    }
                else:
                    result = None
            else:
                conn.commit()
                result = None

        except sqlite3.Error as e:
            print(f"Ошибка SQL: {e}")
            raise

    return result


async def create_tables():
    # Пользователи
    await SQL_request_async("""
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
    )""")
    logger.debug("База настроена")


async def extract_user_data(
    bot_data, update=True
):  # Извлекает данные пользователя из объекта бота/сообщения
    if hasattr(bot_data, "message"):
        message = bot_data.message
        message_id = message.message_id
    else:
        message = bot_data
        try:
            if update is True:
                message_id = message.message_id
                if message.text.startswith("/"):
                    logger.debug("Обновление сообщения пользователя")
                    message_id = message.message_id + 1
            else:
                user = await SQL_request_async(
                    "SELECT * FROM TTA WHERE telegram_id = ?", (message.chat.id,), "one"
                )
                message_id = user.get("message_id") if user else message.message_id
        except Exception as e:
            logger.error(f"Ошибка при обработке данных пользователя: {e}")
            message_id = message.message_id

    return {
        "telegram_id": message.chat.id,
        "first_name": message.chat.first_name,
        "last_name": message.chat.last_name,
        "username": message.chat.username,
        "message_id": message_id,
        "message_text": message.text,
    }


async def create_user(bot_data):
    """Создает нового пользователя в базе данных."""
    user_data = await extract_user_data(bot_data)
    try:
        await SQL_request_async(
            """
            INSERT INTO TTA (
                telegram_id,
                first_name,
                last_name,
                username,
                message_id
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_data["telegram_id"],
                user_data["first_name"],
                user_data["last_name"],
                user_data["username"],
                user_data["message_id"],
            ),
            "",
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка SQL при регистрации: {e}")
        return False


async def update_user_data(bot_data, update):
    """Обновляет данные пользователя в базе данных."""
    user_data = await extract_user_data(bot_data, update)
    try:
        await SQL_request_async(
            """
            UPDATE TTA
            SET
                first_name = ?,
                last_name = ?,
                username = ?,
                message_id = ?
            WHERE telegram_id = ?
            """,
            (
                user_data["first_name"],
                user_data["last_name"],
                user_data["username"],
                user_data["message_id"],
                user_data["telegram_id"],
            ),
            "",
        )
    except Exception as e:
        logger.error(f"Не удалось обновить данные пользователя: {e}")


async def get_user(bot_data, update=False) -> dict[str, Any] | None:
    """Возвращает пользователя, создает нового при отсутствии."""
    user_data = await extract_user_data(bot_data)
    telegram_id = user_data["telegram_id"]
    user = await SQL_request_async(
        "SELECT * FROM TTA WHERE telegram_id = ?", (telegram_id,), "one"
    )

    if user:
        await update_user_data(bot_data, update)
        return await SQL_request_async(
            "SELECT * FROM TTA WHERE telegram_id = ?", (telegram_id,), "one"
        )
    else:
        if await create_user(bot_data):
            logger.info(f"Зарегистрирован новый пользователь: {telegram_id}")
            return await SQL_request_async(
                "SELECT * FROM TTA WHERE telegram_id = ?", (telegram_id,)
            )
        else:
            logger.error(f"Не удалось зарегистрировать пользователя {telegram_id}")
            return None


async def get_role_id(role):
    ids = await SQL_request_async("SELECT * FROM TTA WHERE role = ?", (role,), "all")
    return ids
