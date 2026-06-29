import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dash_app'))

from waitress import serve
from app import app

if __name__ == '__main__':
    print("Starting production server with Waitress on http://0.0.0.0:8050...")
    # Lắng nghe trên tất cả các IP mạng (0.0.0.0) và port 8050
    # Số lượng threads có thể điều chỉnh tùy thuộc vào cấu hình CPU của máy chủ
    serve(app.server, host='0.0.0.0', port=8050, threads=8)
