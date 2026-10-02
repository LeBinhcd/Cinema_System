"""Isolated SQLite fixtures: never depend on or mutate the demo database."""
from pathlib import Path
import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from app.database import get_connection


@pytest.fixture
def app(tmp_path):
    application = create_app({"TESTING": True, "APP_ENV": "testing", "DB_ENGINE": "sqlite",
                              "SQLITE_PATH": str(tmp_path / "cinema.db"),
                              "SECRET_KEY": "test-only-key", "SESSION_COOKIE_SECURE": False})
    with application.app_context():
        connection = get_connection()
        connection.executescript((Path(__file__).resolve().parents[1] / "database/sqlite_schema.sql").read_text(encoding="utf-8"))
        for user_id, role in ((1, "ADMIN"), (2, "STAFF"), (3, "CUSTOMER")):
            connection.execute("INSERT INTO users(id,full_name,email,phone,password_hash,role) VALUES(?,?,?,?,?,?)",
                               (user_id, role, role.lower() + "@example.com", f"090000000{user_id}", generate_password_hash("valid-password"), role))
        connection.commit()
        connection.close()
    return application