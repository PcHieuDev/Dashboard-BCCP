@echo off
echo ====================================================
echo   TAI TOAN BO CAC NHANH TU GITHUB VE MAY (PULL ALL)
echo ====================================================
echo.
echo Duong dan thu muc hien tai: %~dp0
cd /d "%~dp0"

:: Lay ten nhanh hien tai de quay lai dung nhanh nay
for /f "tokens=*" %%a in ('git symbolic-ref --short HEAD 2^>nul') do set CURRENT_BRANCH=%%a
if "%CURRENT_BRANCH%"=="" (
    for /f "tokens=*" %%a in ('git rev-parse --short HEAD 2^>nul') do set CURRENT_BRANCH=%%a
)

echo Nhanh hien tai cua Sep: %CURRENT_BRANCH%
echo.

echo 1. Dang tai thong tin moi nhat tu GitHub...
git fetch origin --prune --tags

echo.
echo 2. Dang dong bo va cap nhat tat ca cac nhanh cuc bo...
:: Lap qua tat ca cac nhanh remote tren github (loai tru HEAD)
for /f "tokens=1,2* delims=/" %%a in ('git branch -r ^| findstr /v "origin/HEAD"') do (
    echo   - Dang cap nhat nhanh: %%b
    git checkout %%b 2>nul
    git pull origin %%b 2>nul
)

echo.
echo 3. Dang quay tro lai nhanh ban dau (%CURRENT_BRANCH%)...
git checkout %CURRENT_BRANCH% 2>nul
git pull origin %CURRENT_BRANCH% 2>nul

echo.
echo ====================================================
echo TAI TOAN BO CAC NHANH VA DU LIEU THANH CONG!
echo ====================================================
pause
