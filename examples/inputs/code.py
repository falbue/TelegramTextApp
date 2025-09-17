import TelegramTextApp
import json

if __name__ == "__main__":
    TelegramTextApp.start()

def test(tta_data):
    if not tta_data.get("user_text"):
        return {"user_text":""}

def processing_input(tta_data):
    print(f'Сохранение введённых данных: {tta_data["user_text"]}')
    return {"notification_text":"Данные успешно сохранены"}