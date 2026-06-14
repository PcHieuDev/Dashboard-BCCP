# -*- coding: utf-8 -*-
"""
Script cập nhật danh mục dịch vụ HCC, TCBC, PPBL theo yêu cầu điều chỉnh
và tự động sinh lại các file tham chiếu, mapping.
"""

import os
import sqlite3
import pandas as pd

import logging
try:
    from config.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    try:
        from config.logger import get_logger
        logger = get_logger(__name__)
    except ImportError:
        logger = logging.getLogger(__name__)


DB_PATH = r'E:\OneDrive\z.Database-TTKD-Data\dashboard.db'
EXCEL_PATH = r'E:\Projects\worktrees\Dashboard-BCCP\feat-update-services\data\dieu-chinh\dieu_chinh_dichvu.xlsx'
CSV_OUT_PATH = r'E:\Projects\worktrees\Dashboard-BCCP\feat-update-services\data\mapping-spdv.csv'
MA_REF_PATH = r'E:\Projects\worktrees\Dashboard-BCCP\feat-update-services\data\mau-file-import\ma_tham_chieu.xlsx'

def main():
    logger.error("=== BAT DAU CAP NHAT DANH MUC DICH VU & SINH MA THAM CHIEU ===")
    
    if not os.path.exists(EXCEL_PATH):
        logger.error(f"Loi: Khong tim thay file Excel tai {EXCEL_PATH}")
        return
        
    # 1. Đọc file Excel điều chỉnh
    logger.error(f"Dang doc file Excel: {os.path.basename(EXCEL_PATH)}...")
    df_new = pd.read_excel(EXCEL_PATH)
    
    # Chuẩn hóa dữ liệu đầu vào
    df_new['nhom_chinh'] = df_new['nhom_chinh'].astype(str).str.strip()
    df_new['nhom_dich_vu'] = df_new['nhom_dich_vu'].astype(str).str.strip()
    df_new['ma_dich_vu'] = df_new['ma_dich_vu'].astype(str).str.strip()
    df_new['ten_dich_vu'] = df_new['ten_dich_vu'].astype(str).str.strip()
    
    logger.error(f"Tim thay {len(df_new)} dong dich vu can cap nhat.")
    
    # 2. Kết nối CSDL và cập nhật dim_dichvu
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Xóa danh mục cũ của 3 nhóm chính này
        logger.error("Dang xoa cac dong danh muc cu cua HCC, TCBC, PPBL trong dim_dichvu...")
        cursor.execute("DELETE FROM dim_dichvu WHERE nhom_chinh IN ('HCC', 'TCBC', 'PPBL')")
        logger.error(f"Da xoa {cursor.rowcount} dong danh muc cu.")
        
        # Chèn danh mục mới
        logger.error("Dang nap danh muc moi vao dim_dichvu...")
        inserted_count = 0
        for _, row in df_new.iterrows():
            cursor.execute("""
                INSERT INTO dim_dichvu (id, nhom_chinh, ma_dich_vu, ten_dich_vu, nhom_dich_vu)
                VALUES (?, ?, ?, ?, ?)
            """, (
                int(row['id']),
                row['nhom_chinh'],
                row['ma_dich_vu'],
                row['ten_dich_vu'],
                row['nhom_dich_vu']
            ))
            inserted_count += 1
            
        conn.commit()
        logger.error(f"Nap thanh cong {inserted_count} dong danh muc moi vao dim_dichvu.")
        
        # 3. Xuất ra file CSV mapping để đồng bộ Git tracking
        logger.error(f"Dang doc lai toan bo dim_dichvu de xuat ra CSV...")
        df_all = pd.read_sql_query("SELECT id, nhom_chinh, ma_dich_vu, ten_dich_vu, nhom_dich_vu FROM dim_dichvu ORDER BY id", conn)
        df_all.to_csv(CSV_OUT_PATH, index=False, encoding='utf-8')
        logger.error(f"Da xuat va dong bo file mapping tai: {CSV_OUT_PATH}")
        
        # 4. Sinh lại file ma_tham_chieu.xlsx với 3 sheet
        logger.error(f"Dang sinh lai file ma_tham_chieu.xlsx tai: {MA_REF_PATH}...")
        
        # Đọc dữ liệu Danh mục bưu cục
        df_buucuc = pd.read_sql_query("SELECT ma_bc as [Mã bưu cục], ten_buu_cuc as [Tên bưu cục], ten_bdx as [Xã / Phường], ten_cum as [Cụm], ma_bdx as [Mã xã / Phường] FROM dim_buucuc ORDER BY ma_bc", conn)
        
        # Đọc dữ liệu Sản phẩm (BCCP) từ dim_dichvu
        df_spdv = pd.read_sql_query("SELECT ma_dich_vu as [Mã sản phẩm], ten_dich_vu as [Tên sản phẩm], nhom_dich_vu as [Nhóm dịch vụ con] FROM dim_dichvu WHERE nhom_chinh = 'BCCP' ORDER BY ma_dich_vu", conn)
        
        # Định dạng lại bảng Nhóm dịch vụ (dim_dichvu) hiển thị đẹp cho Sếp tra cứu
        df_dichvu_ref = df_all.rename(columns={
            'nhom_chinh': 'Nhóm chính',
            'nhom_dich_vu': 'Nhóm dịch vụ',
            'ma_dich_vu': 'Mã dịch vụ (Dùng nạp file)',
            'ten_dich_vu': 'Tên dịch vụ'
        })[['Nhóm chính', 'Nhóm dịch vụ', 'Mã dịch vụ (Dùng nạp file)', 'Tên dịch vụ']]
        
        # Ghi đè file Excel với 3 sheet
        with pd.ExcelWriter(MA_REF_PATH, engine='openpyxl') as writer:
            df_dichvu_ref.to_excel(writer, sheet_name='Nhóm dịch vụ', index=False)
            df_buucuc.to_excel(writer, sheet_name='Danh mục bưu cục', index=False)
            df_spdv.to_excel(writer, sheet_name='Sản phẩm', index=False)
            
        logger.error("Da sinh va cap nhat thanh cong ma_tham_chieu.xlsx voi 3 sheet moi nhat.")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Co loi xay ra: {e}")
    finally:
        conn.close()
        
    logger.error("=== HOAN THANH CAP NHAT DANH MUC DICH VU & SINH MA THAM CHIEU ===")

if __name__ == '__main__':
    main()
