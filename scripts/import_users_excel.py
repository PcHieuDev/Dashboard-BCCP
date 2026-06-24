# -*- coding: utf-8 -*-
"""
Script đọc file Excel danh sách tài khoản và import vào bảng `users`.
Hỗ trợ tự động tạo mật khẩu băm (hashed password) từ mật khẩu gốc trong file.
"""

import sys
import argparse
import pandas as pd
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

# Thêm thư mục gốc vào path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH

def import_users_from_excel(excel_path):
    if not Path(excel_path).exists():
        print(f"Lỗi: Không tìm thấy file {excel_path}")
        return

    if not DB_PATH.exists():
        print(f"Lỗi: Không tìm thấy cơ sở dữ liệu tại {DB_PATH}")
        return

    try:
        # Đọc file Excel
        df = pd.read_excel(excel_path)
        
        # Đảm bảo các cột cần thiết tồn tại
        required_cols = ['username', 'password', 'role']
        for col in required_cols:
            if col not in df.columns:
                print(f"Lỗi: File Excel thiếu cột '{col}'")
                return

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Đảm bảo bảng users tồn tại
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            assigned_cum TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        success_count = 0
        update_count = 0

        for _, row in df.iterrows():
            username = str(row['username']).strip()
            password = str(row['password']).strip()
            role = str(row['role']).strip()
            
            # Xử lý cột assigned_cum nếu có, nếu bỏ trống thì để None
            assigned_cum = None
            if 'assigned_cum' in df.columns and pd.notna(row['assigned_cum']):
                val = str(row['assigned_cum']).strip()
                if val != "":
                    assigned_cum = val

            hashed_pw = generate_password_hash(password)

            try:
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, assigned_cum) VALUES (?, ?, ?, ?)",
                    (username, hashed_pw, role, assigned_cum)
                )
                success_count += 1
            except sqlite3.IntegrityError:
                # Nếu tài khoản đã tồn tại, cập nhật lại mật khẩu và quyền
                cursor.execute(
                    "UPDATE users SET password_hash = ?, role = ?, assigned_cum = ? WHERE username = ?",
                    (hashed_pw, role, assigned_cum, username)
                )
                update_count += 1

        conn.commit()
        print(f"✅ Đã import thành công {success_count} tài khoản mới.")
        print(f"✅ Đã cập nhật {update_count} tài khoản đã tồn tại.")

    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình import: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import danh sách user từ file Excel.")
    parser.add_argument("excel_file", help="Đường dẫn đến file Excel chứa danh sách tài khoản")
    args = parser.parse_args()
    
    import_users_from_excel(args.excel_file)
