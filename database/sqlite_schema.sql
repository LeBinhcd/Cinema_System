PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, phone TEXT UNIQUE, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('CUSTOMER','STAFF','ADMIN')), created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS movies (id INTEGER PRIMARY KEY, title TEXT NOT NULL UNIQUE, duration_minutes INTEGER NOT NULL CHECK(duration_minutes>0), age_rating TEXT, synopsis TEXT, keywords TEXT, metadata_json TEXT, status TEXT NOT NULL DEFAULT 'COMING_SOON', release_date TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS genres (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS movie_genres (movie_id INTEGER NOT NULL REFERENCES movies(id), genre_id INTEGER NOT NULL REFERENCES genres(id), PRIMARY KEY(movie_id,genre_id));
CREATE TABLE IF NOT EXISTS screening_rooms (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, row_count INTEGER NOT NULL, column_count INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','MAINTENANCE')));
CREATE TABLE IF NOT EXISTS seats (id INTEGER PRIMARY KEY, room_id INTEGER NOT NULL REFERENCES screening_rooms(id), row_label TEXT NOT NULL, seat_number INTEGER NOT NULL, seat_type TEXT NOT NULL CHECK(seat_type IN ('STANDARD','VIP','COUPLE')), UNIQUE(room_id,row_label,seat_number));
CREATE TABLE IF NOT EXISTS screenings (id INTEGER PRIMARY KEY, movie_id INTEGER NOT NULL REFERENCES movies(id), room_id INTEGER NOT NULL REFERENCES screening_rooms(id), start_time TEXT NOT NULL, end_time TEXT NOT NULL, CHECK(end_time>start_time), UNIQUE(room_id,start_time));
CREATE TABLE IF NOT EXISTS ai_contents (id INTEGER PRIMARY KEY, movie_id INTEGER REFERENCES movies(id), content_type TEXT NOT NULL, source_text TEXT NOT NULL, generated_text TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'DRAFT', generated_at TEXT DEFAULT CURRENT_TIMESTAMP, reviewed_by INTEGER REFERENCES users(id), reviewed_at TEXT, draft_title TEXT, draft_genre TEXT, draft_duration_minutes INTEGER, draft_age_rating TEXT, draft_keywords TEXT, draft_release_date TEXT, draft_status TEXT, draft_metadata_json TEXT);
CREATE TABLE IF NOT EXISTS seat_holds (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id), screening_id INTEGER NOT NULL REFERENCES screenings(id), seat_id INTEGER NOT NULL REFERENCES seats(id), expires_at TEXT NOT NULL, group_code TEXT, UNIQUE(screening_id,seat_id));
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    booking_id TEXT NOT NULL UNIQUE,
    amount NUMERIC NOT NULL CHECK(amount >= 0),
    payment_method TEXT NOT NULL CHECK(payment_method IN ('VNPAY','MOMO','DOMESTIC_CARD','CASH','BANKING')),
    status TEXT NOT NULL CHECK(status IN ('PENDING','SUCCESS','FAILED','REFUNDED')),
    transaction_code TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    booking_code TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    screening_id INTEGER NOT NULL REFERENCES screenings(id),
    seat_id INTEGER NOT NULL REFERENCES seats(id),
    price NUMERIC CHECK(price >= 0),
    amount NUMERIC CHECK(amount >= 0),
    qr_code TEXT UNIQUE,
    status TEXT NOT NULL CHECK(status IN ('BOOKED','USED','CANCELLED','HELD','PAID','CHECKED_IN')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    checked_in_at TEXT
);
CREATE TABLE IF NOT EXISTS counter_sales (booking_code TEXT PRIMARY KEY, customer_name TEXT NOT NULL,
    customer_phone TEXT, staff_id INTEGER NOT NULL REFERENCES users(id));
CREATE INDEX IF NOT EXISTS ix_counter_sales_phone ON counter_sales(customer_phone);