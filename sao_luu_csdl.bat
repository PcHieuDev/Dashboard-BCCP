@echo off
chcp 65001 > nul
echo ==================================================
echo         SAO LUU CO SO DU LIEU DASHBOARD BCCP
echo ==================================================
echo.
echo Dang thuc hien sao luu CSDL an toan...
python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd())); from etl.backup import backup_database; from config.settings import DB_PATH; res = backup_database(str(DB_PATH)); print('>>> BAN SAO LUU DA DUOC TAO TAI:', res) if res else print('>>> LOI: Khong the sao luu CSDL.')"
echo.
echo ==================================================
echo Da hoan tat qua trinh sao luu!
echo ==================================================
pause
