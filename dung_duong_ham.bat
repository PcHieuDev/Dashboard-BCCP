@echo off
chcp 65001 > nul
:: Tu dong yeu cau quyen Administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :admin
) else (
    echo Dang yeu cau quyen quan tri...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:admin
echo ==================================================
echo   DUNG DUONG HAM CLOUDFLARE (OFFLINE)
echo ==================================================
echo.
net stop cloudflared
echo.
echo Duong ham da duoc TAM DUNG. May tinh se khong nhan yeu cau tu domain nua.
echo.
pause
