@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo =====================================================
echo   MediVoice VN — Cài đặt / Install
echo   Phiên bản: 0.5.3 ^| Windows 10/11 x64
echo =====================================================
echo.

:: ── Bước 1: Kiểm tra Python ──────────────────────────
echo [1/6] Kiểm tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] Python chưa được cài.
    echo.
    echo   Tải Python 3.10 tại: https://www.python.org/downloads/
    echo   Tích chọn "Add Python to PATH" khi cài.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo   [OK] Python %PY_VER%

:: Kiểm tra version >= 3.10
for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)
if %PY_MAJOR% LSS 3 (
    echo   [FAIL] Cần Python 3.10+. Đang dùng %PY_VER%.
    pause & exit /b 1
)
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 10 (
    echo   [FAIL] Cần Python 3.10+. Đang dùng %PY_VER%.
    pause & exit /b 1
)

:: ── Bước 2: Tạo virtual environment ──────────────────
echo.
echo [2/6] Tạo môi trường ảo (venv)...
if exist venv\Scripts\python.exe (
    echo   [OK] venv đã có sẵn.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo   [FAIL] Không tạo được venv.
        pause & exit /b 1
    )
    echo   [OK] venv đã tạo.
)

:: ── Bước 3: Cài packages ─────────────────────────────
echo.
echo [3/6] Cài đặt packages (có thể mất 5-15 phút lần đầu)...
echo   Đang cài: fastapi, uvicorn, torch, transformers, reportlab...
call venv\Scripts\pip install --quiet --upgrade pip
call venv\Scripts\pip install --quiet -r requirements-prod.txt
if errorlevel 1 (
    echo.
    echo   [FAIL] Lỗi cài packages. Kiểm tra kết nối Internet.
    echo   Thử chạy thủ công: venv\Scripts\pip install -r requirements-prod.txt
    pause & exit /b 1
)
echo   [OK] Tất cả packages đã cài.

:: ── Bước 4: Kiểm tra reference data ──────────────────
echo.
echo [4/6] Kiểm tra dữ liệu tham chiếu...
if not exist data\reference\icd10vn.json (
    echo   [FAIL] Thiếu data\reference\icd10vn.json
    echo   Liên hệ Andy Phan để nhận bộ data đầy đủ.
    pause & exit /b 1
)
if not exist data\reference\drug_db.json (
    echo   [FAIL] Thiếu data\reference\drug_db.json
    pause & exit /b 1
)
echo   [OK] ICD-10-VN + drug_db sẵn sàng.

:: ── Bước 5: Cấu hình phòng khám ──────────────────────
echo.
echo [5/6] Cấu hình thông tin phòng khám...
if exist config\facility_config.json (
    echo   [OK] Config đã có. Bỏ qua.
    echo   (Chạy: venv\Scripts\python scripts\setup_facility.py để thay đổi)
) else (
    echo   Điền thông tin phòng khám...
    call venv\Scripts\python scripts\setup_facility.py
)

:: ── Bước 6: Pre-flight check ──────────────────────────
echo.
echo [6/6] Kiểm tra môi trường...
call venv\Scripts\python scripts\check_env.py
if errorlevel 1 (
    echo.
    echo   [FAIL] Có lỗi cần xử lý trước khi chạy app.
    pause & exit /b 1
)

:: ── Tạo shortcut start.bat ────────────────────────────
echo.
echo Cài đặt hoàn tất!
echo =====================================================
echo   Để chạy MediVoice VN:
echo     1. Nhấp đúp vào start.bat
echo     2. Mở trình duyệt: http://localhost:8000
echo =====================================================
echo.
echo   Lưu ý: PhoWhisper model (~150MB) sẽ tự download
echo   lần đầu chạy app (cần Internet).
echo.
pause
