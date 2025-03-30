import config
import re

def input_text(tta_data, input_text):
    print("Работает")

def input_number(tta_data, input_text):
    try:
        int(input_text)
        return "Работает"
    except:
        return False    

def newsletter(tta_data, input_text=None):
    print(f"Выполнение функции: {5+3}")
    return tta_data

def formating_text(tta_data, text, type_text=None):
    format_dict = {}
    call_data = tta_data["call_data"]
    try:
        format_dict = {
        "input_text":call_data["input_text"],
        "data":call_data['data']
        }
        formatted_text = text.format_map(
            {key: format_dict.get(key, None) for key in re.findall(r'\{(.*?)\}', text)}
        )
    except Exception as e:
        formatted_text = text.format_map(
            {key: format_dict.get(key, None) for key in re.findall(r'\{(.*?)\}', text)}
        )

    return formatted_text

if __name__ == "__main__":
    from TelegramTextApp import TTA
    TTA.start(config.API, "test", debug=True, formating_text="formating_text", tta_experience=True, app=False)