# -*- coding: utf-8 -*-
"""
Module ETL Importer - Import dữ liệu từ file Excel (.xlsx) vào SQLite.
"""

import os
import sys
import re
import sqlite3
import logging
from datetime import datetime
import openpyxl
from config.settings import (
    COLUMN_NAMES, ABNORMAL_CMS, EXCEL_DATA_START_ROW, EXCEL_NUM_COLS
)

logger = logging.getLogger(__name__)

# BATCH SIZE cho INSERT
BATCH_SIZE = 5000

def _parse_date(date_str):
    """
    Chuyển đổi ngày từ định dạng dd/mm/yyyy → YYYY-MM-DD (ISO).
    Hỗ trợ cả datetime, pandas.Timestamp, và chuỗi.
    """
    if date_str is None:
        return None
    
    # pandas.Timestamp kế thừa từ datetime    
    if isinstance(date_str, datetime):
        return date_str.strftime('%Y-%m-%d')
    
    # Xử lý pandas Timestamp nếu không bắt được ở trên
    try:
        import pandas as pd
        if isinstance(date_str, pd.Timestamp):
            return date_str.strftime('%Y-%m-%d')
    except ImportError:
        pass
        
    date_str = str(date_str).strip()
    if not date_str:
        return None
        
    # Thử parse dd/mm/yyyy
    try:
        dt = datetime.strptime(date_str, '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass
        
    # Thử parse yyyy-mm-dd (có thể kèm giờ phút giây)
    try:
        dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass
        
    logger.warning(f"Không parse được ngày: '{date_str}'")
    return None

def _detect_month(filename):
    """
    Tự động phát hiện tháng từ tên file Excel (ví dụ T4 -> T04).
    """
    match = re.match(r'^T(\d{1,2})\s*[-_\s]', filename, re.IGNORECASE)
    if match:
        month_num = int(match.group(1))
        if 1 <= month_num <= 12:
            return f'T{month_num:02d}'
            
    # Thử tìm chữ T + số bất kỳ trong tên file
    match_any = re.search(r'[T](\d{1,2})', filename, re.IGNORECASE)
    if match_any:
        month_num = int(match_any.group(1))
        if 1 <= month_num <= 12:
            return f'T{month_num:02d}'
            
    return None

def _safe_float(value):
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def _safe_int(value):
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

def import_excel_file(db_path, excel_path, thang=None):
    """
    Import 1 file Excel (.xlsx) vào SQLite.
    """
    filename = os.path.basename(excel_path)
    logger.info(f"Bắt đầu import file: {filename}")
    
    # Phát hiện tháng
    if thang is None:
        thang = _detect_month(filename)
        if thang is None:
            # Thử thư mục cha
            parent_dir = os.path.basename(os.path.dirname(excel_path))
            thang = _detect_month(parent_dir)
            
    if thang is None:
        thang = "T01"  # Mặc định fallback
        logger.warning(f"Không phát hiện được tháng cho file: {filename}, fallback sang T01")
        
    # Tạo batch_id
    batch_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + filename
    
    # Mở file Excel
    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
    ws = wb.active
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    insert_cols = [
        'thang_du_lieu', 'nam_du_lieu', 'import_batch', 'stt', 'cms', 'ma_hop_dong', 'buu_cuc',
        'san_pham_dv', 'ngay_chap_nhan', 'san_luong',
        'khoi_luong_thuc', 'khoi_luong_tinh_cuoc',
        'cuoc_cb_cp', 'cuoc_cb_gtgt', 'cuoc_cb_cod', 'cuoc_cb_tong',
        'cuoc_tt_cp', 'cuoc_tt_gtgt', 'cuoc_tt_cod', 'cuoc_tt_tong',
        'thue_vat', 'cuoc_tt_gom_vat', 'cuoc_chenh_lech',
        'tien_cod', 'nho_thu_khac'
    ]
    placeholders = ', '.join(['?'] * len(insert_cols))
    col_names_sql = ', '.join(insert_cols)
    insert_sql = f"INSERT OR IGNORE INTO transactions ({col_names_sql}) VALUES ({placeholders})"
    
    total_rows = 0
    inserted = 0
    warnings = []
    batch_buffer = []
    
    for row_idx, row in enumerate(ws.iter_rows(min_row=EXCEL_DATA_START_ROW, 
                                                 max_col=EXCEL_NUM_COLS,
                                                 values_only=True), 
                                    start=EXCEL_DATA_START_ROW):
        # Bỏ qua dòng trống
        if row[0] is None:
            continue
            
        total_rows += 1
        
        stt = _safe_int(row[0])
        cms = str(row[1]).strip() if row[1] is not None and str(row[1]).strip() != '' else None
        ma_hop_dong = str(row[2]).strip() if row[2] is not None and str(row[2]).strip() != '' else None
        buu_cuc = str(row[3]).strip() if row[3] is not None else None
        san_pham_dv = str(row[4]).strip() if row[4] is not None else None
        ngay_chap_nhan = _parse_date(row[5])
        san_luong = _safe_int(row[6])
        khoi_luong_thuc = _safe_float(row[7])
        khoi_luong_tinh_cuoc = _safe_float(row[8])
        cuoc_cb_cp = _safe_float(row[9])
        cuoc_cb_gtgt = _safe_float(row[10])
        cuoc_cb_cod = _safe_float(row[11])
        cuoc_cb_tong = _safe_float(row[12])
        cuoc_tt_cp = _safe_float(row[13])
        cuoc_tt_gtgt = _safe_float(row[14])
        cuoc_tt_cod = _safe_float(row[15])
        cuoc_tt_tong = _safe_float(row[16])
        thue_vat = _safe_float(row[17])
        cuoc_tt_gom_vat = _safe_float(row[18])
        cuoc_chenh_lech = _safe_float(row[19])
        tien_cod = _safe_float(row[20])
        nho_thu_khac = _safe_float(row[21])
        
        # Xử lý CMS vãng lai
        if cms is None:
            if buu_cuc:
                cms = f'VANGLAI_{buu_cuc}'
            else:
                cms = 'VANGLAI_UNKNOWN'
                warnings.append(f"Dòng {row_idx}: CMS null và bưu cục cũng null")
                
        # Cảnh báo CMS bất thường
        if cms in ABNORMAL_CMS:
            warnings.append(f"Dòng {row_idx}: CMS bất thường (tên người): '{cms}'")
            
        # Trích năm từ ngày chấp nhận
        nam = int(ngay_chap_nhan[:4]) if ngay_chap_nhan and len(ngay_chap_nhan) >= 4 else None
        
        row_data = (
            thang, nam, batch_id, stt, cms, ma_hop_dong, buu_cuc,
            san_pham_dv, ngay_chap_nhan, san_luong,
            khoi_luong_thuc, khoi_luong_tinh_cuoc,
            cuoc_cb_cp, cuoc_cb_gtgt, cuoc_cb_cod, cuoc_cb_tong,
            cuoc_tt_cp, cuoc_tt_gtgt, cuoc_tt_cod, cuoc_tt_tong,
            thue_vat, cuoc_tt_gom_vat, cuoc_chenh_lech,
            tien_cod, nho_thu_khac
        )
        batch_buffer.append(row_data)
        
        if len(batch_buffer) >= BATCH_SIZE:
            cursor.executemany(insert_sql, batch_buffer)
            inserted += cursor.rowcount
            conn.commit()
            batch_buffer = []
            
    if batch_buffer:
        cursor.executemany(insert_sql, batch_buffer)
        inserted += cursor.rowcount
        conn.commit()
        
    skipped = total_rows - inserted
    wb.close()
    
    # Kiểm tra thiếu mapping sản phẩm/bưu cục
    missing = check_missing_mappings(db_path)
    if missing['missing_products']:
        warnings.append(f"Mã sản phẩm mới chưa phân nhóm: {', '.join(missing['missing_products'][:3])}")
    if missing['missing_post_offices']:
        warnings.append(f"Mã bưu cục mới chưa phân cụm: {', '.join(missing['missing_post_offices'][:3])}")
        
    # Ghi log import
    ghi_chu = '; '.join(warnings[:5]) if warnings else None
    cursor.execute("""
        INSERT INTO import_log (batch_id, file_name, thang_du_lieu, 
                                so_dong_import, so_dong_trung, trang_thai, ghi_chu)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        batch_id, filename, thang,
        inserted, skipped,
        'SUCCESS' if not warnings else 'SUCCESS_WITH_WARNINGS',
        ghi_chu
    ))
    conn.commit()
    conn.close()
    
    return {
        'batch_id': batch_id,
        'file': filename,
        'thang': thang,
        'total_rows': total_rows,
        'inserted': inserted,
        'skipped': skipped,
        'warnings': warnings
    }

def clean_str_field(val):
    import pandas as pd
    if pd.isna(val):
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        try:
            float(val_str)
            val_str = val_str[:-2]
        except ValueError:
            pass
    return val_str

def import_raw_excel_file(db_path, excel_path, thang=None):
    """
    Import file Excel dữ liệu chi tiết bưu gửi (RAW) từ CAS.
    Sẽ thực hiện đọc, trích xuất dòng, nén dữ liệu (group by) và chèn vào SQLite.
    Tháng dữ liệu được tự động xác định từ ngày chấp nhận của dòng chi tiết đầu tiên.
    Sản lượng = số mã bưu gửi duy nhất (nunique) trong mỗi nhóm.
    """
    import pandas as pd
    import gc
    filename = os.path.basename(excel_path)
    logger.info(f"Bắt đầu import RAW file: {filename}")
        
    batch_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_RAW_' + filename
    
    # 1. Đọc từng sheet để thu thập all_records
    all_records = []
    total_ignored = 0
    warnings = []
    first_date_str = None  # Để phát hiện tháng từ dữ liệu
    
    try:
        xl = pd.ExcelFile(excel_path)
        sheets = xl.sheet_names
        
        current_cms = None
        for sheetname in sheets:
            engine = "openpyxl" if excel_path.endswith(".xlsx") else None
            df = pd.read_excel(excel_path, sheet_name=sheetname, header=None, engine=engine)
            
            start_row = 0
            for idx in range(min(50, len(df))):
                val_a = str(df.iloc[idx, 0]).strip() if pd.notna(df.iloc[idx, 0]) else ""
                if "1. Chi tiết sản lượng phát sinh" in val_a:
                    start_row = idx
                    break
                    
            for idx in range(start_row, len(df)):
                row_vals = df.iloc[idx].tolist()
                if len(row_vals) < 32:
                    total_ignored += 1
                    continue
                    
                val_a = str(row_vals[0]).strip() if pd.notna(row_vals[0]) else ""
                val_b = clean_str_field(row_vals[1])
                val_d = str(row_vals[3]).strip() if pd.notna(row_vals[3]) else ""
                
                # Bỏ qua dòng tiêu đề section
                if "1. Chi tiết sản lượng phát sinh" in val_a or "2. Chi tiết sản lượng điều chỉnh" in val_a:
                    continue
                    
                # Nhận diện dòng group CMS
                if val_a != "" and val_d == "":
                    current_cms = val_b
                    continue
                    
                # Dòng chi tiết bưu gửi
                is_valid_bg = val_d != "" and val_d != "Số hiệu bưu gửi" and not (val_d.startswith("(") and val_d.endswith(")"))
                if is_valid_bg:
                    if current_cms is None:
                        total_ignored += 1
                        continue
                        
                    def get_num(val):
                        if pd.isna(val): return 0.0
                        try: return float(val)
                        except: return 0.0
                    
                    raw_date_val = row_vals[4] if pd.notna(row_vals[4]) else None
                    parsed_date = _parse_date(raw_date_val)
                    
                    # Ghi nhận ngày đầu tiên để xác định tháng dữ liệu
                    if first_date_str is None and parsed_date:
                        first_date_str = parsed_date
                        
                    record = {
                        'CMS': current_cms,
                        'Ma_HD': clean_str_field(row_vals[7]),
                        'Buu_Cuc': clean_str_field(row_vals[5]),
                        'San_Pham': clean_str_field(row_vals[9]),
                        'Ngay_CN': parsed_date,
                        'Ma_BG': val_d,
                        'KL_Thuc': get_num(row_vals[13]),
                        'KL_TinhCuoc': get_num(row_vals[14]),
                        'CB_CP': get_num(row_vals[15]),
                        'CB_GTGT': get_num(row_vals[16]),
                        'CB_COD': get_num(row_vals[17]),
                        'CB_Tong': get_num(row_vals[18]),
                        'TT_CP': get_num(row_vals[19]),
                        'TT_GTGT': get_num(row_vals[20]),
                        'TT_COD': get_num(row_vals[21]),
                        'TT_Tong': get_num(row_vals[22]),
                        'TT_VAT': get_num(row_vals[23]),
                        'TT_TongVAT': get_num(row_vals[24]),
                        'Cuoc_CL': get_num(row_vals[25]),
                        'COD_Tien': get_num(row_vals[30]),
                        'COD_Khac': get_num(row_vals[31])
                    }
                    all_records.append(record)
                else:
                    total_ignored += 1
                    
            del df
            gc.collect()
    except Exception as e:
        logger.error(f"Lỗi xử lý file RAW {filename}: {e}")
        return {'batch_id': batch_id, 'file': filename, 'thang': 'N/A', 'total_rows': 0, 'inserted': 0, 'skipped': 0, 'warnings': [str(e)]}

    if not all_records:
        return {'batch_id': batch_id, 'file': filename, 'thang': 'N/A', 'total_rows': 0, 'inserted': 0, 'skipped': 0, 'warnings': ['Không tìm thấy dữ liệu phát sinh']}

    # Xác định tháng từ ngày chấp nhận dòng đầu tiên (VD: 2026-01-06 → T01)
    if thang is None:
        if first_date_str:
            try:
                month_num = int(first_date_str.split('-')[1])
                thang = f'T{month_num:02d}'
                logger.info(f"Phát hiện tháng từ dữ liệu: {thang} (ngày đầu: {first_date_str})")
            except (IndexError, ValueError):
                thang = "T01"
                warnings.append(f"Không parse được tháng từ ngày '{first_date_str}', fallback T01")
        else:
            thang = "T01"
            warnings.append("Không tìm thấy ngày chấp nhận trong dữ liệu, fallback T01")

    # 2. Gom nhóm — san_luong = nunique(Ma_BG) đảm bảo chỉ đếm số hiệu duy nhất
    df_all = pd.DataFrame(all_records)
    groupby_cols = ['CMS', 'Ma_HD', 'Buu_Cuc', 'San_Pham', 'Ngay_CN']
    agg_dict = {
        'Ma_BG': 'nunique',
        'KL_Thuc': 'sum', 'KL_TinhCuoc': 'sum',
        'CB_CP': 'sum', 'CB_GTGT': 'sum', 'CB_COD': 'sum', 'CB_Tong': 'sum',
        'TT_CP': 'sum', 'TT_GTGT': 'sum', 'TT_COD': 'sum', 'TT_Tong': 'sum',
        'TT_VAT': 'sum', 'TT_TongVAT': 'sum', 'Cuoc_CL': 'sum',
        'COD_Tien': 'sum', 'COD_Khac': 'sum'
    }
    df_grouped = df_all.groupby(groupby_cols, as_index=False).agg(agg_dict)
    
    # 3. Ghi vào SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Trích năm từ tháng (VD: T01 → lấy từ first_date_str)
    nam_du_lieu = int(first_date_str[:4]) if first_date_str and len(first_date_str) >= 4 else None
    
    insert_cols = [
        'thang_du_lieu', 'nam_du_lieu', 'import_batch', 'stt', 'cms', 'ma_hop_dong', 'buu_cuc',
        'san_pham_dv', 'ngay_chap_nhan', 'san_luong',
        'khoi_luong_thuc', 'khoi_luong_tinh_cuoc',
        'cuoc_cb_cp', 'cuoc_cb_gtgt', 'cuoc_cb_cod', 'cuoc_cb_tong',
        'cuoc_tt_cp', 'cuoc_tt_gtgt', 'cuoc_tt_cod', 'cuoc_tt_tong',
        'thue_vat', 'cuoc_tt_gom_vat', 'cuoc_chenh_lech',
        'tien_cod', 'nho_thu_khac'
    ]
    placeholders = ', '.join(['?'] * len(insert_cols))
    insert_sql = f"INSERT OR IGNORE INTO transactions ({', '.join(insert_cols)}) VALUES ({placeholders})"
    
    batch_buffer = []
    inserted = 0
    
    for idx, row in df_grouped.iterrows():
        cms_val = row['CMS'] if pd.notna(row['CMS']) and str(row['CMS']).strip() != '' else f"VANGLAI_{row['Buu_Cuc']}"
        # Chuyển "" → None để khớp với NULL trong DB (SQLite: NULL ≠ "" → sẽ gây duplicate nếu không sửa)
        ma_hd_val = row['Ma_HD'] if row['Ma_HD'] != '' else None

        row_data = (
            thang, nam_du_lieu, batch_id, idx + 1, cms_val, ma_hd_val, row['Buu_Cuc'],
            row['San_Pham'], row['Ngay_CN'], row['Ma_BG'],
            row['KL_Thuc'], row['KL_TinhCuoc'],
            row['CB_CP'], row['CB_GTGT'], row['CB_COD'], row['CB_Tong'],
            row['TT_CP'], row['TT_GTGT'], row['TT_COD'], row['TT_Tong'],
            row['TT_VAT'], row['TT_TongVAT'], row['Cuoc_CL'],
            row['COD_Tien'], row['COD_Khac']
        )
        batch_buffer.append(row_data)
        
        if len(batch_buffer) >= BATCH_SIZE:
            cursor.executemany(insert_sql, batch_buffer)
            inserted += cursor.rowcount
            batch_buffer = []
            
    if batch_buffer:
        cursor.executemany(insert_sql, batch_buffer)
        inserted += cursor.rowcount
        
    # Kiểm tra thiếu mapping sản phẩm/bưu cục
    missing = check_missing_mappings(db_path)
    if missing['missing_products']:
        warnings.append(f"Mã sản phẩm mới chưa phân nhóm: {', '.join(missing['missing_products'][:3])}")
    if missing['missing_post_offices']:
        warnings.append(f"Mã bưu cục mới chưa phân cụm: {', '.join(missing['missing_post_offices'][:3])}")

    # Ghi log
    skipped = len(df_grouped) - inserted
    cursor.execute("""
        INSERT INTO import_log (batch_id, file_name, thang_du_lieu, 
                                so_dong_import, so_dong_trung, trang_thai, ghi_chu)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (batch_id, filename, thang, inserted, skipped, 'SUCCESS_RAW' if not warnings else 'SUCCESS_RAW_WITH_WARNINGS', '; '.join(warnings[:5]) if warnings else None))
    conn.commit()
    conn.close()
    
    return {
        'batch_id': batch_id,
        'file': filename,
        'thang': thang,
        'total_rows': len(df_grouped),
        'inserted': inserted,
        'skipped': skipped,
        'warnings': warnings
    }

def check_missing_mappings(db_path):
    """
    Kiểm tra xem có mã sản phẩm hoặc bưu cục nào trong transactions chưa được định nghĩa trong bảng dim.
    Trả về dict chứa danh sách các mã thiếu.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    missing_sp = []
    missing_bc = []
    
    try:
        # Kiểm tra sản phẩm
        cursor.execute("""
            SELECT DISTINCT t.san_pham_dv 
            FROM transactions t 
            LEFT JOIN dim_spdv d ON t.san_pham_dv = d.ma_spdv 
            WHERE d.ma_spdv IS NULL AND t.san_pham_dv IS NOT NULL AND t.san_pham_dv != ''
        """)
        missing_sp = [r[0] for r in cursor.fetchall()]
        
        # Kiểm tra bưu cục
        cursor.execute("""
            SELECT DISTINCT t.buu_cuc 
            FROM transactions t 
            LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc 
            WHERE b.ma_bc IS NULL AND t.buu_cuc IS NOT NULL AND t.buu_cuc != ''
        """)
        missing_bc = [r[0] for r in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Lỗi khi kiểm tra danh mục chưa phân loại: {e}")
    finally:
        conn.close()
        
    return {
        'missing_products': missing_sp,
        'missing_post_offices': missing_bc
    }

def import_any_excel_file(db_path, excel_path, thang=None):
    """
    Hàm điều phối thông minh: Tự động phân tích cấu trúc file Excel để nhận diện
    đây là file dữ liệu thô (RAW từ CAS) hay file mẫu nén/thủ công (Template).
    Sau đó gọi hàm import tương ứng.
    """
    import pandas as pd
    filename = os.path.basename(excel_path)
    logger.info(f"Phân tích loại file để import: {filename}")
    
    # Xác định engine dựa trên định dạng file
    engine = "openpyxl" if excel_path.endswith(".xlsx") else "xlrd"
    
    try:
        # Đọc sheet đầu tiên (chỉ lấy 50 dòng đầu để phân tích cấu trúc rất nhanh)
        xl = pd.ExcelFile(excel_path, engine=engine)
        sheet_name = xl.sheet_names[0]
        df_sample = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=50, header=None, engine=engine)
        
        # Tìm xem có chứa chuỗi chỉ thị của file RAW CAS không
        is_raw = False
        for idx in range(len(df_sample)):
            val_a = str(df_sample.iloc[idx, 0]).strip() if pd.notna(df_sample.iloc[idx, 0]) else ""
            if "1. Chi tiết sản lượng phát sinh" in val_a:
                is_raw = True
                break
                
        if is_raw:
            logger.info(f"Nhận diện file '{filename}' là dữ liệu thô (RAW) từ CAS. Tiến hành nén và import...")
            return import_raw_excel_file(db_path, excel_path, thang)
        else:
            logger.info(f"Nhận diện file '{filename}' là tệp tin mẫu (Template). Tiến hành import trực tiếp...")
            # Nếu file template là .xls thì openpyxl hiện tại sẽ bị lỗi.
            # Ta có thể báo lỗi thân thiện nếu file template là .xls
            if excel_path.endswith(".xls"):
                raise ValueError("Tệp mẫu điền tay (Template) phải là định dạng .xlsx (Excel mới). Vui lòng lưu tệp mẫu dưới dạng .xlsx và thử lại.")
            return import_excel_file(db_path, excel_path, thang)
            
    except Exception as e:
        logger.error(f"Lỗi phân loại file Excel {filename}: {e}")
        raise

def import_service_excel(db_path, excel_path, service_type, thang=None):
    """
    Import file Excel dữ liệu tổng hợp cho các dịch vụ mới (HCC, TCBC, PPBL).
    Format mong đợi: STT | Mã bưu cục | Tên dịch vụ | Sản lượng | Doanh thu
    """
    import pandas as pd
    filename = os.path.basename(excel_path)
    logger.info(f"Bắt đầu import {service_type}: {filename}")
    
    if thang is None:
        thang = _detect_month(filename)
        if thang is None:
            thang = "T01"
            logger.warning(f"Không phát hiện được tháng cho file: {filename}, fallback sang T01")
            
    # Lấy năm từ batch hoặc lấy mặc định năm nay
    nam_du_lieu = datetime.now().year
            
    batch_id = datetime.now().strftime('%Y%m%d_%H%M%S') + f'_{service_type}_' + filename
    table_name = f"transactions_{service_type.lower()}"
    
    try:
        engine = "openpyxl" if str(excel_path).endswith(".xlsx") else "xlrd"
        df = pd.read_excel(excel_path, engine=engine)
        
        # Nếu DataFrame không có đủ 5 cột thì lấy theo thứ tự: Mã BC, Tên DV, Sản lượng, Doanh thu
        if len(df.columns) < 5:
            return {'batch_id': batch_id, 'file': filename, 'thang': thang, 'total_rows': 0, 'inserted': 0, 'skipped': 0, 'warnings': [f"File không đủ 5 cột cơ bản (STT, Mã BC, Dịch vụ, SL, DT). Số cột: {len(df.columns)}"]}
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        insert_sql = f"""
        INSERT OR IGNORE INTO {table_name} 
        (thang_du_lieu, nam_du_lieu, ma_buu_cuc, ten_dich_vu, san_luong, doanh_thu, import_batch)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        batch_buffer = []
        inserted = 0
        total_rows = 0
        warnings = []
        
        for idx, row in df.iterrows():
            stt_val = row.iloc[0]
            if pd.isna(stt_val) and idx > 0:
                continue # Skip empty rows
                
            total_rows += 1
            ma_bc = clean_str_field(row.iloc[1])
            ten_dv = clean_str_field(row.iloc[2])
            sl = _safe_int(row.iloc[3])
            dt = _safe_float(row.iloc[4])
            
            if not ma_bc:
                warnings.append(f"Dòng {idx+2}: Thiếu mã bưu cục")
                
            batch_buffer.append((thang, nam_du_lieu, ma_bc, ten_dv, sl, dt, batch_id))
            
            if len(batch_buffer) >= BATCH_SIZE:
                cursor.executemany(insert_sql, batch_buffer)
                inserted += cursor.rowcount
                batch_buffer = []
                
        if batch_buffer:
            cursor.executemany(insert_sql, batch_buffer)
            inserted += cursor.rowcount
            
        skipped = total_rows - inserted
        
        # Ghi log
        cursor.execute("""
            INSERT INTO import_log (batch_id, file_name, thang_du_lieu, 
                                    so_dong_import, so_dong_trung, trang_thai, ghi_chu)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (batch_id, filename, thang, inserted, skipped, 'SUCCESS' if not warnings else 'SUCCESS_WITH_WARNINGS', '; '.join(warnings[:5]) if warnings else None))
        
        conn.commit()
        conn.close()
        
        return {
            'batch_id': batch_id,
            'file': filename,
            'thang': thang,
            'total_rows': total_rows,
            'inserted': inserted,
            'skipped': skipped,
            'warnings': warnings
        }
    except Exception as e:
        logger.error(f"Lỗi khi import {service_type}: {e}")
        return {'batch_id': batch_id, 'file': filename, 'thang': thang, 'total_rows': 0, 'inserted': 0, 'skipped': 0, 'warnings': [str(e)]}


def import_plan_excel(db_path, excel_path):
    """
    Import file Excel Kế hoạch vào bảng plans.
    Format mong đợi: Năm | Tháng | Nhóm DV | Tên DV | Mã BC | KH Doanh thu | KH Sản lượng
    """
    import pandas as pd
    filename = os.path.basename(excel_path)
    logger.info(f"Bắt đầu import Kế hoạch: {filename}")
    
    batch_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_PLAN_' + filename
    
    try:
        engine = "openpyxl" if str(excel_path).endswith(".xlsx") else "xlrd"
        df = pd.read_excel(excel_path, engine=engine)
        
        if len(df.columns) < 6:
            return {'batch_id': batch_id, 'file': filename, 'thang': 'N/A', 'total_rows': 0, 'inserted': 0, 'skipped': 0, 'warnings': [f"File Kế hoạch không đủ số cột cơ bản. Số cột: {len(df.columns)}"]}
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        insert_sql = """
        INSERT OR REPLACE INTO plans 
        (nam, thang, nhom_dich_vu, ten_dich_vu, ma_buu_cuc, ke_hoach_doanh_thu, ke_hoach_san_luong)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        batch_buffer = []
        replaced = 0
        total_rows = 0
        warnings = []
        
        valid_groups = {'BCCP', 'HCC', 'TCBC', 'PPBL', 'Hành chính công', 'Tài chính Bưu chính', 'Phân phối bán lẻ'}
        
        for idx, row in df.iterrows():
            nam = _safe_int(row.iloc[0])
            thang = _safe_int(row.iloc[1])
            if nam == 0 or thang == 0:
                continue # Bỏ qua dòng trống
                
            total_rows += 1
            nhom_dv = clean_str_field(row.iloc[2])
            ten_dv = clean_str_field(row.iloc[3]) if len(df.columns) > 3 and pd.notna(row.iloc[3]) else None
            ma_bc = clean_str_field(row.iloc[4]) if len(df.columns) > 4 else None
            kh_dt = _safe_float(row.iloc[5]) if len(df.columns) > 5 else 0.0
            kh_sl = _safe_int(row.iloc[6]) if len(df.columns) > 6 else 0
            
            if nhom_dv not in valid_groups:
                warnings.append(f"Dòng {idx+2}: Nhóm DV không hợp lệ ('{nhom_dv}')")
                continue
                
            if thang < 1 or thang > 12:
                warnings.append(f"Dòng {idx+2}: Tháng không hợp lệ ('{thang}')")
                continue
                
            batch_buffer.append((nam, thang, nhom_dv, ten_dv, ma_bc, kh_dt, kh_sl))
            
            if len(batch_buffer) >= BATCH_SIZE:
                cursor.executemany(insert_sql, batch_buffer)
                replaced += cursor.rowcount
                batch_buffer = []
                
        if batch_buffer:
            cursor.executemany(insert_sql, batch_buffer)
            replaced += cursor.rowcount
            
        skipped = total_rows - replaced
        
        # Ghi log
        cursor.execute("""
            INSERT INTO import_log (batch_id, file_name, thang_du_lieu, 
                                    so_dong_import, so_dong_trung, trang_thai, ghi_chu)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (batch_id, filename, 'PLAN', replaced, skipped, 'SUCCESS' if not warnings else 'SUCCESS_WITH_WARNINGS', '; '.join(warnings[:5]) if warnings else None))
        
        conn.commit()
        conn.close()
        
        return {
            'batch_id': batch_id,
            'file': filename,
            'thang': 'PLAN',
            'total_rows': total_rows,
            'inserted': replaced,
            'skipped': skipped,
            'warnings': warnings
        }
    except Exception as e:
        logger.error(f"Lỗi khi import Kế hoạch: {e}")
        return {'batch_id': batch_id, 'file': filename, 'thang': 'N/A', 'total_rows': 0, 'inserted': 0, 'skipped': 0, 'warnings': [str(e)]}
