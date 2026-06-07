# -*- coding: utf-8 -*-
"""
Layout trang Báo cáo Khách hàng mới/tái bán v2.0 (/bccp/new-customer).
Hiển thị 3 chỉ số KPI chính và danh sách KH mới/tái bán hỗ trợ xuất Excel.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

def make_simple_kpi_card(card_id, title, icon, border_color):
    """Tạo card KPI đơn giản hiển thị số lượng / doanh thu khách hàng mới"""
    return html.Div([
        html.Div([
            html.Span(icon, style={"fontSize": "22px", "marginRight": "8px"}),
            html.Span(title, className="kpi-title", style={"fontWeight": "bold", "color": "#1E293B", "fontSize": "13px"}),
        ], style={"display": "flex", "alignItems": "center", "borderBottom": "1px solid #E2E8F0", "paddingBottom": "6px"}),
        html.Div("—", id=f"{card_id}-value", className="kpi-value", style={"fontSize": "26px", "fontWeight": "bold", "color": "#0F172A", "marginTop": "8px"}),
        html.Div(id=f"{card_id}-subtext", className="delta-row", style={"fontSize": "12px", "color": "#64748B", "marginTop": "4px"})
    ], className="kpi-card", style={
        "borderTop": f"4px solid {border_color}", 
        "padding": "12px",
        "backgroundColor": "#FFFFFF",
        "borderRadius": "8px",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
        "height": "100%"
    })

def create_new_customer_layout():
    """Tạo Layout chính cho trang Khách hàng mới/tái bán v2.0"""
    return html.Div([
        # SECTION 1: 3 Chỉ số KPI
        html.Div("🆕 Khách hàng mới/tái bán", className="section-header", style={"marginTop": 0, "marginBottom": "12px", "fontWeight": "bold", "fontSize": "16px"}),
        dbc.Row([
            dbc.Col(make_simple_kpi_card("new-cust-kpi-count", "Số KH mới/tái bán trong kỳ", "🆕", "#3B82F6"), md=4, xs=12, className="mb-3"),
            dbc.Col(make_simple_kpi_card("new-cust-kpi-4m-count", "KH mới/tái bán 4 tháng gần nhất", "👥", "#10B981"), md=4, xs=12, className="mb-3"),
            dbc.Col(make_simple_kpi_card("new-cust-kpi-revenue", "Doanh thu của KH mới 4 tháng", "💰", "#F59E0B"), md=4, xs=12, className="mb-3")
        ], className="g-3"),
        
        # SECTION 2: Bảng danh sách KH mới/tái bán
        html.Div([
            html.Div([
                html.Span("📋 Danh sách Khách hàng mới / Tái bán", style={"fontWeight": "bold", "fontSize": "15px", "color": "#1E293B"}),
                html.Div([
                    dbc.Button("📥 Xuất Excel", id="new-cust-btn-export-excel", color="success", size="sm"),
                    dcc.Download(id="new-cust-download")
                ], style={"display": "flex", "alignItems": "center"})
            ], style={"display": "flex", "justifyContent": "between", "alignItems": "center", "flexWrap": "wrap", "marginBottom": "15px", "marginTop": "20px"}),
            
            dbc.Spinner(
                html.Div(id="new-cust-table-container"),
                color="primary"
            )
        ])
    ])
