# -*- coding: utf-8 -*-
"""
Module quản lý kết nối và truy vấn Cơ sở dữ liệu (Database Abstraction Layer).
Hỗ trợ cả SQLite và PostgreSQL thông qua cấu hình môi trường hoặc cấu hình chung.
"""

import os
import sqlite3
import pandas as pd
from pathlib import Path
from functools import lru_cache
import sys

# Thêm thư mục gốc vào sys.path để import cấu hình chung
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH

# Lấy kiểu cơ sở dữ liệu từ cấu hình (Mặc định là sqlite, có thể chuyển postgresql)
DB_TYPE = os.environ.get("DB_TYPE", "sqlite").lower()

class DatabaseManager:
    """
    Class quản lý kết nối và thực thi câu lệnh SQL đến Database.
    Hỗ trợ Context Manager:
        with DatabaseManager() as db:
            df = db.execute_query(sql, params)
    """
    def __init__(self):
        self.conn = None

    def __enter__(self):
        self.get_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_connection(self):
        """
        Khởi tạo và trả về kết nối Database hiện tại.
        Tự động chọn SQLite hoặc PostgreSQL tùy theo cấu hình.
        """
        if self.conn is not None:
            return self.conn

        if DB_TYPE == "postgresql":
            import psycopg2
            # Lấy thông số kết nối PostgreSQL từ biến môi trường
            pg_host = os.environ.get("PGHOST", "localhost")
            pg_port = os.environ.get("PGPORT", "5432")
            pg_user = os.environ.get("PGUSER", "postgres")
            pg_password = os.environ.get("PGPASSWORD", "")
            pg_database = os.environ.get("PGDATABASE", "bccp")
            
            self.conn = psycopg2.connect(
                host=pg_host,
                port=pg_port,
                user=pg_user,
                password=pg_password,
                database=pg_database
            )
        else:
            # Mặc định sử dụng SQLite
            self.conn = sqlite3.connect(str(DB_PATH))
            
        return self.conn

    def execute_query(self, sql: str, params: list | tuple | None = None) -> pd.DataFrame:
        """
        Thực thi câu SQL query (SELECT) và trả về dữ liệu dạng Pandas DataFrame.
        """
        connection = self.get_connection()
        return pd.read_sql_query(sql, connection, params=params)

    def close(self):
        """
        Đóng kết nối cơ sở dữ liệu nếu đang mở.
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None


# Caching layer cho query results nhằm tăng tốc độ tải trang
@lru_cache(maxsize=128)
def _execute_query_cached_raw(sql: str, params_tuple: tuple | None = None) -> str:
    """
    Thực hiện truy vấn và chuyển đổi DataFrame thành JSON String.
    Sử dụng JSON string làm kiểu trả về để lru_cache hoạt động chính xác (tránh lỗi cache object mutable).
    """
    params = list(params_tuple) if params_tuple is not None else None
    with DatabaseManager() as db:
        df = db.execute_query(sql, params)
    return df.to_json(orient='split', date_format='iso')


def execute_query_cached(sql: str, params: list | tuple | None = None) -> pd.DataFrame:
    """
    Hàm tiện ích bọc bên ngoài để lấy dữ liệu có cache dưới dạng DataFrame.
    """
    params_tuple = tuple(params) if params is not None else None
    json_data = _execute_query_cached_raw(sql, params_tuple)
    return pd.read_json(json_data, orient='split')


def clear_db_cache():
    """
    Xóa toàn bộ cache truy vấn database (gọi khi có dữ liệu mới được nạp vào).
    """
    _execute_query_cached_raw.cache_clear()
