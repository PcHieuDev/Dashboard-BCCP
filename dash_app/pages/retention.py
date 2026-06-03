# -*- coding: utf-8 -*-
"""
Layout trang Báo cáo Duy trì & Biến động Khách hàng Hiện hữu (/bccp/retention).
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

def make_simple_kpi_card(card_id, title, icon):
    return html.Div([
        html.Div([
            html.Div(title, className="kpi-title"),
            html.Span(icon, style={"fontSize": "20px", "float": "right", "marginTop": "-24px"})
        ]),
        html.Div("0", id=f"{card_id}-value", className="kpi-value"),
        html.Div(id=f"{card_id}-subtext", className="delta-row")
    ], className="kpi-card")

def make_retention_rate_card(card_id, title, color_theme="#0F766E"):
    return html.Div([
        html.Div(title, style={"fontSize": "14px", "fontWeight": "bold", "color": "#64748B", "marginBottom": "8px"}),
        html.Div("0.0%", id=f"{card_id}-value", style={"fontSize": "32px", "fontWeight": "bold", "color": color_theme, "lineHeight": "1"}),
        html.Div("0/0", id=f"{card_id}-subtext", style={"fontSize": "12px", "color": "#64748B", "marginTop": "8px"})
    ], className="kpi-card", style={"padding": "20px", "textAlign": "center"})

def create_retention_layout():
    """
    Tạo Layout cho trang Báo cáo Duy trì Khách hàng hiện hữu.
    """
    return html.Div([
        # Block 1: KPI Cards tổng hợp (3 cards)
        html.Div("🔄 Tổng hợp Duy trì & Mất khách hàng", className="section-header", style={"marginTop": 0}),
        dbc.Row([
            dbc.Col(make_simple_kpi_card("ret-kpi-prev-count", "KHHH tháng trước", "👥"), md=4, xs=12),
            dbc.Col(make_simple_kpi_card("ret-kpi-retained-revenue", "Doanh thu KH duy trì", "💰"), md=4, xs=12),
            dbc.Col(make_simple_kpi_card("ret-kpi-lost-count", "Số lượng KH mất đi", "📉"), md=4, xs=12)
        ], style={"marginBottom": "20px"}),
        
        # Block 2: Chỉ số duy trì (2 cards lớn)
        html.Div("🎯 Tỷ lệ duy trì thực tế (Retention Rate)", className="section-header"),
        dbc.Row([
            dbc.Col(make_retention_rate_card("ret-rate-sl", "Tỷ lệ Duy trì Khách hàng (SL)", "#0F766E"), md=6, xs=12),
            dbc.Col(make_retention_rate_card("ret-rate-dt", "Tỷ lệ Duy trì Doanh thu (DT)", "#2563EB"), md=6, xs=12)
        ], style={"marginBottom": "20px"}),
        
        # Block 3: Bảng chi tiết biến động theo bộ lọc
        html.Div("📊 Phân tích Biến động Doanh thu & Khách hàng", className="section-header"),
        dbc.Row([
            # Dropdown lọc BĐX (lọc động theo Cụm đã chọn ở Sidebar)
            dbc.Col([
                html.Label("Bưu điện Huyện/Xã", className="filter-label"),
                dcc.Dropdown(
                    id="ret-filter-bdx",
                    options=[{"label": "Tất cả BĐX", "value": "Tất cả"}],
                    value="Tất cả",
                    clearable=False
                )
            ], md=4, xs=12),
            
            # Nút xuất Excel
            dbc.Col([
                dbc.Button("📥 Xuất Excel", id="ret-btn-export-excel", color="success", size="sm", style={"marginTop": "28px"}),
                dcc.Download(id="ret-download")
            ], md=8, xs=12, style={"textAlign": "right"})
        ], style={"marginBottom": "15px"}),
        
        html.Hr(),
        
        # Vùng chứa bảng dữ liệu động
        dbc.Spinner(
            html.Div(id="ret-table-container"),
            color="primary"
        )
    ])
