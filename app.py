from flask import Flask, request as flask_request
from config import Config

from db.db import engine
from db.models import Base

from routes.auth.auth_routes import auth_bp
from routes.tables.tables_routes import table_bp
from routes.rooms.rooms_routes import room_bp
from routes.recommendations.recommendations_routes import recommendation_bp
from routes.ai.ai_routes import ai_bp

from flask_cors import CORS
from flask_jwt_extended import JWTManager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        supports_credentials=True
    )

    @app.before_request
    def handle_options():
        if flask_request.method == "OPTIONS":
            return {}, 200

    # 🔥 JWT
    jwt = JWTManager(app)

    @jwt.unauthorized_loader
    def unauthorized_response(callback):
        return {"message": "Token requerido"}, 401

    @jwt.invalid_token_loader
    def invalid_token_response(callback):
        return {"message": "Token inválido"}, 401

    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        return {"message": "Token expirado"}, 401

    # 🔥 RUTAS
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(table_bp, url_prefix="/tables")
    app.register_blueprint(room_bp, url_prefix="/rooms")
    app.register_blueprint(recommendation_bp, url_prefix="/recommendations")
    app.register_blueprint(ai_bp, url_prefix="/ai")

    @app.route("/")
    def home():
        return {"message": "API Mesas de Centro funcionando 🚀"}

    @app.errorhandler(404)
    def not_found(error):
        return {"message": "Ruta no encontrada"}, 404

    @app.errorhandler(500)
    def server_error(error):
        return {"message": "Error interno del servidor"}, 500

    return app


app = create_app()

if __name__ == "__main__":
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Base de datos conectada y tablas creadas")
    except Exception as e:
        print("❌ Error conectando a la DB:", e)

    print("🚀 Servidor corriendo en http://localhost:5000")
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)