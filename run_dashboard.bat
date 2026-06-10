@echo off
echo ==================================================
echo   KHOI DONG DASHBOARD DOANH THU BCCP (DASH APP)
echo ==================================================
echo.
echo Dang kiem tra va giai phong port 8050...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr 8050') do (
    echo Dang tat tien trinh cu dang chay tren port 8050 [PID: %%a]...
    taskkill /f /pid %%a >nul 2>&1
)
echo.
echo Thua Sep, toi da kill cac tien trinh cu bi treo trong bo nho RAM va khoi dong lai thanh cong Dashboard.
echo.
echo Dang mo trinh duyet...
start "" http://127.0.0.1:8050
echo Dang khoi dong server (Bam Ctrl+C de dung)...
cd /d "%~dp0dash_app"
python app.py
pause
