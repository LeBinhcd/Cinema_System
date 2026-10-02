"""Upgrade SQLite for grouped bookings and simulated refunds without seed data."""
from pathlib import Path

from app.database import get_connection


def migrate_booking():
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        columns = {row['name'] for row in connection.execute('PRAGMA table_info(seat_holds)')}
        if 'group_code' not in columns:
            connection.execute('ALTER TABLE seat_holds ADD COLUMN group_code TEXT')
        # Rebuild from the canonical definitions to remove booking_code uniqueness
        # and allow REFUNDED, including databases upgraded by the earlier migration.
        schema = (Path(__file__).parent / 'sqlite_schema.sql').read_text(encoding='utf-8')
        for table in ('tickets', 'payments', 'seat_holds'):
            definition = next(part.strip() for part in schema.split(';')
                              if part.strip().startswith(f'CREATE TABLE IF NOT EXISTS {table} ('))
            connection.execute(definition.replace(f'{table} (', f'{table}_upgrade (', 1))
            old_columns = {row['name'] for row in connection.execute(f'PRAGMA table_info({table})')}
            new_columns = [row['name'] for row in connection.execute(f'PRAGMA table_info({table}_upgrade)')]
            shared = ','.join(name for name in new_columns if name in old_columns)
            connection.execute(f'INSERT INTO {table}_upgrade({shared}) SELECT {shared} FROM {table}')
            connection.execute(f'DROP TABLE {table}')
            connection.execute(f'ALTER TABLE {table}_upgrade RENAME TO {table}')
        connection.execute('CREATE INDEX IF NOT EXISTS ix_tickets_booking_code ON tickets(booking_code)')
        connection.execute('CREATE INDEX IF NOT EXISTS ix_holds_group ON seat_holds(group_code)')
        connection.execute('CREATE INDEX IF NOT EXISTS ix_holds_expiry ON seat_holds(expires_at)')
        if connection.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('Foreign key validation failed; migration rolled back')
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == '__main__':
    from app import create_app
    application = create_app()
    if application.config['DB_ENGINE'] != 'sqlite':
        raise ValueError('Booking migration requires SQLite')
    with application.app_context():
        migrate_booking()
    print('Grouped bookings and refunds ready')