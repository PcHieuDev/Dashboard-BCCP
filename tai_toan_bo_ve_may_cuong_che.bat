@echo off
color 0C
echo ====================================================
echo   DONG BO CUONG CHE MA NGUON (FORCE SYNC CODE)
echo ====================================================
echo WARNING: Lenh nay se xoa sach cac file code thay doi rieng tren may nay
echo de lay dung 100%% code moi nhat tu may co quan ve.
echo.
pause
echo.
echo Dang dong bo code...
cd /d "%~dp0"
git fetch origin
git reset --hard origin/main
git clean -fd
echo.
echo ====================================================
echo DONG BO CUONG CHE CODE THANH CONG!
echo ====================================================
pause
