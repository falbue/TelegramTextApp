import config
import re

def input_text(message, menu_id, call, menu):
    print("Работает")

def newsletter(message, menu_id, call, menu):
    pass

def formating_text(tta_data, text):        
    format_dict = {}
    try:
        input_text = tta_data["data"].split(":")[1]
        format_dict = {"input_text":input_text}
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
    TTA.start(config.API, "test", debug=True, formating_text="formating_text", tta_experience=True)