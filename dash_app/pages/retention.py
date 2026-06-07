# -*- coding: utf-8 -*-
"""
Layout trang Báo cáo Duy trì & Biến động Khách hàng Hiện hữu v2.0 (/bccp/retention).
Hiển thị 4 thẻ KPI biến động và 3 bảng chi tiết Tăng / Giảm / Rời bỏ.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

def make_simple_kpi_card(card_id, title, icon, border_color):
    """Tạo KPI card biến động"""
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

def create_retention_layout():
    """Tạo Layout chính cho trang Biến động & Duy trì v2.0"""
    return html.Div([
        # SECTION 1: 4 Thẻ KPI biến động
        html.Div("🔄 Biến động & Duy trì Khách hàng", className="section-header", style={"marginTop": 0, "marginBottom": "12px", "fontWeight": "bold", "fontSize": "16px"}),
        dbc.Row([
            dbc.Col(make_simple_kpi_card("ret-kpi-tang", "Khách hàng TĂNG doanh thu", "📈", "#10B981"), lg=3, md=6, className="mb-3"),
            dbc.Col(make_simple_kpi_card("ret-kpi-giam", "Khách hàng GIẢM doanh thu", "📉", "#F59E0B"), lg=3, md=6, className="mb-3"),
            dbc.Col(make_simple_kpi_card("ret-kpi-roibo", "Khách hàng RỜI BỎ (Churn)", "🚪", "#EF4444"), lg=3, md=6, className="mb-3"),
            dbc.Col(make_simple_kpi_card("ret-kpi-duytri", "Khách hàng DUY TRÌ (Ổn định)", "✅", "#3B82F6"), lg=3, md=6, className="mb-3")
        ], className="g-3"),
        
        # SECTION 2: Bảng chi tiết doanh thu TĂNG
        html.Div([
            html.Div([
                html.Span("📈 Chi tiết Khách hàng Hiện hữu TĂNG doanh thu", style={"fontWeight": "bold", "fontSize": "15px", "color": "#1E293B"}),
                html.Div([
                    dbc.Button("📥 Xuất Excel", id="ret-btn-export-tang", color="success", size="sm"),
                    dcc.Download(id="ret-download-tang")
                ], style={"display": "flex", "alignItems": "center"})
            ], style={"display": "flex", "justifyContent": "between", "alignItems": "center", "flexWrap": "wrap", "marginBottom": "15px", "marginTop": "20px"}),
            dbc.Spinner(html.Div(id="ret-table-tang-container"), color="primary")
        ]),
        
        # SECTION 3: Bảng chi tiết doanh thu GIẢM
        html.Div([
            html.Div([
                html.Span("📉 Chi tiết Khách hàng Hiện hữu GIẢM doanh thu", style={"fontWeight": "bold", "fontSize": "15px", "color": "#1E293B"}),
                html.Div([
                    dbc.Button("📥 Xuất Excel", id="ret-btn-export-giam", color="warning", size="sm"),
                    dcc.Download(id="ret-download-giam")
                ], style={"display": "flex", "alignItems": "center"})
            ], style={"display": "flex", "justifyContent": "between", "alignItems": "center", "flexWrap": "wrap", "marginBottom": "15px", "marginTop": "30px"}),
            dbc.Spinner(html.Div(id="ret-table-giam-container"), color="primary")
        ]),
        
        # SECTION 4: Bảng chi tiết khách hàng RỜI BỎ (Churn)
        html.Div([
            html.Div([
                html.Span("🚪 Chi tiết Khách hàng Hiện hữu RỜI BỎ (Churn)", style={"fontWeight": "bold", "fontSize": "15px", "color": "#1E293B"}),
                html.Div([
                    dbc.Button("📥 Xuất Excel", id="ret-btn-export-roibo", color="danger", size="sm"),
                    dcc.Download(id="ret-download-roibo")
                ], style={"display": "flex", "alignItems": "center"})
            ], style={"display": "flex", "justifyContent": "between", "alignItems": "center", "flexWrap": "wrap", "marginBottom": "15px", "marginTop": "30px"}),
            dbc.Spinner(html.Div(id="ret-table-roibo-container"), color="primary")
        ])
    ])
