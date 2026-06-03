@echo off
chcp 65001 > nul
echo ====================================================
echo   ĐỒNG BỘ TOÀN BỘ CÁC NHÁNH LÊN GITHUB (PUSH ALL)
echo ====================================================
echo.
echo Đường dẫn thư mục hiện tại: %~dp0
cd /d "%~dp0"

echo.
echo Đang đẩy tất cả các nhánh cục bộ lên GitHub...
git push origin --all

echo.
echo Đang đẩy tất cả các thẻ (tags) lên GitHub...
git push origin --tags

echo.
echo ====================================================
echo ĐỒNG BỘ LÊN GITHUB THÀNH CÔNG!
echo ====================================================
pause
