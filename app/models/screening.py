"""Parameterized persistence operations for screenings."""
from app.database import get_connection
from flask import current_app


class ScreeningModel:
    @staticmethod
    def create_checked(data, validate_schedule):
        connection = get_connection()
        try:
            if current_app.config["DB_ENGINE"] == "sqlite":
                connection.execute("BEGIN IMMEDIATE")
                if connection.execute("SELECT id FROM screening_rooms WHERE id=?", (data["room_id"],)).fetchone() is None:
                    raise ValueError("Room does not exist")
                rows = connection.execute("SELECT id,start_time,end_time FROM screenings WHERE room_id=?", (data["room_id"],)).fetchall()
                validate_schedule([dict(row) for row in rows])
                cursor = connection.execute("INSERT INTO screenings(movie_id,room_id,start_time,end_time) VALUES(?,?,?,?)",
                                            (data["movie_id"], data["room_id"], data["start_time"].isoformat(sep=" "), data["end_time"].isoformat(sep=" ")))
                screening_id = cursor.lastrowid
                connection.commit()
                return screening_id
            connection.start_transaction()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id FROM screening_rooms WHERE id=%s FOR UPDATE", (data["room_id"],))
            if cursor.fetchone() is None:
                raise ValueError("Room does not exist")
            cursor.execute("SELECT id, start_time, end_time FROM screenings WHERE room_id=%s FOR UPDATE", (data["room_id"],))
            validate_schedule(cursor.fetchall())
            cursor.execute(
                "INSERT INTO screenings (movie_id, room_id, start_time, end_time) VALUES (%s, %s, %s, %s)",
                (data["movie_id"], data["room_id"], data["start_time"], data["end_time"]),
            )
            screening_id = cursor.lastrowid
            connection.commit()
            return screening_id
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def find_conflicts(room_id, start_time, end_time, exclude_id=None):
        connection = get_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            sql = """SELECT id, start_time, end_time FROM screenings
                     WHERE room_id=%s AND start_time < %s AND end_time > %s"""
            params = [room_id, end_time, start_time]
            if exclude_id is not None:
                sql += " AND id <> %s"
                params.append(exclude_id)
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def create(data):
        # Compatibility entry point must not bypass the service validation.
        from app.services.screening_service import ScreeningService
        normalized = dict(data)
        for field in ("start_time", "end_time"):
            if not isinstance(normalized[field], str):
                normalized[field] = normalized[field].isoformat(sep=" ")
        return ScreeningService.create(normalized)

    @staticmethod
    def list_all():
        connection = get_connection()
        try:
            if current_app.config["DB_ENGINE"] == "sqlite":
                return [dict(row) for row in connection.execute("""SELECT s.*,m.title AS movie_title,r.name AS room_name
                    FROM screenings s JOIN movies m ON m.id=s.movie_id
                    JOIN screening_rooms r ON r.id=s.room_id ORDER BY s.start_time""").fetchall()]
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""SELECT s.*, m.title AS movie_title, r.name AS room_name
                FROM screenings s JOIN movies m ON m.id=s.movie_id
                JOIN screening_rooms r ON r.id=s.room_id ORDER BY s.start_time""")
            return cursor.fetchall()
        finally:
            connection.close()