# -*- coding: utf-8 -*-
"""
Module tính toán và lưu trữ danh sách khách hàng mới phát sinh theo từng tháng.
Khách hàng mới (KHM) là khách hàng phát sinh giao dịch trong tháng target
nhưng KHÔNG phát sinh giao dịch nào trong 3 tháng liền trước đó (loại trừ vãng lai).
"""

import sqlite3
import sys
from pathlib import Path

# Đảm bảo in tiếng Việt ra console không bị lỗi trên Windows
sys.stdout.reconfigure(encoding='utf-8')

# Thêm thư mục gốc vào path để import được config
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import DB_PATH

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


def init_db(conn: sqlite3.Connection):
    """
    Khởi tạo bảng new_customers nếu chưa tồn tại.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS new_customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cms TEXT NOT NULL,
            thang INTEGER NOT NULL,
            nam INTEGER NOT NULL,
            buu_cuc TEXT,
            ma_bdx TEXT,
            ten_cum TEXT,
            nhom_dv TEXT,
            tong_doanh_thu REAL DEFAULT 0,
            ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(cms, thang, nam)
        );
    """)
    # Thêm cột ngay_phat_sinh nếu chưa tồn tại
    try:
        cursor.execute("PRAGMA table_info(new_customers)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'ngay_phat_sinh' not in columns:
            cursor.execute("ALTER TABLE new_customers ADD COLUMN ngay_phat_sinh DATE;")
            logger.error("[NewCustomer] Đã ALTER TABLE new_customers thêm cột ngay_phat_sinh.")
    except Exception as e:
        logger.error(f"[NewCustomer] Lỗi kiểm tra/ALTER ngay_phat_sinh: {e}")
    conn.commit()

def calculate_new_customers(db_path: str, nam: int, thang: int) -> int:
    """
    Tính toán danh sách khách hàng mới cho tháng target.
    
    1. Lấy danh sách CMS phát sinh trong tháng target (loại trừ vãng lai).
    2. Lấy danh sách CMS phát sinh trong 3 tháng lookback trước đó.
    3. Tìm hiệu của 2 danh sách -> CMS bán mới.
    4. Xác định các thông tin đi kèm: bưu cục (nhiều nhất), ma_bdx, ten_cum, nhom_dv (đầu tiên), tổng DT.
    5. Xóa dữ liệu cũ của tháng đó và insert mới vào bảng new_customers.
    
    Trả về số lượng khách hàng mới tìm được.
    """
    conn = sqlite3.connect(db_path)
    # Da tat che do vua doc vua ghi (WAL) theo yeu cau cua Sep de tranh loi lock tren OneDrive
    conn.execute("PRAGMA journal_mode=delete;")
    conn.execute("PRAGMA busy_timeout=30000;")
    init_db(conn)
    cursor = conn.cursor()
    
    thang_str = f"T{thang:02d}"
    
    # 1. Tính 3 tháng lookback
    lookback_months = []
    curr_y, curr_m = nam, thang
    for _ in range(3):
        curr_m -= 1
        if curr_m == 0:
            curr_m = 12
            curr_y -= 1
        lookback_months.append((curr_y, f"T{curr_m:02d}"))
        
    # 2. Lấy tất cả CMS target (loại trừ vãng lai) có doanh thu dương (ĐK MỚI)
    cursor.execute("""
        SELECT DISTINCT cms 
        FROM transactions 
        WHERE nam_du_lieu = ? AND thang_du_lieu = ?
          AND cms IS NOT NULL AND cms != '' 
          AND cms NOT LIKE 'VANGLAI_%' AND LOWER(cms) != 'none'
          AND cuoc_tt_tong > 0
    """, (nam, thang_str))
    target_cms = {row[0].strip() for row in cursor.fetchall() if row[0]}
    
    if not target_cms:
        # Xóa dữ liệu cũ nếu tháng target không có giao dịch nào
        cursor.execute("DELETE FROM new_customers WHERE nam = ? AND thang = ?;", (nam, thang))
        conn.commit()
        conn.close()
        logger.error(f"[{thang_str}/{nam}] Không có giao dịch phát sinh.")
        return 0
        
    # 3. Lấy CMS trong 3 tháng lookback có doanh thu dương (ĐK MỚI)
    lookback_cms = set()
    for y, m_str in lookback_months:
        cursor.execute("""
            SELECT DISTINCT cms 
            FROM transactions 
            WHERE nam_du_lieu = ? AND thang_du_lieu = ?
              AND cms IS NOT NULL AND cms != '' 
              AND cms NOT LIKE 'VANGLAI_%' AND LOWER(cms) != 'none'
              AND cuoc_tt_tong > 0
        """, (y, m_str))
        for row in cursor.fetchall():
            if row[0]:
                lookback_cms.add(row[0].strip())
                
    # 4. Xác định CMS bán mới
    new_cms = target_cms - lookback_cms
    
    if not new_cms:
        # Xóa dữ liệu cũ nếu không có CMS mới nào
        cursor.execute("DELETE FROM new_customers WHERE nam = ? AND thang = ?;", (nam, thang))
        conn.commit()
        conn.close()
        logger.error(f"[{thang_str}/{nam}] Không tìm thấy khách hàng bán mới nào.")
        return 0
        
    # 5. Load dim_buucuc vào bộ nhớ để lookup nhanh
    cursor.execute("SELECT ma_bc, ma_bdx, ten_cum FROM dim_buucuc;")
    dim_buucuc_dict = {row[0]: (row[1], row[2]) for row in cursor.fetchall() if row[0]}
    
    new_cms_list = list(new_cms)
    chunk_size = 500
    cms_to_buucuc = {}
    cms_to_nhomdv = {}
    cms_to_revenue = {}
    
    for i in range(0, len(new_cms_list), chunk_size):
        chunk = new_cms_list[i:i+chunk_size]
        placeholders = ",".join(["?"] * len(chunk))
        
        # A. Lấy bưu cục có số lần phát sinh giao dịch nhiều nhất (nếu bằng thì lấy tổng doanh thu cao nhất)
        query_bc = f"""
            WITH cms_bc_counts AS (
                SELECT cms, buu_cuc, COUNT(*) as cnt, SUM(cuoc_tt_tong) as sum_rev,
                       ROW_NUMBER() OVER (PARTITION BY cms ORDER BY COUNT(*) DESC, SUM(cuoc_tt_tong) DESC) as rn
                FROM transactions
                WHERE nam_du_lieu = ? AND thang_du_lieu = ? AND cms IN ({placeholders})
                GROUP BY cms, buu_cuc
            )
            SELECT cms, buu_cuc FROM cms_bc_counts WHERE rn = 1
        """
        cursor.execute(query_bc, [nam, thang_str] + chunk)
        for row in cursor.fetchall():
            cms_to_buucuc[row[0].strip()] = row[1]
            
        # B. Lấy nhóm dịch vụ phát sinh đầu tiên (sắp xếp theo ngày chấp nhận tăng dần, sau đó theo ID dòng tăng dần)
        query_ndv = f"""
            WITH cms_first_tx AS (
                SELECT t.cms, d.nhom_dich_vu,
                       ROW_NUMBER() OVER (PARTITION BY t.cms ORDER BY t.ngay_chap_nhan ASC, t.id ASC) as rn
                FROM transactions t
                JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
                WHERE t.nam_du_lieu = ? AND t.thang_du_lieu = ? AND t.cms IN ({placeholders})
            )
            SELECT cms, nhom_dich_vu FROM cms_first_tx WHERE rn = 1
        """
        cursor.execute(query_ndv, [nam, thang_str] + chunk)
        for row in cursor.fetchall():
            cms_to_nhomdv[row[0].strip()] = row[1]
            
        # C. Tính tổng doanh thu của CMS trong tháng target
        query_rev = f"""
            SELECT cms, SUM(cuoc_tt_tong)
            FROM transactions
            WHERE nam_du_lieu = ? AND thang_du_lieu = ? AND cms IN ({placeholders})
              AND cuoc_tt_tong > 0
            GROUP BY cms
        """
        cursor.execute(query_rev, [nam, thang_str] + chunk)
        for row in cursor.fetchall():
            cms_to_revenue[row[0].strip()] = row[1]
            
        # D. Lấy ngày phát sinh (MIN(ngay_chap_nhan)) của từng CMS có doanh thu dương (Yêu cầu mới)
        query_np_sinh = f"""
            SELECT cms, MIN(ngay_chap_nhan)
            FROM transactions
            WHERE nam_du_lieu = ? AND thang_du_lieu = ? AND cms IN ({placeholders})
              AND cuoc_tt_tong > 0
            GROUP BY cms
        """
        cursor.execute(query_np_sinh, [nam, thang_str] + chunk)
        cms_to_ngay_phat_sinh = {}
        for row in cursor.fetchall():
            cms_to_ngay_phat_sinh[row[0].strip()] = row[1]
            
    # 6. Chuẩn bị dữ liệu và Insert vào DB
    # Trước tiên, DELETE dữ liệu cũ để tránh lỗi UNIQUE (cms, thang, nam)
    cursor.execute("DELETE FROM new_customers WHERE nam = ? AND thang = ?;", (nam, thang))
    
    insert_data = []
    for cms in new_cms_list:
        buu_cuc = cms_to_buucuc.get(cms)
        nhom_dv = cms_to_nhomdv.get(cms, "Truyền thống")  # Fallback nếu không map được dịch vụ
        tong_doanh_thu = cms_to_revenue.get(cms, 0.0)
        
        ma_bdx = None
        ten_cum = None
        
        # Tra cứu mã bđx và cụm từ dim_buucuc
        if buu_cuc and buu_cuc in dim_buucuc_dict:
            ma_bdx, ten_cum = dim_buucuc_dict[buu_cuc]
        else:
            # Fallback lấy 4 chữ số đầu của bưu cục làm ma_bdx
            if buu_cuc and len(buu_cuc) >= 4:
                ma_bdx = buu_cuc[:4]
                # Thử tìm tên Cụm tương ứng với ma_bdx này
                for bc_id, (bdx, cum) in dim_buucuc_dict.items():
                    if bdx == ma_bdx:
                        ten_cum = cum
                        break
            if not ten_cum:
                ten_cum = "Khác"
                
        insert_data.append((cms, thang, nam, buu_cuc, ma_bdx, ten_cum, nhom_dv, tong_doanh_thu, cms_to_ngay_phat_sinh.get(cms)))
        
    cursor.executemany("""
        INSERT INTO new_customers (cms, thang, nam, buu_cuc, ma_bdx, ten_cum, nhom_dv, tong_doanh_thu, ngay_phat_sinh)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, insert_data)
    
    conn.commit()
    conn.close()
    
    logger.error(f"[{thang_str}/{nam}] Hoàn thành. Đã tìm thấy và lưu trữ {len(insert_data)} KH bán mới.")
    return len(insert_data)

def populate_historical_new_customers(db_path: str):
    """
    Tính toán dữ liệu lịch sử khách hàng mới từ T10/2025 đến T06/2026.
    """
    logger.error("--- BẮT ĐẦU TÍNH TOÁN DỮ LIỆU LỊCH SỬ KHÁCH HÀNG MỚI (T10/2025 - T06/2026) ---")
    
    # Danh sách các tháng lịch sử cần tính theo thứ tự thời gian
    months = [
        (2025, 10),
        (2025, 11),
        (2025, 12),
        (2026, 1),
        (2026, 2),
        (2026, 3),
        (2026, 4),
        (2026, 5),
        (2026, 6)
    ]
    
    total_added = 0
    for y, m in months:
        logger.error(f"Đang tính cho tháng T{m:02d}/{y}...")
        try:
            count = calculate_new_customers(db_path, y, m)
            total_added += count
        except Exception as e:
            logger.error(f"Lỗi khi tính toán cho tháng T{m:02d}/{y}: {str(e)}")
            
    logger.error(f"--- HOÀN THÀNH. Tổng số dòng khách hàng mới đã thêm: {total_added} ---")

if __name__ == "__main__":
    db_file = str(DB_PATH)
    logger.error(f"Đường dẫn DB: {db_file}")
    
    # 1. Chạy tính toán lịch sử
    populate_historical_new_customers(db_file)
