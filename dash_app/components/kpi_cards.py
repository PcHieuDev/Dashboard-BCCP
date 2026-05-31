# -*- coding: utf-8 -*-
"""
Component KPI Cards hiển thị các chỉ số doanh thu điều hành chính và sparkline xu hướng.
"""

from dash import html
import dash_bootstrap_components as dbc

def make_kpi_card_layout(card_id, title, icon):
    """
    Tạo cấu trúc layout HTML cho một thẻ KPI Card đơn lẻ.
    
    Args:
        card_id (str): Định danh ID của thẻ (VD: kpi-tong, kpi-bccp).
        title (str): Tiêu đề hiển thị của thẻ KPI.
        icon (str): Emoji đại diện cho thẻ KPI.
        
    Returns:
        html.Div: Cấu trúc layout của 1 thẻ KPI.
    """
    return html.Div([
        html.Div([
            html.Div(title, className="kpi-title"),
            html.Span(icon, style={"fontSize": "20px", "float": "right", "marginTop": "-24px"})
        ]),
        html.Div("0.00 đ", id=f"{card_id}-value", className="kpi-value"),
        html.Div(id=f"{card_id}-sparkline"),
        html.Div(id=f"{card_id}-delta-prev", className="delta-row"),
        html.Div(id=f"{card_id}-delta-yoy", className="delta-row", style={"marginTop": "2px"})
    ], className="kpi-card")

def create_kpi_grid():
    """
    Tạo Layout Grid chứa toàn bộ 7 thẻ KPI và một hộp thông tin hướng dẫn.
    
    Returns:
        html.Div: Layout Grid các thẻ KPI.
    """
    return html.Div([
        html.Div("💰 Chỉ số doanh thu điều hành chính", className="section-header"),
        dbc.Row([
            dbc.Col(make_kpi_card_layout("kpi-tong", "Tổng Doanh thu", "💵"), md=4),
            dbc.Col(make_kpi_card_layout("kpi-bccp", "Doanh thu BCCP", "📦"), md=4),
            dbc.Col(make_kpi_card_layout("kpi-hcc", "Doanh thu Hành chính công", "🏛️"), md=4),
        ], style={"marginBottom": "20px"}),
        
        html.Div("📦 Chi tiết cấu phần BCCP", className="section-header"),
        dbc.Row([
            dbc.Col(make_kpi_card_layout("kpi-tt", "Bưu chính Truyền thống", "📮"), md=4),
            dbc.Col(make_kpi_card_layout("kpi-tmdt", "Bưu chính TMĐT", "🛒"), md=4),
            dbc.Col(make_kpi_card_layout("kpi-qt", "Bưu chính Quốc tế", "🌍"), md=4),
        ], style={"marginBottom": "20px"}),
        
        html.Div("👥 Phát triển Khách hàng", className="section-header"),
        dbc.Row([
            dbc.Col(make_kpi_card_layout("kpi-kh", "Khách hàng phát sinh (Có HĐ)", "👥"), md=4),
            dbc.Col([
                html.Div([
                    html.H4("💡 Hướng dẫn nhanh điều hành"),
                    html.Ul([
                        html.Li("Sử dụng Thanh bộ lọc bên trái (Sidebar) để lọc nhanh doanh thu theo Cụm, BĐX hoặc Bưu cục chấp nhận."),
                        html.Li("Dữ liệu khách hàng phát sinh chỉ tính các khách hàng có mã CMS hợp đồng (không tính vãng lai)."),
                        html.Li("Để xem chi tiết dữ liệu, thực hiện Group By hoặc xuất file Excel, vui lòng bấm chọn tab Doanh thu chi tiết."),
                        html.Li("Hệ thống tự động tính toán loại khách hàng (Bán mới, Tái bán, Hiện hữu) theo nhịp tháng của kỳ đang lọc.")
                    ])
                ], className="info-box")
            ], md=8)
        ])
    ])
