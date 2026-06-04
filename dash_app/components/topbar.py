# -*- coding: utf-8 -*-
"""
Component Topbar chứa các bộ lọc đa chiều toàn cục.
Nằm ngang trên cùng của phần nội dung chính, với nút "Lọc dữ liệu" ở góc phải.
"""

from datetime import date, datetime
from dash import html, dcc
import dash_bootstrap_components as dbc
from flask_login import current_user

def create_topbar_layout(filter_opts):
    """
    Tạo cấu trúc Layout cho Topbar dựa trên danh sách dữ liệu lọc được cung cấp.
    Đồng thời áp dụng phân quyền hiển thị theo tài khoản đăng nhập.
    
    Args:
        filter_opts (dict): Từ điển chứa danh sách các năm, nhóm dịch vụ, spdv, cụm, bdx, bưu cục.
    
    Returns:
        html.Div: Component topbar của Dash.
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    default_year = current_year if (filter_opts["years"] and current_year in filter_opts["years"]) else (filter_opts["years"][0] if filter_opts["years"] else 2026)

    # Phân quyền bộ lọc Cụm dựa trên vai trò người dùng
    cum_value = "Tất cả"
    cum_options = [{"label": "Tất cả Cụm", "value": "Tất cả"}] + [{"label": c, "value": c} for c in filter_opts["cum"]]
    cum_disabled = False
    
    if current_user and current_user.is_authenticated and current_user.role == 'user' and current_user.assigned_cum:
        cum_value = current_user.assigned_cum
        cum_options = [{"label": current_user.assigned_cum, "value": current_user.assigned_cum}]
        cum_disabled = True

    return html.Div([
        html.Div([
            # Nhóm 1: Thời gian
            html.Div([
                html.Label("Năm", className="filter-label mb-0 me-2"),
                dcc.Dropdown(
                    id="sidebar-year",
                    options=[{"label": str(y), "value": y} for y in filter_opts["years"]],
                    value=default_year,
                    clearable=False,
                    style={"minWidth": "100px"}
                )
            ], className="d-flex align-items-center me-3"),
            
            html.Div([
                html.Label("Chu kỳ", className="filter-label mb-0 me-2"),
                dcc.Dropdown(
                    id="sidebar-period",
                    options=[
                        {"label": "Ngày", "value": "Ngày"},
                        {"label": "Tuần", "value": "Tuần"},
                        {"label": "Tháng", "value": "Tháng"}
                    ],
                    value="Tháng",
                    clearable=False,
                    style={"minWidth": "100px"}
                )
            ], className="d-flex align-items-center me-3"),
            
            # Lọc theo Ngày
            html.Div(id="filter-container-day", children=[
                html.Label("Từ-Đến", className="filter-label mb-0 me-2"),
                dcc.DatePickerRange(
                    id="sidebar-date-range",
                    display_format="DD/MM/YYYY",
                    min_date_allowed=date(2025, 1, 1),
                    max_date_allowed=date(2027, 12, 31),
                    start_date=date(2026, 1, 1),
                    end_date=date(2026, 1, 31)
                )
            ], className="d-flex align-items-center me-3"),
            
            # Lọc theo Tuần
            html.Div(id="filter-container-week", children=[
                html.Label("Tuần", className="filter-label mb-0 me-2"),
                dcc.Dropdown(id="sidebar-week-select", clearable=False, style={"minWidth": "100px"})
            ], className="d-flex align-items-center me-3", style={"display": "none"}),
            
            # Lọc theo Tháng
            html.Div(id="filter-container-month", children=[
                html.Label("Tháng", className="filter-label mb-0 me-2"),
                dcc.Dropdown(
                    id="sidebar-month-select",
                    options=[{"label": f"Tháng {i:02d}", "value": i} for i in range(1, 13)],
                    value=current_month,
                    clearable=False,
                    style={"minWidth": "120px"}
                )
            ], className="d-flex align-items-center me-3"),

            # Chế độ so sánh
            html.Div([
                html.Label("So sánh", className="filter-label mb-0 me-2"),
                dcc.Dropdown(
                    id="sidebar-compare-mode",
                    options=[
                        {"label": "Kỳ trước", "value": "prev_period"},
                        {"label": "Cùng kỳ", "value": "yoy"},
                        {"label": "Kế hoạch", "value": "plan"}
                    ],
                    value="prev_period",
                    multi=True,
                    style={"minWidth": "180px"}
                )
            ], className="d-flex align-items-center me-3"),
        ], className="d-flex flex-wrap align-items-center mb-2"),
        
        html.Div([
            # Nhóm 2: Không gian
            html.Div([
                html.Label("Cụm", className="filter-label mb-0 me-2"),
                dcc.Dropdown(
                    id="sidebar-cum",
                    options=cum_options,
                    value=cum_value,
                    disabled=cum_disabled,
                    clearable=False,
                    style={"minWidth": "150px"}
                )
            ], className="d-flex align-items-center me-3"),
            
            html.Div([
                html.Label("Huyện/Xã", className="filter-label mb-0 me-2"),
                dcc.Dropdown(
                    id="sidebar-bdx",
                    options=[{"label": "Tất cả BĐX", "value": "Tất cả"}] + [{"label": b, "value": b} for b in filter_opts["bdx"]],
                    value="Tất cả",
                    clearable=False,
                    style={"minWidth": "180px"}
                )
            ], className="d-flex align-items-center me-3"),
            
            html.Div([
                html.Label("Bưu cục", className="filter-label mb-0 me-2"),
                dcc.Dropdown(
                    id="sidebar-buu-cuc",
                    options=[{"label": "Tất cả BC", "value": "Tất cả"}] + filter_opts["buu_cuc"],
                    value="Tất cả",
                    clearable=False,
                    style={"minWidth": "200px"}
                )
            ], className="d-flex align-items-center me-3"),

            # Nút Lọc (Góc phải)
            html.Div([
                dbc.Button(
                    "🔍 Lọc dữ liệu",
                    id="btn-apply-filter",
                    color="primary",
                    className="fw-bold px-4"
                )
            ], className="ms-auto")
            
        ], className="d-flex flex-wrap align-items-center")
        
        # Các filter ẩn cho BCCP
        ,html.Div(id="bccp-extra-filters", style={"display": "none"}, children=[
            dcc.Store(id="sidebar-nhom-dv", data=None),
            dcc.Store(id="sidebar-loai-kh", data=[]),
            dcc.Store(id="sidebar-hop-dong", data=[])
        ])
    ], className="topbar-container bg-white p-3 rounded shadow-sm mb-4 border")
