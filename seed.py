"""Initialize and idempotently populate the local SQLite cinema.db preview."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from werkzeug.security import generate_password_hash
from app import create_app
from app.database import get_connection
from app.services.screening_rules import CLEANING_BUFFER_MINUTES, validate_schedule
from database.migrate_sqlite_phone import migrate_phone

MOVIES = (
    ("Hành Trình Ánh Sao", 124, "T13", "Một cuộc phiêu lưu vượt qua những chân trời mới.", "Khoa học viễn tưởng", "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=800&q=80"),
    ("Bí Mật Thành Phố", 105, "T16", "Bí ẩn đằng sau những con phố quen thuộc.", "Bí ẩn", "https://images.unsplash.com/photo-1519608487953-e999c86e7455?w=800&q=80"),
    ("Mùa Hè Dịu Dàng", 98, "P", "Một câu chuyện về tình bạn và những ngày hè.", "Tình cảm", "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=800&q=80"),
)


def seed(app=None):
    app = app or create_app()
    if app.config["DB_ENGINE"] != "sqlite":
        raise ValueError("seed.py requires DB_ENGINE=sqlite")
    if app.config["APP_ENV"].lower() not in ("development", "demo", "testing"):
        raise RuntimeError("Demo seed is disabled outside development/demo/testing")
    with app.app_context():
        connection = get_connection()
        try:
            connection.executescript((Path(__file__).parent / "database/sqlite_schema.sql").read_text(encoding="utf-8"))
        finally:
            connection.close()
        migrate_phone()
        connection = get_connection()
        try:
            for name, email, phone, password, role in (
                ("Quản trị viên", "admin@cinema.com", "0900000001", "admin123", "ADMIN"),
                ("Nhân viên rạp", "staff@cinema.com", "0900000002", "staff123", "STAFF"),
                ("Khách hàng", "customer@gmail.com", "0900000003", "cust123", "CUSTOMER"),
            ):
                if not connection.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
                    connection.execute("INSERT INTO users(full_name,email,phone,password_hash,role) VALUES(?,?,?,?,?)",
                                       (name, email, phone, generate_password_hash(password), role))
                else:
                    connection.execute("UPDATE users SET phone=? WHERE email=? AND (phone IS NULL OR phone='')", (phone, email))
            ids = []
            for title, duration, rating, synopsis, genre, poster in MOVIES:
                connection.execute("""INSERT OR IGNORE INTO movies(title,duration_minutes,age_rating,synopsis,keywords,metadata_json,status)
                    VALUES(?,?,?,?,?,?,'SHOWING')""", (title, duration, rating, synopsis, genre, json.dumps({"poster_url": poster})))
                movie_id = connection.execute("SELECT id FROM movies WHERE title=?", (title,)).fetchone()[0]
                ids.append(movie_id)
                connection.execute("INSERT OR IGNORE INTO genres(name) VALUES(?)", (genre,))
                genre_id = connection.execute("SELECT id FROM genres WHERE name=?", (genre,)).fetchone()[0]
                connection.execute("INSERT OR IGNORE INTO movie_genres VALUES(?,?)", (movie_id, genre_id))
            connection.execute("INSERT OR IGNORE INTO screening_rooms(name,row_count,column_count) VALUES('Phòng Ánh Sao',6,6)")
            room_id = connection.execute("SELECT id FROM screening_rooms WHERE name='Phòng Ánh Sao'").fetchone()[0]
            connection.execute('UPDATE screening_rooms SET row_count=MAX(row_count,6) WHERE id=?', (room_id,))
            for label in "ABCDEF":
                for number in range(1, 7):
                    connection.execute("""INSERT OR IGNORE INTO seats(room_id,row_label,seat_number,seat_type)
                        VALUES(?,?,?,?)""", (room_id, label, number,
                                             'COUPLE' if label == 'F' else 'VIP' if label in 'DE' else 'STANDARD'))
            # A separate room keeps the immediate demo independent of existing timetables.
            connection.execute("INSERT OR IGNORE INTO screening_rooms(name,row_count,column_count) VALUES('Phòng Demo Hôm Nay',3,6)")
            today_room = connection.execute("SELECT id FROM screening_rooms WHERE name='Phòng Demo Hôm Nay'").fetchone()[0]
            for label, kind in (('A', 'STANDARD'), ('B', 'VIP'), ('C', 'COUPLE')):
                for number in range(1, 7):
                    connection.execute('INSERT OR IGNORE INTO seats(room_id,row_label,seat_number,seat_type) VALUES(?,?,?,?)',
                                       (today_room, label, number, kind))
            now = datetime.now()
            start = (now + timedelta(minutes=35)).replace(microsecond=0)
            existing = [dict(row) for row in connection.execute(
                'SELECT start_time,end_time FROM screenings WHERE room_id=? ORDER BY start_time', (today_room,))]
            future_today = any(now + timedelta(minutes=30) <= datetime.fromisoformat(row['start_time'])
                               and datetime.fromisoformat(row['start_time']).date() == now.date() for row in existing)
            if not future_today:
                for row in existing:
                    end = start + timedelta(minutes=MOVIES[2][1])
                    if start < datetime.fromisoformat(row['end_time']) + timedelta(minutes=CLEANING_BUFFER_MINUTES) and end + timedelta(minutes=CLEANING_BUFFER_MINUTES) > datetime.fromisoformat(row['start_time']):
                        start = datetime.fromisoformat(row['end_time']) + timedelta(minutes=15)
                end = start + timedelta(minutes=MOVIES[2][1])
                validate_schedule(start, end, existing)
                connection.execute('INSERT INTO screenings(movie_id,room_id,start_time,end_time) VALUES(?,?,?,?)',
                                   (ids[2], today_room, start.isoformat(sep=' '), end.isoformat(sep=' ')))
                if start.date() != now.date():
                    print('Too close to midnight or existing shows overlap: immediate demo starts on the next available day.')
            # Preserve history, but add a new pair if every existing screening has passed.
            if not connection.execute("SELECT id FROM screenings WHERE room_id=? AND start_time>=?", (room_id, (datetime.now().date() + timedelta(days=1)).isoformat())).fetchone():
                start = datetime.combine(datetime.now().date() + timedelta(days=1), datetime.min.time()).replace(hour=14)
                for movie_id, duration in ((ids[0], MOVIES[0][1]), (ids[1], MOVIES[1][1])):
                    end = start + timedelta(minutes=duration)
                    existing = [dict(row) for row in connection.execute(
                        "SELECT start_time,end_time FROM screenings WHERE room_id=?", (room_id,)).fetchall()]
                    validate_schedule(start, end, existing)
                    connection.execute("INSERT INTO screenings(movie_id,room_id,start_time,end_time) VALUES(?,?,?,?)",
                                       (movie_id, room_id, start.isoformat(sep=" "), end.isoformat(sep=" ")))
                    # Keep the demo timetable aligned with the shared cleaning buffer.
                    start = end + timedelta(minutes=CLEANING_BUFFER_MINUTES)
            if not connection.execute("SELECT id FROM ai_contents WHERE movie_id=? AND source_text=?", (ids[0], "Dữ liệu mẫu: hành trình giữa các vì sao")).fetchone():
                connection.execute("""INSERT INTO ai_contents(movie_id,content_type,source_text,generated_text,status)
                    VALUES(?,'MOVIE_DESCRIPTION',?,?,'DRAFT')""", (ids[0], "Dữ liệu mẫu: hành trình giữa các vì sao",
                    "Bản nháp minh họa cho quy trình kiểm duyệt nội dung AI; chưa được duyệt."))
            connection.commit()
            print("SQLite sẵn sàng: " + app.config["SQLITE_PATH"])
            print("Admin admin@cinema.com/admin123 | Staff staff@cinema.com/staff123 | Customer customer@gmail.com/cust123")
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


if __name__ == "__main__":
    seed()