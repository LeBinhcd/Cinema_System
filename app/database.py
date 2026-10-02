"""Connections for the local SQLite preview and legacy MySQL service."""
import sqlite3
import mysql.connector
from flask import current_app


def get_connection():
    if current_app.config["DB_ENGINE"] == "sqlite":
        connection = sqlite3.connect(current_app.config["SQLITE_PATH"], timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=15000")
        return connection
    return mysql.connector.connect(
        host=current_app.config["DB_HOST"],
        port=current_app.config["DB_PORT"],
        user=current_app.config["DB_USER"],
        password=current_app.config["DB_PASSWORD"],
        database=current_app.config["DB_NAME"],
    )