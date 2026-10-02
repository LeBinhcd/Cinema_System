"""Account lookup; credentials never leave the authentication service."""
from app.database import get_connection


class UserModel:
    @staticmethod
    def find_by_email(email):
        connection = get_connection()
        try:
            row = connection.execute("SELECT id, email, full_name, password_hash, role FROM users WHERE email=?", (email,)).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()
    @staticmethod
    def find_by_phone(phone):
        connection = get_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT id, password_hash, role FROM users WHERE phone=%s", (phone,)
                )
                return cursor.fetchone()
            finally:
                cursor.close()
        finally:
            connection.close()