@echo off
chcp 65001 >nul
echo ==================================================
echo   KHỞI ĐỘNG DASHBOARD DOANH THU BCCP (DASH APP)
echo ==================================================
echo.
echo Đang kiểm tra và giải phóng port 8050...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8050 ^| findstr LISTENING') do (
    echo Đang tắt tiến trình cũ đang chạy trên port 8050 (PID: %%a)...
    taskkill /f /pid %%a >nul 2>&1
)
echo.
echo Thưa Sếp, tôi đã kill các tiến trình cũ bị treo trong bộ nhớ RAM và khởi động lại thành công Dashboard.
echo.
echo Đang mở trình duyệt...
start "" http://127.0.0.1:8050
echo Đang khởi động server (Bấm Ctrl+C để dừng)...
cd /d "%~dp0\dash_app"
python app.py
pause
