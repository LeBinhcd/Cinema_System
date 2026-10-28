"""Connections for the local SQLite preview and legacy MySQL service."""
import sqlite3
import mysql.connector
import re
class RowDict(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)

class CursorProxy:
    def __init__(self, cursor): self.cursor = cursor
    def _row(self, row): return RowDict(row) if isinstance(row, dict) else row
    def fetchone(self): return self._row(self.cursor.fetchone())
    def fetchall(self): return [self._row(row) for row in self.cursor.fetchall()]
    def __getattr__(self, name): return getattr(self.cursor, name)

from flask import current_app


def get_connection():
    if current_app.config["DB_ENGINE"] == "sqlite":
        connection = sqlite3.connect(current_app.config["SQLITE_PATH"], timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=15000")
        return connection
    raw = mysql.connector.connect(
        host=current_app.config["DB_HOST"],
        port=current_app.config["DB_PORT"],
        user=current_app.config["DB_USER"],
        password=current_app.config["DB_PASSWORD"],
        database=current_app.config["DB_NAME"],
        autocommit=False,
    )
    return MySQLConnection(raw)


class MySQLConnection:
    """Small DB-API compatibility layer for the existing SQLite-oriented models."""
    def __init__(self, connection):
        self.raw = connection

    def cursor(self, dictionary=False, buffered=True):
        return self.raw.cursor(dictionary=dictionary, buffered=buffered)

    @staticmethod
    def _sql(sql):
        sql = sql.replace('BEGIN IMMEDIATE', 'START TRANSACTION')
        sql = re.sub(r"datetime\('now'(?:,'localtime')?\)", 'CURRENT_TIMESTAMP', sql, flags=re.I)
        sql = re.sub(r'INSERT\s+OR\s+IGNORE', 'INSERT IGNORE', sql, flags=re.I)
        sql = sql.replace('?', '%s')
        return sql

    def execute(self, sql, params=()):
        cursor = self.raw.cursor(dictionary=True, buffered=True)
        cursor.execute(self._sql(sql), tuple(params or ()))
        return CursorProxy(cursor)

    def executemany(self, sql, params):
        cursor = self.raw.cursor(dictionary=True, buffered=True)
        cursor.executemany(self._sql(sql), params)
        return CursorProxy(cursor)

    def executescript(self, script):
        cursor = self.raw.cursor()
        for statement in script.split(';'):
            if statement.strip():
                cursor.execute(self._sql(statement))
        cursor.close()

    def commit(self): self.raw.commit()
    def rollback(self): self.raw.rollback()
    def close(self): self.raw.close()
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        if exc_type: self.rollback()
        else: self.commit()
        self.close()