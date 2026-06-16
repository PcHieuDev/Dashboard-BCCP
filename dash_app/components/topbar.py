# -*- coding: utf-8 -*-
"""
Component Topbar chứa các bộ lọc toàn cục (Thời gian, Địa lý) và nút Áp dụng.
Thay thế bộ lọc cũ trong Sidebar để tối ưu hóa không gian hiển thị.
"""

from datetime import datetime
from dash import html, dcc
import dash_bootstrap_components as dbc

def create_topbar_layout(filter_opts: dict) -> html.Div:
    """
    Tạo layout ngang chứa các dropdown bộ lọc thời gian và địa lý.
    
    Args:
        filter_opts (dict): Các lựa chọn năm, cụm, bdx, bưu cục.
        
    Returns:
        html.Div: Component Topbar
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    default_year = current_year if (filter_opts.get("years") and current_year in filter_opts["years"]) else (filter_opts["years"][0] if filter_opts.get("years") else 2026)
    
    # 1. Nhóm lọc thời gian
    time_group = html.Div([
        # Dropdown Năm
        html.Div([
            html.Label("Năm", className="topbar-label"),
            dcc.Dropdown(
                id="sidebar-year",
                options=[{"label": str(y), "value": y} for y in filter_opts.get("years", [])],
                value=default_year,
                clearable=False,
                className="topbar-dropdown"
            )
        ], className="topbar-filter-item"),
        
        # Dropdown Chu kỳ (Chỉ Tuần & Tháng)
        html.Div([
            html.Label("Chu kỳ", className="topbar-label"),
            dcc.Dropdown(
                id="sidebar-period",
                options=[
                    {"label": "Tuần", "value": "Tuần"},
                    {"label": "Tháng", "value": "Tháng"}
                ],
                value="Tháng",
                clearable=False,
                className="topbar-dropdown"
            )
        ], className="topbar-filter-item"),
        
        # Container Tuần
        html.Div(id="week-container", children=[
            html.Label("Chọn Tuần", className="topbar-label"),
            dcc.Dropdown(
                id="sidebar-week-select",
                clearable=False,
                className="topbar-dropdown"
            )
        ], className="topbar-filter-item", style={"display": "none"}),
        
        # Container Tháng
        html.Div(id="month-container", children=[
            html.Label("Chọn Tháng", className="topbar-label"),
            dcc.Dropdown(
                id="sidebar-month-select",
                options=[{"label": f"Tháng {i:02d}", "value": i} for i in range(1, 13)],
                value=current_month,
                clearable=False,
                className="topbar-dropdown"
            )
        ], className="topbar-filter-item")
    ], className="topbar-filter-group")
    
    # 2. Nhóm lọc địa lý
    geo_group = html.Div([
        # Dropdown Cụm
        html.Div([
            html.Label("Cụm", className="topbar-label"),
            dcc.Dropdown(
                id="sidebar-cum",
                options=[{"label": "Tất cả Cụm", "value": "Tất cả"}] + [{"label": c, "value": c} for c in filter_opts.get("cum", [])],
                value="Tất cả",
                clearable=False,
                className="topbar-dropdown"
            )
        ], className="topbar-filter-item"),
        
        # Dropdown Bưu điện xã/phường
        html.Div([
            html.Label("Bưu điện xã/phường", className="topbar-label"),
            dcc.Dropdown(
                id="sidebar-bdx",
                options=[{"label": "Tất cả BĐX", "value": "Tất cả"}] + [{"label": b, "value": b} for b in filter_opts.get("bdx", [])],
                value="Tất cả",
                clearable=False,
                className="topbar-dropdown"
            )
        ], className="topbar-filter-item"),
        
        # Dropdown Bưu cục chấp nhận
        html.Div([
            html.Label("Mã bưu cục", className="topbar-label"),
            dcc.Dropdown(
                id="sidebar-buu-cuc",
                options=[{"label": "Tất cả Bưu cục", "value": "Tất cả"}] + filter_opts.get("buu_cuc", []),
                value="Tất cả",
                clearable=False,
                className="topbar-dropdown"
            )
        ], className="topbar-filter-item")
    ], className="topbar-filter-group")
    
    # 3. Nút hành động & Các Store tương thích ngược
    actions_group = html.Div([
        dbc.Button(
            "🔍 Áp dụng",
            id="btn-apply-filter",
            color="primary",
            className="topbar-apply-btn"
        ),
        # Các dcc.Store tương thích ngược phục vụ các trang chưa chuyển đổi inline
        dcc.Store(id="global-filters-store", storage_type="memory"),
        dcc.Store(id="sidebar-compare-mode", data=["prev_period", "yoy"]),
        dcc.Store(id="sidebar-nhom-dv", data=None),
        dcc.Store(id="sidebar-loai-kh", data=[]),
        dcc.Store(id="sidebar-hop-dong", data=[])
    ], className="topbar-actions-group")
    
    return html.Div([
        dbc.Row([
            dbc.Col(time_group, xs=12, lg=5, className="d-flex align-items-center flex-wrap"),
            dbc.Col(geo_group, xs=12, lg=5, className="d-flex align-items-center flex-wrap"),
            dbc.Col(actions_group, xs=12, lg=2, className="d-flex align-items-center justify-content-lg-end mt-2 mt-lg-0")
        ], className="g-2 align-items-end")
    ], id="topbar-container", className="topbar-container")
