import telebot
import threading
from TelegramTextApp import TTA_menus
from TelegramTextApp import TTA_scripts
import inspect
from telebot import apihelper
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s [%(asctime)s]   %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

VERSION="0.5.3.3"

def start(api, menus, debug=False, tta_experience=False, formating_text=None, app=None, port=5000):
    TTA_scripts.create_file_menus(f"{menus}.json")

    # путь файла, откуда был запущен TTA
    current_frame = inspect.currentframe()
    caller_frame = current_frame.f_back
    caller_filename = caller_frame.f_code.co_filename # полный путь

    locale = TTA_menus.settings_menu(f"{menus}.json", caller_filename, formating_text, tta_experience) # получение всего json файла

    # добавление функций в глобальный список функций из файла запуска 
    import sys
    from importlib.util import spec_from_file_location, module_from_spec
    sys.path.append("scripts.py")
    module = module_from_spec(spec_from_file_location("scripts", caller_filename))
    module.__spec__.loader.exec_module(module)
    globals().update(vars(module))

    if app == True: # запуск приложения
        from TelegramTextApp.developer_application import app
        app.start_app(f"{menus}.json", caller_filename, port=port)

    # установка команд бота
    TTA_scripts.get_config()
    bot = telebot.TeleBot(api)
    commands = []
    for command in locale["commands"]:
        commands.append(telebot.types.BotCommand(command, locale["commands"][command]["text"]))
    bot.set_my_commands(commands)

    # установка описаний бота
    if locale.get('bot'):
        try:
            bot.set_my_name(locale['bot'].get('name'))
            bot.set_my_description(locale['bot'].get('description'))
            bot.set_my_short_description(locale['bot'].get('short_description'))
        except:
            logging.error("Не удалось обновить данные бота")
            pass

# ----------------------------------------------------------

    def step_handler(message, menu_data, menu_id): # ожидание ввода от пользователя (пока только сообщения)
        handler_menu = {}
        call = menu_data['call']
        user_id = call.message.chat.id
        menu_data["input_text"] = message.text
        if tta_experience == True:
            bot.delete_message(user_id, message.message_id)
        if menu_data["handler"].get("function"):
            function = globals()[menu_data["handler"]["function"]]
            menu_data['menu'] = menu_data["handler"]["menu"].split(":")[0]
            if len(menu_data["handler"]["menu"].split(":")) > 1:
                menu_data['data'] = menu_data["handler"]["menu"].split(":")[1]
            else: menu_data['data'] = None
            menu_data["handler_data"] = message
            function_data = function(menu_data)
            if function_data == False and menu_data.get("error_text") is not None:
                bot.edit_message_text(chat_id=user_id, message_id=menu_id, text=menu_data["error_text"], reply_markup=menu_data["keyboard"], parse_mode="MarkdownV2")
                bot.register_next_step_handler(call.message, step_handler, menu_data, menu_id)
                return
            elif function_data:
                menu_data['data'] = function_data

        menu_data = TTA_menus.open_menu(call=call, menu_data=menu_data)
        if menu_data.get("loading"):
            bot.edit_message_text(chat_id=user_id, message_id=menu_id, text=menu_data["text"], parse_mode="MarkdownV2")
            menu_data = TTA_menus.open_menu(call=call, loading=True)
        if menu_data.get("handler"):
            bot.register_next_step_handler(call.message, step_handler, menu_data, menu_id)
        if menu_data.get("send"):
            send_menu(menu_data, message.text)
        
        try:
            bot.edit_message_text(chat_id=user_id, message_id=menu_id, text=menu_data["text"], reply_markup=menu_data["keyboard"], parse_mode="MarkdownV2")
        except Exception as e:
            pass

        if debug == True:
            pass

    def send_menu(menu_data, input_text=None):
        type_send = menu_data["send"]
        recipient = type_send["recipient"]
        menu_data["input_text"] = input_text
        menu = type_send.get("menu")
        menu_data = TTA_menus.open_menu(call=menu_data['call'], menu_data=menu_data)
        if menu:
            send_text = menu_data["text"]
        else:
            send_text = type_send["text"]
        if recipient == 'all':
            role_users = TTA_scripts.SQL_request("SELECT telegram_id FROM TTA WHERE role IS NOT NULL",(), True)
        else:
            role_users = TTA_scripts.SQL_request("SELECT telegram_id FROM TTA WHERE role=?",(recipient,), True)

        for user_id in role_users:
            bot.send_message(user_id[0], send_text, reply_markup=menu_data["keyboard"], parse_mode="MarkdownV2")

