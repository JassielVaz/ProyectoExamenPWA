
from flask import Flask, jsonify
from flask_cors import CORS
from config import config
from database import mysql
from blueprints.pizzeria import pizzeria_bp

app = Flask(__name__)

app.config.from_object(config['development'])

CORS(app)

mysql.init_app(app)

app.register_blueprint(pizzeria_bp)


@app.route('/')
def inicio():
    return jsonify({
        'mensaje': 'API de Pizzeria funcionando',
        'exito': True
    })


print(app.url_map)


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5001,
        debug=True
    )
