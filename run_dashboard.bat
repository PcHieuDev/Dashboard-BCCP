@echo off
echo ==================================================
echo   KHOI DONG DASHBOARD DOANH THU BCCP (DASH APP)
echo ==================================================
echo.
echo Dang mo trinh duyet...
start "" http://127.0.0.1:8050
echo Dang khoi dong server (Bam Ctrl+C de dung)...
cd /d "%~dp0\dash_app"
python app.py
pause
