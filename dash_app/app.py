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
from pages.revenue_detail import create_revenue_detail_layout
from pages.customer_detail import create_customer_detail_layout
from pages.charts import create_charts_page_layout
from pages.import_data import create_import_page_layout

# Import các Callbacks đăng ký
from callbacks.sidebar_callbacks import register_sidebar_callbacks
from callbacks.kpi_callbacks import register_kpi_callbacks
from callbacks.revenue_callbacks import register_revenue_callbacks
from callbacks.customer_callbacks import register_customer_callbacks
from callbacks.import_callbacks import register_import_callbacks
from callbacks.charts_callbacks import register_charts_callbacks
from callbacks.alerts_callbacks import register_alerts_callbacks

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
            
        # Load Nhóm dịch vụ
        df_nhom = pd.read_sql_query("SELECT DISTINCT nhom_dich_vu FROM dim_spdv WHERE nhom_dich_vu IS NOT NULL", conn)
        if not df_nhom.empty:
            options["nhom_dv"] = df_nhom.iloc[:, 0].tolist()
        
        # Load Sản phẩm dịch vụ chi tiết
        df_spdv = pd.read_sql_query("SELECT ma_spdv, ten_spdv FROM dim_spdv WHERE ma_spdv IS NOT NULL", conn)
        if not df_spdv.empty:
            options["spdv"] = [{"label": f"{r.iloc[0]} - {r.iloc[1]}", "value": r.iloc[0]} for _, r in df_spdv.iterrows()]
        
        # Load Cụm địa lý
        df_cum = pd.read_sql_query("SELECT DISTINCT ten_Cum FROM dim_buucuc WHERE ten_Cum IS NOT NULL ORDER BY ten_Cum", conn)
        if not df_cum.empty:
            options["cum"] = df_cum.iloc[:, 0].tolist()
        
        # Load Bưu điện huyện/xã (BDX)
        df_bdx = pd.read_sql_query("SELECT DISTINCT ten_BDX FROM dim_buucuc WHERE ten_BDX IS NOT NULL ORDER BY ten_BDX", conn)
        if not df_bdx.empty:
            options["bdx"] = df_bdx.iloc[:, 0].tolist()
        
        # Load Bưu cục chấp nhận
        df_bc = pd.read_sql_query("SELECT ma_bc, ten_Buu_cuc FROM dim_buucuc ORDER BY ma_bc", conn)
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
        
    if not current_user.is_authenticated:
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
        # Location để nhận tín hiệu đăng xuất
        dcc.Location(id="sidebar-logout-url", refresh=True),
        
        # Sidebar lọc dữ liệu
        create_sidebar_layout(FILTER_OPTS),
        
        # Vùng hiển thị nội dung chính bên phải
        html.Div([
            # Header Tiêu đề
            html.Div([
                html.H1("📊 Dashboard Doanh thu BCCP (Dash App)", className="main-title"),
                html.Div(id="header-sub-title", className="sub-title")
            ]),
            
            # Thanh điều hướng Tab chính
            dcc.Tabs(id="tabs-navigation", value="tab-kpi", children=[
                dcc.Tab(label="📈 TỔNG QUAN KPI", value="tab-kpi", className="nav-link", selected_className="nav-link active"),
                dcc.Tab(label="📊 DOANH THU CHI TIẾT", value="tab-revenue", className="nav-link", selected_className="nav-link active"),
                dcc.Tab(label="🔍 CHI TIẾT KHÁCH HÀNG", value="tab-customer", className="nav-link", selected_className="nav-link active"),
                dcc.Tab(label="📈 BIỂU ĐỒ TRỰC QUAN", value="tab-charts", className="nav-link", selected_className="nav-link active"),
                dcc.Tab(label="🚨 CẢNH BÁO DOANH THU", value="tab-alerts", className="nav-link", selected_className="nav-link active"),
                dcc.Tab(label="📥 NHẬP DỮ LIỆU", value="tab-import", className="nav-link", selected_className="nav-link active")
            ]),
            
            # Vùng chứa layout động của từng trang
            html.Div(id="tabs-content", style={"paddingTop": "20px"})
            
        ], className="content")
    ])

# Gán hàm serve_layout để Dash sinh giao diện động cho mỗi request
app.layout = serve_layout

# --------------------------------------------------------------------------
# CALLBACK ĐIỀU HƯỚNG TAB CHÍNH
# --------------------------------------------------------------------------
@app.callback(
    Output("tabs-content", "children"),
    [Input("tabs-navigation", "value")]
)
def render_tab_content(tab_name):
    """
    Render nội dung layout tương ứng với Tab được chọn.
    """
    # Bảo mật: nếu chưa auth thì không trả về gì
    if not current_user.is_authenticated:
        return html.Div("Vui lòng đăng nhập hệ thống", style={"textAlign": "center", "padding": "50px"})
        
    if tab_name == "tab-kpi":
        return create_kpi_page_layout()
    elif tab_name == "tab-revenue":
        return create_revenue_detail_layout()
    elif tab_name == "tab-customer":
        return create_customer_detail_layout()
    elif tab_name == "tab-charts":
        return create_charts_page_layout()
    elif tab_name == "tab-alerts":
        from pages.alerts import create_alerts_page_layout
        return create_alerts_page_layout()
    elif tab_name == "tab-import":
        return create_import_page_layout()
    return html.Div("Trang không tồn tại", style={"textAlign": "center", "padding": "20px"})

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
register_revenue_callbacks(app)
register_customer_callbacks(app)
register_import_callbacks(app)
register_charts_callbacks(app)
register_alerts_callbacks(app)

# --------------------------------------------------------------------------
# CHẠY ỨNG DỤNG
# --------------------------------------------------------------------------
if __name__ == '__main__':
    # Chạy trên cổng mặc định 8050
    app.run(debug=False, port=8050, host='127.0.0.1')
