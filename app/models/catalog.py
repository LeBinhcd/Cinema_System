"""Read-only SQLite catalog for the browser preview."""
from app.database import get_connection


class CatalogModel:
    @staticmethod
    def query(sql, params=()):
        connection = get_connection()
        try:
            return [dict(row) for row in connection.execute(sql, params).fetchall()]
        finally:
            connection.close()

    @staticmethod
    def movies():
        return CatalogModel.query("""SELECT m.*, (SELECT GROUP_CONCAT(g.name, ', ') FROM genres g
            JOIN movie_genres mg ON mg.genre_id=g.id WHERE mg.movie_id=m.id) AS genres
            FROM movies m ORDER BY m.title""")

    @staticmethod
    def screenings():
        return CatalogModel.query("""SELECT s.*, m.title AS movie_title, r.name AS room_name,
            (SELECT COUNT(*) FROM tickets t WHERE t.screening_id=s.id
             AND t.status IN ('BOOKED','USED','PAID','CHECKED_IN')) AS sold_tickets
            FROM screenings s JOIN movies m ON m.id=s.movie_id
            JOIN screening_rooms r ON r.id=s.room_id ORDER BY s.start_time""")

    @staticmethod
    def drafts():
        return CatalogModel.query("""SELECT a.id, a.generated_text, a.content_type, a.status,
            COALESCE(m.title, a.draft_title) AS movie_title,
            COALESCE(m.age_rating, a.draft_age_rating) AS age_rating,
            COALESCE(m.duration_minutes, a.draft_duration_minutes) AS duration_minutes,
            COALESCE(a.draft_genre, (SELECT GROUP_CONCAT(g.name, ', ') FROM genres g JOIN movie_genres mg
             ON mg.genre_id=g.id WHERE mg.movie_id=m.id)) AS genres
            FROM ai_contents a LEFT JOIN movies m ON m.id=a.movie_id
            WHERE a.status='DRAFT' AND a.content_type='MOVIE_DESCRIPTION'
            ORDER BY a.generated_at DESC""")