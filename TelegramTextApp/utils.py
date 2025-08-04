import re
import os
import json
import random
import inspect
import importlib.util
import sys

from .logger import setup_logger
from .database import *

def markdown(text, full=False):  # экранирование
    if full == True: special_characters = r'*|~[]()>|_'
    special_characters = r'#+-={}.!'
    escaped_text = ''
    for char in text:
        if char in special_characters:
            escaped_text += f'\\{char}'
        else:
            escaped_text += char
    return escaped_text

def utils_config(debug):
    global logger
    logger = setup_logger(debug)


def default_values():
    data = {"number": random.randint(1, 100)}
    return data


def formatting_text(text, format_data=None): # форматирование текста
    values = {**default_values(), **(format_data or {})}
    
    start = text.find('{')
    while start != -1:
        end = text.find('}', start + 1)
        if end == -1:
            break
        
        key = text[start+1:end]

        if key in values:
            replacement = str(values[key])
            text = text[:start] + replacement + text[end+1:]
            start = start + len(replacement)
        else:
            if key == "notification_text":
                not_found_wrapper = ""
            else:
                not_found_wrapper = f"`{{{key}}}`"
            text = text[:start] + not_found_wrapper + text[end+1:]
            start = start + len(not_found_wrapper)
        
        start = text.find('{', start)

    return text


def is_template_match(template: str, input_string: str) -> bool:
    """Проверяет, соответствует ли текст шаблону (без учета динамических частей)."""
    # Экранируем все спецсимволы, кроме {.*?} (они заменяются на .*?)
    pattern = re.escape(template)
    pattern = re.sub(r'\\\{.*?\\\}', '.*?', pattern)  # Заменяем \{...\} на .*?
    return bool(re.fullmatch(pattern, input_string))

def parse_bot_data(template: str, input_string: str) -> dict | None:
    """Извлекает данные из строки по шаблону и возвращает словарь."""
    if not is_template_match(template, input_string):
        return None  # Если шаблон не подходит, возвращаем None
    
    # Извлекаем имена полей из шаблона
    fields = re.findall(r'\{(.*?)\}', template)
    
    # Заменяем {field} на (?P<field>.*?) для именованных групп
    pattern = re.sub(r'\{.*?\}', '(.*?)', template)
    pattern = re.escape(pattern)
    for field in fields:
        pattern = pattern.replace(re.escape('(.*?)'), f'(?P<{field}>.*?)', 1)
    pattern = '^' + pattern + '$'
    
    match = re.match(pattern, input_string)
    return match.groupdict() if match else None


def get_caller_file_path():
    current_frame = inspect.currentframe()
    try:
        caller_frame = current_frame.f_back
        if caller_frame is None:
            return None
        
        grand_caller_frame = caller_frame.f_back
        if grand_caller_frame is None:
            return None
        caller_file = inspect.getframeinfo(grand_caller_frame).filename
        abs_path = os.path.abspath(caller_file)
        return abs_path
    finally:
        del current_frame

def load_custom_functions(file_path):
    try:
        module_name = file_path.split('\\')[-1].replace('.py', '')
        
        # Загружаем модуль динамически
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        custom_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = custom_module
        spec.loader.exec_module(custom_module)
        
        logger.debug(f"Успешно загружен модуль: {file_path}")
        return custom_module
    except Exception as e:
        logger.error(f"Ошибка загрузки модуля {file_path}: {e}")
        return None

async def process_custom_function(key, format_data, menu_data, custom_module):
    if menu_data.get(key):
        keyboard = None
        func_name = menu_data[key]
        if "function" in menu_data["keyboard"]:
            func_name = menu_data["keyboard"]['function']
            keyboard = menu_data['keyboard']
        if not isinstance(func_name, str):
            return format_data, menu_data
        logger.debug(f"Выполнение функции: {func_name}")
        custom_func = getattr(custom_module, func_name, None)
        
        if custom_func and callable(custom_func):
            try:
                result = await asyncio.to_thread(custom_func, format_data)
                
                if key in ("function", "bot_input") and isinstance(result, dict):
                    format_data = {**format_data, **(result or {})}
                elif key == "keyboard" and isinstance(result, dict):
                    if keyboard:
                        menu_data["keyboard"] = replace_element(keyboard, result)
                    else:
                        menu_data["keyboard"] = result
                    
            except Exception as e:
                logger.error(f"Ошибка при вызове функции {func_name}: {e}")
    return format_data, menu_data

def replace_dict_element(data, new_values):
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            if key == "function":
                if isinstance(new_values, dict):
                    for k, v in new_values.items():
                        new_data[k] = v
                else:
                    new_data[key] = new_values
            else:
                new_data[key] = replace_element(value, new_values)
        return new_data
    return data