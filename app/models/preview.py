"""SQLite data access with explicit transaction ownership and no business rules."""
from contextlib import contextmanager
from app.database import get_connection


class PreviewModel:
    def __init__(self, connection):
        self.connection = connection

    @classmethod
    @contextmanager
    def transaction(cls):
        connection = get_connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield cls(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def movie(self, movie_id):
        return self.connection.execute("SELECT duration_minutes FROM movies WHERE id=?", (movie_id,)).fetchone()

    def has_screenings(self, movie_id):
        return self.connection.execute("SELECT 1 FROM screenings WHERE movie_id=?", (movie_id,)).fetchone() is not None

    def update_movie(self, movie_id, duration, status):
        return self.connection.execute("UPDATE movies SET duration_minutes=?,status=? WHERE id=?", (duration, status, movie_id)).rowcount == 1

    def screening(self, screening_id):
        return self.connection.execute("SELECT room_id,start_time FROM screenings WHERE id=?", (screening_id,)).fetchone()

    def seat_in_room(self, seat_id, room_id):
        return self.connection.execute("SELECT 1 FROM seats WHERE id=? AND room_id=?", (seat_id, room_id)).fetchone() is not None

    def sold(self, screening_id, seat_id):
        return self.connection.execute("SELECT 1 FROM tickets WHERE screening_id=? AND seat_id=? AND status IN ('BOOKED','USED','PAID','CHECKED_IN')", (screening_id, seat_id)).fetchone() is not None

    def hold(self, screening_id, seat_id):
        return self.connection.execute("SELECT user_id,expires_at FROM seat_holds WHERE screening_id=? AND seat_id=?", (screening_id, seat_id)).fetchone()

    def save_hold(self, user_id, screening_id, seat_id, expiry, group_code):
        return self.connection.execute(
            'INSERT INTO seat_holds(user_id,screening_id,seat_id,expires_at,group_code) VALUES(?,?,?,?,?)',
            (user_id, screening_id, seat_id, expiry, group_code),
        ).lastrowid

    def draft(self, draft_id):
        return self.connection.execute("SELECT * FROM ai_contents WHERE id=?", (draft_id,)).fetchone()

    def update_synopsis(self, movie_id, text):
        self.connection.execute("UPDATE movies SET synopsis=? WHERE id=?", (text, movie_id))

    def publish_draft(self, draft, text):
        from app.models.admin import AdminModel
        return AdminModel(self.connection).publish_movie_draft(draft, text)

    def review(self, draft_id, reviewer_id, decision, reviewed_at):
        self.connection.execute("UPDATE ai_contents SET status=?,reviewed_by=?,reviewed_at=? WHERE id=?", (decision, reviewer_id, reviewed_at, draft_id))

    @staticmethod
    def lookup(query):
        connection = get_connection()
        try:
            return [dict(row) for row in connection.execute("""SELECT t.id,t.status,t.qr_code,u.email,u.phone,m.title,
                s.start_time,se.row_label,se.seat_number FROM tickets t JOIN users u ON u.id=t.user_id
                JOIN screenings s ON s.id=t.screening_id JOIN movies m ON m.id=s.movie_id
                JOIN seats se ON se.id=t.seat_id WHERE LOWER(u.email)=? OR u.phone=? OR t.qr_code=?
                ORDER BY t.created_at DESC LIMIT 50""", (query.lower(), query, query)).fetchall()]
        finally:
            connection.close()