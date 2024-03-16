from flask import Flask
from config import config

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hola mundo'

if __name__ == '__main__':
    app.run(debug = True)