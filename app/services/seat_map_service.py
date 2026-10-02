"""Public, read-only view of seats; holds/payments are out of scope."""
from app.models.seat_map import SeatMapModel


class SeatMapService:
    @staticmethod
    def get_for_screening(screening_id):
        return SeatMapModel.get_for_screening(screening_id)