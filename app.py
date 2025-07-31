import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
#from CashMultiDB import cash1_bp
#from CashMultiDB2 import cash2_bp  # tu blueprint de backend
from cash_logic import create_cash_blueprint
import json

# Cargar configuración desde config.json
with open('config.json') as config_file:
    config = json.load(config_file)

#frontend_path = os.path.abspath(config.get("frontend_path", "frontend/dist"))

# Ruta absoluta a tu frontend build
#frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/dist'))
#frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'frontend/dist'))
#frontend_path = r'C:\Users\usuario\Desktop\Heinsontech\IDF\CASH\HT_APP_WEB\backend\frontend\dist'

"""def create_app():
    app = Flask(__name__, static_folder=frontend_path, static_url_path='')

    # 🧠 Configura CORS dinámicamente (dev vs prod)
    env = os.getenv("FLASK_ENV", "development")
    if env == "development":
        CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
        print("🚧 CORS: localhost:3000")
    else:
        CORS(app, resources={r"/api/*": {"origins": "https://miapp.com"}})
        print("🚀 CORS: producción")

    # 🧠 Rutas de API (tu lógica de negocio)
    app.register_blueprint(create_cash_blueprint('DB1', '/db1'), url_prefix='/api')
    app.register_blueprint(create_cash_blueprint('DB2', '/db2'), url_prefix='/api')

    # 🧠 Ruta principal (carga el index.html del frontend)
    @app.route('/')
    def index():
        return send_from_directory(frontend_path, 'index.html')

    # 🧠 Rutas para los assets (JS, CSS, imágenes)
    @app.route('/<path:path>')
    def static_proxy(path):
        return send_from_directory(frontend_path, path)

    return app """
"""def create_app():
    app = Flask(__name__)

    # 🧠 CORS solo para desarrollo
    env = os.getenv("FLASK_ENV", "development")
    if env == "development":
        CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
        print("🚧 CORS: localhost:3000")
    else:
        CORS(app, resources={r"/*": {"origins": "https://miapp.com"}})
        print("🚀 CORS: producción")

    # 🧠 Rutas de API
    
    app.register_blueprint(create_cash_blueprint('DB1', '/db1'), url_prefix='/api')
    app.register_blueprint(create_cash_blueprint('DB2', '/db2'), url_prefix='/api')

    return app"""

def create_app():
    app = Flask(__name__)

    # 🧠 CORS solo para desarrollo
    env = os.getenv("FLASK_ENV", "development")
    if env == "development":
        CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})
        print("🚧 CORS: localhost:3000")
    else:
        CORS(app, resources={r"/*": {"origins": "https://miapp.com"}})
        print("🚀 CORS: producción")


    # Registra cada base con su URL única
    app.register_blueprint(create_cash_blueprint('DB1', '/db1'), url_prefix='/api')
    app.register_blueprint(create_cash_blueprint('DB2', '/db2'), url_prefix='/api')
    return app


# 🔥 Ejecutar servidor
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
