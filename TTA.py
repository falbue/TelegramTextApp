import telebot
import threading
import TTA_menus
import TTA_scripts
import inspect

VERSION="0.1.1"

def start(api, menus, debug=False):
    current_frame = inspect.currentframe()
    caller_frame = current_frame.f_back
    caller_filename = caller_frame.f_code.co_filename
    config = TTA_scripts.get_config(menus)
    TTA_menus.get_locale(config, caller_filename)
    bot = telebot.TeleBot(api)
    commands = []
    for command in config["commands"]:
        commands.append(telebot.types.BotCommand(command, config["commands"][command]["text"]))
    bot.set_my_commands(commands)
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
        user_id, menu_id = TTA_scripts.update_user(call)
        bot.clear_step_handler_by_chat_id(chat_id=user_id)
            
        if call.data == "none": return
    
        elif call.data == "notification":
            bot.delete_message(user_id, menu_id)
            return
    
        else:
            menu_data = TTA_menus.open_menu(call=call)
            if menu_data.get("loading"):
                bot.edit_message_text(chat_id=user_id, message_id=menu_id, text=menu_data["text"], parse_mode="MarkdownV2")
                menu_data = TTA_menus.open_menu(call=call, loading=True)
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
    if debug == False: start_polling()
    else:
        print(f"Режим разработчика\nВерсия TTA: {VERSION}") 
        bot.polling()