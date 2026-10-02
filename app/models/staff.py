"""SQLite-only counter operations. All writes use PaymentModel's immediate transaction."""
from datetime import datetime

from app.database import get_connection
from app.models.payment import PaymentModel


class StaffModel(PaymentModel):
    @staticmethod
    def todays_screenings():
        connection = get_connection()
        try:
            return [dict(row) for row in connection.execute('''SELECT s.id,s.start_time,s.end_time,
                m.title AS movie_title,r.name AS room_name FROM screenings s
                JOIN movies m ON m.id=s.movie_id JOIN screening_rooms r ON r.id=s.room_id
                WHERE date(s.start_time)=? AND r.status='ACTIVE' ORDER BY s.start_time''',
                (datetime.now().date().isoformat(),))]
        finally:
            connection.close()

    def screening(self, screening_id):
        return self.connection.execute('''SELECT s.id,s.start_time,r.status AS room_status
            FROM screenings s JOIN screening_rooms r ON r.id=s.room_id WHERE s.id=?''',
            (screening_id,)).fetchone()

    def counter_seats(self, screening_id, seat_ids):
        marks = ','.join('?' for _ in seat_ids)
        return self.connection.execute(f'''SELECT se.id,se.seat_type FROM seats se
            JOIN screenings s ON s.room_id=se.room_id
            WHERE s.id=? AND se.id IN ({marks}) ORDER BY se.id''', (screening_id, *seat_ids)).fetchall()

    def active_hold(self, screening_id, seat_id):
        return self.connection.execute('''SELECT 1 FROM seat_holds WHERE screening_id=? AND seat_id=?
            AND expires_at>?''', (screening_id, seat_id, datetime.now().isoformat(sep=' '))).fetchone() is not None

    def counter_customer(self, name, phone, booking_code):
        # A walk-in is a separate account: never attach a sale to an existing login by phone.
        email = 'pos-' + booking_code.lower() + '@counter.invalid'
        return self.connection.execute('''INSERT INTO users(full_name,email,phone,password_hash,role)
            VALUES(?,?,?,?,'CUSTOMER')''', (name, email, None, '!counter-no-login')).lastrowid

    def create_counter_ticket(self, user_id, screening_id, seat_id, price, code, qr):
        self.connection.execute('''INSERT INTO tickets(booking_code,user_id,screening_id,seat_id,price,amount,qr_code,status)
            VALUES(?,?,?,?,?,?,?,'BOOKED')''', (code, user_id, screening_id, seat_id, price, price, qr))

    def store_counter_contact(self, code, name, phone, staff_id):
        self.connection.execute('''INSERT INTO counter_sales(booking_code,customer_name,customer_phone,staff_id)
            VALUES(?,?,?,?)''', (code, name, phone, staff_id))

    def staff_booking(self, code):
        return self.connection.execute('''SELECT c.customer_name,c.customer_phone,c.staff_id,u.full_name AS staff_name
            FROM counter_sales c JOIN users u ON u.id=c.staff_id WHERE c.booking_code=?''', (code,)).fetchone()

    def lookup_codes(self, query):
        return [row['booking_code'] for row in self.connection.execute('''SELECT DISTINCT t.booking_code
            FROM tickets t JOIN users u ON u.id=t.user_id
            LEFT JOIN counter_sales c ON c.booking_code=t.booking_code
            WHERE t.booking_code=? COLLATE NOCASE OR t.qr_code=? OR u.phone=? OR c.customer_phone=?
            ORDER BY t.booking_code DESC LIMIT 50''', (query, query, query, query))]

    def lookup_checkin_codes(self, query):
        return [row['booking_code'] for row in self.connection.execute('''SELECT DISTINCT booking_code
            FROM tickets WHERE booking_code=? COLLATE NOCASE OR qr_code=?''', (query, query))]

    @staticmethod
    def migrate():
        connection = get_connection()
        try:
            connection.execute('BEGIN IMMEDIATE')
            columns = {row['name'] for row in connection.execute('PRAGMA table_info(tickets)')}
            if columns and 'checked_in_at' not in columns:
                connection.execute('ALTER TABLE tickets ADD COLUMN checked_in_at TEXT')
            # Upgrade only old payment constraints, preserving rows and all ticket references.
            sql = connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='payments'").fetchone()
            if sql and "'BANKING'" not in sql['sql']:
                connection.execute('''CREATE TABLE payments_staff_upgrade (id INTEGER PRIMARY KEY,
                    booking_id TEXT NOT NULL UNIQUE, amount NUMERIC NOT NULL CHECK(amount >= 0),
                    payment_method TEXT NOT NULL CHECK(payment_method IN ('VNPAY','MOMO','DOMESTIC_CARD','CASH','BANKING')),
                    status TEXT NOT NULL CHECK(status IN ('PENDING','SUCCESS','FAILED','REFUNDED')),
                    transaction_code TEXT NOT NULL UNIQUE, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
                connection.execute('''INSERT INTO payments_staff_upgrade
                    SELECT id,booking_id,amount,payment_method,status,transaction_code,created_at FROM payments''')
                connection.execute('DROP TABLE payments')
                connection.execute('ALTER TABLE payments_staff_upgrade RENAME TO payments')
            if columns:
                connection.execute('''CREATE TABLE IF NOT EXISTS counter_sales (
                    booking_code TEXT PRIMARY KEY, customer_name TEXT NOT NULL, customer_phone TEXT,
                    staff_id INTEGER NOT NULL REFERENCES users(id))''')
                connection.execute('CREATE INDEX IF NOT EXISTS ix_counter_sales_phone ON counter_sales(customer_phone)')
            if connection.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Invalid foreign keys during staff migration')
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()