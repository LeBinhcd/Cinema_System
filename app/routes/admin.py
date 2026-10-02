from flask import Blueprint, jsonify, request
from app.auth import admin_required
from app.services.movie_service import MovieService
from app.services.room_service import RoomService
from app.services.screening_service import ScreeningService

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def payload():
    return request.get_json(silent=True) or {}


@admin_bp.get("/movies")
@admin_required
def movies():
    return jsonify(MovieService.list_all())


@admin_bp.post("/movies")
@admin_required
def create_movie():
    try:
        data = payload()
        movie_id = MovieService.create(data, bool(data.get("generate_ai_description")))
        return jsonify({"id": movie_id}), 201
    except (ValueError, RuntimeError) as exc:
        return jsonify({"error": str(exc)}), 400


@admin_bp.put("/movies/<int:movie_id>")
@admin_required
def update_movie(movie_id):
    try:
        return jsonify({"updated": MovieService.update(movie_id, payload())})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@admin_bp.delete("/movies/<int:movie_id>")
@admin_required
def delete_movie(movie_id):
    return jsonify({"deleted": MovieService.delete(movie_id)})


@admin_bp.get("/rooms")
@admin_required
def rooms():
    return jsonify(RoomService.list_all())


@admin_bp.post("/rooms")
@admin_required
def create_room():
    try:
        return jsonify({"id": RoomService.create(payload())}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@admin_bp.get("/screenings")
@admin_required
def screenings():
    return jsonify(ScreeningService.list_all())


@admin_bp.post("/screenings")
@admin_required
def create_screening():
    try:
        return jsonify({"id": ScreeningService.create(payload())}), 201
    except (ValueError, KeyError) as exc:
        return jsonify({"error": str(exc)}), 400