"""Credential verification without exposing passwords or hashes to routes."""
from werkzeug.security import check_password_hash

from app.models.user import UserModel
from flask import current_app


class AuthService:
    @staticmethod
    def authenticate(email, password):
        if not isinstance(email, str) or not email.strip() or not isinstance(password, str) or not password:
            return None
        user = (UserModel.find_by_email(email.strip().lower()) if current_app.config["DB_ENGINE"] == "sqlite"
                else UserModel.find_by_phone(email.strip()))
        if user is None or not check_password_hash(user["password_hash"], password):
            return None
        return {"user_id": user["id"], "role": user["role"],
                "email": user.get("email", ""), "full_name": user.get("full_name", "")}