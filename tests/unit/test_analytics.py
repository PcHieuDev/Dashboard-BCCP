import pytest
import pandas as pd
from analytics.global_metrics import get_period_detail_by_xa

# Lưu ý: Các hàm hiện tại trong dự án đang đọc trực tiếp DB_PATH từ config. 
# Trong môi trường test thực tế, ta cần sửa các hàm để nhận `conn` làm tham số (Dependency Injection),
# hoặc monkey-patch `config.settings.DB_PATH` trỏ vào một file db tạm.
# Dưới đây là bài test mẫu giả định.

def test_dummy_analytics():
    """
    Một bài test mẫu kiểm tra phép tính đơn giản, 
    chứng minh hệ thống Pytest đã hoạt động.
    """
    assert 1 + 1 == 2

def test_mock_db_connection(mock_db):
    """
    Kiểm tra xem fixture mock_db có hoạt động và chứa dữ liệu mẫu không.
    """
    df = pd.read_sql_query("SELECT * FROM dim_buucuc", mock_db)
    assert not df.empty
    assert df.iloc[0]['ma_bc'] == '123456'
    assert df.iloc[0]['ten_cum'] == 'Cụm Test'
