"""SQLite seat availability including active temporary holds."""
from datetime import datetime
from app.database import get_connection
from app.models.hold_cleanup import cleanup_expired_holds


class SeatMapModel:
    @staticmethod
    def get_for_screening(screening_id):
        cleanup_expired_holds()
        connection = get_connection()
        try:
            row = connection.execute("""SELECT s.id,s.room_id,s.start_time,r.name AS room_name,
                r.row_count,r.column_count,m.title AS movie_title FROM screenings s
                JOIN screening_rooms r ON r.id=s.room_id JOIN movies m ON m.id=s.movie_id WHERE s.id=?""",
                (screening_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            result["start_time"] = datetime.fromisoformat(result["start_time"])
            result["seats"] = [dict(seat) for seat in connection.execute("""SELECT se.id,se.row_label,se.seat_number,se.seat_type,
                CASE WHEN EXISTS(SELECT 1 FROM tickets t WHERE t.screening_id=? AND t.seat_id=se.id AND t.status IN ('BOOKED','USED','PAID','CHECKED_IN')) THEN 'SOLD'
                WHEN EXISTS(SELECT 1 FROM seat_holds h WHERE h.screening_id=? AND h.seat_id=se.id AND h.expires_at>?) THEN 'HELD'
                ELSE 'AVAILABLE' END AS status FROM seats se WHERE se.room_id=? ORDER BY se.row_label,se.seat_number""",
                (screening_id, screening_id, datetime.now().isoformat(sep=" "), result["room_id"])).fetchall()]
            return result
        finally:
            connection.close()