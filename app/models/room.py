"""Parameterized persistence operations for rooms and seats."""
from app.database import get_connection


class RoomModel:
    @staticmethod
    def create(data):
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO screening_rooms (name, row_count, column_count) VALUES (%s, %s, %s)",
                (data["name"], data["row_count"], data["column_count"]),
            )
            room_id = cursor.lastrowid
            seats = data.get("seats", [])
            if seats:
                cursor.executemany(
                    """INSERT INTO seats (room_id, row_label, seat_number, seat_type)
                    VALUES (%s, %s, %s, %s)""",
                    [(room_id, s["row_label"], s["seat_number"], s["seat_type"]) for s in seats],
                )
            connection.commit()
            return room_id
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def list_all():
        connection = get_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM screening_rooms ORDER BY name")
            rooms = cursor.fetchall()
            for room in rooms:
                cursor.execute(
                    "SELECT id, row_label, seat_number, seat_type FROM seats WHERE room_id=%s ORDER BY row_label, seat_number",
                    (room["id"],),
                )
                room["seats"] = cursor.fetchall()
            return rooms
        finally:
            connection.close()