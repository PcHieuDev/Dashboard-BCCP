# -*- coding: utf-8 -*-
"""
Layout trang Tổng quan chung (Global Overview) v2.0.
Hiển thị KPI 4 dịch vụ, Top 10 xã theo 3 chỉ tiêu, biểu đồ 12 kỳ, và 2 bảng chi tiết xã/lũy kế.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

def make_global_kpi_card_layout(card_id, title, icon, border_color):
    """Tạo KPI card 3 chỉ tiêu ngang cho trang Tổng quan với viền màu đặc trưng"""
    return html.Div([
        html.Div([
            html.Span(icon, style={"fontSize": "20px", "marginRight": "8px"}),
            html.Span(title, className="kpi-title", style={"fontWeight": "bold", "color": "#1E293B"}),
        ], style={"display": "flex", "alignItems": "center", "borderBottom": "1px solid #E2E8F0", "paddingBottom": "8px"}),
        
        # Doanh thu kỳ hiện tại
        html.Div([
            html.Div("Doanh thu kỳ này", style={"fontSize": "11px", "color": "#64748B", "marginTop": "6px"}),
            html.Div("— đ", id=f"{card_id}-value", className="kpi-value", style={"fontSize": "20px", "fontWeight": "bold", "color": "#0F172A"}),
        ]),
        
        # So sánh 3 chỉ số
        html.Div([
            # 1. So với Kỳ trước
            html.Div([
                html.Span("Kỳ trước: ", style={"color": "#64748B"}),
                html.Span("—", id=f"{card_id}-compare-prev", style={"fontWeight": "bold"})
            ], style={"fontSize": "12px", "marginTop": "4px"}),
            
            # 2. So với Cùng kỳ năm trước
            html.Div([
                html.Span("Cùng kỳ: ", style={"color": "#64748B"}),
                html.Span("—", id=f"{card_id}-compare-yoy", style={"fontWeight": "bold"})
            ], style={"fontSize": "12px", "marginTop": "2px"}),
            
            # 3. So với Kế hoạch hoàn thành
            html.Div([
                html.Span("Kế hoạch: ", style={"color": "#64748B"}),
                html.Span("—", id=f"{card_id}-compare-plan", style={"fontWeight": "bold"})
            ], style={"fontSize": "12px", "marginTop": "2px"}),
        ], style={"marginTop": "6px", "borderTop": "1px solid #F1F5F9", "paddingTop": "6px"})
        
    ], className="kpi-card", style={
        "borderTop": f"4px solid {border_color}", 
        "padding": "12px",
        "backgroundColor": "#FFFFFF",
        "borderRadius": "8px",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
        "height": "100%"
    })

def create_global_overview_layout():
    """Tạo layout chính cho trang Tổng quan chung v2.0"""
    return html.Div([
        # SECTION 1: 4 Thẻ KPI dịch vụ
        html.Div("📊 Doanh thu & Tiến độ các nhóm dịch vụ", className="section-header", style={"marginTop": 0, "marginBottom": "12px", "fontWeight": "bold", "fontSize": "16px"}),
        dbc.Row([
            dbc.Col(make_global_kpi_card_layout("global-kpi-bccp", "Bưu chính Chuyển phát (BCCP)", "📦", "#3B82F6"), lg=3, md=6, className="mb-3"),
            dbc.Col(make_global_kpi_card_layout("global-kpi-hcc", "Hành chính công (HCC)", "🏛️", "#10B981"), lg=3, md=6, className="mb-3"),
            dbc.Col(make_global_kpi_card_layout("global-kpi-tcbc", "Tài chính Bưu chính (TCBC)", "💰", "#F59E0B"), lg=3, md=6, className="mb-3"),
            dbc.Col(make_global_kpi_card_layout("global-kpi-ppbl", "Phân phối bán lẻ (PPBL)", "🛍️", "#8B5CF6"), lg=3, md=6, className="mb-3"),
        ], className="g-3"),
        
        # SECTION 2: Top 10 Bưu điện xã/phường
        html.Div("🏆 Top 10 Bưu điện Xã / Phường nổi bật", className="section-header", style={"marginTop": "15px", "marginBottom": "12px", "fontWeight": "bold", "fontSize": "16px"}),
        dbc.Row([
            # Top 10 tăng trưởng kỳ trước
            dbc.Col([
                html.Div([
                    html.Div("📈 Top 10 tăng trưởng vs Kỳ trước", style={"fontWeight": "bold", "color": "#1E293B", "fontSize": "13px", "marginBottom": "8px"}),
                    dbc.Spinner(html.Div(id="global-top10-prev-container"))
                ], className="info-box", style={"padding": "12px", "backgroundColor": "#FFFFFF", "borderRadius": "8px", "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"})
            ], lg=4, md=12, className="mb-3"),
            
            # Top 10 tăng trưởng cùng kỳ (YoY)
            dbc.Col([
                html.Div([
                    html.Div("📅 Top 10 tăng trưởng vs Cùng kỳ", style={"fontWeight": "bold", "color": "#1E293B", "fontSize": "13px", "marginBottom": "8px"}),
                    dbc.Spinner(html.Div(id="global-top10-yoy-container"))
                ], className="info-box", style={"padding": "12px", "backgroundColor": "#FFFFFF", "borderRadius": "8px", "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"})
            ], lg=4, md=12, className="mb-3"),
            
            # Top 10 hoàn thành kế hoạch
            dbc.Col([
                html.Div([
                    html.Div("🎯 Top 10 hoàn thành Kế hoạch", style={"fontWeight": "bold", "color": "#1E293B", "fontSize": "13px", "marginBottom": "8px"}),
                    dbc.Spinner(html.Div(id="global-top10-plan-container"))
                ], className="info-box", style={"padding": "12px", "backgroundColor": "#FFFFFF", "borderRadius": "8px", "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"})
            ], lg=4, md=12, className="mb-3")
        ], className="g-3"),
        
        # SECTION 3: Biểu đồ cột doanh thu 12 kỳ liên tiếp
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div("📊 Biến động doanh thu 12 kỳ liên tiếp (Phân nhóm dịch vụ)", className="section-header", style={"fontWeight": "bold", "fontSize": "14px", "marginBottom": "10px"}),
                    dcc.Graph(id="global-stacked-bar-12p", config={"displayModeBar": False})
                ], className="info-box", style={"padding": "15px", "backgroundColor": "#FFFFFF", "borderRadius": "8px", "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"})
            ], lg=12, className="mb-3")
        ], className="g-3 mt-1"),
        
        # SECTION 4: 2 Bảng doanh thu chi tiết theo xã & lũy kế
        # Bảng A: Chi tiết kỳ hiện tại
        html.Div([
            html.Div([
                html.Span("📋 Chi tiết doanh thu", style={"fontWeight": "bold", "fontSize": "15px", "color": "#1E293B"}),
                html.Div([
                    html.Span("So sánh với: ", style={"fontSize": "13px", "color": "#64748B", "marginRight": "10px"}),
                    dbc.RadioItems(
                        id="global-table-a-compare-selector",
                        options=[
                            {"label": "Kỳ trước", "value": "prev"},
                            {"label": "Cùng kỳ năm trước", "value": "yoy"},
                            {"label": "Kế hoạch", "value": "plan"}
                        ],
                        value="plan",
                        inline=True,
                        style={"fontSize": "13px"}
                    )
                ], style={"display": "flex", "alignItems": "center"})
            ], style={"display": "flex", "justifyContent": "between", "alignItems": "center", "flexWrap": "wrap", "marginBottom": "10px", "marginTop": "20px"}),
            dbc.Spinner(html.Div(id="global-table-a-container"))
        ]),
        
        # Bảng B: Chi tiết lũy kế YTD
        html.Div([
            html.Div([
                html.Span("📋 Chi tiết doanh thu lũy kế YTD", style={"fontWeight": "bold", "fontSize": "15px", "color": "#1E293B"}),
                html.Div([
                    html.Span("So sánh với: ", style={"fontSize": "13px", "color": "#64748B", "marginRight": "10px"}),
                    dbc.RadioItems(
                        id="global-table-b-compare-selector",
                        options=[
                            {"label": "Cùng kỳ năm trước", "value": "yoy"},
                            {"label": "Kế hoạch", "value": "plan"}
                        ],
                        value="plan",
                        inline=True,
                        style={"fontSize": "13px"}
                    )
                ], style={"display": "flex", "alignItems": "center"})
            ], style={"display": "flex", "justifyContent": "between", "alignItems": "center", "flexWrap": "wrap", "marginBottom": "10px", "marginTop": "30px"}),
            dbc.Spinner(html.Div(id="global-table-b-container"))
        ])
    ])
