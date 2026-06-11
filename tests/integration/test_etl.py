import pytest
import pandas as pd

def test_dummy_integration():
    """
    Bài test tích hợp mẫu.
    Sau này sẽ viết các kịch bản nạp file Excel vào hàm import_data()
    và kiểm tra kết quả trong DB.
    """
    # Khởi tạo một DataFrame mẫu giống file Excel
    df = pd.DataFrame({
        'Mã BC': ['123456'],
        'Doanh thu': [5000.0]
    })
    assert len(df) == 1
    assert 'Mã BC' in df.columns
