"""Role guards for browser pages and API endpoints."""
from functools import wraps
from flask import jsonify, redirect, request, session, url_for

def _guard(role, view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        is_api = request.path.startswith('/api/') or request.path.startswith('/admin/api/') or request.path.startswith('/admin/movies/generate-description')
        if not session.get('user_id') or session.get('role') != role:
            if is_api:
                return jsonify(error=f'Yêu cầu quyền {role}.'), 403
            return redirect(url_for('frontend.login'))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view): return _guard('ADMIN', view)
def staff_required(view): return _guard('STAFF', view)
def customer_required(view): return _guard('CUSTOMER', view)
