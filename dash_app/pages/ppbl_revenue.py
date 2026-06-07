# -*- coding: utf-8 -*-
"""
Trang Tổng quan dịch vụ Phân phối bán lẻ (PPBL).
"""

from dash_app.pages.service_overview import create_service_overview_layout

def create_ppbl_revenue_layout():
    """Tạo layout cho trang PPBL"""
    return create_service_overview_layout("Phân phối bán lẻ", "🛍️", "#8B5CF6")
