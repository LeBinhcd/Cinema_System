"""Account lookup and registration persistence."""
from werkzeug.security import generate_password_hash
from app.database import get_connection
from flask import current_app

class UserModel:
    @staticmethod
    def find_by_email(email):
        connection = get_connection()
        try:
            row = connection.execute("SELECT id,email,phone,full_name,user_code,password_hash,role FROM users WHERE email=?", (email,)).fetchone()
            return dict(row) if row else None
        finally: connection.close()

    @staticmethod
    def create_customer(full_name, email, phone, password, user_code):
        connection = get_connection()
        try:
            row=connection.execute("INSERT INTO users(full_name,email,phone,user_code,password_hash,role) VALUES(?,?,?,?,?,?)", (full_name,email,phone,user_code,generate_password_hash(password),'CUSTOMER'))
            connection.commit(); return row.lastrowid
        finally: connection.close()

    @staticmethod
    def create_role(full_name,email,password,user_code,role):
        connection=get_connection()
        try:
            row=connection.execute('INSERT INTO users(full_name,email,user_code,password_hash,role) VALUES(?,?,?,?,?)',(full_name,email,user_code,generate_password_hash(password),role)); connection.commit(); return row.lastrowid
        finally: connection.close()

    @staticmethod
    def find_by_phone(phone):
        connection=get_connection()
        try:
            if current_app.config.get('DB_ENGINE') == 'sqlite':
                row = connection.execute("SELECT id,email,phone,full_name,user_code,password_hash,role FROM users WHERE phone=?", (phone,)).fetchone()
                return dict(row) if row else None
            cursor=connection.cursor(dictionary=True)
            try: cursor.execute("SELECT id,email,phone,full_name,user_code,password_hash,role FROM users WHERE phone=%s",(phone,)); return cursor.fetchone()
            finally: cursor.close()
        finally: connection.close()

    @staticmethod
    def find_by_identifier(identifier):
        connection = get_connection()
        try:
            row = connection.execute(
                "SELECT id,email,phone,full_name,user_code,password_hash,role FROM users WHERE email=? OR phone=?",
                (identifier, identifier),
            ).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()
