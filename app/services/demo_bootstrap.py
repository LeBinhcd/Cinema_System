"""Prepare the local demo while preserving existing bookings and credentials."""
from datetime import datetime
from contextlib import closing
from pathlib import Path
import sqlite3


def prepare_demo(application):
    path = Path(application.config['SQLITE_PATH'])
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        # SQLite backup API also safely includes committed WAL data.
        backup = path.with_name(path.name + '.backup-startup-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        with closing(sqlite3.connect(str(path))) as source, closing(sqlite3.connect(str(backup))) as target:
            if source.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise RuntimeError('SQLite integrity check failed; database was not modified')
            source.backup(target)
    from seed import seed
    seed(application)