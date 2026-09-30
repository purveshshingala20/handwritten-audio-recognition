"""Flask application entry point."""
from flask import Flask, jsonify
from flask_cors import CORS

from app import database
from app.errors import ApiError
from app.routers.history import history_bp
from app.routers.recognition import recognition_bp


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    with app.app_context():
        database.init_db()

    app.register_blueprint(recognition_bp)
    app.register_blueprint(history_bp)

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return jsonify({"detail": error.message}), error.status_code

    @app.get("/")
    def root():
        return jsonify({"status": "ok", "service": "Handwritten Text & Audio Recognition API"})

    return app


app = create_app()
