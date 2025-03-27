from flask import Flask, render_template, jsonify
import json

app = Flask(__name__)
MENU = 'data.json'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    with open(MENU, 'r', encoding='utf-8') as file:
        return jsonify(json.load(file))

@app.route('/menu/<menu>')
def open_menu(menu):
    with open(MENU, 'r', encoding='utf-8') as file:
        data = json.load(file)
    data_menu = data['menus'][menu]
    data = {menu:data_menu}
    formatted_data = json.dumps(data, ensure_ascii=False, indent=4)

    return render_template('menu.html', data=formatted_data)

if __name__ == '__main__':
    app.run(debug=True)