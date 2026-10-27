"""SQLite admin persistence; callers own validation and transactions."""
from app.database import get_connection
from app.models.preview import PreviewModel


class AdminModel(PreviewModel):
    @staticmethod
    def migrate():
        connection = get_connection()
        try:
            connection.execute('BEGIN IMMEDIATE')
            movie_columns = connection.execute('PRAGMA table_info(movies)').fetchall()
            if movie_columns and 'age_rating' not in {row['name'] for row in movie_columns}:
                connection.execute("ALTER TABLE movies ADD COLUMN age_rating TEXT NOT NULL DEFAULT 'P' CHECK(age_rating IN ('P','K','T13','T16','T18','C'))")
            connection.execute('''CREATE TABLE IF NOT EXISTS refund_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, request_code TEXT NOT NULL UNIQUE, booking_code TEXT NOT NULL, user_id INTEGER NOT NULL, reason TEXT, status TEXT NOT NULL DEFAULT 'PENDING', reviewed_by INTEGER, reviewed_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
            user_columns = {row['name'] for row in connection.execute('PRAGMA table_info(users)').fetchall()}
            if user_columns and 'user_code' not in user_columns:
                connection.execute('ALTER TABLE users ADD COLUMN user_code TEXT')
                connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_user_code ON users(user_code)")
            columns = connection.execute('PRAGMA table_info(screening_rooms)').fetchall()
            card_columns = {row['name'] for row in connection.execute('PRAGMA table_info(saved_cards)').fetchall()}
            if not card_columns:
                connection.execute('''CREATE TABLE IF NOT EXISTS saved_cards (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL REFERENCES users(id),cardholder_name TEXT NOT NULL,brand TEXT NOT NULL,last4 TEXT NOT NULL,token TEXT NOT NULL UNIQUE,created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

            if columns and 'status' not in {row['name'] for row in columns}:
                connection.execute("ALTER TABLE screening_rooms ADD COLUMN status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','MAINTENANCE'))")
            draft_columns = {row['name'] for row in connection.execute('PRAGMA table_info(ai_contents)').fetchall()}
            for name, definition in (
                ('draft_title', 'TEXT'), ('draft_genre', 'TEXT'), ('draft_duration_minutes', 'INTEGER'),
                ('draft_age_rating', 'TEXT'), ('draft_keywords', 'TEXT'), ('draft_release_date', 'TEXT'),
                ('draft_status', 'TEXT'), ('draft_metadata_json', 'TEXT')):
                if draft_columns and name not in draft_columns:
                    connection.execute(f'ALTER TABLE ai_contents ADD COLUMN {name} {definition}')
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def add_movie(self, data):
        movie_id = self.connection.execute("""INSERT INTO movies
            (title,duration_minutes,release_date,synopsis,metadata_json,status,age_rating,keywords)
            VALUES(?,?,?,?,?,?,?,?)""", (data['title'], data['duration'], data['release_date'],
                                    data['synopsis'], data['metadata_json'], data['status'],
                                    data['age_rating'], data['keywords'])).lastrowid
        self.connection.execute('INSERT OR IGNORE INTO genres(name) VALUES(?)', (data['genre'],))
        genre = self.connection.execute('SELECT id FROM genres WHERE name=?', (data['genre'],)).fetchone()
        self.connection.execute('INSERT INTO movie_genres VALUES(?,?)', (movie_id, genre['id']))
        return movie_id

    def add_movie_draft(self, data):
        return self.connection.execute("""INSERT INTO ai_contents
            (movie_id,content_type,source_text,generated_text,status,draft_title,draft_genre,
             draft_duration_minutes,draft_age_rating,draft_keywords,draft_release_date,draft_status,draft_metadata_json)
            VALUES(NULL,'MOVIE_DESCRIPTION',?,?,?,?,?,?,?,?,?,?,?)""",
            (data['title'], data['synopsis'], 'DRAFT', data['title'], data['genre'],
             data['duration'], data['age_rating'], data['keywords'], data['release_date'], data['status'],
             data['metadata_json'])).lastrowid

    def publish_movie_draft(self, draft, synopsis):
        movie_id = self.add_movie({
            'title': draft['draft_title'], 'duration': draft['draft_duration_minutes'],
            'release_date': draft['draft_release_date'], 'synopsis': synopsis,
            'metadata_json': draft['draft_metadata_json'] or '{}', 'status': draft['draft_status'] or 'COMING_SOON',
            'age_rating': draft['draft_age_rating'] or 'P', 'keywords': draft['draft_keywords'] or '',
            'genre': draft['draft_genre'] or 'Khác'})
        self.connection.execute('UPDATE ai_contents SET movie_id=? WHERE id=?', (movie_id, draft['id']))
        return movie_id

    def movie_details(self, movie_id):
        return self.connection.execute('SELECT * FROM movies WHERE id=?', (movie_id,)).fetchone()

    def update_movie(self, movie_id, data):
        updated = self.connection.execute("""UPDATE movies SET title=?, duration_minutes=?, release_date=?, synopsis=?, metadata_json=?, status=?, age_rating=?, keywords=? WHERE id=?""", (data['title'], data['duration'], data['release_date'], data['synopsis'], data['metadata_json'], data['status'], data['age_rating'], data['keywords'], movie_id)).rowcount
        if not updated:
            return False
        self.connection.execute('DELETE FROM movie_genres WHERE movie_id=?', (movie_id,))
        self.connection.execute('INSERT OR IGNORE INTO genres(name) VALUES(?)', (data['genre'],))
        genre = self.connection.execute('SELECT id FROM genres WHERE name=?', (data['genre'],)).fetchone()
        self.connection.execute('INSERT INTO movie_genres(movie_id,genre_id) VALUES(?,?)', (movie_id, genre['id']))
        return True

    def set_movie_status(self, movie_id, status):
        self.connection.execute('UPDATE movies SET status=? WHERE id=?', (status, movie_id))

    def room(self, room_id):


        return self.connection.execute('SELECT * FROM screening_rooms WHERE id=?', (room_id,)).fetchone()

    def set_room_status(self, room_id, status):
        self.connection.execute('UPDATE screening_rooms SET status=? WHERE id=?', (status, room_id))

    def add_room(self, data, seats):
        room_id = self.connection.execute('INSERT INTO screening_rooms(name,row_count,column_count) VALUES(?,?,?)',
                                          (data['name'], data['row_count'], data['column_count'])).lastrowid
        self.connection.executemany('INSERT INTO seats(room_id,row_label,seat_number,seat_type) VALUES(?,?,?,?)',
                                    [(room_id, *seat) for seat in seats])
        return room_id

    def room_screenings(self, room_id):
        return self.connection.execute('SELECT id,start_time,end_time FROM screenings WHERE room_id=?', (room_id,)).fetchall()

    def add_screening(self, movie_id, room_id, start, end):
        return self.connection.execute('INSERT INTO screenings(movie_id,room_id,start_time,end_time) VALUES(?,?,?,?)',
                                       (movie_id, room_id, start.isoformat(sep=' '), end.isoformat(sep=' '))).lastrowid

    @staticmethod
    def revenue_report(from_date, to_date):
        connection = get_connection()
        try:
            connection.execute('BEGIN')
            params = (from_date, to_date)
            revenue = connection.execute("""SELECT COALESCE(SUM(amount),0) FROM payments
                WHERE status='SUCCESS' AND date(created_at) BETWEEN ? AND ?""", params).fetchone()[0]
            tickets = connection.execute("""SELECT COUNT(*) FROM tickets
                WHERE status IN ('BOOKED','USED','PAID','CHECKED_IN')
                AND date(created_at) BETWEEN ? AND ?""", params).fetchone()[0]
            occupancy = connection.execute("""SELECT
                COALESCE(SUM((SELECT COUNT(*) FROM seats se WHERE se.room_id=s.room_id)),0),
                COALESCE(SUM((SELECT COUNT(DISTINCT t.seat_id) FROM tickets t
                    JOIN seats se ON se.id=t.seat_id AND se.room_id=s.room_id
                    WHERE t.screening_id=s.id AND t.status IN ('BOOKED','USED','PAID','CHECKED_IN'))),0)
                FROM screenings s WHERE date(s.start_time) BETWEEN ? AND ?""", params).fetchone()
            return {'total_revenue': revenue, 'tickets_sold': tickets,
                    'total_seats': occupancy[0], 'occupied_seats': occupancy[1],
                    'occupancy_rate': round(100 * occupancy[1] / occupancy[0], 2) if occupancy[0] else 0}
        finally:
            connection.close()

    @staticmethod
    def rooms():
        connection = get_connection()
        try:
            return [dict(row) for row in connection.execute("""SELECT r.*,
                COUNT(s.id) AS total_seats,
                SUM(CASE WHEN s.seat_type='STANDARD' THEN 1 ELSE 0 END) AS standard_seats,
                SUM(CASE WHEN s.seat_type='VIP' THEN 1 ELSE 0 END) AS vip_seats,
                SUM(CASE WHEN s.seat_type='COUPLE' THEN 1 ELSE 0 END) AS couple_seats
                FROM screening_rooms r LEFT JOIN seats s ON s.room_id=r.id GROUP BY r.id ORDER BY r.name""")]
        finally:
            connection.close()