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
    - Phần 1: 5 KPI cards (TT, TMĐT, QT, PHBC, SL)
    - Phần 2: 2 KPI cards (Khách hàng, % Kế hoạch)

    Returns:
        html.Div: Layout Grid các thẻ KPI.
    """
    return html.Div([

        # ── Phần 1: Chi tiết cấu phần & Sản lượng BCCP (5 thành phần) ─────────────────
        html.Div("📦 Chi tiết cấu phần & Sản lượng BCCP", className="section-header", style={"marginTop": 0}),
        dbc.Row([
            dbc.Col(make_kpi_card_layout("kpi-tt",   "Bưu chính Truyền thống", "📮"), lg=2, md=4, sm=6, className="mb-3"),
            dbc.Col(make_kpi_card_layout("kpi-tmdt", "Bưu chính TMĐT",         "🛒"), lg=2, md=4, sm=6, className="mb-3"),
            dbc.Col(make_kpi_card_layout("kpi-qt",   "Bưu chính Quốc tế",      "🌍"), lg=2, md=4, sm=6, className="mb-3"),
            dbc.Col(make_kpi_card_layout("kpi-phbc", "Phát hành báo chí",       "📰"), lg=2, md=4, sm=6, className="mb-3"),
            dbc.Col(make_kpi_card_layout("kpi-sl",   "Sản lượng tổng",         "📦"), lg=2, md=4, sm=6, className="mb-3"),
        ], className="g-2", style={"marginBottom": "20px"}),

        # ── Phần 2: Phát triển Khách hàng & Kế hoạch ───────────────────────────────────
        html.Div("👥 Phát triển Khách hàng & Kế hoạch", className="section-header"),
        dbc.Row([
            dbc.Col(make_kpi_card_layout("kpi-kh", "Khách hàng phát sinh (Có HĐ)", "👥"), lg=6, md=6, className="mb-3"),
            dbc.Col(html.Div([
                html.Div([
                    html.Div("% Hoàn thành Kế hoạch", className="kpi-title"),
                    html.Span("🎯", style={"fontSize": "20px", "float": "right", "marginTop": "-24px"})
                ]),
                html.Div("— %", id="kpi-plan-value", className="kpi-value"),
                html.Div(id="kpi-plan-subtext", className="delta-row", style={"marginTop": "8px", "color": "#64748B", "fontSize": "12px"})
            ], className="kpi-card"), lg=6, md=6, className="mb-3"),
        ], className="g-3")
    ])
