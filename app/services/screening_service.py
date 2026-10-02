from datetime import datetime
from app.models.screening import ScreeningModel
from app.services.screening_rules import CLEANING_BUFFER_MINUTES, sales_open, validate_schedule


class ScreeningService:
    MIN_CLEANUP_MINUTES = CLEANING_BUFFER_MINUTES

    @staticmethod
    def list_all():
        return ScreeningModel.list_all()

    @staticmethod
    def sales_open(start_time, now):
        return sales_open(start_time, now)

    @staticmethod
    def validate_schedule(start, end, screenings):
        validate_schedule(start, end, screenings)

    @staticmethod
    def create(data):
        start = datetime.fromisoformat(data["start_time"])
        end = datetime.fromisoformat(data["end_time"])
        if end <= start:
            raise ValueError("end_time must be after start_time")
        if start.tzinfo is not None or end.tzinfo is not None:
            raise ValueError("Timezone-aware times require an agreed database timezone policy")
        data["start_time"], data["end_time"] = start, end
        return ScreeningModel.create_checked(data, lambda rows: ScreeningService.validate_schedule(start, end, rows))