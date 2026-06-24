import sqlite3
import uuid
import pandas as pd
import os
import sys

# Đảm bảo có thể import từ config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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


def generate_tokens():
    logger.info(f"Connecting to DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    # Tạo bảng
    conn.execute('''
    CREATE TABLE IF NOT EXISTS access_tokens (
        token TEXT PRIMARY KEY,
        level TEXT,
        value TEXT
    )
    ''')
    
    # Lấy danh sách
    df_cum = pd.read_sql_query("SELECT DISTINCT ten_cum FROM dim_buucuc WHERE ten_cum IS NOT NULL AND ten_cum != ''", conn)
    df_bdx = pd.read_sql_query("SELECT DISTINCT ten_bdx FROM dim_buucuc WHERE ten_bdx IS NOT NULL AND ten_bdx != ''", conn)
    
    tokens = []
    
    # Token cho Cụm
    for c in df_cum['ten_cum']:
        t = uuid.uuid4().hex[:8]
        tokens.append({'Token': t, 'Level': 'cum', 'Value': c})
        
    # Token cho BĐX
    for b in df_bdx['ten_bdx']:
        t = uuid.uuid4().hex[:8]
        tokens.append({'Token': t, 'Level': 'bdx', 'Value': b})
        
    # Xóa dữ liệu cũ và chèn mới
    conn.execute('DELETE FROM access_tokens')
    
    batch_data = [(row['Token'], row['Level'], row['Value']) for row in tokens]
    conn.executemany('INSERT INTO access_tokens (token, level, value) VALUES (?, ?, ?)', batch_data)
    conn.commit()
    
    # Xuất Excel (lưu vào thư mục cùng DB)
    output_path = os.path.join(os.path.dirname(DB_PATH), 'phan_quyen_url.xlsx')
    
    # Tạo URL mẫu cho user dễ hình dung (Đã sửa lại port 8050 của Dash)
    df_out = pd.DataFrame(tokens)
    # LƯU Ý: Nếu server dùng tên miền, bạn có thể thay 'localhost' bằng tên miền của bạn
    # Ví dụ: 'http://dashboard.bdna.io.vn/?token=' hoặc 'http://192.168.1.100:8050/?token='
    domain_or_ip = 'http://localhost:8050'
    df_out['URL Truy Cập'] = domain_or_ip + '/?token=' + df_out['Token']
    df_out.to_excel(output_path, index=False)
    
    logger.info(f"✅ Đã tạo thành công {len(tokens)} token phân quyền!")
    logger.info(f"✅ Đã xuất kết quả ra file: {output_path}")
    
    conn.close()

if __name__ == "__main__":
    generate_tokens()
