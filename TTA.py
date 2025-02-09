import telebot
import threading

import config
from scripts import *
import menus


VERSION="0.0.1"
print(VERSION)
bot = telebot.TeleBot(config.API)

commands = [  # КОМАНДЫ
telebot.types.BotCommand("start", "Перезапуск бота"),
]
bot.set_my_commands(commands)


def step_handler(message, menu_id, call, get_data, function_name, menu_name):
    bot.delete_message(message.chat.id, message.message_id)
    menu_function = globals().get(function_name)
    get_data = menu_function(message, get_data)
    menu_data = menus.open_menu(menu_name, get_data=get_data, status=get_data)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=menu_id, text=menu_data["text"], reply_markup=menu_data["keyboard"], parse_mode="MarkdownV2")
    if menu_data.get("handler"):
        bot.register_next_step_handler(call.message, step_handler, menu_id, call, menu_data["get_data"], menu_data["handler"]["function"], menu_data["handler"]["open_menu"])

def send_menu(menu_data):
    user_id = []
    send_menu_data = menus.open_menu(menu_data["send_menu"], user_id=menu_data.get("user_id"), get_data=menu_data.get("get_data"))
    if menu_data["send_to"] == "admin":
        admin_id = SQL_request("SELECT telegram_id FROM users WHERE role = 'admin'", all_data=True)
        for i in admin_id:
            user_id.append(i[0])
    else:
        user_id.append(menu_data["send_to"])
    for user in user_id:
        bot.send_message(user, send_menu_data["text"], reply_markup=send_menu_data["keyboard"], parse_mode="MarkdownV2")


@bot.message_handler(content_types=['document'])
def handle_document(message):
    pass


@bot.message_handler()
def text_handler(message):
    user_id = message.chat.id
    user = SQL_request("SELECT * FROM users WHERE telegram_id = ?", (int(user_id),))
    if user is None: user = [0,0,0,0,0,0]
    if message.text == "/start":
        registration(message)
        menu_name = "main"
    elif (message.text).replace(message.text, "🕒 Создание чека на ") in message.text:
        status, order_id = create_order(message)
        if status == True:
            menu_name = "upadate_balance"
        else:
            menu_name = "error_upadate_balance"
    try:
        menu_data = menus.open_menu(menu_name, message=message) 
        bot.send_message(message.chat.id, menu_data["text"], reply_markup=menu_data["keyboard"], parse_mode="MarkdownV2")
        if menu_data.get("send_menu"):
            send_menu(menu_data)

    except Exception as e: 
        print(f"Ошибка в сообщениях {e}")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):  # работа с вызовами inline кнопок
    user_id, menu_id = update_user(call)
    bot.clear_step_handler_by_chat_id(chat_id=user_id)
        
    if call.data == "none":
        return
    elif call.data == "notification":
        bot.delete_message(user_id, menu_id)
        return
    else:
        menu = (call.data).split(":")[0]
        page = 0
        get_data = None
        forwarded_message = None

        if (call.data).split(":")[0] == "return":            
            menu = (call.data).split(":")[1] 
        if len((call.data).split(":"))>1:
            get_data = (call.data).split(":")[1]
        if len(menu.split("-"))>1:
            page = int(menu.split("-")[1])
            menu = menu.split("-")[0]
        if menu == 'order_info':
            data = order_data(int((call.data).split(":")[1]))
            forwarded_message = bot.forward_message(user_id, data["user"], data["message_id"])
            bot.delete_message(user_id, forwarded_message.message_id)
        menu_data = menus.open_menu(menu, call=call, page=page, get_data=get_data, order=forwarded_message)

        if menu_data.get("handler"):
            bot.register_next_step_handler(call.message, step_handler, menu_id, call, get_data, menu_data["handler"]["function"], menu_data["handler"]["open_menu"])

    if menu_data.get("notification"):
        bot.answer_callback_query(call.id, show_alert=menu_data["notification_show"], text=menu_data["notification"])
    if menu_data.get("send_menu"):
        send_menu(menu_data)
    bot.edit_message_text(chat_id=user_id, message_id=menu_id, text=menu_data["text"], reply_markup=menu_data["keyboard"], parse_mode="MarkdownV2")


print(f"бот запущен...")
def start_polling():
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Перезапуск...")


if __name__ == "__main__":
    start_polling()
    # bot.polling()
