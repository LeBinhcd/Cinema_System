"""Add optional phone lookup to an existing SQLite database without resetting data."""
from app.database import get_connection


def migrate_phone():
    connection = get_connection()
    try:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
        if "phone" not in columns:
            connection.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone ON users(phone)")
        ticket_columns = {row["name"] for row in connection.execute("PRAGMA table_info(tickets)")}
        if "booking_code" not in ticket_columns:
            connection.execute("ALTER TABLE tickets ADD COLUMN booking_code TEXT")
        if "price" not in ticket_columns:
            connection.execute("ALTER TABLE tickets ADD COLUMN price NUMERIC")
        connection.execute("CREATE INDEX IF NOT EXISTS ix_tickets_booking_code ON tickets(booking_code)")
        connection.execute("CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, booking_id TEXT NOT NULL UNIQUE, amount NUMERIC NOT NULL CHECK(amount >= 0), payment_method TEXT NOT NULL, status TEXT NOT NULL, transaction_code TEXT NOT NULL UNIQUE, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    from database.migrate_sqlite_booking import migrate_booking
    migrate_booking()
    from app.models.staff import StaffModel
    StaffModel.migrate()


if __name__ == "__main__":
    from app import create_app

    application = create_app()
    if application.config["DB_ENGINE"] != "sqlite":
        raise ValueError("Phone migration requires DB_ENGINE=sqlite")
    with application.app_context():
        migrate_phone()
    print("SQLite phone column ready")