# -*- coding: utf-8 -*-
"""
Script đối chiếu số liệu giữa CSDL SQLite sau khi cập nhật với các file Excel báo cáo gộp V2.
"""

import os
import sys
import glob
import sqlite3
import openpyxl
from pathlib import Path

# Đảm bảo in tiếng Việt chính xác trên Windows Console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DB_PATH = Path(r"E:\z.Database-TTKD-Data\dashboard.db")
EXCEL_DIR = Path(r"E:\OneDrive\TTKD - Công việc hàng ngày\0. KHM, tai ban hang thang\chi-tiet-KH-hopdong-loaidichvu\du-lieu-goc-4.2.4-casreport\ket-qua-gop-tung-thang-new")

def get_db_summary(conn, thang, nam=2026):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(san_luong), SUM(cuoc_tt_tong), SUM(cuoc_tt_gom_vat)
        FROM transactions
        WHERE thang_du_lieu = ? AND nam_du_lieu = ?
    """, (thang, nam))
    res = cursor.fetchone()
    return {
        'san_luong': res[0] or 0,
        'doanh_thu': res[1] or 0.0,
        'doanh_thu_vat': res[2] or 0.0
    }

def get_excel_summary(filepath):
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active
    
    total_rows = 0
    total_sl = 0
    total_dt = 0.0
    total_dt_vat = 0.0
    
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is None:
            continue
        total_rows += 1
        
        # Sản lượng ở cột K (index 10)
        sl = int(row[10]) if len(row) > 10 and row[10] is not None else 0
        
        # Doanh thu chưa VAT ở cột U (index 20)
        dt = float(row[20]) if len(row) > 20 and row[20] is not None else 0.0
        
        # Doanh thu gồm VAT ở cột W (index 22)
        dt_vat = float(row[22]) if len(row) > 22 and row[22] is not None else 0.0
        
        total_sl += sl
        total_dt += dt
        total_dt_vat += dt_vat
        
    wb.close()
    return {
        'total_rows': total_rows,
        'san_luong': total_sl,
        'doanh_thu': total_dt,
        'doanh_thu_vat': total_dt_vat
    }

def main():
    print("=" * 90)
    print("TIẾN TRÌNH ĐỐI CHIẾU SỐ LIỆU: SQLite vs Excel Gộp V2")
    print(f" - Database: {DB_PATH}")
    print(f" - Thư mục Excel V2: {EXCEL_DIR}")
    print("=" * 90)
    
    if not DB_PATH.exists():
        print(f"Lỗi: Không tìm thấy database tại {DB_PATH}")
        sys.exit(1)
        
    if not EXCEL_DIR.exists():
        print(f"Lỗi: Không tìm thấy thư mục Excel V2 tại {EXCEL_DIR}")
        sys.exit(1)
        
    conn = sqlite3.connect(str(DB_PATH))
    
    excel_files = sorted(glob.glob(os.path.join(str(EXCEL_DIR), "T*.xlsx")))
    
    has_error = False
    
    print(f"{'Tháng':<10} | {'Nguồn':<8} | {'Số dòng':<10} | {'Sản Lượng':<15} | {'Doanh Thu (Chưa VAT)':<23} | {'Doanh Thu (Gồm VAT)':<23}")
    print("-" * 105)
    
    for filepath in excel_files:
        filename = os.path.basename(filepath)
        # Tên file dạng: "T1 - Chi-tiet-KH-hopdong-loaidichvu.xlsx"
        thang_num = int(filename.split(" ")[0][1:])
        thang_str = f"T{thang_num:02d}"
        
        # 1. Lấy dữ liệu từ Excel
        ex_data = get_excel_summary(filepath)
        
        # 2. Lấy dữ liệu từ DB
        db_data = get_db_summary(conn, thang_str, 2026)
        
        # In kết quả đối chiếu Excel
        print(f"{thang_str:<10} | {'Excel':<8} | {ex_data['total_rows']:<10} | {ex_data['san_luong']:<15,} | {ex_data['doanh_thu']:<23,.2f} | {ex_data['doanh_thu_vat']:<23,.2f}")
        # In kết quả đối chiếu DB
        print(f"{thang_str:<10} | {'SQLite':<8} | {'N/A':<10} | {db_data['san_luong']:<15,} | {db_data['doanh_thu']:<23,.2f} | {db_data['doanh_thu_vat']:<23,.2f}")
        
        # Tính chênh lệch
        diff_sl = db_data['san_luong'] - ex_data['san_luong']
        diff_dt = db_data['doanh_thu'] - ex_data['doanh_thu']
        diff_dt_vat = db_data['doanh_thu_vat'] - ex_data['doanh_thu_vat']
        
        print(f"{thang_str:<10} | {'Lệch':<8} | {'':<10} | {diff_sl:<15,} | {diff_dt:<23,.2f} | {diff_dt_vat:<23,.2f}")
        
        is_ok = abs(diff_sl) == 0 and abs(diff_dt) < 0.01 and abs(diff_dt_vat) < 0.01
        if is_ok:
            print(f"👉 Kết luận: ✅ KHỚP 100%")
        else:
            print(f"👉 Kết luận: ❌ CÓ SAI LỆCH!")
            has_error = True
            
        print("-" * 105)
        
    conn.close()
    
    print("=" * 90)
    if not has_error:
        print("🎉 TẤT CẢ SỐ LIỆU ĐÃ TRÙNG KHỚP 100% GIỮA DATABASE VÀ EXCEL BÁO CÁO V2!")
    else:
        print("⚠️ CẢNH BÁO: Phát hiện sai lệch số liệu, vui lòng kiểm tra lại log import.")
    print("=" * 90)

if __name__ == "__main__":
    main()
