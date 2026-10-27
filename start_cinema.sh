#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd -- "$PROJECT_DIR"
LOG_FILE="${CINEVISTA_LOG_FILE:-$PROJECT_DIR/cinevista.log}"
export PYTHONUNBUFFERED=1 APP_ENV="${APP_ENV:-development}" DB_ENGINE=sqlite SQLITE_PATH="${SQLITE_PATH:-$PROJECT_DIR/cinema.db}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export CINEVISTA_LOG_HTTP="${CINEVISTA_LOG_HTTP:-1}"
mkdir -p "$(dirname -- "$LOG_FILE")"
touch "$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1

say(){ printf '\n[CineVista] %s\n' "$*"; }
fail(){ printf '\n[CineVista] LỖI: %s\n' "$*" >&2; if [[ -t 0 ]]; then read -r -p 'Nhấn Enter để đóng...' _ || true; fi; exit 1; }
trap 'fail "Không thể khởi động tại dòng $LINENO."' ERR
command -v python3 >/dev/null 2>&1 || fail 'Chưa cài Python 3.'
python3 -m venv --help >/dev/null 2>&1 || fail 'Thiếu python3-venv. Chạy: sudo apt install python3-venv'
if [[ ! -x "$PROJECT_DIR/.venv/bin/python" ]]; then say 'Đang tạo môi trường Python riêng...'; python3 -m venv "$PROJECT_DIR/.venv"; fi
PYTHON="$PROJECT_DIR/.venv/bin/python"; PIP="$PROJECT_DIR/.venv/bin/pip"
if ! "$PYTHON" -c 'import flask, dotenv' >/dev/null 2>&1; then say 'Đang cài thư viện lần đầu...'; "$PIP" install --upgrade pip; "$PIP" install -r "$PROJECT_DIR/requirements.txt"; fi
if [[ ! -f "$PROJECT_DIR/.env" ]]; then
  say 'Tạo cấu hình SQLite local...'
  "$PYTHON" - "$PROJECT_DIR/.env" "$PROJECT_DIR/cinema.db" <<'PY'
import secrets, sys
from pathlib import Path
env_path = Path(sys.argv[1]).resolve()
env_path.parent.mkdir(parents=True, exist_ok=True)
env_path.write_text(
    'FLASK_APP=app.py\nFLASK_ENV=development\nAPP_ENV=development\n'
    f'OPENAI_COMPATIBLE_API_KEY=\nOPENAI_COMPATIBLE_BASE_URL=https://api.xpiki.com/v1\nOPENAI_COMPATIBLE_MODEL=claude-haiku-4-5\n'
    f'TMDB_API_KEY=\n'

    f'SECRET_KEY={secrets.token_urlsafe(32)}\nDB_ENGINE=sqlite\n'
    f'SQLITE_PATH={sys.argv[2]}\n',
    encoding='utf-8',
)
PY
fi
command -v npm >/dev/null 2>&1 || fail 'Chưa cài Node.js/npm. Cần Node.js 18+ để build frontend React.'
if [[ ! -d "$PROJECT_DIR/node_modules" ]]; then
  say 'Cài dependency frontend lần đầu...'; npm install --no-audit --no-fund
fi
say 'Build frontend React/Vite...'; npm run build
[[ -f "$PROJECT_DIR/dist/index.html" ]] || fail 'Không tạo được dist/index.html; dừng để không chạy frontend cũ.'
say 'Frontend React đã build xong.'

say 'Nạp dữ liệu mẫu SQLite...'; "$PYTHON" "$PROJECT_DIR/seed.py"

say 'Nạp dữ liệu mẫu SQLite...'; "$PYTHON" "$PROJECT_DIR/seed.py"

say 'Dừng phiên CineVista cũ để reset đăng nhập...'
old_pids=$(pgrep -f "$PROJECT_DIR/.venv/bin/python $PROJECT_DIR/app.py" || true)
if [[ -n "$old_pids" ]]; then
  kill $old_pids 2>/dev/null || true
  for _ in {1..20}; do
    sleep 0.1
    pgrep -f "$PROJECT_DIR/.venv/bin/python $PROJECT_DIR/app.py" >/dev/null 2>&1 || break
  done
fi

say 'Khởi động CineVista tại http://127.0.0.1:5000'; say 'Đóng cửa sổ này để dừng server.'

exec "$PYTHON" "$PROJECT_DIR/app.py"

