"""Initialisation de l'application Flask.

Lancement : python app.py   (puis ouvrir http://127.0.0.1:5000)
"""
import logging
import os

from flask import Flask, request, send_from_directory

from config import Config
from routes.automate_routes import bp as automate_bp
from utils.errors import AppError, register_error_handlers
from utils.rate_limiter import RateLimiter
from utils.store import AutomateStore

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       "object-src 'none'; base-uri 'none'; frame-ancestors 'none'")


def create_app(overrides=None):
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)

    app.extensions["automate_store"] = AutomateStore(
        app.config["AUTOMATON_TTL_SECONDS"], app.config["MAX_STORED_AUTOMATA"])
    app.extensions["rate_limiter"] = RateLimiter(
        app.config["RATE_LIMIT_REQUESTS"], app.config["RATE_LIMIT_WINDOW_SECONDS"])

    register_error_handlers(app)
    app.register_blueprint(automate_bp)

    @app.before_request
    def limit_rate():
        if request.path.startswith("/api/"):
            if not app.extensions["rate_limiter"].allow(request.remote_addr or "inconnu"):
                raise AppError("Trop de requêtes. Veuillez patienter quelques instants.", 429)

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = CSP
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_app().run(host="0.0.0.0", port=5000, debug=False)
