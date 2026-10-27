"""SQLite persistence for holds, mock payments, tickets and check-in."""
from contextlib import contextmanager
from app.database import get_connection


class PaymentModel:
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

    def hold_order(self, hold_id, user_id):
        return self.connection.execute("""SELECT h.id,h.user_id,h.screening_id,h.seat_id,h.expires_at,h.group_code,
            s.start_time,s.end_time,m.title AS movie_title,r.name AS room_name,
            se.row_label,se.seat_number,se.seat_type
            FROM seat_holds h JOIN screenings s ON s.id=h.screening_id
            JOIN movies m ON m.id=s.movie_id JOIN screening_rooms r ON r.id=s.room_id
            JOIN seats se ON se.id=h.seat_id
            WHERE h.id=? AND h.user_id=?""", (hold_id, user_id)).fetchone()

    def paid(self, screening_id, seat_id):
        return self.connection.execute("SELECT 1 FROM tickets WHERE screening_id=? AND seat_id=? AND status IN ('BOOKED','USED','PAID','CHECKED_IN')", (screening_id, seat_id)).fetchone() is not None

    def hold_group(self, hold_id, user_id):
        anchor = self.connection.execute(
            'SELECT * FROM seat_holds WHERE id=? AND user_id=?', (hold_id, user_id)
        ).fetchone()
        if not anchor:
            return []
        ids = self.connection.execute(
            'SELECT id FROM seat_holds WHERE user_id=? AND screening_id=? AND group_code=? ORDER BY id',
            (user_id, anchor['screening_id'], anchor['group_code']),
        ).fetchall() if anchor['group_code'] else [anchor]
        return [dict(self.hold_order(row['id'], user_id)) for row in ids]

    def ticket_group(self, booking_code):
        return self.connection.execute('''SELECT t.*,m.title AS movie_title,s.start_time,s.end_time,
            r.name AS room_name,se.row_label,se.seat_number,se.seat_type,u.phone,u.email,u.full_name,
            p.status AS payment_status FROM tickets t
            JOIN screenings s ON s.id=t.screening_id JOIN movies m ON m.id=s.movie_id
            JOIN screening_rooms r ON r.id=s.room_id JOIN seats se ON se.id=t.seat_id
            JOIN users u ON u.id=t.user_id LEFT JOIN payments p ON p.booking_id=t.booking_code
            WHERE t.booking_code=? ORDER BY t.id''', (booking_code,)).fetchall()

    def tickets_for_user(self, user_id):
        return self.connection.execute('''SELECT t.*,m.title AS movie_title,s.start_time,s.end_time,
            r.name AS room_name,se.row_label,se.seat_number,se.seat_type,
            p.status AS payment_status FROM tickets t
            JOIN screenings s ON s.id=t.screening_id JOIN movies m ON m.id=s.movie_id
            JOIN screening_rooms r ON r.id=s.room_id JOIN seats se ON se.id=t.seat_id
            LEFT JOIN payments p ON p.booking_id=t.booking_code
            WHERE t.user_id=? AND t.booking_code IS NOT NULL
            ORDER BY t.created_at DESC,t.id DESC''', (user_id,)).fetchall()

    def watched_movies_for_user(self, user_id):
        return self.connection.execute("""SELECT m.id AS movie_id, m.title, s.start_time,
            t.status, t.checked_in_at,
            (SELECT GROUP_CONCAT(g.name, ', ') FROM genres g JOIN movie_genres mg
             ON mg.genre_id=g.id WHERE mg.movie_id=m.id) AS genres
            FROM tickets t JOIN screenings s ON s.id=t.screening_id JOIN movies m ON m.id=s.movie_id
            WHERE t.user_id=? AND t.status IN ('USED','CHECKED_IN')
            GROUP BY t.booking_code, m.id, m.title, s.start_time, t.status, t.checked_in_at
            ORDER BY COALESCE(t.checked_in_at, s.start_time) DESC""", (user_id,)).fetchall()

    def refund(self, booking_code):
        return self.connection.execute(
            "UPDATE payments SET status='REFUNDED' WHERE booking_id=? AND status='SUCCESS'",
            (booking_code,),
        ).rowcount == 1

    def cancel_group(self, booking_code):
        self.connection.execute("UPDATE tickets SET status='CANCELLED' WHERE booking_code=?", (booking_code,))

    def create_payment(self, booking_id, amount, method, status, transaction_code):
        return self.connection.execute("INSERT INTO payments(booking_id,amount,payment_method,status,transaction_code) VALUES(?,?,?,?,?)", (booking_id, amount, method, status, transaction_code)).lastrowid

    def issue_ticket(self, order, booking_code, qr_code, price):
        cursor = self.connection.execute("INSERT INTO tickets(booking_code,user_id,screening_id,seat_id,price,amount,qr_code,status) VALUES(?,?,?,?,?,?,?,'BOOKED')", (booking_code, order["user_id"], order["screening_id"], order["seat_id"], price, price, qr_code))
        self.connection.execute("DELETE FROM seat_holds WHERE id=?", (order["id"],))
        return cursor.lastrowid

    def release_hold(self, hold_id, user_id):
        return self.connection.execute("DELETE FROM seat_holds WHERE id=? AND user_id=?", (hold_id, user_id)).rowcount == 1

    def ticket(self, booking_code):
        return self.connection.execute("""SELECT t.*,m.title AS movie_title,s.start_time,s.end_time,
            r.name AS room_name,se.row_label,se.seat_number,u.phone,u.email
            FROM tickets t JOIN screenings s ON s.id=t.screening_id JOIN movies m ON m.id=s.movie_id
            JOIN screening_rooms r ON r.id=s.room_id JOIN seats se ON se.id=t.seat_id JOIN users u ON u.id=t.user_id
            WHERE t.booking_code=?""", (booking_code,)).fetchone()

    def find_tickets(self, query):
        return self.connection.execute("""SELECT t.booking_code,t.status,t.qr_code,t.price,t.created_at,
            u.full_name,u.email,u.phone,m.title,s.start_time,se.row_label,se.seat_number
            FROM tickets t JOIN users u ON u.id=t.user_id JOIN screenings s ON s.id=t.screening_id
            JOIN movies m ON m.id=s.movie_id JOIN seats se ON se.id=t.seat_id
            WHERE LOWER(t.booking_code)=? OR t.qr_code=? OR u.phone=? ORDER BY t.created_at DESC LIMIT 50""", (query.lower(), query, query)).fetchall()

    def check_in_candidates(self, query):
        return self.connection.execute("""SELECT t.id,t.status,t.booking_code,t.qr_code,s.start_time
            FROM tickets t JOIN screenings s ON s.id=t.screening_id JOIN users u ON u.id=t.user_id
            WHERE (t.booking_code=? OR t.qr_code=? OR u.phone=?)""", (query, query, query)).fetchall()

    def mark_used(self, ticket_id):
        return self.connection.execute("UPDATE tickets SET status='USED',checked_in_at=datetime('now','localtime') WHERE id=? AND status IN ('BOOKED','PAID')", (ticket_id,)).rowcount == 1