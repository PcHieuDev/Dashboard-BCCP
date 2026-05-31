# -*- coding: utf-8 -*-
"""
Callbacks xử lý việc tải lên file Excel dữ liệu doanh thu mới và hiển thị lịch sử nhập liệu.
"""

import base64
import tempfile
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import dash
from dash import Output, Input, State, html, dash_table
import dash_bootstrap_components as dbc
import sys

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH
from etl.importer import import_excel_file
from callbacks.utils import clear_query_cache
from db.connection import clear_db_cache

def get_import_history_layout():
    """
    Truy vấn lịch sử nhập liệu từ bảng import_log và trả về DataTable.
    """
    if not DB_PATH.exists():
        return html.Div("Chưa có cơ sở dữ liệu.")
        
    conn = sqlite3.connect(str(DB_PATH))
    try:
        df_hist = pd.read_sql_query(
            "SELECT id, file_name, row_count, import_time, nam_du_lieu, status, error_message FROM import_log ORDER BY import_time DESC LIMIT 10",
            conn
        )
    except Exception as e:
        return html.Div(f"Lỗi đọc lịch sử import: {e}")
    finally:
        conn.close()
        
    if df_hist.empty:
        return html.Div("Chưa có lịch sử nhập dữ liệu nào.")
        
    columns = [
        {"name": "File", "id": "file_name"},
        {"name": "Thời gian", "id": "import_time"},
        {"name": "Số dòng", "id": "row_count"},
        {"name": "Năm dữ liệu", "id": "nam_du_lieu"},
        {"name": "Trạng thái", "id": "status"}
    ]
    
    # Định dạng các cột để hiển thị đẹp hơn
    df_hist['import_time'] = df_hist['import_time'].apply(lambda x: datetime.fromisoformat(x).strftime('%d/%m/%Y %H:%M') if x else '')
    df_hist['row_count'] = df_hist['row_count'].apply(lambda x: f"{x:,}" if pd.notna(x) else '0')
    
    table = dash_table.DataTable(
        columns=columns,
        data=df_hist.to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_header={
            'backgroundColor': '#F8FAFC',
            'fontWeight': 'bold',
            'fontSize': '12px'
        },
        style_cell={
            'padding': '6px 8px',
            'fontSize': '12px',
            'textAlign': 'left'
        }
    )
    return table


def register_import_callbacks(app):
    """
    Đăng ký các callback liên quan đến nạp dữ liệu với ứng dụng Dash.
    """
    
    # 1. Callback hiển thị lịch sử nhập liệu (gọi lúc load Tab hoặc sau khi nạp xong)
    @app.callback(
        Output('import-history-container', 'children'),
        [Input('tabs-navigation', 'value'),
         Input('upload-status-message', 'children')]
    )
    def render_import_history(tab_val, upload_msg):
        if tab_val != "tab-import":
            return dash.no_update
        return get_import_history_layout()

    # 2. Callback tiếp nhận file Excel, ghi tạm và import vào DB
    @app.callback(
        Output('upload-status-message', 'children'),
        [Input('upload-data', 'contents')],
        [State('upload-data', 'filename')]
    )
    def process_uploaded_file(contents, filename):
        if contents is None:
            return ""
            
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Ghi file tạm ra đĩa
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp.write(decoded)
            tmp_path = tmp.name
            
        try:
            # Gọi hàm import dữ liệu từ ETL engine
            # DB_PATH là database SQLite, tmp_path là đường dẫn tệp Excel tạm
            res = import_excel_file(str(DB_PATH), tmp_path)
            
            # Xóa file tạm ngay sau khi chạy xong
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
                
            inserted = res.get('inserted', 0)
            skipped = res.get('skipped', 0)
            warnings = res.get('warnings', [])
            
            # Xóa cache query ở cả 2 tầng (Query cache & DB cache) do dữ liệu đã cập nhật
            clear_query_cache()
            clear_db_cache()
            
            msg = f"✅ Nạp dữ liệu thành công! Đã thêm {inserted:,} dòng (bỏ qua {skipped:,} dòng trùng lặp) từ file '{filename}'."
            if warnings:
                msg += f" (Cảnh báo: {', '.join(warnings[:3])})"
            return dbc.Alert(msg, color="success")
                
        except Exception as e:
            # Đảm bảo xóa file tạm nếu có lỗi xảy ra
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
            return dbc.Alert(f"❌ Lỗi hệ thống khi xử lý file: {str(e)}", color="danger")