# -----

    def processing_data(data):
        bot_data = TTA_menus.open_menu(data=data)

        if hasattr(data, 'data') and data.data is not None:
            user_id, menu_id = TTA_scripts.update_user(call=data)
            if bot_data.get("loading"):
                try:
                    bot.edit_message_text(chat_id=user_id, message_id=menu_id, text=bot_data["text"], parse_mode="MarkdownV2")
                except apihelper.ApiTelegramException as e: # проверка на двойное нажатие
                    if "message is not modified" in str(e): pass
                bot_data = TTA_menus.open_menu(data, loading=True)
            if bot_data.get("handler"):
                bot.register_next_step_handler(data.message, step_handler, bot_data, menu_id)
            if bot_data.get("send"):
                send_menu(bot_data)
            if bot_data.get("query"):
                bot.answer_callback_query(callback_query_id=data.id,text=bot_data['query']['text'], show_alert=bot_data['query']['show_alert'])
    
            try:
                bot.edit_message_text(chat_id=user_id, message_id=menu_id, text=bot_data["text"], reply_markup=bot_data["keyboard"], parse_mode="MarkdownV2")
            except apihelper.ApiTelegramException as e: # проверка на двойное нажатие
                if "message is not modified" in str(e): pass

        elif hasattr(data, 'text') and data.text is not None:
            user_id = data.chat.id
            if bot_data.get("loading"):
                new_message = bot.send_message(data.chat.id, bot_data["text"], parse_mode="MarkdownV2")
                TTA_scripts.update_user(message=new_message) # обновление данных пользователя
                bot_data = TTA_menus.open_menu(data, loading=True)
                bot.edit_message_text(chat_id=user_id, message_id=new_message.message_id, text=bot_data["text"], reply_markup=bot_data["keyboard"], parse_mode="MarkdownV2")
            else:
                new_message = bot.send_message(data.chat.id, bot_data["text"], reply_markup=bot_data["keyboard"], parse_mode="MarkdownV2")
                TTA_scripts.update_user(message=new_message)

            if bot_data.get("handler"):
                bot.register_next_step_handler(call.message, step_handler, bot_data, menu_id)

            if bot_data.get("send"):
                send_menu(bot_data)


    @bot.message_handler()
    def text_handler(message): # обработка полученного текста
        user_id = message.chat.id
        old_menu = None

        if message.text[0] == "/": # проверка на команду
            old_menu = TTA_scripts.SQL_request("SELECT menu_id FROM TTA WHERE telegram_id = ?", (user_id,))
            if debug == True:
                logging.info(f"{user_id}: {message.text}")

            processing_data(message)

        if tta_experience == True:
            if old_menu:
                try:
                    bot.delete_message(user_id, int(old_menu[0]))
                except: pass
            bot.delete_message(user_id, message.message_id)
    
    
    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):  # работа с вызовами inline кнопок
        user_id, menu_id = TTA_scripts.update_user(call=call)
        bot.clear_step_handler_by_chat_id(chat_id=user_id)
        if debug == True:
            logging.info(f"{user_id}: {call.data}")
            
        if call.data == "none": return
    
        elif (call.data).split("-")[0] == "notification":
            bot.delete_message(user_id, menu_id)
            return
    
        processing_data(call)
    
    
    def start_polling():
        logging.info(f"бот запущен...")
        while True:
            try:
                bot.polling(none_stop=True, timeout=60)
            except Exception as e:
                logging.error(e)
                logging.info(f"Перезапуск...")
    if debug == False: start_polling()
    else:
        logging.info(f"Режим разработчика")
        logging.info(f"Версия TTA: {VERSION}")
        logging.info(f"бот запущен...")
        bot.polling()