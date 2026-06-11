@echo off
chcp 65001 >nul
echo ----------------------------------------------------
echo BẮT ĐẦU CHẠY KIỂM THỬ (PYTEST)
echo ----------------------------------------------------
pytest tests/ -v
echo.
echo ----------------------------------------------------
echo ĐÃ HOÀN TẤT. BẤM PHÍM BẤT KỲ ĐỂ THOÁT.
pause
