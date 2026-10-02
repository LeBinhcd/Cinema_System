"""Flask application factory package."""
import os
import secrets

from dotenv import load_dotenv
from flask import Flask, session


def create_app(config=None):
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        APP_ENV=os.getenv("APP_ENV", "development"),
        DB_ENGINE=os.getenv("DB_ENGINE", "sqlite"),
        SQLITE_PATH=os.getenv("SQLITE_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "cinema.db")),
        DB_HOST=os.getenv("DB_HOST", os.getenv("MYSQL_HOST", "localhost")),
        DB_PORT=int(os.getenv("DB_PORT", os.getenv("MYSQL_PORT", "3306"))),
        DB_NAME=os.getenv("DB_NAME", os.getenv("MYSQL_DATABASE", "cinema_system")),
        DB_USER=os.getenv("DB_USER", os.getenv("MYSQL_USER", "root")),
        DB_PASSWORD=os.getenv("DB_PASSWORD", os.getenv("MYSQL_PASSWORD", "")),
        GROQ_API_KEY=os.getenv("GROQ_API_KEY", ""),
        GROQ_MODEL=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("APP_ENV", "development") != "development",
    )
    if config:
        app.config.update(config)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = secrets.token_hex(32)
        app.logger.warning("SECRET_KEY is missing; generated an ephemeral key. Configure a stable environment secret before deployment; sessions reset on restart.")

    @app.before_request
    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)

    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.seats import seats_bp
    from app.routes.pages import pages_bp
    if app.config["DB_ENGINE"] == "mysql":
        app.register_blueprint(admin_bp)
    else:
        from app.models.admin import AdminModel
        with app.app_context():
            AdminModel.migrate()
            from app.models.staff import StaffModel
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
        from flask import jsonify, render_template, request
        if request.path.startswith("/api/"):
            return jsonify({"error": "Database unavailable"}), 503
        return render_template("error.html"), 503

    return app