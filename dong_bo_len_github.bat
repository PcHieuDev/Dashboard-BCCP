@echo off
echo ====================================================
echo   DONG BO TOAN BO CAC NHANH LEN GITHUB (PUSH ALL)
echo ====================================================
echo.
echo Duong dan thu muc hien tai: %~dp0
cd /d "%~dp0"

echo.
echo Dang day tat ca cac nhanh cuc bo len GitHub...
git push origin --all

echo.
echo Dang day tat ca cac the (tags) len GitHub...
git push origin --tags

echo.
echo ====================================================
echo DONG BO LEN GITHUB THANH CONG!
echo ====================================================
pause
