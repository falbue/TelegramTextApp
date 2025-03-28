from flask import Flask, render_template, jsonify, request
import json

app = Flask(__name__)
MENU = 'data.json'

def create_menu(menu):
    with open(MENU, 'r', encoding='utf-8') as file:
        data = json.load(file)

    data['menus'][menu] = {"text":"Нужно настроить меню"}

    with open(MENU, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        
    return data['menus'][menu]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    with open(MENU, 'r', encoding='utf-8') as file:
        return jsonify(json.load(file))

@app.route('/menu/<menu>', methods=['GET', 'POST'])
def open_menu(menu):
    if request.method == 'GET':
        with open(MENU, 'r', encoding='utf-8') as file:
            data = json.load(file)
        try:
            data_menu = data['menus'][menu]
        except:
            data_menu = create_menu(menu)
        data = {menu:data_menu}
        formatted_data = json.dumps(data, ensure_ascii=False, indent=4)
    
        return render_template('menu.html', data=formatted_data)

if __name__ == '__main__':
    app.run(debug=True)