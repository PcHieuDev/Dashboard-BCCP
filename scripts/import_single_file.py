# -*- coding: utf-8 -*-
"""
Script nhập dữ liệu từ một file Excel cụ thể (Dữ liệu thô từ CAS hoặc file mẫu điền tay).
Cách chạy:
    python scripts/import_single_file.py "đường_dẫn_đến_file_excel" [--mode append/overwrite] [--thang Txx]
"""

import os
import sys
import sqlite3
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Đảm bảo in tiếng Việt chính xác trên Windows Console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Thêm thư mục gốc vào path để import các module của dự án
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
    
dash_app_dir = project_root / 'dash_app'
if str(dash_app_dir) not in sys.path:
    sys.path.append(str(dash_app_dir))

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("import_single")

from config.settings import DB_PATH
from etl.backup import backup_database
from etl.importer import import_any_excel_file

def _get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=delete;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn

def main():
    parser = argparse.ArgumentParser(description="Nhập dữ liệu từ một file Excel cụ thể vào CSDL.")
    parser.add_argument("excel_path", type=str, help="Đường dẫn tuyệt đối hoặc tương đối đến file Excel.")
    parser.add_argument("--mode", type=str, choices=["append", "overwrite"], default="append", 
                        help="Chế độ nhập liệu: 'append' (bổ sung) hoặc 'overwrite' (ghi đè dữ liệu cũ cùng danh mục/ngày). Mặc định là append.")
    parser.add_argument("--thang", type=str, default=None, 
                        help="Tháng dữ liệu (Ví dụ: T06). Nếu không truyền, hệ thống tự động nhận diện.")
    args = parser.parse_args()

    excel_path = Path(args.excel_path).resolve()
    if not excel_path.exists():
        logger.error(f"❌ Không tìm thấy file Excel tại đường dẫn: {excel_path}")
        sys.exit(1)

    db_path = str(DB_PATH)
    filename = excel_path.name
    logger.info("=" * 80)
    logger.info("BẮT ĐẦU TIẾN TRÌNH NHẬP DỮ LIỆU FILE ĐƠN")
    logger.info(f" - Đường dẫn file: {excel_path}")
    logger.info(f" - Cơ sở dữ liệu: {db_path}")
    logger.info(f" - Chế độ: {args.mode}")
    logger.info(f" - Tháng chỉ định: {args.thang}")
    logger.info("=" * 80)

    # 1. Tạo bản sao lưu dự phòng trước khi thay đổi dữ liệu
    logger.info("Bước 1: Đang tạo bản sao lưu cơ sở dữ liệu...")
    backup_res = backup_database(db_path)
    if backup_res:
        logger.info(f"✅ Bản sao lưu được lưu thành công tại: {backup_res}")
    else:
        logger.warning("⚠️ Không thể tạo bản sao lưu dự phòng. Tiếp tục tiến trình...")

    # 2. Tạo bản ghi log tạm thời (PENDING) trong import_log
    logger.info("Bước 2: Đang đăng ký tác vụ trong lịch sử hệ thống (import_log)...")
    batch_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_BCCP_' + filename
    if args.mode == 'overwrite':
        batch_id += '_OVERWRITE'

    conn = _get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO import_log (batch_id, file_name, thang_du_lieu, so_dong_import, so_dong_trung, trang_thai, ghi_chu)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (batch_id, filename, args.thang or 'AUTO', 'PENDING', f"Đang xử lý thông qua script CLI ({'Ghi đè' if args.mode == 'overwrite' else 'Bổ sung'})..."))
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Không thể tạo bản ghi log trong CSDL: {e}")
    finally:
        conn.close()

    # 3. Tiến hành import file Excel
    logger.info("Bước 3: Đang đọc và import dữ liệu từ file Excel...")
    try:
        res = import_any_excel_file(db_path, str(excel_path), import_batch=batch_id, thang=args.thang, mode=args.mode)
        
        inserted = res.get('inserted', 0)
        skipped = res.get('skipped', 0)
        warnings = res.get('warnings', [])
        thang_str = res.get('thang')

        logger.info(f"   => Nhập liệu hoàn tất: Thành công {inserted} dòng, bỏ qua {skipped} dòng.")
        if warnings:
            logger.warning(f"   => Cảnh báo: {'; '.join(warnings)}")

        # 4. Tính toán khách hàng mới (nếu là BCCP)
        logger.info("Bước 4: Tính toán lại khách hàng mới...")
        new_cust_count = 0
        if thang_str:
            try:
                thang_int = int(thang_str[1:]) if thang_str.startswith('T') else int(thang_str)
                
                # Tìm năm dữ liệu vừa nạp
                conn_tmp = _get_db_connection(db_path)
                cursor_tmp = conn_tmp.cursor()
                cursor_tmp.execute(
                    "SELECT DISTINCT nam_du_lieu FROM transactions WHERE thang_du_lieu = ? AND import_batch = ? LIMIT 1",
                    (thang_str, batch_id)
                )
                row_nam = cursor_tmp.fetchone()
                conn_tmp.close()
                
                if row_nam and row_nam[0]:
                    nam_int = int(row_nam[0])
                    logger.info(f"   => Tính toán khách hàng bán mới cho {thang_str}/{nam_int}...")
                    from analytics.new_customer_calculator import calculate_new_customers
                    new_cust_count = calculate_new_customers(db_path, nam_int, thang_int)
                    logger.info(f"   => Tìm thấy {new_cust_count} khách hàng bán mới.")
            except Exception as ex_cust:
                logger.error(f"❌ Lỗi tính toán khách hàng bán mới: {ex_cust}")

        # 5. Cập nhật trạng thái import_log thành SUCCESS
        msg = f"SUCCESS: Đã xử lý {inserted:,} dòng."
        if skipped > 0:
            msg += f" (Bỏ qua/Cập nhật {skipped:,} dòng)."
        if new_cust_count > 0:
            msg += f" Đã cập nhật KH bán mới ({new_cust_count:,})."
        if warnings:
            msg += f" (Cảnh báo: {', '.join(warnings[:2])})"

        conn = _get_db_connection(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE import_log 
                SET trang_thai = ?, ghi_chu = ?, so_dong_import = ?, so_dong_trung = ?, created_at = CURRENT_TIMESTAMP
                WHERE batch_id = ?
            """, ("SUCCESS", msg, inserted, skipped, batch_id))
            conn.commit()
            logger.info("✅ Đã cập nhật trạng thái import_log thành SUCCESS.")
        except Exception as e:
            logger.error(f"❌ Lỗi cập nhật trạng thái import_log: {e}")
        finally:
            conn.close()

        # 6. Dọn dẹp cache của Dashboard
        logger.info("Bước 5: Dọn dẹp bộ nhớ đệm cache của Dashboard...")
        try:
            from callbacks.utils import clear_query_cache
            from db.connection import clear_db_cache
            from analytics.global_metrics import clear_global_metrics_cache
            clear_query_cache()
            clear_db_cache()
            clear_global_metrics_cache()
            logger.info("🧹 Đã làm sạch bộ nhớ cache của Dashboard thành công.")
        except Exception as ex_cache:
            logger.debug(f"Bỏ qua dọn cache (độc lập): {ex_cache}")

        logger.info("=" * 80)
        logger.info("TIẾN TRÌNH HOÀN TẤT THÀNH CÔNG!")
        logger.info("=" * 80)

    except Exception as err:
        logger.error(f"❌ LỖI NGHIÊM TRỌNG TRONG QUÁ TRÌNH NHẬP DỮ LIỆU: {err}", exc_info=True)
        
        # Cập nhật trạng thái import_log thành FAILED
        conn = _get_db_connection(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE import_log 
                SET trang_thai = ?, ghi_chu = ?, created_at = CURRENT_TIMESTAMP
                WHERE batch_id = ?
            """, ("FAILED", f"FAILED: Lỗi xử lý file Excel: {str(err)}", batch_id))
            conn.commit()
            logger.info("❌ Đã cập nhật trạng thái import_log thành FAILED.")
        except Exception as e:
            logger.error(f"❌ Lỗi cập nhật trạng thái FAILED: {e}")
        finally:
            conn.close()
            
        sys.exit(1)

if __name__ == "__main__":
    main()
