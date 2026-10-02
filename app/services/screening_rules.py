"""Shared cinema time constraints; naive times use the local demo clock."""
from datetime import datetime, timedelta

CLEANING_BUFFER_MINUTES = 15
SALES_CUTOFF_MINUTES = 15
SEAT_HOLD_MINUTES = 5


def as_datetime(value):
    return datetime.fromisoformat(value) if isinstance(value, str) else value


def sales_open(start_time, now):
    return now < as_datetime(start_time) + timedelta(minutes=SALES_CUTOFF_MINUTES)


def validate_schedule(start, end, screenings):
    start, end = as_datetime(start), as_datetime(end)
    if start.tzinfo is not None or end.tzinfo is not None:
        raise ValueError("Timezone-aware times require an agreed database timezone policy")
    if end <= start:
        raise ValueError("end_time must be after start_time")
    cleanup = timedelta(minutes=CLEANING_BUFFER_MINUTES)
    for screening in screenings:
        if start < as_datetime(screening["end_time"]) + cleanup and end + cleanup > as_datetime(screening["start_time"]):
            raise ValueError(f"Xung đột suất #{screening['id'] if 'id' in screening.keys() else '?'} "
                             f"({as_datetime(screening['start_time']):%d/%m/%Y %H:%M} – "
                             f"{as_datetime(screening['end_time']):%H:%M}); cần ít nhất "
                             f"{CLEANING_BUFFER_MINUTES} phút dọn phòng.")