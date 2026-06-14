import pytest
import sqlite3
import pandas as pd
from etl.aggregator import rebuild_plans_weekly

@pytest.fixture
def temp_db():
    """
    Tạo database tạm thời in-memory để chạy test nhất quán kế hoạch
    """
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Tạo bảng plans và plans_weekly
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        nam INTEGER,
        thang INTEGER,
        ma_buu_cuc TEXT,
        nhom_chinh TEXT,
        nhom_dich_vu TEXT,
        ke_hoach_doanh_thu REAL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plans_weekly (
        nam INTEGER,
        tuan_so INTEGER,
        tuan_bat_dau TEXT,
        tuan_ket_thuc TEXT,
        ma_buu_cuc TEXT,
        nhom_chinh TEXT,
        nhom_dich_vu TEXT,
        ke_hoach_doanh_thu REAL
    )
    """)
    
    # Chèn dữ liệu kế hoạch tháng mẫu cho năm 2026
    # Giả định bưu cục '123456', nhóm chính 'BCCP', nhóm con 'TMĐT'
    # Phân bổ kế hoạch 12 tháng, mỗi tháng 10,000,000đ -> Tổng 120,000,000đ
    test_plans = []
    for month in range(1, 13):
        test_plans.append((2026, month, '123456', 'BCCP', 'TMĐT', 10000000.0))
        test_plans.append((2026, month, '123456', 'BCCP', 'Truyền thống', 5000000.0))
        
    cursor.executemany("""
    INSERT INTO plans (nam, thang, ma_buu_cuc, nhom_chinh, nhom_dich_vu, ke_hoach_doanh_thu)
    VALUES (?, ?, ?, ?, ?, ?)
    """, test_plans)
    
    conn.commit()
    yield conn
    conn.close()

def test_plans_weekly_allocation_consistency(temp_db):
    """
    Kiểm tra xem khi phân bổ kế hoạch tuần (rebuild_plans_weekly)
    tổng kế hoạch tuần của năm 2026 có khớp chính xác tổng kế hoạch tháng năm 2026 không.
    """
    # 1. Tính tổng kế hoạch tháng ban đầu
    cursor = temp_db.cursor()
    cursor.execute("SELECT SUM(ke_hoach_doanh_thu) FROM plans WHERE nam = 2026")
    total_monthly_plan = cursor.fetchone()[0]
    assert total_monthly_plan == 180000000.0 # (10M + 5M) * 12 tháng = 180M
    
    # 2. Chạy hàm rebuild_plans_weekly
    rebuild_plans_weekly(temp_db, 2026)
    
    # 3. Tính tổng kế hoạch tuần sau khi phân bổ
    cursor.execute("SELECT SUM(ke_hoach_doanh_thu) FROM plans_weekly WHERE nam = 2026")
    total_weekly_plan = cursor.fetchone()[0]
    
    # 4. Kiểm tra xem sai số giữa kế hoạch tuần và tháng có cực kỳ nhỏ không (chênh lệch làm tròn float < 0.01đ)
    diff = abs(total_monthly_plan - total_weekly_plan)
    assert diff < 0.01, f"Chênh lệch kế hoạch tuần và tháng quá lớn: {diff}"
    
    # 5. Kiểm tra xem các cột nhom_chinh, nhom_dich_vu có được giữ nguyên không
    cursor.execute("SELECT DISTINCT nhom_dich_vu FROM plans_weekly")
    weekly_services = [row[0] for row in cursor.fetchall()]
    assert set(weekly_services) == {"TMĐT", "Truyền thống"}
