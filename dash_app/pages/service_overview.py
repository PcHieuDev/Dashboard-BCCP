# -*- coding: utf-8 -*-
"""
Layout trang Tổng quan dịch vụ (BCCP, HCC, TCBC, PPBL) v2.0.
Cấu trúc trang hiển thị đồng nhất sử dụng mô hình của trang Tổng quan chung nhưng lọc theo dịch vụ.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import sqlite3
from config.settings import DB_PATH

def get_sub_services(service_key):
    """Lấy danh sách các nhóm dịch vụ con của nhóm dịch vụ chính từ danh mục"""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT nhom_dich_vu FROM dim_dichvu 
            WHERE nhom_chinh = ? AND nhom_dich_vu IS NOT NULL
            ORDER BY nhom_dich_vu
        """, (service_key,))
        lst = [r[0] for r in cursor.fetchall()]
        if service_key == "BCCP":
            order = {"Truyền thống": 0, "TMĐT": 1, "Quốc tế": 2, "Phát hành báo chí": 3}
            lst.sort(key=lambda x: order.get(x, 99))
        return lst
    except Exception as e:
        print(f"Lỗi truy vấn nhóm con cho {service_key}: {e}")
        return []
    finally:
        conn.close()

def make_service_kpi_card_layout(prefix, card_id, title, icon, border_color):
    """Tạo KPI card cho nhóm dịch vụ con"""
    return html.Div([
        html.Div([
            html.Span(icon, style={"fontSize": "18px", "marginRight": "8px"}),
            html.Span(title, className="kpi-title", style={"fontWeight": "bold", "color": "#1E293B", "fontSize": "13px"}),
        ], style={"display": "flex", "alignItems": "center", "borderBottom": "1px solid #E2E8F0", "paddingBottom": "6px"}),
        
        html.Div([
            html.Div("Doanh thu kỳ này", style={"fontSize": "11px", "color": "#64748B", "marginTop": "4px"}),
            html.Div("— đ", id=f"{prefix}-{card_id}-value", className="kpi-value", style={"fontSize": "18px", "fontWeight": "bold", "color": "#0F172A"}),
        ]),
        
        html.Div([
            html.Div([
                html.Span("Kỳ trước: ", style={"color": "#64748B"}),
                html.Span("—", id=f"{prefix}-{card_id}-compare-prev", style={"fontWeight": "bold"})
            ], style={"fontSize": "12px", "marginTop": "4px"}),
            
            html.Div([
                html.Span("Cùng kỳ: ", style={"color": "#64748B"}),
                html.Span("—", id=f"{prefix}-{card_id}-compare-yoy", style={"fontWeight": "bold"})
            ], style={"fontSize": "12px", "marginTop": "2px"}),
            
            html.Div([
                html.Span("Kế hoạch: ", style={"color": "#64748B"}),
                html.Span("—", id=f"{prefix}-{card_id}-compare-plan", style={"fontWeight": "bold"})
            ], style={"fontSize": "12px", "marginTop": "2px"}),
        ], style={"marginTop": "6px", "borderTop": "1px solid #F1F5F9", "paddingTop": "6px"})
        
    ], className="kpi-card", style={
        "borderTop": f"4px solid {border_color}", 
        "padding": "10px",
        "backgroundColor": "#FFFFFF",
        "borderRadius": "8px",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
        "height": "100%"
    })

