# -*- coding: utf-8 -*-
"""
Component Sidebar chứa các bộ lọc đa chiều (Thời gian, Dịch vụ, Địa lý, Loại KH, Hợp đồng).
Tích hợp hiển thị thông tin tài khoản đăng nhập và tự động khóa/phân quyền địa lý theo Cụm.
"""

from datetime import date, datetime
from dash import html, dcc
import dash_bootstrap_components as dbc
from flask_login import current_user

def create_sidebar_layout(filter_opts):
    """
    Tạo cấu trúc Layout cho Sidebar dựa trên danh sách dữ liệu lọc được cung cấp.
    Đồng thời áp dụng phân quyền hiển thị theo tài khoản đăng nhập.
    
    Args:
        filter_opts (dict): Từ điển chứa danh sách các năm, nhóm dịch vụ, spdv, cụm, bdx, bưu cục.
    
    Returns:
        html.Div: Component sidebar của Dash.
    """
    # Lấy thời gian hiện tại làm mặc định
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    default_year = current_year if (filter_opts["years"] and current_year in filter_opts["years"]) else (filter_opts["years"][0] if filter_opts["years"] else 2026)

    # 1. Tạo hộp thông tin tài khoản đăng nhập (Profile Box)
    profile_box = None
    if current_user and current_user.is_authenticated:
        display_role = "Admin" if current_user.role == "admin" else "Nhân viên"
        profile_box = html.Div([
            html.Div([
                html.Span(f"👤 {current_user.username}", className="user-name"),
                html.Span(f"Quyền: {display_role}" + (f" ({current_user.assigned_cum})" if current_user.assigned_cum else ""), className="user-role"),
            ], className="user-profile-info"),
            dbc.Button("Đăng xuất", id="btn-logout", color="danger", size="sm", className="btn-logout-sidebar")
        ], className="user-profile-box")

    # 2. Phân quyền bộ lọc Cụm dựa trên vai trò người dùng
    cum_value = "Tất cả"
    cum_options = [{"label": "Tất cả Cụm", "value": "Tất cả"}] + [{"label": c, "value": c} for c in filter_opts["cum"]]
    cum_disabled = False
    
    if current_user and current_user.is_authenticated and current_user.role == 'user' and current_user.assigned_cum:
        cum_value = current_user.assigned_cum
        cum_options = [{"label": current_user.assigned_cum, "value": current_user.assigned_cum}]
        cum_disabled = True

    return html.Div([
        # Hiển thị profile box ở đầu sidebar
        profile_box if profile_box else html.Div(),
        
        html.Div([
            html.H3("📅 Thời gian", className="section-header", style={"marginTop": 0}),
            
            # Chọn Năm
            html.Div([
                html.Label("Năm", className="filter-label"),
                dcc.Dropdown(
                    id="sidebar-year",
                    options=[{"label": str(y), "value": y} for y in filter_opts["years"]],
                    value=default_year,
                    clearable=False
                )
            ], className="filter-group"),
            
            # Chọn Chu kỳ (Ngày / Tuần / Tháng)
            html.Div([
                html.Label("Chu kỳ", className="filter-label"),
                dcc.Dropdown(
                    id="sidebar-period",
                    options=[
                        {"label": "Ngày", "value": "Ngày"},
                        {"label": "Tuần", "value": "Tuần"},
                        {"label": "Tháng", "value": "Tháng"}
                    ],
                    value="Tháng",
                    clearable=False
                )
            ], className="filter-group"),
            
            # Lọc theo Ngày (DatePickerRange)
            html.Div(id="filter-container-day", children=[
                html.Label("Khoảng ngày", className="filter-label"),
                dcc.DatePickerRange(
                    id="sidebar-date-range",
                    display_format="DD/MM/YYYY",
                    min_date_allowed=date(2025, 1, 1),
                    max_date_allowed=date(2027, 12, 31),
                    start_date=date(2026, 1, 1),
                    end_date=date(2026, 1, 31),
                    style={"width": "100%"}
                )
            ], className="filter-group"),
            
            # Lọc theo Tuần
            html.Div(id="filter-container-week", children=[
                html.Label("Chọn Tuần", className="filter-label"),
                dcc.Dropdown(id="sidebar-week-select", clearable=False)
            ], className="filter-group", style={"display": "none"}),
            
            # Lọc theo Tháng
            html.Div(id="filter-container-month", children=[
                html.Label("Chọn Tháng", className="filter-label"),
                dcc.Dropdown(
                    id="sidebar-month-select",
                    options=[{"label": f"Tháng {i:02d}", "value": i} for i in range(1, 13)],
                    value=current_month,
                    clearable=False
                )
            ], className="filter-group"),
            
            # Chế độ so sánh (Kỳ trước / Cùng kỳ năm trước / Cả hai)
            html.Div([
                html.Label("Chế độ so sánh", className="filter-label"),
                dcc.RadioItems(
                    id="sidebar-compare-mode",
                    options=[
                        {"label": " Kỳ trước", "value": "prev_period"},
                        {"label": " Cùng kỳ năm trước", "value": "yoy"},
                        {"label": " Cả hai", "value": "both"}
                    ],
                    value="prev_period",
                    labelStyle={"display": "block", "marginBottom": "4px"}
                )
            ], className="filter-group"),
            
        ], style={"marginBottom": "20px"}),
        
        html.Hr(),
        
        html.Div([
            html.H3("🔍 Bộ lọc chiều", className="section-header"),
            
            # Lọc Nhóm Dịch vụ
            html.Div([
                html.Label("Nhóm dịch vụ", className="filter-label"),
                dcc.Dropdown(
                    id="sidebar-nhom-dv",
                    options=[{"label": n, "value": n} for n in filter_opts["nhom_dv"]],
                    multi=True,
                    placeholder="Tất cả dịch vụ"
                )
            ], className="filter-group"),
            
            # Lọc Dịch vụ Chi tiết
            html.Div([
                html.Label("Dịch vụ chi tiết", className="filter-label"),
                dcc.Dropdown(
                    id="sidebar-spdv",
                    options=filter_opts["spdv"],
                    multi=True,
                    placeholder="Tất cả mã SPDV"
                )
            ], className="filter-group"),
            
            # Lọc Cụm (Có phân quyền)
            html.Div([
                html.Label("Cụm", className="filter-label"),
                dcc.Dropdown(
                    id="sidebar-cum",
                    options=cum_options,
                    value=cum_value,
                    disabled=cum_disabled,
                    clearable=False
                )
            ], className="filter-group"),
            
            # Lọc Bưu điện Huyện/Xã (BDX)
            html.Div([
                html.Label("Bưu điện Huyện/Xã", className="filter-label"),
                dcc.Dropdown(
                    id="sidebar-bdx",
                    options=[{"label": "Tất cả BĐX", "value": "Tất cả"}] + [{"label": b, "value": b} for b in filter_opts["bdx"]],
                    value="Tất cả",
                    clearable=False
                )
            ], className="filter-group"),
            
            # Lọc Bưu cục chấp nhận
            html.Div([
                html.Label("Mã bưu cục", className="filter-label"),
                dcc.Dropdown(
                    id="sidebar-buu-cuc",
                    options=[{"label": "Tất cả Bưu cục", "value": "Tất cả"}] + filter_opts["buu_cuc"],
                    value="Tất cả",
                    clearable=False
                )
            ], className="filter-group"),
            
            # Lọc Loại Khách hàng
            html.Div([
                html.Label("Loại khách hàng", className="filter-label"),
                dbc.Checklist(
                    id="sidebar-loai-kh",
                    options=[
                        {"label": " Hiện hữu", "value": "Hiện hữu"},
                        {"label": " KHM/Tái bán", "value": "KHM/Tái bán"},
                        {"label": " Vãng lai", "value": "Vãng lai"}
                    ],
                    value=[],
                    className="custom-checklist",
                    labelStyle={"display": "block", "marginBottom": "4px"}
                )
            ], className="filter-group"),
            
            # Lọc Trạng thái Hợp đồng
            html.Div([
                html.Label("Trạng thái Hợp đồng", className="filter-label"),
                dbc.Checklist(
                    id="sidebar-hop-dong",
                    options=[
                        {"label": " Có HĐ", "value": "Có HĐ"},
                        {"label": " Không HĐ", "value": "Không HĐ"}
                    ],
                    value=[],
                    className="custom-checklist",
                    labelStyle={"display": "block", "marginBottom": "4px"}
                )
            ], className="filter-group"),
        ])
    ], className="sidebar")
