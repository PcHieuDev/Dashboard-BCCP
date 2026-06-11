@echo off
chcp 65001 >nul
echo ----------------------------------------------------
echo BẮT ĐẦU KIỂM TRA MÃ NGUỒN (FLAKE8)
echo ----------------------------------------------------
flake8 .
echo.
echo ----------------------------------------------------
echo ĐÃ HOÀN TẤT. BẤM PHÍM BẤT KỲ ĐỂ THOÁT.
pause
