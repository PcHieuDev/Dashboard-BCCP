# -*- coding: utf-8 -*-
"""
Module etl/backup.py - Tu dong va thu cong sao luu CSDL SQLite an toan.
"""
import os
import sqlite3
import shutil
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def backup_database(db_path, backup_dir=None):
    """
    Sao lưu cơ sở dữ liệu SQLite một cách an toàn bằng API sqlite3.Connection.backup().
    Phương thức này an toàn tuyệt đối ngay cả khi CSDL đang mở đọc.
    """
    if not os.path.exists(db_path):
        logger.error(f"[Backup] Khong tim thay file DB de sao luu: {db_path}")
        return False
        
    if backup_dir is None:
        # Mac dinh tao thu muc backups cung cap voi file DB
        backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
        
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        # Dat ten file backup dang: dashboard_backup_YYYYMMDD_HHMMSS.db
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"dashboard_backup_{date_str}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        logger.info(f"[Backup] Dang thuc hien sao luu an toan {db_path} -> {backup_path}...")
        
        # Ket noi nguon va dich
        src_conn = sqlite3.connect(db_path)
        dst_conn = sqlite3.connect(backup_path)
        
        # Su dung API SQLite Backup an toan cap page
        with dst_conn:
            src_conn.backup(dst_conn)
            
        dst_conn.close()
        src_conn.close()
        
        # Don dep cac ban backup cu hon 30 ngay
        clean_old_backups(backup_dir, keep_days=30)
        
        logger.info("[Backup] Sao luu CSDL hoan tat thanh cong.")
        return backup_path
    except Exception as e:
        logger.error(f"[Backup] Gap su co khi thuc hien sao luu CSDL: {e}", exc_info=True)
        return False

def clean_old_backups(backup_dir, keep_days=30):
    """
    Xóa các file backup cũ hơn keep_days ngày để bao ve o dia dung luong.
    """
    import time
    now = time.time()
    cutoff = now - (keep_days * 86400)
    
    try:
        for filename in os.listdir(backup_dir):
            if filename.startswith("dashboard_backup_") and filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                if os.path.isfile(filepath):
                    file_mtime = os.path.getmtime(filepath)
                    if file_mtime < cutoff:
                        os.remove(filepath)
                        logger.info(f"[Backup] Da xoa ban backup het han: {filename}")
    except Exception as e:
        logger.warning(f"[Backup] Loi khi don dep ban backup cu: {e}")

def run_backup_by_schedule(db_path):
    """
    Kiem tra va thuc hien tu dong backup cuoi ngay neu chua lam.
    Goi y chay cuoi ngay (tu 17:00 tro di).
    """
    now = datetime.now()
    # Chỉ tự động chạy từ 17:00 đến 23:59
    if now.hour >= 17:
        backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Tim kiem xem hom nay da co ban backup nao chua (dang dashboard_backup_YYYYMMDD_*.db)
        today_prefix = f"dashboard_backup_{now.strftime('%Y%m%d')}"
        today_backups = [f for f in os.listdir(backup_dir) if f.startswith(today_prefix)]
        
        if not today_backups:
            logger.info(f"[Auto-Backup] Phat hien chua co ban backup cuoi ngay hom nay ({now.strftime('%d/%m/%Y')}). Dang tu dong sao luu...")
            backup_database(db_path, backup_dir)
            return True
    return False
