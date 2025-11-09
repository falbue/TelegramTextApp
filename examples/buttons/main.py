import TelegramTextApp

if __name__ == "__main__":
    TelegramTextApp.start()


def custom_buttons(tta_data):
    buttons_num = 10
    buttons = {}
    for i in range(buttons_num):
        buttons[f"menu|{i}"] = f"Кнопка {i}"
    return buttons
