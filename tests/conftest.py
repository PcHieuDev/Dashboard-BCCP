import pytest
import sqlite3
import pandas as pd
from pathlib import Path
import tempfile
import os

@pytest.fixture(scope="session")
def mock_db():
    """
    Fixture tạo ra một in-memory SQLite database dùng chung cho toàn bộ các bài test.
    Khởi tạo cấu trúc bảng cơ bản.
    """
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    
    # Tạo schema cơ bản để test
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS dim_buucuc (
            ma_buu_cuc TEXT PRIMARY KEY,
            ten_buu_cuc TEXT,
            ma_bdx TEXT,
            ten_bdx TEXT,
            ten_cum TEXT
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_buu_cuc TEXT,
            tong_dt REAL,
            nam_du_lieu INTEGER
        );
        CREATE TABLE IF NOT EXISTS agg_monthly (
            nam INTEGER,
            thang INTEGER,
            ma_buu_cuc TEXT,
            tong_dt REAL
        );
    """)
    
    # Chèn dữ liệu mẫu
    conn.execute("INSERT INTO dim_buucuc (ma_buu_cuc, ten_buu_cuc, ma_bdx, ten_bdx, ten_cum) VALUES ('123456', 'BC Test', '1234', 'Xã Test', 'Cụm Test')")
    conn.execute("INSERT INTO transactions (ma_buu_cuc, tong_dt, nam_du_lieu) VALUES ('123456', 1000.0, 2026)")
    conn.commit()
    
    yield conn
    conn.close()
