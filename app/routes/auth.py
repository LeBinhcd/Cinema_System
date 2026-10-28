"""Session login/logout for local email accounts."""
import secrets
from hmac import compare_digest
from flask import Blueprint, current_app, jsonify, request, session

from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.before_request
def validate_csrf():
    if request.endpoint in ('auth.login', 'auth.register') or current_app.testing:
        return None
    token = session.get('csrf_token')
    if not token or not compare_digest(request.headers.get('X-CSRF-Token', ''), token):
        return jsonify({'error': 'Mã xác nhận không hợp lệ; hãy tải lại trang.'}), 403


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Expected JSON object'), 400
    try:
        account = AuthService.register_customer(data.get('full_name'), data.get('email'), data.get('phone'), data.get('password'))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    session.clear()
    session.update(account)
    session['csrf_token'] = secrets.token_urlsafe(32)
    return jsonify(account), 201


@auth_bp.post("/login")
def login():

    if not current_app.secret_key:
        current_app.logger.error("SECRET_KEY is missing; refusing session login")
        return jsonify({"error": "Session configuration unavailable"}), 503
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Expected JSON object"}), 400
    account = AuthService.authenticate(data.get("identifier"), data.get("password"))
    if account is None:
        session.clear()
        return jsonify({"error": "Invalid credentials"}), 401
    session.clear()
    session.update(account)
    session["csrf_token"] = secrets.token_urlsafe(32)
    return jsonify(account)


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"status": "logged_out"})