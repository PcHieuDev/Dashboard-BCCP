# -*- coding: utf-8 -*-
"""
Callbacks xử lý việc tải lên file Excel dữ liệu doanh thu mới và hiển thị lịch sử nhập liệu.
"""

import base64
import threading
import queue
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


def _get_db_connection(db_path):
    conn = sqlite3.connect(str(db_path))
    # Da tat che do vua doc vua ghi (WAL) theo yeu cau cua Sep de tranh loi lock tren OneDrive
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn

def get_import_history_layout():
    """
    Truy vấn lịch sử nhập liệu từ bảng import_log và trả về DataTable.
    """
    if not DB_PATH.exists():
        return html.Div("Chưa có cơ sở dữ liệu.")
        
    conn = _get_db_connection(DB_PATH)
    try:
        # Tăng giới hạn lên 50 dòng gần nhất, chuyển đổi created_at sang giờ địa phương (localtime)
        # Sử dụng alias created_at_local để tránh xung đột với tên cột gốc của bảng
        df_hist = pd.read_sql_query(
            "SELECT id, file_name, so_dong_import, datetime(created_at, 'localtime') as created_at_local, trang_thai, ghi_chu FROM import_log ORDER BY created_at DESC LIMIT 50",
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
        {"name": "Thời gian nhập", "id": "created_at_local"},
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
                
    # Định dạng trạng thái hiển thị bằng tiếng Việt trực quan
    def format_trang_thai(val):
        if not val:
            return ""
        val_upper = str(val).upper()
        if "SUCCESS" in val_upper:
            if "WARNING" in val_upper:
                return "Thành công (Cảnh báo)"
            return "Thành công"
        if "FAIL" in val_upper or "ERROR" in val_upper:
            return "Thất bại/Lỗi"
        return str(val)
        
    df_hist['trang_thai'] = df_hist['trang_thai'].apply(format_trang_thai)
    df_hist['created_at_local'] = df_hist['created_at_local'].apply(format_time)
    df_hist['so_dong_import'] = df_hist['so_dong_import'].apply(lambda x: f"{x:,}" if pd.notna(x) else '0')
    
    table = dash_table.DataTable(
        columns=columns,
        data=df_hist.to_dict('records'),
        page_size=10,
        page_action='native',
        sort_action='native',
        filter_action='native',
        style_table={
            'overflowX': 'auto',
            'overflowY': 'auto',
            'maxHeight': '400px'
        },
        style_header={
            'backgroundColor': '#F8FAFC',
            'fontWeight': 'bold',
            'fontSize': '12px',
            'position': 'sticky',
            'top': 0,
            'zIndex': 999
        },
        style_cell={
            'padding': '8px 10px',
            'fontSize': '12px',
            'textAlign': 'left',
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_cell_conditional=[
            {
                'if': {'column_id': 'file_name'},
                'width': '22%',
                'minWidth': '150px',
                'maxWidth': '220px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'whiteSpace': 'nowrap'
            },
            {
                'if': {'column_id': 'created_at_local'},
                'width': '15%',
                'minWidth': '120px',
            },
            {
                'if': {'column_id': 'so_dong_import'},
                'width': '10%',
                'minWidth': '90px',
            },
            {
                'if': {'column_id': 'trang_thai'},
                'width': '13%',
                'minWidth': '110px',
            },
            {
                'if': {'column_id': 'ghi_chu'},
                'width': '40%',
                'minWidth': '250px',
            }
        ],
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#F8FAFC'
            },
            {
                'if': {
                    'filter_query': '{trang_thai} contains "Thành công"',
                    'column_id': 'trang_thai'
                },
                'color': '#059669',
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'filter_query': '{trang_thai} contains "Thất bại"',
                    'column_id': 'trang_thai'
                },
                'color': '#DC2626',
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'filter_query': '{trang_thai} contains "Lỗi"',
                    'column_id': 'trang_thai'
                },
                'color': '#DC2626',
                'fontWeight': 'bold'
            }
        ]
    )
    return table



