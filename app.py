"""One-command local SQLite demo entry point (not a production server)."""
import os
from pathlib import Path
import secrets
import threading
import time
from urllib.request import urlopen
import webbrowser

from dotenv import load_dotenv
from app import create_app


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')


def create_demo_app(database_path=None):
    engine = os.getenv('DB_ENGINE', 'sqlite').lower()
    config = {
        'APP_ENV': os.getenv('APP_ENV', 'development'),
        'DB_ENGINE': engine,
        'SECRET_KEY': os.getenv('SECRET_KEY') or secrets.token_hex(32),
        'SESSION_COOKIE_SECURE': False,
        'SESSION_COOKIE_NAME': 'cinevista_session_' + secrets.token_hex(8),
    }
    if engine == 'sqlite':
        config['SQLITE_PATH'] = str(database_path or ROOT / 'cinema.db')
    application = create_app(config)
    if engine == 'sqlite':
        from app.services.demo_bootstrap import prepare_demo
        prepare_demo(application)
    return application


def open_browser_when_ready():
    for _ in range(50):
        try:
            with urlopen('http://127.0.0.1:5000/health', timeout=1) as response:
                if response.status == 200:
                    webbrowser.open('http://127.0.0.1:5000')
                    return
        except OSError:
            time.sleep(0.2)

if __name__ == "__main__":
    app = create_demo_app()
    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
else:
    app = create_app()
