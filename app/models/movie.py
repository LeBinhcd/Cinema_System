"""Parameterized persistence operations for movies."""
from app.database import get_connection


class MovieModel:
    @staticmethod
    def create_with_draft(data, source_text, generated_text):
        """Save a movie and its unapproved AI content atomically."""
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """INSERT INTO movies
                (title, duration_minutes, age_rating, synopsis, keywords, metadata_json, status, release_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (data["title"], data["duration_minutes"], data.get("age_rating"),
                 data.get("synopsis"), data.get("keywords"), data.get("metadata_json"),
                 data.get("status", "COMING_SOON"), data.get("release_date")),
            )
            movie_id = cursor.lastrowid
            cursor.execute(
                """INSERT INTO ai_contents
                (movie_id, content_type, source_text, generated_text, status)
                VALUES (%s, 'MOVIE_DESCRIPTION', %s, %s, 'DRAFT')""",
                (movie_id, source_text, generated_text),
            )
            connection.commit()
            return movie_id
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
            cursor.execute("SELECT * FROM movies ORDER BY created_at DESC")
            return cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def create(data):
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """INSERT INTO movies
                (title, duration_minutes, age_rating, synopsis, keywords, metadata_json, status, release_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (data["title"], data["duration_minutes"], data.get("age_rating"),
                 data.get("synopsis"), data.get("keywords"), data.get("metadata_json"),
                 data.get("status", "COMING_SOON"), data.get("release_date")),
            )
            connection.commit()
            return cursor.lastrowid
        finally:
            connection.close()

    @staticmethod
    def update(movie_id, data):
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """UPDATE movies SET title=%s, duration_minutes=%s, age_rating=%s,
                synopsis=%s, keywords=%s, metadata_json=%s, status=%s, release_date=%s
                WHERE id=%s""",
                (data["title"], data["duration_minutes"], data.get("age_rating"),
                 data.get("synopsis"), data.get("keywords"), data.get("metadata_json"),
                 data["status"], data.get("release_date"), movie_id),
            )
            connection.commit()
            return cursor.rowcount
        finally:
            connection.close()

    @staticmethod
    def delete(movie_id):
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM movies WHERE id=%s", (movie_id,))
            connection.commit()
            return cursor.rowcount
        finally:
            connection.close()