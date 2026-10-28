"""Credential verification and customer/staff registration."""
import re
import secrets
from flask import current_app
from werkzeug.security import check_password_hash
from app.models.user import UserModel

CODE_ALPHABET = '0123456789'

def new_user_code():
    return '#' + ''.join(secrets.choice(CODE_ALPHABET) for _ in range(4))

def unique_user_code():
    from app.database import get_connection
    for _ in range(100):
        code = new_user_code(); connection = get_connection()
        try:
            if not connection.execute('SELECT 1 FROM users WHERE user_code=?', (code,)).fetchone(): return code
        finally: connection.close()
    raise RuntimeError('Không thể tạo mã người dùng duy nhất.')

def validate_phone(phone, check_existing=True):
    phone = phone.strip() if isinstance(phone, str) else ''
    if not re.fullmatch(r'0\d{9}', phone): raise ValueError('Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0.')
    if check_existing and UserModel.find_by_phone(phone): raise ValueError('Số điện thoại đã được đăng ký.')
    return phone

def validate_person(full_name, email, password, phone=None):
    full_name = full_name.strip() if isinstance(full_name, str) else ''
    email = email.strip().lower() if isinstance(email, str) else ''
    if not re.fullmatch(r'[A-Za-zÀ-ỹĐđ0-9]+(?:[ .-][A-Za-zÀ-ỹĐđ0-9]+)*', full_name) or not 2 <= len(full_name) <= 120: raise ValueError('Họ tên không hợp lệ; không dùng ký tự đặc biệt.')
    if '@' not in email or len(email) > 255: raise ValueError('Email không hợp lệ.')
    if not isinstance(password, str) or not 6 <= len(password) <= 128: raise ValueError('Mật khẩu phải từ 6 đến 128 ký tự.')
    if UserModel.find_by_email(email): raise ValueError('Email đã được đăng ký.')
    return full_name, email, validate_phone(phone) if phone is not None else None, password

class AuthService:
    @staticmethod
    def register_customer(full_name, email, phone, password):
        full_name, email, phone, password = validate_person(full_name, email, password, phone)
        code = unique_user_code(); uid = UserModel.create_customer(full_name, email, phone, password, code)
        return {'user_id': uid, 'role': 'CUSTOMER', 'email': email, 'full_name': full_name, 'user_code': code}

    @staticmethod
    def create_staff(full_name, email, password):
        full_name, email, _, password = validate_person(full_name, email, password)
        code = unique_user_code(); uid = UserModel.create_role(full_name, email, password, code, 'STAFF')
        return {'user_id': uid, 'role': 'STAFF', 'email': email, 'full_name': full_name, 'user_code': code}

    @staticmethod
    def authenticate(identifier, password):
        if not isinstance(identifier, str) or not identifier.strip() or not isinstance(password, str) or not password: return None
        identifier = identifier.strip().lower() if '@' in identifier else identifier.strip()
        user = UserModel.find_by_identifier(identifier)
        if '@' not in identifier and user is not None and user.get('role') != 'CUSTOMER':
            return None
        if user is None or not check_password_hash(user['password_hash'], password): return None
        return {'user_id': user['id'], 'role': user['role'], 'email': user.get('email', ''), 'full_name': user.get('full_name', ''), 'user_code': user.get('user_code', '')}