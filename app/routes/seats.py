"""Read-only seat-map endpoint for UC05."""
from flask import Blueprint, jsonify

from app.services.seat_map_service import SeatMapService

seats_bp = Blueprint("seats", __name__, url_prefix="/api/screenings")


@seats_bp.get("/<int:screening_id>/seats")
def seat_map(screening_id):
    result = SeatMapService.get_for_screening(screening_id)
    if result is None:
        return jsonify({"error": "Screening not found"}), 404
    return jsonify(result)