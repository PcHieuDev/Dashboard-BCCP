# -*- coding: utf-8 -*-
"""
Component KPI Cards hiển thị các chỉ số doanh thu chi tiết cấu phần BCCP.
"""

from dash import html
import dash_bootstrap_components as dbc


def make_kpi_card_layout(card_id, title, icon):
    """
    Tạo cấu trúc layout HTML cho một thẻ KPI Card đơn lẻ.

    Args:
        card_id (str): Định danh ID của thẻ (VD: kpi-tt, kpi-tmdt).
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
    Tạo Layout Grid KPI trang /bccp:
    - Phần 1: 4 KPI cards chi tiết cấu phần BCCP (TT, TMĐT, QT, PHBC)
    - Phần 2: Card Khách hàng

    Returns:
        html.Div: Layout Grid các thẻ KPI.
    """
    return html.Div([

        # ── Phần 1: Chi tiết cấu phần BCCP (4 thành phần) ─────────────────
        html.Div("📦 Chi tiết cấu phần BCCP", className="section-header", style={"marginTop": 0}),
        dbc.Row([
            dbc.Col(make_kpi_card_layout("kpi-tt",   "Bưu chính Truyền thống", "📮"), md=3),
            dbc.Col(make_kpi_card_layout("kpi-tmdt", "Bưu chính TMĐT",         "🛒"), md=3),
            dbc.Col(make_kpi_card_layout("kpi-qt",   "Bưu chính Quốc tế",      "🌍"), md=3),
            dbc.Col(make_kpi_card_layout("kpi-phbc", "Phát hành báo chí",       "📰"), md=3),
        ], style={"marginBottom": "20px"}),

        # ── Phần 2: Phát triển Khách hàng ───────────────────────────────────
        html.Div("👥 Phát triển Khách hàng", className="section-header"),
        dbc.Row([
            dbc.Col(make_kpi_card_layout("kpi-kh", "Khách hàng phát sinh (Có HĐ)", "👥"), md=4),
        ]),
    ])
