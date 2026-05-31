# -*- coding: utf-8 -*-
"""
Script khởi tạo bảng `users` và các tài khoản mẫu trong cơ sở dữ liệu SQLite.
Mật khẩu được mã hóa an toàn bằng thư viện `werkzeug.security`.
"""

import sys
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

# Cấu hình UTF-8 cho Windows
sys.stdout.reconfigure(encoding='utf-8')

# Đường dẫn DB
project_root = Path(__file__).resolve().parent.parent
DB_PATH = project_root / 'database' / 'bccp.db'

print(f"Database Path: {DB_PATH}")

def init_users_table():
    if not DB_PATH.exists():
        print(f"Lỗi: Không tìm thấy cơ sở dữ liệu tại {DB_PATH}")
        return
        
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # 1. Tạo bảng users nếu chưa tồn tại
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,         -- 'admin' hoặc 'user'
            assigned_cum TEXT,          -- Tên Cụm (ví dụ: 'TTKD T.Tâm', 'TTKD Hòa Vang'), NULL nếu là admin
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("Đã tạo bảng `users` thành công.")
        
        # 2. Tạo dữ liệu tài khoản mẫu
        users_data = [
            ("admin", "Admin@123", "admin", None),
            ("user_hcm", "User@123", "user", "Diễn Châu"),
            ("user_hoavang", "User@123", "user", "Quỳnh Lưu")
        ]
        
        for username, password, role, assigned_cum in users_data:
            hashed_pw = generate_password_hash(password)
            try:
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, assigned_cum) VALUES (?, ?, ?, ?)",
                    (username, hashed_pw, role, assigned_cum)
                )
                print(f"Đã tạo tài khoản mẫu thành công: {username} (Quyền: {role})")
            except sqlite3.IntegrityError:
                # Nếu tài khoản đã tồn tại, ta cập nhật mật khẩu và thông tin mới
                cursor.execute(
                    "UPDATE users SET password_hash = ?, role = ?, assigned_cum = ? WHERE username = ?",
                    (hashed_pw, role, assigned_cum, username)
                )
                print(f"Đã cập nhật mật khẩu/quyền cho tài khoản: {username}")
                
        conn.commit()
        print("Hoàn tất thiết lập bảng người dùng mẫu!")
        
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    init_users_table()
