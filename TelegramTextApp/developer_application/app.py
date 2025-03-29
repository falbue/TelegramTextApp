from flask import Flask, render_template, jsonify, request
import json
import os
import logging

VERSION_APP = "0.0.2.2"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(BASE_DIR, 'templates')

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)

logging.getLogger('werkzeug').handlers = []
logging.getLogger('werkzeug').propagate = False

def start_app(menu, code, port=5000):
    MENU = menu
    CODE = code

    def create_menu(menu):
        with open(MENU, 'r', encoding='utf-8') as file:
            data = json.load(file)
    
        data['menus'][menu] = {"text":"Нужно настроить меню"}
    
        with open(MENU, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            
        return data['menus'][menu]
    
    @app.route('/')
    def index():
        return render_template(f'index.html')
    
    @app.route('/data')
    def data():
        with open(MENU, 'r', encoding='utf-8') as file:
            return jsonify(json.load(file))
    
    @app.route('/menu/<menu>', methods=['GET', 'POST'])
    def open_menu(menu):
        if request.method == 'GET':
            return render_template(f'menu.html')
    
        elif request.method == 'POST':
            with open(MENU, 'r', encoding='utf-8') as file:
                data = json.load(file)
            try:
                data_menu = data['menus'][menu]
            except:
                data_menu = create_menu(menu)
            data = {"menu":data_menu, "name":menu}
            formatted_data = json.dumps(data, ensure_ascii=False, indent=4)
            return jsonify(formatted_data)
    
    @app.route('/function/<function_name>', methods=['GET', 'POST'])
    def find_function(function_name):
        try:
            with open(CODE, 'r', encoding='utf-8') as file:
                lines = file.readlines()
    
            # Флаг для обнаружения начала функции
            in_function = False
            function_indent = None
            code_function = []  # Список для сбора строк функции
    
            for line in lines:
                # Убираем лишние пробелы в начале и конце строки
                stripped_line = line.lstrip()
    
                # Проверяем, начинается ли строка с определения функции
                if stripped_line.startswith(f"def {function_name}("):
                    in_function = True
                    function_indent = len(line) - len(stripped_line)  # Запоминаем отступ
                    code_function.append(line)  # Добавляем строку с определением функции
                    continue
    
                # Если мы внутри функции, проверяем отступы
                if in_function:
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= function_indent and stripped_line != '':
                        # Если отступ меньше или равен начальному, значит функция закончилась
                        break
                    code_function.append(line)  # Добавляем строку тела функции
    
            # Если функция найдена, объединяем строки в одну строку
            if code_function:
                code_function = ''.join(code_function[:-1])
                return jsonify(code_function)
            else:
                return jsonify(f"Функция '{function_name}' не найдена в файле.")
    
        except FileNotFoundError:
            return jsonify(f"Файл '{file_path}' не найден.")
        except Exception as e:
            return jsonify(f"Произошла ошибка: {e}")
    
    print(f"Версия приложения: {VERSION_APP}")
    app.run(debug=True, host='0.0.0.0', port=port)

if __name__=='__main__':
    start_app(f"{BASE_DIR}/../../test.json", f'{BASE_DIR}/../../bot.py')