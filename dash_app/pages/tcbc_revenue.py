# -*- coding: utf-8 -*-
"""
Trang Tổng quan dịch vụ Tài chính Bưu chính (TCBC).
"""

from dash_app.pages.service_overview import create_service_overview_layout

def create_tcbc_revenue_layout():
    """Tạo layout cho trang TCBC"""
    return create_service_overview_layout("TCBC", "💰", "#F59E0B")

