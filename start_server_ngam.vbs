Set WshShell = CreateObject("WScript.Shell")
' Chuyển hướng về đúng thư mục dự án
WshShell.CurrentDirectory = "D:\Dashboard-BCCP"
' Chạy lệnh bằng pythonw để hoàn toàn tàng hình, số 0 nghĩa là ẩn cửa sổ
WshShell.Run "pythonw wsgi.py", 0, False
