"""Remove expired holds using either an existing transaction or a short one."""
from datetime import datetime

from app.database import get_connection


def cleanup_expired_holds(connection=None, now=None):
    owns_connection = connection is None
    if owns_connection:
        connection = get_connection()
    try:
        if owns_connection:
            connection.execute('BEGIN IMMEDIATE')
        count = connection.execute(
            'DELETE FROM seat_holds WHERE expires_at <= ?',
            ((now or datetime.now()).isoformat(sep=' ', timespec='microseconds'),),
        ).rowcount
        if owns_connection:
            connection.commit()
        return count
    except Exception:
        if owns_connection:
            connection.rollback()
        raise
    finally:
        if owns_connection:
            connection.close()