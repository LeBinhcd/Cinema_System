"""Credential verification and customer/staff registration."""
import re
import secrets
from werkzeug.security import check_password_hash
from app.models.user import UserModel
from flask import current_app
CODE_ALPHABET='0123456789'
def new_user_code(): return '#'+''.join(secrets.choice(CODE_ALPHABET) for _ in range(4))
def unique_user_code():
 from app.database import get_connection
 for _ in range(100):
  code=new_user_code(); c=get_connection()
  try:
   if not c.execute('SELECT 1 FROM users WHERE user_code=?',(code,)).fetchone(): return code
  finally: c.close()
 raise RuntimeError('Không thể tạo mã người dùng duy nhất.')
def validate_person(full_name,email,password):
 full_name=full_name.strip() if isinstance(full_name,str) else ''; email=email.strip().lower() if isinstance(email,str) else ''
 if not re.fullmatch(r'[A-Za-zÀ-ỹĐđ0-9]+(?:[ .-][A-Za-zÀ-ỹĐđ0-9]+)*',full_name) or not 2<=len(full_name)<=120: raise ValueError('Họ tên không hợp lệ; không dùng ký tự đặc biệt.')
 if '@' not in email or len(email)>255: raise ValueError('Email không hợp lệ.')
 if not isinstance(password,str) or not 6<=len(password)<=128: raise ValueError('Mật khẩu phải từ 6 đến 128 ký tự.')
 if UserModel.find_by_email(email): raise ValueError('Email đã được đăng ký.')
 return full_name,email,password
class AuthService:
 @staticmethod
 def register_customer(full_name,email,password):
  full_name,email,password=validate_person(full_name,email,password); code=unique_user_code(); uid=UserModel.create_customer(full_name,email,password,code); return {'user_id':uid,'role':'CUSTOMER','email':email,'full_name':full_name,'user_code':code}
 @staticmethod
 def create_staff(full_name,email,password):
  full_name,email,password=validate_person(full_name,email,password); code=unique_user_code(); uid=UserModel.create_role(full_name,email,password,code,'STAFF'); return {'user_id':uid,'role':'STAFF','email':email,'full_name':full_name,'user_code':code}
 @staticmethod
 def authenticate(email,password):
  if not isinstance(email,str) or not email.strip() or not isinstance(password,str) or not password:return None
  user=UserModel.find_by_email(email.strip().lower()) if current_app.config['DB_ENGINE']=='sqlite' else UserModel.find_by_phone(email.strip())
  if user is None or not check_password_hash(user['password_hash'],password): return None
  return {'user_id':user['id'],'role':user['role'],'email':user.get('email',''),'full_name':user.get('full_name',''),'user_code':user.get('user_code','')}