def create_service_overview_layout(service_key, service_icon, border_color):
    """
    Tạo layout Tổng quan dịch vụ chung cho một nhóm dịch vụ (BCCP, HCC, TCBC, PPBL).
    Prefix ID sẽ được định nghĩa là: bccp-overview-, hcc-overview-, v.v.
    """
    prefix = f"{service_key.lower()}-overview"
    sub_services = get_sub_services(service_key)
    
    # Render KPI Cards cho các dịch vụ con
    kpi_cols = []
    # Palette màu cho các sub-services
    sub_colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#6366F1", "#14B8A6"]
    
    for i, sub_svc in enumerate(sub_services):
        color = sub_colors[i % len(sub_colors)]
        card_id = f"sub-{i}"
        kpi_cols.append(
            dbc.Col(make_service_kpi_card_layout(prefix, card_id, sub_svc, service_icon, color), lg=3, md=6, className="mb-3")
        )
        
    if not kpi_cols:
        kpi_cols.append(dbc.Col(html.Div("Không tìm thấy dịch vụ con nào được cấu hình.", style={"color": "#64748B"}), lg=12))

    return html.Div([
        # Dùng dcc.Store để lưu trữ cấu hình dịch vụ này cho callbacks nhận diện
        dcc.Store(id=f"{prefix}-service-key-store", data={"service_key": service_key, "sub_services": sub_services}),
        
        # SECTION 1: Các Thẻ KPI
        html.Div(f"📊 Doanh thu & Tiến độ chi tiết nhóm dịch vụ {service_key}", className="section-header", style={"marginTop": 0, "marginBottom": "12px", "fontWeight": "bold", "fontSize": "16px"}),
        dbc.Row(kpi_cols, className="g-3"),
        
        # SECTION 2: Top 10 Bưu điện xã/phường
        html.Div(f"🏆 Top 10 Bưu điện Xã / Phường nổi bật ({service_key})", className="section-header", style={"marginTop": "15px", "marginBottom": "12px", "fontWeight": "bold", "fontSize": "16px"}),
        dbc.Row([
            # Top 10 tăng trưởng kỳ trước
            dbc.Col([
                html.Div([
                    html.Div("📈 Top 10 tăng trưởng vs Kỳ trước", style={"fontWeight": "bold", "color": "#1E293B", "fontSize": "13px", "marginBottom": "8px"}),
                    dbc.Spinner(html.Div(id=f"{prefix}-top10-prev-container"))
                ], className="info-box", style={"padding": "12px", "backgroundColor": "#FFFFFF", "borderRadius": "8px", "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"})
            ], lg=4, md=12, className="mb-3"),
            
            # Top 10 tăng trưởng cùng kỳ (YoY)
            dbc.Col([
                html.Div([
                    html.Div("📅 Top 10 tăng trưởng vs Cùng kỳ", style={"fontWeight": "bold", "color": "#1E293B", "fontSize": "13px", "marginBottom": "8px"}),
                    dbc.Spinner(html.Div(id=f"{prefix}-top10-yoy-container"))
                ], className="info-box", style={"padding": "12px", "backgroundColor": "#FFFFFF", "borderRadius": "8px", "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"})
            ], lg=4, md=12, className="mb-3"),
            
            # Top 10 hoàn thành kế hoạch
            dbc.Col([
                html.Div([
                    html.Div("🎯 Top 10 hoàn thành Kế hoạch", style={"fontWeight": "bold", "color": "#1E293B", "fontSize": "13px", "marginBottom": "8px"}),
                    dbc.Spinner(html.Div(id=f"{prefix}-top10-plan-container"))
                ], className="info-box", style={"padding": "12px", "backgroundColor": "#FFFFFF", "borderRadius": "8px", "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"})
            ], lg=4, md=12, className="mb-3")
        ], className="g-3"),
        
        # SECTION 3: Biểu đồ cột doanh thu 12 kỳ liên tiếp
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div(f"📊 Biến động doanh thu {service_key} qua 12 kỳ liên tiếp (Phân nhóm dịch vụ con)", className="section-header", style={"fontWeight": "bold", "fontSize": "14px", "marginBottom": "10px"}),
                    dcc.Graph(id=f"{prefix}-stacked-bar-12p", config={"displayModeBar": False})
                ], className="info-box", style={"padding": "15px", "backgroundColor": "#FFFFFF", "borderRadius": "8px", "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"})
            ], lg=12, className="mb-3")
        ], className="g-3 mt-1"),
        
        # SECTION 4: 2 Bảng doanh thu chi tiết theo xã & lũy kế
        # Bảng A: Chi tiết kỳ hiện tại
        html.Div([
            html.Div([
                html.Span(f"📋 Chi tiết doanh thu theo Bưu cục Xã ({service_key} - Kỳ hiện tại)", style={"fontWeight": "bold", "fontSize": "15px", "color": "#1E293B"}),
                html.Div([
                    html.Span("So sánh với: ", style={"fontSize": "13px", "color": "#64748B", "marginRight": "10px"}),
                    dbc.RadioItems(
                        id=f"{prefix}-table-a-compare-selector",
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
            dbc.Spinner(html.Div(id=f"{prefix}-table-a-container"))
        ]),
        
        # Bảng B: Chi tiết lũy kế YTD
        html.Div([
            html.Div([
                html.Span(f"📋 Chi tiết doanh thu lũy kế YTD theo Bưu cục Xã ({service_key} - Đầu năm đến nay)", style={"fontWeight": "bold", "fontSize": "15px", "color": "#1E293B"}),
                html.Div([
                    html.Span("So sánh với: ", style={"fontSize": "13px", "color": "#64748B", "marginRight": "10px"}),
                    dbc.RadioItems(
                        id=f"{prefix}-table-b-compare-selector",
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
            ], style={"display": "flex", "justifyContent": "between", "alignItems": "center", "flexWrap": "wrap", "marginBottom": "10px", "marginTop": "30px"}),
            dbc.Spinner(html.Div(id=f"{prefix}-table-b-container"))
        ])
    ])
