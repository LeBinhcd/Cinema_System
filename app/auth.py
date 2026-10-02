"""Session-backed role guard for administrative endpoints."""
from functools import wraps
from flask import abort, session


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id") or session.get("role") != "ADMIN":
            abort(403, description="Admin authentication required")
        return view(*args, **kwargs)

    return wrapped


def staff_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id") or session.get("role") != "STAFF":
            abort(403, description="Staff authentication required")
        return view(*args, **kwargs)
    return wrapped