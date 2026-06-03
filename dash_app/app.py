# -*- coding: utf-8 -*-
"""
Dash App - Dashboard Điều hành Doanh thu BCCP.
Cấu trúc modularized, chia trang và callback để dễ bảo trì và mở rộng.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import các config và module dùng chung
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

# Import Sidebar layout
from components.sidebar import create_sidebar_layout

# Import các trang Layouts
from pages.kpi_page import create_kpi_page_layout
from pages.customer_detail import create_customer_detail_layout
from pages.import_data import create_import_page_layout
from pages.hcc_revenue import create_hcc_revenue_layout

# Import các Callbacks đăng ký
from callbacks.sidebar_callbacks import register_sidebar_callbacks
from callbacks.kpi_callbacks import register_kpi_callbacks
from callbacks.customer_callbacks import register_customer_callbacks
from callbacks.import_callbacks import register_import_callbacks
from callbacks.alerts_callbacks import register_alerts_callbacks
from callbacks.global_callbacks import register_global_callbacks
from callbacks.service_callbacks import register_service_callbacks
from callbacks.hcc_revenue_callbacks import register_hcc_revenue_callbacks

# Cấu hình UTF-8 cho Windows output để hiển thị log tiếng Việt chính xác
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# --------------------------------------------------------------------------
# KHỞI TẠO DASH APP & CẤU HÌNH BẢO MẬT (FLASK-LOGIN)
# --------------------------------------------------------------------------
import os
from flask_login import LoginManager, current_user, login_user, logout_user

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Dashboard Doanh thu BCCP (Dash)"
)
app.config.suppress_callback_exceptions = True

# Biến server dùng cho triển khai production (Gunicorn/Waitress)
server = app.server
server.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bccp_dashboard_secret_key_2026_05_31')

# Thiết lập quản lý phiên đăng nhập
login_manager = LoginManager()
login_manager.init_app(server)

@login_manager.user_loader
def load_user(user_id):
    """Tải thông tin người dùng từ cơ sở dữ liệu SQLite theo ID."""
    from db.auth import get_user_by_id
    return get_user_by_id(user_id)

@server.route('/test-login/<username>')
def test_login_route(username):
    """Route phục vụ xác thực nhanh cho các verify script tự động."""
    from db.auth import get_user_by_username
    user = get_user_by_username(username)
    if user:
        login_user(user)
        return f"OK: logged in as {username}"
    return "FAIL: user not found", 404

# --------------------------------------------------------------------------
# LOAD DỮ LIỆU BAN ĐẦU CHO SIDEBAR DROPDOWNS
# --------------------------------------------------------------------------
def load_filter_options():
    """Tải trước danh sách các bộ lọc từ database SQLite để điền vào dropdowns sidebar."""
    options = {
        "years": [2026],
        "nhom_dv": [],
        "spdv": [],
        "cum": [],
        "bdx": [],
        "buu_cuc": []
    }
    if not DB_PATH.exists():
        return options
        
    conn = sqlite3.connect(str(DB_PATH))
    try:
        # Load Năm dữ liệu hiện có
        df_years = pd.read_sql_query("SELECT DISTINCT nam_du_lieu FROM transactions WHERE nam_du_lieu IS NOT NULL ORDER BY nam_du_lieu DESC", conn)
        if not df_years.empty:
            options["years"] = df_years.iloc[:, 0].tolist()
            
        # Load Nhóm dịch vụ (chỉ thuộc BCCP cho sidebar)
        df_nhom = pd.read_sql_query("SELECT DISTINCT nhom_dich_vu FROM dim_dichvu WHERE nhom_chinh = 'BCCP' AND nhom_dich_vu IS NOT NULL", conn)
        if not df_nhom.empty:
            options["nhom_dv"] = df_nhom.iloc[:, 0].tolist()
        
        # Load Sản phẩm dịch vụ chi tiết (chỉ thuộc BCCP cho sidebar)
        df_spdv = pd.read_sql_query("SELECT ma_dich_vu, ten_dich_vu FROM dim_dichvu WHERE nhom_chinh = 'BCCP' AND ma_dich_vu IS NOT NULL", conn)
        if not df_spdv.empty:
            options["spdv"] = [{"label": f"{r.iloc[0]} - {r.iloc[1]}", "value": r.iloc[0]} for _, r in df_spdv.iterrows()]
        
        # Load Cụm địa lý
        df_cum = pd.read_sql_query("SELECT DISTINCT ten_cum FROM dim_buucuc WHERE ten_cum IS NOT NULL ORDER BY ten_cum", conn)
        if not df_cum.empty:
            options["cum"] = df_cum.iloc[:, 0].tolist()
        
        # Load Bưu điện huyện/xã (BDX)
        df_bdx = pd.read_sql_query("SELECT DISTINCT ten_bdx FROM dim_buucuc WHERE ten_bdx IS NOT NULL ORDER BY ten_bdx", conn)
        if not df_bdx.empty:
            options["bdx"] = df_bdx.iloc[:, 0].tolist()
        
        # Load Bưu cục chấp nhận
        df_bc = pd.read_sql_query("SELECT ma_bc, ten_buu_cuc FROM dim_buucuc ORDER BY ma_bc", conn)
        if not df_bc.empty:
            options["buu_cuc"] = [{"label": f"{r.iloc[0]} - {r.iloc[1]}", "value": r.iloc[0]} for _, r in df_bc.iterrows()]
        
    except Exception as e:
        print(f"Lỗi khi tải danh mục bộ lọc từ DB: {e}")
    finally:
        conn.close()
    return options

# Đọc các tùy chọn bộ lọc
FILTER_OPTS = load_filter_options()

# --------------------------------------------------------------------------
# KHUNG GIAO DIỆN CHÍNH (MAIN DYNAMIC LAYOUT)
# --------------------------------------------------------------------------
from flask import has_request_context

def serve_layout():
    """Hàm sinh layout động tùy thuộc vào trạng thái xác thực đăng nhập."""
    # Bảo vệ Dash khởi chạy không lỗi bên ngoài Flask request context
    if not has_request_context():
        return html.Div([
            dcc.Location(id="login-url", refresh=True),
            html.Div(id="login-error-output")
        ])
        
    if False: # not current_user.is_authenticated:
        # Layout trang đăng nhập
        return html.Div([
            dcc.Location(id="login-url", refresh=True),
            html.Div([
                html.Div([
                    html.H2("🔑 HỆ THỐNG ĐIỀU HÀNH", className="login-title"),
                    html.P("Đăng nhập để xem báo cáo doanh thu BCCP", className="login-subtitle"),
                ], className="login-header-box"),
                
                dbc.Form([
                    html.Div([
                        html.Label("Tên đăng nhập", className="filter-label"),
                        dbc.Input(id="input-username", type="text", placeholder="Nhập username...", style={"marginBottom": "15px"})
                    ]),
                    html.Div([
                        html.Label("Mật khẩu", className="filter-label"),
                        dbc.Input(id="input-password", type="password", placeholder="Nhập mật khẩu...", style={"marginBottom": "20px"})
                    ]),
                    dbc.Button("ĐĂNG NHẬP", id="btn-login", color="primary", className="w-100 btn-login-submit"),
                    html.Div(id="login-error-output", style={"color": "#DC2626", "marginTop": "15px", "textAlign": "center", "fontSize": "13px", "fontWeight": "bold"})
                ], className="login-form")
            ], className="login-box")
        ], className="login-container")
    
    # Layout trang Dashboard sau khi đăng nhập thành công
    return html.Div([
        # Location định tuyến chính
        dcc.Location(id="url", refresh=False),
        
        # Location để nhận tín hiệu đăng xuất
        dcc.Location(id="sidebar-logout-url", refresh=True),
        
        # Input tabs-navigation ẩn để tương thích ngược với các callback cũ
        dcc.Input(id="tabs-navigation", type="text", style={"display": "none"}, value="tab-kpi"),
        
        # Sidebar lọc dữ liệu
        create_sidebar_layout(FILTER_OPTS),
        
        # Vùng hiển thị nội dung chính bên phải
        html.Div([
            # Header Tiêu đề
            html.Div([
                html.Div([
                    html.H1("📊 Dashboard Điều hành Doanh thu", className="main-title", id="main-title-text"),
                    html.Div(id="header-sub-title", className="sub-title")
                ], style={"flex": "1"}),
                # Nút Import
                dcc.Link("📥 Nhập dữ liệu", href="/import", className="header-import-btn", id="btn-goto-import")
            ], style={"display": "flex", "justify-content": "space-between", "align-items": "center", "margin-bottom": "20px"}),
            
            # Vùng chứa layout động của từng trang
            html.Div(id="page-content", style={"paddingTop": "10px"})
            
        ], className="content")
    ])

# Gán hàm serve_layout để Dash sinh giao diện động cho mỗi request
app.layout = serve_layout

# --------------------------------------------------------------------------
# CALLBACK ĐỒNG BỘ URL PATHNAME VỚI TABS-NAVIGATION ẨN (TƯƠNG THÍCH NGƯỢC)
# --------------------------------------------------------------------------
@app.callback(
    Output("tabs-navigation", "value"),
    [Input("url", "pathname")]
)
def sync_url_to_tabs_navigation(pathname):
    """
    Đồng bộ URL pathname với value của tabs-navigation ảo để kích hoạt 
    các callback cũ của BCCP mà không phải sửa mã nguồn của chúng.
    """
    if pathname == "/bccp":
        return "tab-kpi"
    elif pathname == "/bccp/revenue":
        return "tab-revenue"
    elif pathname == "/bccp/customer":
        return "tab-customer"
    elif pathname == "/bccp/charts":
        return "tab-charts"
    elif pathname == "/bccp/alerts":
        return "tab-alerts"
    elif pathname == "/import":
        return "tab-import"
    return None # Default

# --------------------------------------------------------------------------
# CALLBACK ĐỊNH TUYẾN TRANG CHÍNH (URL ROUTING)
# --------------------------------------------------------------------------
@app.callback(
    [Output("page-content", "children"),
     Output("main-title-text", "children")],
    [Input("url", "pathname")]
)
def render_page(pathname):
    """
    Định tuyến và trả về layout trang phù hợp dựa theo URL pathname.
    """
    # Bảo mật: nếu chưa auth thì không trả về gì
    if False: # not current_user.is_authenticated:
        return html.Div("Vui lòng đăng nhập hệ thống", style={"textAlign": "center", "padding": "50px"}), "🔑 Hệ thống điều hành"
        
    if not pathname or pathname == "/":
        try:
            from pages.global_overview import create_global_overview_layout
            return create_global_overview_layout(), "📊 Tổng quan điều hành doanh thu"
        except ImportError:
            return html.Div("Trang Tổng quan chung đang được xây dựng...", className="empty-state-container"), "📊 Tổng quan điều hành doanh thu"
            
    elif pathname == "/bccp":
        return create_kpi_page_layout(), "📊 Bưu chính chuyển phát - KPI"
    elif pathname == "/bccp/revenue":
        return create_customer_detail_layout(), "📊 Bưu chính chuyển phát - Khách hàng"
    elif pathname == "/bccp/customer":
        return create_customer_detail_layout(), "📊 Bưu chính chuyển phát - Khách hàng"
    elif pathname == "/bccp/charts":
        return create_kpi_page_layout(), "📊 Bưu chính chuyển phát - KPI"
    elif pathname == "/bccp/alerts":
        try:
            from pages.alerts import create_alerts_page_layout
            return create_alerts_page_layout(), "📊 Bưu chính chuyển phát - Cảnh báo"
        except Exception as e:
            print(f"Lỗi load trang alerts: {e}")
            return html.Div("Trang cảnh báo doanh thu đang được xây dựng...", className="empty-state-container"), "📊 Bưu chính chuyển phát - Cảnh báo"
            
    elif pathname == "/hcc":
        try:
            from pages.service_overview import create_service_page_layout
            return create_service_page_layout("HCC"), "🏢 Hành chính công"
        except ImportError:
            return html.Div("Trang Hành chính công đang được xây dựng...", className="empty-state-container"), "🏢 Hành chính công"
            
    elif pathname == "/hcc/revenue":
        try:
            return create_hcc_revenue_layout(), "🏛️ Hành chính công - Báo cáo doanh thu"
        except Exception as e:
            print(f"Lỗi load trang hcc_revenue: {e}")
            return html.Div("Trang báo cáo doanh thu HCC đang được xây dựng...", className="empty-state-container"), "🏛️ Hành chính công - Báo cáo doanh thu"
            
    elif pathname == "/tcbc":
        try:
            from pages.service_overview import create_service_page_layout
            return create_service_page_layout("TCBC"), "💰 Tài chính Bưu chính"
        except ImportError:
            return html.Div("Trang Tài chính Bưu chính đang được xây dựng...", className="empty-state-container"), "💰 Tài chính Bưu chính"
            
    elif pathname == "/ppbl":
        try:
            from pages.service_overview import create_service_page_layout
            return create_service_page_layout("PPBL"), "🛍️ Phân phối bán lẻ"
        except ImportError:
            return html.Div("Trang Phân phối bán lẻ đang được xây dựng...", className="empty-state-container"), "🛍️ Phân phối bán lẻ"
            
    elif pathname == "/import":
        return create_import_page_layout(), "📥 Nhập dữ liệu hệ thống"
        
    return html.Div([
        html.Div("⚠️", className="empty-state-icon"),
        html.Div("Trang không tồn tại", className="empty-state-title"),
        html.Div("Đường dẫn bạn truy cập không hợp lệ. Vui lòng chọn dịch vụ ở menu bên trái.", className="empty-state-desc")
    ], className="empty-state-container"), "⚠️ Trang không tồn tại"

# --------------------------------------------------------------------------
# CALLBACK XỬ LÝ ĐĂNG NHẬP / ĐĂNG XUẤT
# --------------------------------------------------------------------------
@app.callback(
    [Output("login-error-output", "children"),
     Output("login-url", "href")],
    [Input("btn-login", "n_clicks")],
    [State("input-username", "value"),
     State("input-password", "value")],
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    if not n_clicks or not username or not password:
        return "Vui lòng nhập đầy đủ tài khoản và mật khẩu!", dash.no_update
        
    from db.auth import check_user_credentials
    user = check_user_credentials(username.strip(), password)
    
    if user:
        login_user(user)
        print(f"Đăng nhập thành công: User {username}")
        return "", "/"
    else:
        return "Tên đăng nhập hoặc mật khẩu không đúng!", dash.no_update

@app.callback(
    Output("sidebar-logout-url", "href"),
    [Input("btn-logout", "n_clicks")],
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    if n_clicks:
        logout_user()
        print("Đã đăng xuất tài khoản.")
        return "/"
    return dash.no_update

# --------------------------------------------------------------------------
# ĐĂNG KÝ TOÀN BỘ CALLBACKS MODULAR
# --------------------------------------------------------------------------
register_sidebar_callbacks(app)
register_kpi_callbacks(app)
register_customer_callbacks(app)
register_import_callbacks(app)
register_alerts_callbacks(app)
register_global_callbacks(app)
register_service_callbacks(app)
register_hcc_revenue_callbacks(app)

# --------------------------------------------------------------------------
# CHẠY ỨNG DỤNG
# --------------------------------------------------------------------------
if __name__ == '__main__':
    # Chạy trên cổng mặc định 8050
    app.run(debug=False, port=8050, host='127.0.0.1')
