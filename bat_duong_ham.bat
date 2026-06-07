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
echo   BAT DUONG HAM CLOUDFLARE (ONLINE)
echo ==================================================
echo.
net start cloudflared
echo.
echo Duong ham da duoc KICH HOAT. May tinh da san sang ket noi.
echo.
pause