# Hàng đợi tác vụ import ngầm
import_task_queue = queue.Queue()

def _create_pending_import_log(db_path, filename, service_type, mode):
    """
    Tạo bản ghi log tạm thời với trạng thái PENDING.
    """
    conn = _get_db_connection(db_path)
    cursor = conn.cursor()
    batch_id = datetime.now().strftime('%Y%m%d_%H%M%S') + f'_{service_type}_' + filename
    if mode == 'overwrite':
        batch_id += '_OVERWRITE'
        
    try:
        cursor.execute("""
            INSERT INTO import_log (batch_id, file_name, thang_du_lieu, so_dong_import, so_dong_trung, trang_thai, ghi_chu)
            VALUES (?, ?, ?, 0, 0, ?, ?)
        """, (batch_id, filename, 'PENDING', 'PENDING', f"Đang xếp hàng chờ xử lý ({'Import sửa chữa' if mode == 'overwrite' else 'Import thường'})..."))
        conn.commit()
    except Exception as e:
        logger.error(f"Lỗi tạo pending log: {e}")
    finally:
        conn.close()
    return batch_id

def _update_import_log_status(db_path, batch_id, status, note, inserted=0, skipped=0):
    """
    Cập nhật trạng thái import_log.
    """
    conn = _get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE import_log 
            SET trang_thai = ?, ghi_chu = ?, so_dong_import = ?, so_dong_trung = ?, created_at = CURRENT_TIMESTAMP
            WHERE batch_id = ?
        """, (status, note, inserted, skipped, batch_id))
        conn.commit()
    except Exception as e:
        logger.error(f"Lỗi cập nhật log: {e}")
    finally:
        conn.close()

def _execute_import_task(db_path, tmp_path, service_type, mode, batch_id):
    """
    Thực thi import dữ liệu theo từng loại dịch vụ và mode.
    """
    from etl.importer import import_any_excel_file, import_service_excel, import_plan_excel
    if service_type == "BCCP":
        res = import_any_excel_file(db_path, tmp_path, import_batch=batch_id, mode=mode)
        try:
            thang_str = res.get('thang')
            if thang_str and batch_id:
                thang = int(thang_str[1:])
                conn_tmp = _get_db_connection(db_path)
                cursor_tmp = conn_tmp.cursor()
                cursor_tmp.execute(
                    "SELECT DISTINCT nam_du_lieu FROM transactions WHERE thang_du_lieu = ? AND import_batch = ? LIMIT 1",
                    (thang_str, batch_id)
                )
                row_nam = cursor_tmp.fetchone()
                conn_tmp.close()
                
                if row_nam and row_nam[0]:
                    nam = int(row_nam[0])
                    from analytics.new_customer_calculator import calculate_new_customers
                    num_new_cust = calculate_new_customers(db_path, nam, thang)
                    res['new_customers_count'] = num_new_cust
        except Exception as ex:
            logger.error(f"Lỗi tính toán KH bán mới trong queue: {ex}")
        return res
    elif service_type == "PHBC":
        # PHBC duoc gop vao import_service_excel (import_phbc_excel da bi xoa 2026-06-24)
        return import_service_excel(db_path, tmp_path, "PHBC", import_batch=batch_id, mode=mode)
    elif service_type in ["HCC", "TCBC", "PPBL", "SERVICES"]:
        # "SERVICES" đại diện cho nạp đè/nạp thường tất cả dịch vụ dịch vụ con HCC/TCBC/PPBL/PHBC
        actual_service = "SERVICES" if service_type == "SERVICES" else service_type
        return import_service_excel(db_path, tmp_path, actual_service, import_batch=batch_id, mode=mode)
    elif service_type == "PLAN":
        return import_plan_excel(db_path, tmp_path, import_batch=batch_id, mode=mode)
    else:
        raise ValueError("Loại dịch vụ không hợp lệ.")

def import_worker():
    """
    Worker chạy nền xử lý hàng đợi import.
    """
    while True:
        task = import_task_queue.get()
        if task is None:
            break
            
        task_id, db_path, tmp_path, service_type, filename, mode = task
        
        # Cập nhật trạng thái sang PROCESSING
        _update_import_log_status(db_path, task_id, "PROCESSING", "Đang xử lý dữ liệu và tự động gộp số liệu...")
        
        # Tự động sao lưu cơ sở dữ liệu dự phòng trước khi nạp dữ liệu thay đổi
        try:
            from etl.backup import backup_database
            backup_database(str(db_path))
        except Exception as e_backup:
            logger.error(f"[Backup] Lỗi khi tạo bản sao lưu trước khi import: {e_backup}")
            
        try:
            res = _execute_import_task(db_path, tmp_path, service_type, mode, task_id)
            
            # Xóa file tạm
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
                
            # Đọc kết quả
            inserted = res.get('inserted', 0)
            skipped = res.get('skipped', 0)
            warnings = res.get('warnings', [])
            
            # Đánh giá lỗi nghiêm trọng (Ví dụ: File hỏng, không đọc được dữ liệu nào)
            if inserted == 0 and warnings:
                err_msg = f"FAILED: Lỗi xử lý file Excel: {', '.join(warnings[:3])}"
                _update_import_log_status(db_path, task_id, "FAILED", err_msg, 0, 0)
            else:
                msg = f"SUCCESS: Đã xử lý {inserted:,} dòng."
                if skipped > 0:
                    msg += f" (Bỏ qua/Cập nhật {skipped:,} dòng)."
                if 'new_customers_count' in res:
                    msg += f" Đã cập nhật KH bán mới ({res['new_customers_count']:,})."
                if warnings:
                    msg += f" (Cảnh báo: {', '.join(warnings[:2])})"
                    
                _update_import_log_status(db_path, task_id, "SUCCESS", msg, inserted, skipped)
            
            # Xóa cache
            clear_query_cache()
            clear_db_cache()
            
        except Exception as e:
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
            err_msg = f"FAILED: Lỗi xử lý file Excel: {str(e)}"
            _update_import_log_status(db_path, task_id, "FAILED", err_msg, 0, 0)
            
        finally:
            import_task_queue.task_done()

# Khởi chạy Worker
worker_thread = threading.Thread(target=import_worker, daemon=True)
worker_thread.start()

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
        elif service_type == "SERVICES":
            return html.Div([
                html.B("📋 Định dạng Dịch vụ khác (HCC, TCBC, PPBL, PHBC): "),
                html.Span("Nạp file mẫu doanh thu dịch vụ khác. Yêu cầu các cột tối thiểu: "),
                html.Code("Mã bưu cục, Tên dịch vụ con (mã viết tắt như CT_LH, TK_TT, B2B, PHBC_DEFAULT...), Sản lượng, Doanh thu."),
                html.Br(),
                html.Small("Hệ thống sẽ tự động tra cứu danh mục và phân loại chính xác dòng dữ liệu vào đúng bảng thô của dịch vụ tương ứng.")
            ])
        elif service_type == "PLAN":
            return html.Div([
                html.B("📋 Định dạng Kế hoạch chỉ tiêu: "),
                html.Span("File Excel phân bổ kế hoạch cho các bưu cục. Yêu cầu các cột: "),
                html.Code("Năm, Nhóm Chính (BCCP/HCC/TCBC/PPBL), Nhóm DV (nullable), Mã BC, KH Doanh thu.")
            ])
        return ""

    # 2. Callback hiển thị lịch sử nhập liệu (lắng nghe URL pathname hoặc sau khi nạp xong qua Store)
    @app.callback(
        Output('import-history-container', 'children'),
        [Input('url', 'pathname'),
         Input('import-status-store', 'data')]
    )
    def render_import_history(pathname, import_status):
        if pathname != "/import":
            return dash.no_update
        return get_import_history_layout()

    # 3. Callback hiển thị thông tin file đã chọn và hiện nút Xác nhận
    @app.callback(
        [Output('selected-file-info', 'children'),
         Output('btn-confirm-upload', 'style')],
        [Input('upload-data', 'contents')],
        [State('upload-data', 'filename')]
    )
    def display_selected_file_info(contents, filename):
        if contents is None:
            return "", {'display': 'none'}
            
        # Hiển thị thông tin file đã chọn một cách trực quan
        file_info = html.Div([
            html.Hr(),
            html.Div([
                html.Span("📄 File đã chọn sẵn sàng: ", style={'fontWeight': 'bold'}),
                html.Span(filename, style={'color': '#0F766E', 'fontWeight': 'bold'})
            ], style={
                'padding': '12px 15px', 
                'backgroundColor': '#F0FDFA', 
                'border': '1px solid #CCFBF1', 
                'borderRadius': '8px',
                'fontSize': '13px'
            })
        ])
        
        btn_style = {
            'marginTop': '15px', 
            'display': 'block', 
            'width': '100%', 
            'fontWeight': 'bold',
            'padding': '10px'
        }
        return file_info, btn_style

    # 4. Callback xử lý khi bấm nút "Xác nhận nạp dữ liệu", nạp vào DB tùy theo service_type và reset ô chọn file
    @app.callback(
        [Output('upload-status-message', 'children'),
         Output('upload-data', 'contents'),
         Output('upload-data', 'filename'),
         Output('import-status-store', 'data')],
        [Input('btn-confirm-upload', 'n_clicks')],
        [State('upload-data', 'contents'),
         State('upload-data', 'filename'),
         State('import-service-type', 'value')],
        prevent_initial_call=True
    )
    def process_confirmed_upload(n_clicks, contents, filename, service_type):
        if n_clicks is None or not contents:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Ghi file tạm
        temp_dir = Path(tempfile.gettempdir()) / "dashboard_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = str(temp_dir / filename)
        with open(tmp_path, "wb") as f:
            f.write(decoded)
            
        # Tạo pending log và đưa vào hàng đợi ngầm
        task_id = _create_pending_import_log(str(DB_PATH), filename, service_type, mode='append')
        import_task_queue.put((task_id, str(DB_PATH), tmp_path, service_type, filename, 'append'))
        
        msg = f"📥 Đã đưa tệp '{filename}' vào hàng đợi xử lý ngầm. Vui lòng theo dõi trạng thái tại bảng Lịch sử nạp bên phải."
        return dbc.Alert(msg, color="info", dismissable=True), None, None, int(datetime.now().timestamp())


    # 4.2 Callback hiển thị thông tin file sửa chữa đã chọn
    @app.callback(
        [Output('selected-file-info-overwrite', 'children'),
         Output('btn-confirm-upload-overwrite', 'style')],
        [Input('upload-data-overwrite', 'contents')],
        [State('upload-data-overwrite', 'filename')]
    )
    def display_selected_file_info_overwrite(contents, filename):
        if contents is None:
            return "", {'display': 'none'}
            
        file_info = html.Div([
            html.Hr(),
            html.Div([
                html.Span("🚨 File sửa chữa đã chọn: ", style={'fontWeight': 'bold', 'color': '#DC2626'}),
                html.Span(filename, style={'color': '#B91C1C', 'fontWeight': 'bold'})
            ], style={
                'padding': '12px 15px', 
                'backgroundColor': '#FEF2F2', 
                'border': '1px solid #FCA5A5', 
                'borderRadius': '8px',
                'fontSize': '13px'
            })
        ])
        
        btn_style = {
            'marginTop': '15px', 
            'display': 'block', 
            'width': '100%', 
            'fontWeight': 'bold',
            'padding': '10px'
        }
        return file_info, btn_style

    # 4.3 Callback xử lý khi bấm nút "Xác nhận ghi đè dữ liệu sửa chữa"
    @app.callback(
        [Output('upload-status-message-overwrite', 'children'),
         Output('upload-data-overwrite', 'contents'),
         Output('upload-data-overwrite', 'filename'),
         Output('import-status-store', 'data')],
        [Input('btn-confirm-upload-overwrite', 'n_clicks')],
        [State('upload-data-overwrite', 'contents'),
         State('upload-data-overwrite', 'filename'),
         State('import-service-type-overwrite', 'value')],
        prevent_initial_call=True
    )
    def process_confirmed_upload_overwrite(n_clicks, contents, filename, service_type):
        if n_clicks is None or not contents:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Ghi file tạm
        temp_dir = Path(tempfile.gettempdir()) / "dashboard_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = str(temp_dir / filename)
        with open(tmp_path, "wb") as f:
            f.write(decoded)
            
        # Tạo pending log và đưa vào hàng đợi ngầm với mode='overwrite'
        task_id = _create_pending_import_log(str(DB_PATH), filename, service_type, mode='overwrite')
        import_task_queue.put((task_id, str(DB_PATH), tmp_path, service_type, filename, 'overwrite'))
        
        msg = f"🚨 Đã đưa tệp sửa chữa '{filename}' vào hàng đợi xử lý đè dữ liệu. Vui lòng xem kết quả tại bảng Lịch sử nạp bên phải."
        return dbc.Alert(msg, color="danger", dismissable=True), None, None, int(datetime.now().timestamp())

    # 5. Callback xử lý kéo thả tải file CSV mapping mới
    @app.callback(
        [Output("csv-file-info", "children"),
         Output("btn-sync-mapping", "disabled")],
        [Input("upload-csv-mapping", "contents")],
        [State("upload-csv-mapping", "filename")],
        prevent_initial_call=True
    )
    def process_csv_upload(contents, filename):
        if contents is None:
            return "", True
            
        if not filename.lower().endswith('.csv'):
            return dbc.Alert("❌ Chỉ chấp nhận tệp định dạng CSV (.csv)!", color="danger"), True
            
        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            
            # 1. Đọc thử file CSV để kiểm tra cấu trúc cột (hỗ trợ cả dấu phẩy và dấu chấm phẩy)
            import io
            df_test = None
            for sep in [",", ";"]:
                for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
                    try:
                        df_test_temp = pd.read_csv(io.BytesIO(decoded), sep=sep, encoding=enc)
                        # Chuẩn hóa tên cột
                        temp_cols = [c.strip().lower() for c in df_test_temp.columns]
                        if "ma_spdv" in temp_cols and "ten_spdv" in temp_cols:
                            df_test = df_test_temp
                            break
                    except Exception:
                        continue
                if df_test is not None:
                    break
                    
            if df_test is None:
                return dbc.Alert("❌ Tệp CSV thiếu cột bắt buộc 'ma_spdv' hoặc 'ten_spdv'! Vui lòng kiểm tra lại cấu trúc file.", color="danger"), True
                
            # Chuẩn hóa tên cột trong file tải lên
            orig_cols = list(df_test.columns)
            norm_map = {}
            for col in orig_cols:
                c_clean = col.strip().lower()
                if c_clean == "ma_spdv":
                    norm_map[col] = "ma_spdv"
                elif c_clean == "ten_spdv":
                    norm_map[col] = "ten_spdv"
                elif c_clean in ["loại dịch vụ", "nhom_dich_vu"]:
                    norm_map[col] = "Loại dịch vụ"
                elif c_clean in ["bk/e", "bk_e"]:
                    norm_map[col] = "BK/E"
            
            df_test = df_test.rename(columns=norm_map)
            
            # Đảm bảo các cột chuẩn tồn tại
            standard_cols = ["ma_spdv", "ten_spdv", "Loại dịch vụ", "BK/E"]
            for col in standard_cols:
                if col not in df_test.columns:
                    df_test[col] = None
            df_test = df_test[standard_cols]
            
            # Đọc file mapping hiện tại nếu có để gộp (tránh ghi đè làm mất dữ liệu cũ)
            dest_path = project_root / "data" / "mapping-spdv.csv"
            df_existing = None
            if dest_path.exists():
                for sep in [";", ","]:
                    for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
                        try:
                            df_exist_temp = pd.read_csv(dest_path, sep=sep, encoding=enc)
                            exist_cols = [c.strip().lower() for c in df_exist_temp.columns]
                            if "ma_spdv" in exist_cols:
                                # Chuẩn hóa cột
                                exist_norm = {}
                                for col in df_exist_temp.columns:
                                    c_clean = col.strip().lower()
                                    if c_clean == "ma_spdv":
                                        exist_norm[col] = "ma_spdv"
                                    elif c_clean == "ten_spdv":
                                        exist_norm[col] = "ten_spdv"
                                    elif c_clean in ["loại dịch vụ", "nhom_dich_vu"]:
                                        exist_norm[col] = "Loại dịch vụ"
                                    elif c_clean in ["bk/e", "bk_e"]:
                                        exist_norm[col] = "BK/E"
                                df_existing = df_exist_temp.rename(columns=exist_norm)
                                break
                        except Exception:
                            continue
                    if df_existing is not None:
                        break
            
            if df_existing is not None:
                for col in standard_cols:
                    if col not in df_existing.columns:
                        df_existing[col] = None
                df_existing = df_existing[standard_cols]
                df_combined = pd.concat([df_existing, df_test], ignore_index=True)
            else:
                df_combined = df_test
                
            # Chuẩn hóa cột ma_spdv để drop trùng lặp chính xác
            df_combined['ma_spdv'] = df_combined['ma_spdv'].astype(str).str.strip()
            df_combined = df_combined.drop_duplicates(subset=["ma_spdv"], keep="last")
            
            # Ghi đè vào data/mapping-spdv.csv dưới dạng chuẩn hóa dấu chấm phẩy và utf-8-sig
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            df_combined.to_csv(dest_path, index=False, sep=";", encoding="utf-8-sig")
                
            num_rows = len(df_test)
            total_rows = len(df_combined)
            success_msg = html.Div([
                html.Span(f"✅ Đã tải lên và gộp thành công: ", style={"fontWeight": "bold"}),
                html.Span(f"{filename} (thêm/cập nhật {num_rows} dòng). Tổng danh mục hiện tại: {total_rows} dòng. Sẵn sàng đồng bộ.", style={"color": "#0F766E", "fontWeight": "bold"})
            ], style={
                'padding': '8px 12px', 
                'backgroundColor': '#F0FDFA', 
                'border': '1px solid #CCFBF1', 
                'borderRadius': '6px',
                'fontSize': '13px'
            })
            
            return success_msg, False
        except Exception as e:
            return dbc.Alert(f"❌ Lỗi xử lý tệp: {str(e)}", color="danger"), True

    # 4.4 Callback hiển thị thông tin file kế hoạch đã chọn
    @app.callback(
        [Output('selected-file-info-plan', 'children'),
         Output('btn-confirm-upload-plan', 'style')],
        [Input('upload-data-plan', 'contents')],
        [State('upload-data-plan', 'filename')]
    )
    def display_selected_file_info_plan(contents, filename):
        if contents is None:
            return "", {'display': 'none'}
            
        file_info = html.Div([
            html.Hr(),
            html.Div([
                html.Span("🎯 File kế hoạch đã chọn: ", style={'fontWeight': 'bold', 'color': '#0F766E'}),
                html.Span(filename, style={'color': '#0D9488', 'fontWeight': 'bold'})
            ], style={
                'padding': '12px 15px', 
                'backgroundColor': '#F0FDFA', 
                'border': '1px solid #99F6E4', 
                'borderRadius': '8px',
                'fontSize': '13px'
            })
        ])
        
        btn_style = {
            'marginTop': '15px', 
            'display': 'block', 
            'width': '100%', 
            'fontWeight': 'bold',
            'padding': '10px'
        }
        return file_info, btn_style

    # 4.5 Callback xử lý khi bấm nút "🎯 Xác nhận nạp kế hoạch doanh thu"
    @app.callback(
        [Output('upload-status-message-plan', 'children'),
         Output('upload-data-plan', 'contents'),
         Output('upload-data-plan', 'filename'),
         Output('import-status-store', 'data')],
        [Input('btn-confirm-upload-plan', 'n_clicks')],
        [State('upload-data-plan', 'contents'),
         State('upload-data-plan', 'filename')],
        prevent_initial_call=True
    )
    def process_confirmed_upload_plan(n_clicks, contents, filename):
        if n_clicks is None or not contents:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Ghi file tạm
        temp_dir = Path(tempfile.gettempdir()) / "dashboard_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = str(temp_dir / filename)
        with open(tmp_path, "wb") as f:
            f.write(decoded)
            
        # Tạo pending log và đưa vào hàng đợi ngầm với service_type='PLAN' và mode='append'
        task_id = _create_pending_import_log(str(DB_PATH), filename, 'PLAN', mode='append')
        import_task_queue.put((task_id, str(DB_PATH), tmp_path, 'PLAN', filename, 'append'))
        
        msg = f"🎯 Đã đưa tệp kế hoạch '{filename}' vào hàng đợi xử lý ngầm. Vui lòng xem kết quả tại bảng Lịch sử nạp bên dưới."
        return dbc.Alert(msg, color="info", dismissable=True), None, None, int(datetime.now().timestamp())

    # 6. Callback bấm nút "Đồng bộ danh mục Dịch vụ"
    @app.callback(
        Output("sync-status-message", "children"),
        [Input("btn-sync-mapping", "n_clicks")],
        prevent_initial_call=True
    )
    def process_sync_mapping(n_clicks):
        if n_clicks is None:
            return dash.no_update
            
        import subprocess
        import sys
        
        script_path = str(project_root / "scripts" / "sync_mappings.py")
        try:
            # Chạy đồng bộ qua subprocess
            res = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                cwd=str(project_root),
                timeout=30
            )
            
            if res.returncode == 0:
                # Xóa cache query
                from callbacks.utils import clear_query_cache
                from db.connection import clear_db_cache
                try:
                    from analytics.global_metrics import clear_global_metrics_cache
                    clear_global_metrics_cache()
                except Exception:
                    pass
                clear_query_cache()
                clear_db_cache()
                
                # Tìm số lượng dịch vụ đã đồng bộ trong stdout
                import re
                match = re.search(r"Đồng bộ thành công (\d+) sản phẩm", res.stdout)
                num_svcs = match.group(1) if match else "các"
                
                return dbc.Alert(f"✅ Đồng bộ thành công! Đã cập nhật {num_svcs} dịch vụ vào danh mục.", color="success", dismissable=True)
            else:
                stderr_msg = res.stderr.strip() if res.stderr else "Lỗi không xác định."
                return dbc.Alert(f"❌ Lỗi đồng bộ: {stderr_msg}", color="danger", dismissable=True)
                
        except subprocess.TimeoutExpired:
            return dbc.Alert("❌ Lỗi: Quá trình đồng bộ danh mục bị quá thời gian chờ (timeout > 30s)!", color="danger", dismissable=True)
        except Exception as e:
            return dbc.Alert(f"❌ Lỗi thực thi đồng bộ: {str(e)}", color="danger", dismissable=True)
