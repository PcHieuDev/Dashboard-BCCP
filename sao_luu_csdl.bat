@echo off
chcp 65001 > nul
echo ==================================================
echo         SAO LƯU CƠ SỞ DỮ LIỆU DASHBOARD BCCP
echo ==================================================
echo.
echo Đang thực hiện sao lưu CSDL an toàn...
python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd())); from etl.backup import backup_database; from config.settings import DB_PATH; res = backup_database(str(DB_PATH)); print('>>> BẢN SAO LƯU ĐÃ ĐƯỢC TẠO TẠI:', res) if res else print('>>> LỖI: Không thể sao lưu CSDL.')"
echo.
echo ==================================================
echo Đã hoàn tất quá trình sao lưu!
echo ==================================================
pause
