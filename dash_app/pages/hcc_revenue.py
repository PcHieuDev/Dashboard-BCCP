# -*- coding: utf-8 -*-
"""
Trang Tổng quan dịch vụ Hành chính công (HCC).
"""

from dash_app.pages.service_overview import create_service_overview_layout

def create_hcc_revenue_layout():
    """Tạo layout cho trang HCC"""
    return create_service_overview_layout("HCC", "🏛️", "#10B981")

