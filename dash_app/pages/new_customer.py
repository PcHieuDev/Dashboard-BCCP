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
        
        # Block 2b: Xếp hạng Cụm & Phân dịch vụ
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("🏆 Bảng xếp hạng Cụm (KHM)", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(html.Div(id="new-cust-leaderboard-container"))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)', 'height': '100%'})
            ], lg=7, md=12, className="mb-3"),
            dbc.Col([
                html.Div([
                    html.H4("📊 Phân rã DV mà KHM sử dụng", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B'}),
                    dbc.Spinner(dcc.Graph(id="new-cust-chart-dv", style={'height': '350px'}))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)', 'height': '100%'})
            ], lg=5, md=12, className="mb-3")
        ], className="g-3 mb-4", style={"marginBottom": "20px"}),
        
        # Block 3: Bảng chi tiết theo BĐX và bộ lọc
        html.Div("🏢 Chi tiết thực hiện theo Bưu điện Huyện/Xã (BĐX)", className="section-header"),
        dbc.Row([
            # Nút xuất Excel
            dbc.Col([
                dbc.Button("📥 Xuất Excel", id="new-cust-btn-export-excel", color="success", size="sm", style={"marginTop": "28px"}),
                dcc.Download(id="new-cust-download")
            ], md=12, xs=12, style={"textAlign": "right"})
        ], style={"marginBottom": "15px"}),
        
        html.Hr(),
        
        # Vùng chứa bảng dữ liệu động BĐX
        dbc.Spinner(
            html.Div(id="new-cust-table-container"),
            color="primary"
        ),
        
        # Block 4: Top KHM giá trị cao
        html.Div("🏆 Top Khách hàng mới giá trị cao", className="section-header", style={"marginTop": "20px"}),
        dbc.Row([
            dbc.Col([
                dbc.Button("📥 Xuất toàn bộ danh sách KHM", id="new-cust-btn-export-khm", color="primary", size="sm"),
                dcc.Download(id="new-cust-download-khm")
            ], md=12, xs=12, style={"textAlign": "right", "marginBottom": "10px"})
        ]),
        dbc.Spinner(
            html.Div(id="new-cust-top-khm-container"),
            color="primary"
        )
    ])
