"""Flask application factory package."""
import logging
import os
import secrets
import time

from dotenv import load_dotenv
from flask import Flask, request, session


def create_app(config=None):
    root = os.path.dirname(os.path.dirname(__file__))
    load_dotenv(os.path.join(root, ".env"), override=True)
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"), APP_ENV=os.getenv("APP_ENV", "development"),
        DB_ENGINE=os.getenv("DB_ENGINE", "sqlite"), SQLITE_PATH=os.getenv("SQLITE_PATH", os.path.join(root, "cinema.db")),
        DB_HOST=os.getenv("DB_HOST", "localhost"), DB_PORT=int(os.getenv("DB_PORT", "3306")),
        DB_NAME=os.getenv("DB_NAME", "cinema_system"), DB_USER=os.getenv("DB_USER", "root"), DB_PASSWORD=os.getenv("DB_PASSWORD", ""),
        OPENAI_COMPATIBLE_API_KEY=os.getenv("OPENAI_COMPATIBLE_API_KEY", ""),
        OPENAI_COMPATIBLE_BASE_URL=os.getenv("OPENAI_COMPATIBLE_BASE_URL", "https://api.xpiki.com/v1"),
        OPENAI_COMPATIBLE_MODEL=os.getenv("OPENAI_COMPATIBLE_MODEL", "claude-haiku-4-5"),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("APP_ENV", "development") != "development",
    )
    if config:
        app.config.update(config)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = secrets.token_hex(32)
        app.logger.warning("SECRET_KEY is missing; sessions reset on restart.")
    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    app.logger.setLevel(level)
    logging.getLogger("werkzeug").setLevel(level)

    @app.before_request
    def request_start():
        request._cinevista_started = time.perf_counter()
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        if os.getenv("CINEVISTA_LOG_HTTP", "1") == "1":
            app.logger.info("[HTTP ->] %s %s", request.method, request.path)

    @app.after_request
    def request_end(response):
        if os.getenv("CINEVISTA_LOG_HTTP", "1") == "1":
            elapsed = (time.perf_counter() - getattr(request, "_cinevista_started", time.perf_counter())) * 1000
            app.logger.info("[HTTP <-] %s %s status=%s duration_ms=%.1f", request.method, request.path, response.status_code, elapsed)
        return response

    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.seats import seats_bp
    from app.routes.pages import pages_bp
    if app.config["DB_ENGINE"] == "mysql":
        app.register_blueprint(admin_bp)
    else:
        from app.models.admin import AdminModel
        from app.models.staff import StaffModel
        with app.app_context():
            AdminModel.migrate()
            StaffModel.migrate()
    app.register_blueprint(auth_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(seats_bp)
    app.register_blueprint(pages_bp)

    @app.get("/health")
    def health_check():
        return {"service": "cinema-system", "status": "ok"}

    import sqlite3
    from mysql.connector import Error as MySQLError
    @app.errorhandler(sqlite3.Error)
    @app.errorhandler(MySQLError)
    def database_error(error):
        app.logger.error("Database operation failed (%s)", type(error).__name__)
        from flask import jsonify, render_template
        if request.path.startswith("/api/"):
            return jsonify({"error": "Database unavailable"}), 503
        return render_template("error.html"), 503
    return app
