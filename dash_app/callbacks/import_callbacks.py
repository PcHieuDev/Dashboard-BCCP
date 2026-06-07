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
            'minWidth': '100px', 'width': '150px', 'maxWidth': '350px',
            'whiteSpace': 'normal',
            'height': 'auto',
        },
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
        elif service_type == "PHBC":
            return dbc.Alert([
                html.Strong("📰 Phát hành báo chí (PHBC)"),
                html.Br(),
                "Yêu cầu các cột: ",
                html.Code("ma_buu_cuc"), ", ",
                html.Code("thang_du_lieu"), " (số 1-12), ",
                html.Code("nam_du_lieu"), ", ",
                html.Code("doanh_thu"),
                html.Br(),
                html.Small("Dữ liệu sẽ được nạp vào bảng transactions_phbc.")
            ], color="warning", className="mt-2")
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
         State('import-service-type', 'value')]
    )
    def process_confirmed_upload(n_clicks, contents, filename, service_type):
        # Kiểm tra xem trigger có phải từ việc click nút hay không và có file hay không
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id != 'btn-confirm-upload' or n_clicks is None or not contents:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
            
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Ghi file tạm ra đĩa giữ nguyên tên gốc của người dùng
        # để khi import ghi nhận vào import_log hiển thị đúng tên file gốc.
        temp_dir = Path(tempfile.gettempdir()) / "dashboard_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = str(temp_dir / filename)
        with open(tmp_path, "wb") as f:
            f.write(decoded)
            
        try:
            # Điều phối nạp dữ liệu theo loại dịch vụ được chọn
            if service_type == "BCCP":
                res = import_any_excel_file(str(DB_PATH), tmp_path)
                table_name = "Bưu chính chuyển phát (transactions)"
                
                # TIP-bccp-002: Tự động tính toán danh sách KH bán mới
                try:
                    thang_str = res.get('thang')
                    batch_id = res.get('batch_id')
                    if thang_str and batch_id:
                        thang = int(thang_str[1:])
                        # Truy vấn nam_du_lieu từ bảng transactions vừa import
                        conn_tmp = sqlite3.connect(str(DB_PATH))
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
                            num_new_cust = calculate_new_customers(str(DB_PATH), nam, thang)
                            res['new_customers_count'] = num_new_cust
                except Exception as ex:
                    print(f"Lỗi khi tự động tính toán KH bán mới: {ex}")
            elif service_type == "PHBC":
                from etl.importer import import_phbc_excel
                res = import_phbc_excel(str(DB_PATH), tmp_path)
                table_name = "Phát hành báo chí (transactions_phbc)"
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
            if 'new_customers_count' in res:
                msg += f" Đã cập nhật danh sách KH bán mới ({res['new_customers_count']:,} khách hàng)."
            if warnings:
                msg += f" (Cảnh báo: {', '.join(warnings[:5])})"
            return dbc.Alert(msg, color="success", dismissable=True), None, None, int(datetime.now().timestamp())
                
        except Exception as e:
            # Đảm bảo xóa file tạm nếu có lỗi xảy ra
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
            return dbc.Alert(f"❌ Lỗi hệ thống khi xử lý file: {str(e)}", color="danger", dismissable=True), None, None, int(datetime.now().timestamp())

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
            
            # Đọc thử file CSV để kiểm tra cấu trúc cột (hỗ trợ cả dấu phẩy và dấu chấm phẩy)
            import io
            df_test = None
            for sep in [",", ";"]:
                for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
                    try:
                        df_test = pd.read_csv(io.BytesIO(decoded), sep=sep, encoding=enc)
                        # Chuẩn hóa tên cột
                        df_test.columns = [c.strip().lower() for c in df_test.columns]
                        if "nhom_chinh" in df_test.columns:
                            break
                    except Exception:
                        continue
                if df_test is not None and "nhom_chinh" in df_test.columns:
                    break
                    
            if df_test is None or "nhom_chinh" not in df_test.columns:
                return dbc.Alert("❌ Tệp CSV thiếu cột bắt buộc 'nhom_chinh'! Vui lòng kiểm tra lại cấu trúc file.", color="danger"), True
                
            # Đọc file mapping hiện tại nếu có để gộp (tránh ghi đè làm mất dữ liệu cũ)
            dest_path = project_root / "data" / "mapping-spdv.csv"
            df_existing = None
            if dest_path.exists():
                for sep in [",", ";"]:
                    for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
                        try:
                            df_existing = pd.read_csv(dest_path, sep=sep, encoding=enc)
                            df_existing.columns = [c.strip().lower() for c in df_existing.columns]
                            if "ma_spdv" in df_existing.columns:
                                break
                        except Exception:
                            continue
                    if df_existing is not None and "ma_spdv" in df_existing.columns:
                        break
            
            # Gộp và loại bỏ trùng lặp dựa trên 'ma_spdv'
            cols = ["nhom_chinh", "ma_spdv", "ten_spdv", "nhom_dich_vu", "ghi_chu"]
            
            # Định dạng và chuẩn hóa df_test
            for col in cols:
                if col not in df_test.columns:
                    df_test[col] = None
            df_test = df_test[cols]
            
            if df_existing is not None:
                for col in cols:
                    if col not in df_existing.columns:
                        df_existing[col] = None
                df_existing = df_existing[cols]
                
                df_combined = pd.concat([df_existing, df_test], ignore_index=True)
            else:
                df_combined = df_test
                
            # Chuẩn hóa cột ma_spdv để drop trùng lặp chính xác
            df_combined['ma_spdv'] = df_combined['ma_spdv'].astype(str).str.strip()
            df_combined = df_combined.drop_duplicates(subset=["ma_spdv"], keep="last")
            
            # Ghi đè vào data/mapping-spdv.csv dưới dạng chuẩn hóa dấu phẩy và utf-8-sig
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            df_combined.to_csv(dest_path, index=False, sep=",", encoding="utf-8-sig")
                
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
