@echo off
chcp 65001 > nul
echo ====================================================
echo   TẢI TOÀN BỘ CÁC NHÁNH TỪ GITHUB VỀ MÁY (PULL ALL)
echo ====================================================
echo.
echo Đường dẫn thư mục hiện tại: %~dp0
cd /d "%~dp0"

:: Lấy tên nhánh hiện tại để lát nữa quay lại đúng nhánh này
for /f "tokens=*" %%a in ('git symbolic-ref --short HEAD 2^>nul') do set CURRENT_BRANCH=%%a
if "%CURRENT_BRANCH%"=="" (
    for /f "tokens=*" %%a in ('git rev-parse --short HEAD 2^>nul') do set CURRENT_BRANCH=%%a
)

echo Nhánh hiện tại của Sếp: %CURRENT_BRANCH%
echo.

echo 1. Đang tải thông tin mới nhất từ GitHub...
git fetch origin --prune --tags

echo.
echo 2. Đang đồng bộ và cập nhật tất cả các nhánh cục bộ...
:: Lặp qua tất cả các nhánh remote trên github (loại trừ HEAD)
for /f "tokens=1,2* delims=/" %%a in ('git branch -r ^| findstr /v "origin/HEAD"') do (
    echo   - Đang cập nhật nhánh: %%b
    :: Chuyển sang nhánh đó (nếu chưa có ở máy sẽ tự tạo) và kéo code mới nhất
    git checkout %%b 2>nul
    git pull origin %%b 2>nul
)

echo.
echo 3. Đang quay trở lại nhánh ban đầu (%CURRENT_BRANCH%)...
git checkout %CURRENT_BRANCH% 2>nul
git pull origin %CURRENT_BRANCH% 2>nul

echo.
echo ====================================================
echo TẢI TOÀN BỘ CÁC NHÁNH VÀ DỮ LIỆU THÀNH CÔNG!
echo ====================================================
pause
