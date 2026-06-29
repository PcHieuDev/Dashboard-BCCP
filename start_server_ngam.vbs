Set WshShell = CreateObject("WScript.Shell")
' Chuyển hướng về đúng thư mục dự án
WshShell.CurrentDirectory = "D:\Dashboard-BCCP"
' Chạy lệnh bằng python (vì WScript.Run với số 0 đã tự động ẩn cửa sổ)
' Có ghi thêm log ra file vbs_error.log để kiểm tra nếu bị lỗi
WshShell.Run "cmd.exe /c python wsgi.py > vbs_error.log 2>&1", 0, False
