"""Check whether the environment is ready for a MySQL dry run.

This script does not create, modify, or migrate a database. It is safe to run
before installing MySQL and before changing DB_ENGINE.
"""
from __future__ import annotations

import os
import shutil
import sys

from dotenv import load_dotenv


def main() -> int:
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=True)
    print("MySQL client:", shutil.which("mysql") or "not found")
    print("MySQL server:", shutil.which("mysqld") or "not found")
    print("mysql-connector-python:", end=" ")
    try:
        import mysql.connector  # noqa: F401
        print("installed")
    except ImportError:
        print("not installed")
        return 1
    print("Configured DB_ENGINE:", os.getenv("DB_ENGINE", "sqlite"))
    print("Configured DB_HOST:", os.getenv("DB_HOST", "127.0.0.1"))
    print("Configured DB_PORT:", os.getenv("DB_PORT", "3306"))
    print("Configured DB_NAME:", os.getenv("DB_NAME", "cinema_system"))
    print("Password value: ", "set" if os.getenv("DB_PASSWORD") else "empty", sep="")
    print("No database changes were made.")
    return 0


if __name__ == "__main__":
    sys.exit(main())