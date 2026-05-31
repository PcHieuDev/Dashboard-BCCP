# -*- coding: utf-8 -*-
"""
Layout trang chủ Tổng quan KPI.
"""

import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from components.kpi_cards import create_kpi_grid

def create_kpi_page_layout():
    """
    Trả về layout hoàn chỉnh của trang tổng quan KPI.
    
    Returns:
        html.Div: Layout trang KPI.
    """
    return create_kpi_grid()
