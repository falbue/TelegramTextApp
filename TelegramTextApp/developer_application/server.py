from flask import Flask, render_template, jsonify
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    with open('data.json', 'r', encoding='utf-8') as file:
        return jsonify(json.load(file))

if __name__ == '__main__':
    app.run(debug=True)