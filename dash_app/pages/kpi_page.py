# -*- coding: utf-8 -*-
"""
Trang Tổng quan dịch vụ BCCP (Layout gọi về service_overview).
"""

from dash_app.pages.service_overview import create_service_overview_layout

def create_kpi_page_layout():
    """Tạo layout cho trang chủ dịch vụ BCCP"""
    return create_service_overview_layout("BCCP", "📦", "#3B82F6")
