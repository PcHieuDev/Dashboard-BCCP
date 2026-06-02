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
from etl.importer import import_any_excel_file
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
        # SELECT đúng tên cột thực tế trong SQLite
        df_hist = pd.read_sql_query(
            "SELECT id, file_name, so_dong_import, created_at, trang_thai, ghi_chu FROM import_log ORDER BY created_at DESC LIMIT 10",
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
        {"name": "Thời gian nhập", "id": "created_at"},
        {"name": "Số dòng đã nhập", "id": "so_dong_import"},
        {"name": "Trạng thái", "id": "trang_thai"},
        {"name": "Ghi chú/Cảnh báo", "id": "ghi_chu"}
    ]
    
    # Định dạng cột Thời gian hiển thị đẹp hơn
    def format_time(x):
        if not x:
            return ""
        try:
            # SQLite created_at mặc định là YYYY-MM-DD HH:MM:SS
            dt = datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d/%m/%Y %H:%M')
        except Exception:
            try:
                return datetime.fromisoformat(x).strftime('%d/%m/%Y %H:%M')
            except Exception:
                return str(x)
                
    df_hist['created_at'] = df_hist['created_at'].apply(format_time)
    df_hist['so_dong_import'] = df_hist['so_dong_import'].apply(lambda x: f"{x:,}" if pd.notna(x) else '0')
    
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
    
    # 1. Callback cập nhật hướng dẫn format file Excel tương ứng theo loại lựa chọn
    @app.callback(
        Output("import-format-instructions", "children"),
        [Input("import-service-type", "value")]
    )
    def update_format_instructions(service_type):
        if service_type == "BCCP":
            return html.Div([
                html.B("📋 Định dạng Giao dịch BCCP: "),
                html.Span("Chấp nhận file Excel RAW (từ CAS) hoặc file mẫu điền tay. Yêu cầu các cột tối thiểu: "),
                html.Code("STT, CMS, Ma_HD, Buu_Cuc, San_Pham, Ngay_CN, San_Luong, Cuoc_TT_Tong.")
            ])
        elif service_type in ["HCC", "TCBC", "PPBL"]:
            service_names = {
                "HCC": "Hành chính công (Chi trả lương hưu, BHXH, BTXH, CSHT, ...)",
                "TCBC": "Tài chính bưu chính (Tiết kiệm, Tín dụng, PTI, BHXH-BHYT, Chuyển tiền, ...)",
                "PPBL": "Phân phối bán lẻ (Hàng bán sỉ, Hàng tiêu dùng bán lẻ)"
            }
            return html.Div([
                html.B(f"📋 Định dạng Giao dịch {service_type}: "),
                html.Span(f"Nạp dữ liệu tổng hợp cho nhóm {service_names[service_type]}. Yêu cầu các cột: "),
                html.Code("Mã bưu cục, Tên dịch vụ con, Sản lượng, Doanh thu, Tháng (dạng T01-T12, tùy chọn).")
            ])
        elif service_type == "PLAN":
            return html.Div([
                html.B("📋 Định dạng Kế hoạch chỉ tiêu: "),
                html.Span("File Excel phân bổ kế hoạch cho các bưu cục. Yêu cầu các cột: "),
                html.Code("Năm, Tháng, Nhóm DV (BCCP/HCC/TCBC/PPBL), Tên DV (nullable), Mã BC, KH Doanh thu, KH Sản lượng.")
            ])
        return ""

    # 2. Callback hiển thị lịch sử nhập liệu (lắng nghe URL pathname hoặc sau khi nạp xong)
    @app.callback(
        Output('import-history-container', 'children'),
        [Input('url', 'pathname'),
         Input('upload-status-message', 'children')]
    )
    def render_import_history(pathname, upload_msg):
        if pathname != "/import":
            return dash.no_update
        return get_import_history_layout()

    # 3. Callback tiếp nhận file Excel, ghi tạm và import vào DB tùy thuộc vào loại dữ liệu chọn
    @app.callback(
        Output('upload-status-message', 'children'),
        [Input('upload-data', 'contents')],
        [State('upload-data', 'filename'),
         State('import-service-type', 'value')]
    )
    def process_uploaded_file(contents, filename, service_type):
        if contents is None:
            return ""
            
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Lấy phần mở rộng của file gốc (.xls hoặc .xlsx)
        suffix = Path(filename).suffix
        if suffix.lower() not in ['.xlsx', '.xls']:
            suffix = '.xlsx' # fallback
            
        # Ghi file tạm ra đĩa
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(decoded)
            tmp_path = tmp.name
            
        try:
            # Điều phối nạp dữ liệu theo loại dịch vụ được chọn
            if service_type == "BCCP":
                res = import_any_excel_file(str(DB_PATH), tmp_path)
                table_name = "Bưu chính chuyển phát (transactions)"
            elif service_type in ["HCC", "TCBC", "PPBL"]:
                from etl.importer import import_service_excel
                res = import_service_excel(str(DB_PATH), tmp_path, service_type)
                table_name = f"Giao dịch {service_type} (transactions_{service_type.lower()})"
            elif service_type == "PLAN":
                from etl.importer import import_plan_excel
                res = import_plan_excel(str(DB_PATH), tmp_path)
                table_name = "Kế hoạch chỉ tiêu (plans)"
            else:
                raise ValueError("Loại dịch vụ nạp không hợp lệ.")
            
            # Xóa file tạm ngay sau khi chạy xong
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
                
            inserted = res.get('inserted', 0)
            skipped = res.get('skipped', 0)
            warnings = res.get('warnings', [])
            
            # Xóa cache query ở cả 2 tầng do dữ liệu đã cập nhật
            clear_query_cache()
            clear_db_cache()
            
            msg = f"✅ Nạp dữ liệu vào bảng {table_name} thành công! Đã xử lý {inserted:,} dòng thực tế từ file '{filename}'."
            if skipped > 0:
                msg += f" (Bỏ qua/Cập nhật {skipped:,} dòng)."
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
