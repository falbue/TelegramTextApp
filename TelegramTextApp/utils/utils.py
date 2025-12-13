import asyncio
import importlib.util
import json
import os
import re
import sys
from typing import TypeAlias
import types
import copy

from .. import config
from .logger import setup as setup_logger

logger = setup_logger("UTILS")

Json: TypeAlias = dict[str, str] | dict[str, dict[str, str]]


def markdown(text: str, full: bool = False) -> str:
    """Экранирует специальные символы Markdown в тексте.
    Если указан full=True, экранирует все специальные символы Markdown.
    Иначе экранирует только основные символы Markdown (#+-={}.!).
    Не дублирует обратный слэш, если символ уже экранирован (т.е. уже предварён \).
    """
    if full is True:
        special_characters = r"*|~[]()>|_#+-={}.!"
    else:
        special_characters = r"#+-={}.!"

    escaped_text = ""
    i = 0
    while i < len(text):
        char = text[i]
        if char == "\\" and i + 1 < len(text):
            next_char = text[i + 1]
            if next_char in special_characters:
                escaped_text += "\\" + next_char
                i += 2
                continue
            else:
                escaped_text += char
                i += 1
                continue

        if char in special_characters:
            escaped_text += "\\" + char
        else:
            escaped_text += char
        i += 1

    return escaped_text


async def load_json(
    level: str | None = None,
) -> dict[str, Json]:
    # загрузка json файла с указанием уровня
    filename = config.JSON
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        if level is not None:
            data = data[level]
        return data


async def updated_json(data: dict, level: str) -> None:
    filename = config.JSON
    json_data = await load_json()

    if level is not None:
        if level not in json_data or not isinstance(json_data[level], dict):
            json_data[level] = {}
        json_data[level].update(data)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)


class TelegramTextApp(types.SimpleNamespace):
    pass


async def dict_to_namespace(d):
    for key, value in d.items():
        if isinstance(value, dict):
            d[key] = await dict_to_namespace(value)
    return TelegramTextApp(**d)


async def print_json(data):  # удобный вывод json
    try:
        if isinstance(data, (dict, list)):
            text = json.dumps(data, indent=4, ensure_ascii=False)
        else:
            print(type(data))
            text = str(data)
        print(text)
    except Exception as e:
        logger.error(f"Ошибка при выводе json: {e}")


async def flatten_dict(d, parent_key="", sep=".") -> dict:
    # Функция для "сплющивания" вложенных словарей.
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            if k == "params":
                flattened = await flatten_dict(v, "", sep=sep)
                items.extend(flattened.items())
            else:
                flattened = await flatten_dict(v, f"{new_key}", sep=sep)
                items.extend(flattened.items())
        else:
            items.append((new_key, v))
    return dict(items)


async def replace_keys(data):
    replacements = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (str, int, float, bool)):
                replacements[k] = v

    def replace_recursive(obj):
        if isinstance(obj, dict):
            new_dict = {}
            for k, v in obj.items():
                resolved_key = replace_recursive(k)
                resolved_value = replace_recursive(v)
                new_dict[resolved_key] = resolved_value
            return new_dict
        elif isinstance(obj, list):
            return [replace_recursive(item) for item in obj]
        elif isinstance(obj, str):
            match = re.match(r"^\{(.+)\}$", obj)
            if match:
                key = match.group(1)
                if key in replacements:
                    return replacements[key]
            return obj
        else:
            return obj

    return replace_recursive(data)


async def formatting_text(text, format_data):  # форматирование текста
    data = copy.deepcopy(format_data)
    data["env"] = config.ENV
    values = await flatten_dict(data)
    values = await replace_keys(values)

    start = text.find("{")
    while start != -1:
        end = text.find("}", start + 1)
        if end == -1:
            break

        key = text[start + 1 : end]
        key = key.replace(" ", "")
        key_type = ""
        if len(key.split("|")) > 1:
            key_parts = key.split("|")
            key = key_parts[0]
            key_type = key_parts[1]

        if key in values:
            replacement = str(values[key])
            text = text[:start] + replacement + text[end + 1 :]
            start = start + len(replacement)
        else:
            if key_type == "hide":
                not_found_wrapper = ""
            else:
                not_found_wrapper = f"{{{key}}}"
            text = text[:start] + not_found_wrapper + text[end + 1 :]
            start = start + len(not_found_wrapper)

        start = text.find("{", start)

    def replace_deep_link(match):
        payload = match.group(1)
        payload = markdown(payload, full=True)
        bot_username = markdown(format_data["bot"]["username"], full=True)
        text = f"(https://t.me/{bot_username}?start={payload})"
        print(text)
        return text

    updated_text = re.sub(r"\(deep_link\|([^)]+)\)", replace_deep_link, text)

    return updated_text


async def is_template_match(template: str, input_string: str) -> bool:
    pattern = re.sub(r"\{[^{}]*\}", ".*?", template)
    full_pattern = f"^{pattern}$"
    return bool(re.match(full_pattern, input_string))


async def get_params(template: str, input_string: str) -> dict[str, str] | None:
    field_names = re.findall(r"\{(\w+)\}", template)

    if not field_names:
        return {}

    template_parts = template.split("|")
    input_parts = input_string.split("|")

    result = {}
    input_idx = 0

    for template_part in template_parts:
        if template_part.startswith("{") and template_part.endswith("}"):
            param_name = template_part[1:-1]
            if input_idx < len(input_parts):
                result[param_name] = input_parts[input_idx]
                input_idx += 1
            else:
                result[param_name] = None
        else:
            if input_idx < len(input_parts) and input_parts[input_idx] == template_part:
                input_idx += 1
            else:
                return None

    if input_idx < len(input_parts):
        return None

    return result


async def get_caller_file_path():
    caller_file = sys.argv[0]
    full_path = os.path.abspath(caller_file)
    return full_path


async def load_custom_functions(file_path):
    try:
        module_name = file_path.split("\\")[-1].replace(".py", "")

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            logger.error(f"Не удалось создать spec или loader для модуля: {file_path}")
            return None

        custom_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = custom_module
        spec.loader.exec_module(custom_module)
        return custom_module
    except Exception as e:
        logger.error(f"Ошибка загрузки модуля {file_path}: {e}")
        return None


async def function(func_name: str, format_data: dict):
    custom_module = await load_custom_functions(await get_caller_file_path())
    logger.debug(f"Выполнение функции: {func_name}")
    custom_func = getattr(custom_module, func_name, None)
    if custom_func and callable(custom_func):
        try:
            tta = copy.deepcopy(format_data)
            tta.update(format_data["params"])
            del tta["params"]
            tta = await dict_to_namespace(tta)
            result = {}
            result = await asyncio.to_thread(custom_func, tta)
            if not isinstance(result, dict):
                logger.warning(
                    f"Функция {func_name} должна возвращать словарь,получено: {type(result)}"
                )
                return None
            return result
        except Exception as e:
            logger.error(f"Ошибка при вызове функции {func_name}: {e}")
    return None
