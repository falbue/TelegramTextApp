import telebot
import threading

from TTA_scripts import *
import TTA_menus

VERSION="0.0.1"


def start(): # создание бота
    global bot
    config = get_settings()
    bot = telebot.TeleBot(config["api"])
    return config

config = start()


@bot.message_handler()
def text_handler(message): # обработка полученного текста
    user_id = message.chat.id
    if message.text[0] == "/":
        menu_name = (message.text).replace("/", "")
        if menu_name == 'start':
            menu_name = "main"

    menu_data = TTA_menus.open_menu(message=message) 
    bot.send_message(message.chat.id, menu_data["text"], reply_markup=menu_data["keyboard"], parse_mode="MarkdownV2")
    if menu_data.get("send_menu"):
        send_menu(menu_data)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):  # работа с вызовами inline кнопок
    user_id, menu_id = update_user(call)
    bot.clear_step_handler_by_chat_id(chat_id=user_id)
        
    if call.data == "none": return

    elif call.data == "notification":
        bot.delete_message(user_id, menu_id)
        return

    else:
        menu_data = TTA_menus.open_menu(call=call)
        if menu_data.get("handler"):
            bot.register_next_step_handler(call.message, step_handler, menu_id, call, get_data, menu_data["handler"]["function"], menu_data["handler"]["open_menu"])

    bot.edit_message_text(chat_id=user_id, message_id=menu_id, text=menu_data["text"], reply_markup=menu_data["keyboard"], parse_mode="MarkdownV2")


def start_polling():
    print(f"бот запущен...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(e)
            print(f"Перезапуск...")

if config['debug'] == True: start_polling()
else:
    print(f"Режим разработчика\nВерсия TTA: {VERSION}") 
    bot.polling()