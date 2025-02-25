import config
import re

def input_text(message, menu_id, call, menu):
    print("Работает")

def formating_text(tta_data, text):
    format_dict = {"username": "G"}
    try:
        formatted_text = text.format_map(
            {key: format_dict.get(key, None) for key in re.findall(r'\{(.*?)\}', text)}
        )
    except KeyError as e:
        formatted_text = text.format_map(
            {key: format_dict.get(key, None) for key in re.findall(r'\{(.*?)\}', text)}
        )

    return formatted_text

if __name__ == "__main__":
    from TelegramTextApp import TTA
    TTA.start(config.API, "test.json", debug=True, formating_text="formating_text", tta_experience=True)