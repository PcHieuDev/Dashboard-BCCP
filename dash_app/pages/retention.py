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

def create_retention_layout():
    """
    Tạo Layout cho trang Báo cáo Duy trì Khách hàng hiện hữu.
    """
    return html.Div([
        # Block 1: KPI Cards tổng hợp & 2 Gauge
        html.Div("🔄 Tổng hợp Duy trì & Mất khách hàng (Retention Rate)", className="section-header", style={"marginTop": 0}),
        dbc.Row([
            dbc.Col(make_simple_kpi_card("ret-kpi-prev-count", "KHHH tháng trước", "👥"), lg=2, md=4, xs=12),
            dbc.Col(make_simple_kpi_card("ret-kpi-retained-revenue", "Doanh thu KH duy trì", "💰"), lg=2, md=4, xs=12),
            dbc.Col(make_simple_kpi_card("ret-kpi-lost-count", "Số lượng KH mất đi", "📉"), lg=2, md=4, xs=12),
            dbc.Col([
                html.Div([
                    dcc.Graph(id="ret-gauge-sl")
                ], style={'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)', 'padding': '5px'})
            ], lg=3, md=6, xs=12, className="mb-3"),
            dbc.Col([
                html.Div([
                    dcc.Graph(id="ret-gauge-dt")
                ], style={'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)', 'padding': '5px'})
            ], lg=3, md=6, xs=12, className="mb-3")
        ], className="g-3 mb-4", style={"marginBottom": "20px"}),
        
        # Block 2: Waterfall & Bảng Biến động
        html.Div("📊 Phân tích Biến động Doanh thu & Khách hàng", className="section-header"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("📉 Biến động KHHH", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B', 'marginBottom': '10px'}),
                    dcc.Graph(id="ret-waterfall-chart")
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)', 'height': '100%'})
            ], lg=6, md=12, className="mb-3"),
            
            dbc.Col([
                html.Div([
                    html.H4("📋 Chi tiết biến động", style={'fontSize': '15px', 'fontWeight': 'bold', 'color': '#1E293B', 'marginBottom': '10px'}),
                    dbc.Spinner(html.Div(id="ret-table-container"))
                ], style={'padding': '15px', 'background': '#FFF', 'borderRadius': '12px', 'border': '1px solid #E2E8F0', 'boxShadow': '0 1px 3px rgba(0,0,0,0.05)', 'height': '100%'})
            ], lg=6, md=12, className="mb-3")
        ], className="g-3 mb-4", style={"marginBottom": "20px"}),
        
        # Block 3: Churn Alerts Table
        html.Div("⚠️ Danh sách Khách hàng Hiện hữu có nguy cơ rời bỏ (Churn Alerts)", className="section-header"),
        dbc.Row([
            dbc.Col([
                html.Label("Bưu điện Huyện/Xã", className="filter-label"),
                dcc.Dropdown(
                    id="ret-filter-bdx",
                    options=[{"label": "Tất cả BĐX", "value": "Tất cả"}],
                    value="Tất cả",
                    clearable=False
                )
            ], md=4, xs=12),
            
            dbc.Col([
                dbc.Button("📥 Xuất Excel DS Biến Động", id="ret-btn-export-excel", color="success", size="sm", style={"marginTop": "28px", "marginRight": "10px"}),
                dbc.Button("📥 Xuất Excel DS Cảnh báo", id="ret-btn-export-churn", color="warning", size="sm", style={"marginTop": "28px"}),
                dcc.Download(id="ret-download"),
                dcc.Download(id="ret-download-churn")
            ], md=8, xs=12, style={"textAlign": "right"})
        ], style={"marginBottom": "15px"}),
        
        html.Hr(),
        
        dbc.Spinner(
            html.Div(id="ret-churn-table-container"),
            color="primary"
        )
    ])
