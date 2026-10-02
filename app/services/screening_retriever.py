"""Safe, read-only retrieval of public cinema screenings and seat availability."""
from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any, Mapping, Optional

from app.database import get_connection
from app.services.question_analyzer import VIETNAM_TIMEZONE


MAX_RESULTS = 5
SEAT_TYPES = ("STANDARD", "VIP", "COUPLE")


def _value(intent: Mapping[str, Any], key: str, default=None):
    value = intent.get(key, default)
    return value if value not in (None, "") else default


def _validate_intent(intent: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(intent, Mapping):
        return {}
    normalized = {
        "movie_title": _value(intent, "movie_title"),
        "genre": _value(intent, "genre"),
        "date": _value(intent, "date"),
        "min_time": _value(intent, "min_time"),
        "max_time": _value(intent, "max_time"),
        "time_of_day": _value(intent, "time_of_day"),
        "seat_type": _value(intent, "seat_type"),
    }
    if intent.get("intent") not in (None, "recommend_movie", "search_screenings", "check_seats"):
        return {}
    if any(value is not None and not isinstance(value, str) for value in normalized.values()):
        raise ValueError("Intent filters must be strings or null")
    if normalized["seat_type"] not in (None, *SEAT_TYPES):
        raise ValueError("Invalid seat_type")
    if normalized["time_of_day"] not in (None, "MORNING", "AFTERNOON", "EVENING"):
        raise ValueError("Invalid time_of_day")
    if normalized["date"] is not None:
        if date.fromisoformat(normalized["date"]).isoformat() != normalized["date"]:
            raise ValueError("date must be YYYY-MM-DD")
    for key in ("min_time", "max_time"):
        if normalized[key] is not None:
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", normalized[key]):
                raise ValueError("Time must be HH:MM")
            normalized[key] += ":00" if key == "min_time" else ":59"
    if normalized["min_time"] and normalized["max_time"] and normalized["min_time"] > normalized["max_time"]:
        return {}
    return normalized


def retrieve_screenings(intent: Mapping[str, Any], *, now: Optional[datetime] = None) -> list[dict[str, Any]]:
    """Retrieve at most five screenings matching a validated structured intent.

    The function only returns public screening facts. All values originating from
    the intent are SQL parameters; SQL structure is fixed and never concatenated.
    SQLite only, within a Flask application context. Naive database timestamps
    and naive ``now`` are cinema-local (Asia/Ho_Chi_Minh); aware ``now`` is
    converted to that timezone. Bounds are inclusive (max_time covers its minute).
    seat_type filters rooms that contain that type, not necessarily free seats.
    DB errors propagate; they must not be mistaken for a successful empty result.
    """
    filters = _validate_intent(intent)
    if not filters:
        return []

    clock = now or datetime.now(VIETNAM_TIMEZONE)
    if clock.tzinfo is not None:
        clock = clock.astimezone(VIETNAM_TIMEZONE).replace(tzinfo=None)
    checked_at = clock.isoformat(sep=" ", timespec="microseconds")
    params = dict(filters, checked_at=checked_at, limit=MAX_RESULTS)
    if filters["movie_title"]:
        escaped = filters["movie_title"].replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        params["movie_title"] = "%" + escaped + "%"
    sql = """
        SELECT s.id AS screening_id, m.id AS movie_id, m.title AS movie_title,
               s.start_time, s.end_time, r.id AS room_id, r.name AS room_name,
               (
                   SELECT COALESCE(SUM(CASE WHEN se.seat_type='STANDARD' THEN 1 ELSE 0 END), 0)
                   FROM seats se WHERE se.room_id=s.room_id
                     AND NOT EXISTS (SELECT 1 FROM tickets t WHERE t.screening_id=s.id AND t.seat_id=se.id AND t.status IN ('BOOKED','USED'))
                     AND NOT EXISTS (SELECT 1 FROM seat_holds h WHERE h.screening_id=s.id AND h.seat_id=se.id AND julianday(h.expires_at) > julianday(:checked_at))
               ) AS standard_available,
               (
                   SELECT COALESCE(SUM(CASE WHEN se.seat_type='VIP' THEN 1 ELSE 0 END), 0)
                   FROM seats se WHERE se.room_id=s.room_id
                     AND NOT EXISTS (SELECT 1 FROM tickets t WHERE t.screening_id=s.id AND t.seat_id=se.id AND t.status IN ('BOOKED','USED'))
                     AND NOT EXISTS (SELECT 1 FROM seat_holds h WHERE h.screening_id=s.id AND h.seat_id=se.id AND julianday(h.expires_at) > julianday(:checked_at))
               ) AS vip_available,
               (
                   SELECT COALESCE(SUM(CASE WHEN se.seat_type='COUPLE' THEN 1 ELSE 0 END), 0)
                   FROM seats se WHERE se.room_id=s.room_id
                     AND NOT EXISTS (SELECT 1 FROM tickets t WHERE t.screening_id=s.id AND t.seat_id=se.id AND t.status IN ('BOOKED','USED'))
                     AND NOT EXISTS (SELECT 1 FROM seat_holds h WHERE h.screening_id=s.id AND h.seat_id=se.id AND julianday(h.expires_at) > julianday(:checked_at))
               ) AS couple_available
        FROM screenings s
        JOIN movies m ON m.id=s.movie_id
        JOIN screening_rooms r ON r.id=s.room_id
        WHERE m.status IN ('SHOWING', 'NOW_SHOWING', 'COMING_SOON', 'DANG_CHIEU', 'SAP_CHIEU')
          AND r.status='ACTIVE'
          AND (:date IS NOT NULL OR julianday(s.start_time) >= julianday(:checked_at))
          AND (:movie_title IS NULL OR m.title LIKE :movie_title ESCAPE '\\')
          AND (:genre IS NULL OR EXISTS (
              SELECT 1 FROM movie_genres mg JOIN genres g ON g.id=mg.genre_id
              WHERE mg.movie_id=m.id AND g.name=:genre))
          AND (:date IS NULL OR date(s.start_time)=:date)
          AND (:min_time IS NULL OR time(s.start_time)>=:min_time)
          AND (:max_time IS NULL OR time(s.start_time)<=:max_time)
          AND (:time_of_day IS NULL
               OR (:time_of_day='MORNING' AND time(s.start_time) BETWEEN '08:00:00' AND '11:59:59')
               OR (:time_of_day='AFTERNOON' AND time(s.start_time) BETWEEN '12:00:00' AND '17:59:59')
               OR (:time_of_day='EVENING' AND time(s.start_time)>='18:00:00'))
          AND (:seat_type IS NULL OR EXISTS (
              SELECT 1 FROM seats sf WHERE sf.room_id=s.room_id AND sf.seat_type=:seat_type))
        ORDER BY datetime(s.start_time) ASC, s.id ASC
        LIMIT :limit
    """

    connection = get_connection()
    try:
        connection.execute("PRAGMA query_only=ON")
        rows = connection.execute(sql, params).fetchall()
        return [
            {
                "screening_id": row["screening_id"],
                "movie_id": row["movie_id"],
                "movie_title": row["movie_title"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "room_id": row["room_id"],
                "room_name": row["room_name"],
                "available_seats": {
                    "STANDARD": row["standard_available"],
                    "VIP": row["vip_available"],
                    "COUPLE": row["couple_available"],
                },
                "checked_at": checked_at,
            }
            for row in rows
        ]
    finally:
        connection.close()