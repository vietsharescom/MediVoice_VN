@echo off
chcp 65001 >nul
setlocal

echo =====================================================
echo   MediVoice VN — Khởi động
echo =====================================================

:: Kiểm tra venv
if not exist venv\Scripts\python.exe (
    echo   [FAIL] Chưa cài đặt. Chạy install.bat trước.
    pause & exit /b 1
)

:: Đọc port từ config
set APP_PORT=8000
if exist config\facility_config.json (
    for /f "tokens=2 delims=:, " %%p in ('findstr "app_port" config\facility_config.json') do (
        set /a APP_PORT=%%p 2>nul
    )
)

:: Pre-flight nhanh (chỉ check port)
venv\Scripts\python -c "import socket; s=socket.socket(); s.settimeout(1); r=s.connect_ex(('127.0.0.1',%APP_PORT%)); s.close(); exit(0 if r!=0 else 1)" >nul 2>&1
if errorlevel 1 (
    echo   [WARN] Port %APP_PORT% đang bị chiếm.
    echo   Có thể app đã chạy. Mở: http://localhost:%APP_PORT%
    start http://localhost:%APP_PORT%
    pause & exit /b 0
)

echo   Đang khởi động tại http://localhost:%APP_PORT% ...
echo   (Nhấn Ctrl+C để tắt)
echo.

:: Tự động mở browser sau 3 giây
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:%APP_PORT%"

:: Chạy app
venv\Scripts\python app.py

echo.
echo   MediVoice VN đã tắt.
pause
