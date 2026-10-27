@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"
set "LOG_FILE=%PROJECT_DIR%cinevista-windows.log"
set "PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"
set "PIP=%PROJECT_DIR%.venv\Scripts\pip.exe"

call :log "=============================================="
call :log "CineVista Windows Launcher"
call :log "Project: %PROJECT_DIR%"
call :log "Log: %LOG_FILE%"
call :log "=============================================="

where python >nul 2>&1
if errorlevel 1 (
  call :fail "Khong tim thay Python. Cai Python 3 va chon Add Python to PATH."
  goto :end
)

if not exist "%PYTHON%" (
  call :log "Dang tao moi truong Python .venv..."
  python -m venv "%PROJECT_DIR%.venv"
  if errorlevel 1 (
    call :fail "Khong the tao .venv."
    goto :end
  )
)

if not exist "%PROJECT_DIR%.env" (
  call :log "Tao .env mac dinh cho SQLite..."
  >"%PROJECT_DIR%.env" (
    echo FLASK_APP=app.py
    echo FLASK_ENV=development
    echo APP_ENV=development
    echo DB_ENGINE=sqlite
    echo SQLITE_PATH=%PROJECT_DIR%cinema.db
    echo OPENAI_COMPATIBLE_API_KEY=
    echo OPENAI_COMPATIBLE_BASE_URL=https://api.xpiki.com/v1
    echo OPENAI_COMPATIBLE_MODEL=claude-haiku-4-5
    echo TMDB_API_KEY=
  )
)

"%PYTHON%" -c "import flask, dotenv" >nul 2>&1
if errorlevel 1 (
  call :log "Dang cai dependency Python tu requirements.txt..."
  "%PIP%" install -r "%PROJECT_DIR%requirements.txt"
  if errorlevel 1 (
    call :fail "Cai dependency Python that bai."
    goto :end
  )
)

where npm >nul 2>&1
if errorlevel 1 (
  call :fail "Khong tim thay npm/Node.js. Cai Node.js 18+ de build frontend React."
  goto :end
)

if not exist "%PROJECT_DIR%node_modules" (
  call :log "Dang cai dependency frontend..."
  call npm install --no-audit --no-fund
  if errorlevel 1 (
    call :fail "Cai dependency frontend that bai."
    goto :end
  )
)

call :log "Build frontend React/Vite..."
call npm run build
if errorlevel 1 (
  call :fail "Build frontend that bai. Khong khoi dong fallback Jinja cu."
  goto :end
)
if not exist "%PROJECT_DIR%dist\index.html" (
  call :fail "Khong tim thay dist\index.html sau khi build frontend."
  goto :end
)
call :log "Frontend React da build tai %PROJECT_DIR%dist"

call :log "Nap du lieu mau SQLite..."
"%PYTHON%" "%PROJECT_DIR%seed.py"
if errorlevel 1 (
  call :fail "Seed database that bai."
  goto :end
)

curl --silent --fail --max-time 2 http://127.0.0.1:5000/health >nul 2>&1
if not errorlevel 1 (
  call :log "CineVista dang chay tai http://127.0.0.1:5000"
  call :log "Theo doi log: %LOG_FILE%"
  start "" http://127.0.0.1:5000
  goto :end
)

if not defined LOG_LEVEL set "LOG_LEVEL=INFO"
if not defined CINEVISTA_LOG_HTTP set "CINEVISTA_LOG_HTTP=1"
call :log "Khoi dong CineVista tai http://127.0.0.1:5000"
call :log "Log backend duoc ghi vao %LOG_FILE%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "& { & '%PYTHON%' '%PROJECT_DIR%app.py' 2>&1 | Tee-Object -FilePath '%LOG_FILE%' -Append }"
set "EXIT_CODE=%errorlevel%"
call :log "Flask da dung voi ma loi %EXIT_CODE%."

:end
call :log "Nhan phim bat ky de dong cua so..."
pause >nul
exit /b 0

:log
>> "%LOG_FILE%" echo [%date% %time%] %~1
 echo [%date% %time%] %~1
exit /b 0

:fail
call :log "LOI: %~1"
exit /b 1
