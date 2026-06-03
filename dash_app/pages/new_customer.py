# -*- coding: utf-8 -*-
"""
Layout trang Báo cáo Khách hàng bán mới (/bccp/new-customer).
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

def make_service_kpi_card(card_id, title, icon):
    return html.Div([
        html.Div([
            html.Span(icon, style={"fontSize": "18px", "marginRight": "8px"}),
            html.Strong(title, style={"fontSize": "14px", "color": "#1E293B"})
        ], style={"marginBottom": "12px", "borderBottom": "1px solid #E2E8F0", "paddingBottom": "8px"}),
        dbc.Row([
            dbc.Col([
                html.Div("SL KH mới", style={"fontSize": "11px", "color": "#64748B"}),
                html.Div("0", id=f"{card_id}-count", style={"fontSize": "16px", "fontWeight": "bold", "color": "#0F766E"})
            ], width=3),
            dbc.Col([
                html.Div("DT bán mới", style={"fontSize": "11px", "color": "#64748B"}),
                html.Div("0 đ", id=f"{card_id}-revenue", style={"fontSize": "16px", "fontWeight": "bold", "color": "#0F766E"})
            ], width=3),
            dbc.Col([
                html.Div("Kế hoạch", style={"fontSize": "11px", "color": "#64748B"}),
                html.Div("0 đ", id=f"{card_id}-plan", style={"fontSize": "16px", "fontWeight": "bold", "color": "#64748B"})
            ], width=3),
            dbc.Col([
                html.Div("% Đạt", style={"fontSize": "11px", "color": "#64748B"}),
                html.Div("0%", id=f"{card_id}-percent", style={"fontSize": "16px", "fontWeight": "bold", "color": "#3B82F6"})
            ], width=3)
        ])
    ], className="kpi-card", style={"padding": "15px"})

def create_new_customer_layout():
    """
    Tạo Layout cho trang Báo cáo Khách hàng mới.
    """
    return html.Div([
        # Block 1: KPI Cards tổng hợp (3 cards)
        html.Div("🆕 Tổng hợp Khách hàng bán mới", className="section-header", style={"marginTop": 0}),
        dbc.Row([
            dbc.Col(make_simple_kpi_card("new-cust-kpi-count", "Tổng số KH mới", "🆕"), md=4, xs=12),
            dbc.Col(make_simple_kpi_card("new-cust-kpi-revenue", "Tổng doanh thu bán mới", "💰"), md=4, xs=12),
            dbc.Col(make_simple_kpi_card("new-cust-kpi-percent", "% Hoàn thành Kế hoạch KH mới", "🎯"), md=4, xs=12)
        ], style={"marginBottom": "20px"}),
        
        # Block 2: Chi tiết theo Nhóm DV (2 cards)
        html.Div("📋 Chi tiết theo nhóm dịch vụ", className="section-header"),
        dbc.Row([
            dbc.Col(make_service_kpi_card("new-cust-svc-tt", "Dịch vụ Truyền thống", "📮"), md=6, xs=12),
            dbc.Col(make_service_kpi_card("new-cust-svc-tmdt", "Dịch vụ TMĐT", "🛒"), md=6, xs=12)
        ], style={"marginBottom": "20px"}),
        
        # Block 3: Bảng chi tiết theo BĐX và bộ lọc
        html.Div("🏢 Chi tiết thực hiện theo Bưu điện Huyện/Xã (BĐX)", className="section-header"),
        dbc.Row([
            # Dropdown lọc BĐX (lọc động theo Cụm đã chọn ở Sidebar)
            dbc.Col([
                html.Label("Bưu điện Huyện/Xã", className="filter-label"),
                dcc.Dropdown(
                    id="new-cust-filter-bdx",
                    options=[{"label": "Tất cả BĐX", "value": "Tất cả"}],
                    value="Tất cả",
                    clearable=False
                )
            ], md=4, xs=12),
            
            # Nút xuất Excel
            dbc.Col([
                dbc.Button("📥 Xuất Excel", id="new-cust-btn-export-excel", color="success", size="sm", style={"marginTop": "28px"}),
                dcc.Download(id="new-cust-download")
            ], md=8, xs=12, style={"textAlign": "right"})
        ], style={"marginBottom": "15px"}),
        
        html.Hr(),
        
        # Vùng chứa bảng dữ liệu động
        dbc.Spinner(
            html.Div(id="new-cust-table-container"),
            color="primary"
        )
    ])
