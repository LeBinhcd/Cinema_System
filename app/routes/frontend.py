"""React SPA page routes; business APIs remain in their existing blueprints."""
from pathlib import Path

from flask import Blueprint, abort, current_app, send_from_directory

from app.auth import admin_required, customer_required, staff_required
from app.services.catalog_service import CatalogService

frontend_bp = Blueprint("frontend", __name__)


def spa_index():
    frontend_index = Path(current_app.root_path) / "frontend" / "dist" / "index.html"
    if frontend_index.exists():
        return send_from_directory(frontend_index.parent, "index.html")
    return None


def _serve_spa():
    frontend = spa_index()
    if frontend is not None:
        return frontend
    abort(503, description="React frontend chưa được build trong app/frontend.")


@frontend_bp.get("/")
@frontend_bp.get("/movies")
def index():
    return _serve_spa()


@frontend_bp.get("/login")
def login():
    return _serve_spa()


@frontend_bp.get("/movie/<int:movie_id>")
def movie(movie_id):
    if not any(movie["id"] == movie_id for movie in CatalogService.movies()):
        abort(404)
    return _serve_spa()


@frontend_bp.get("/booking/<int:screening_id>")
@customer_required
def booking(screening_id):
    return _serve_spa()


@frontend_bp.get("/checkout/<int:hold_id>")
@customer_required
def checkout(hold_id):
    return _serve_spa()


@frontend_bp.get("/ticket/<booking_code>")
@customer_required
def ticket(booking_code):
    return _serve_spa()


@frontend_bp.get("/my-tickets")
@customer_required
def my_tickets():
    return _serve_spa()


@frontend_bp.get("/admin")
@admin_required
def dashboard():
    return _serve_spa()


@frontend_bp.get("/staff")
@staff_required
def staff():
    return _serve_spa()