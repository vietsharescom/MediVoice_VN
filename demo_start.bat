@echo off
chcp 65001 >nul
setlocal

echo =====================================================
echo   MediVoice VN — Demo App (Streamlit + Global URL)
echo =====================================================
echo.

:: Kiểm tra venv
if not exist venv\Scripts\python.exe (
    echo   [FAIL] Chua cai dat. Chay install.bat truoc.
    pause & exit /b 1
)

:: Kiểm tra Streamlit
venv\Scripts\python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo   [INFO] Cai streamlit...
    venv\Scripts\pip install streamlit requests --quiet
)

:: Kiểm tra localtunnel (Node.js)
node --version >nul 2>&1
if errorlevel 1 (
    echo   [WARN] Node.js khong co - chi co localhost, khong co global URL
    echo.
    goto :start_local_only
)

echo   Khoi dong Streamlit + Tunnel...
echo.

:: Start Streamlit in background
start /b "" venv\Scripts\streamlit run demo\app.py --server.port 8501 --server.headless true --server.address 0.0.0.0

:: Wait for Streamlit to start
echo   Cho Streamlit khoi dong (5 giay)...
timeout /t 5 /nobreak >nul

:: Start localtunnel and capture URL
echo   Tao tunnel (co the mat 10-15 giay)...
for /f "tokens=*" %%u in ('npx --yes localtunnel --port 8501 2^>^&1') do (
    echo %%u | findstr /C:"your url" >nul
    if not errorlevel 1 (
        set LT_URL=%%u
        goto :show_urls
    )
)

:show_urls
echo.
echo =====================================================
echo   LOCAL:  http://localhost:8501
echo   GLOBAL: %LT_URL%
echo.
echo   Luu y global URL:
echo   - Lan dau mo se hoi mat khau = IP may tinh
echo   - Nhan "Click to Continue" tren trang canh bao
echo.
echo   Groq API key: Da co trong .streamlit/secrets.toml
echo.
echo   Nhan Ctrl+C de tat
echo =====================================================
echo.

:: Keep running localtunnel in foreground for display
cmd /k

goto :end

:start_local_only
start /b "" venv\Scripts\streamlit run demo\app.py --server.port 8501 --server.headless true --server.address 0.0.0.0
timeout /t 3 /nobreak >nul
echo   LOCAL: http://localhost:8501
echo   (Cai Node.js de co global URL: nodejs.org/en/download)
start http://localhost:8501
pause

:end
