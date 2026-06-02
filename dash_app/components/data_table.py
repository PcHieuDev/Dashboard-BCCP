# -*- coding: utf-8 -*-
"""
Component Bảng dữ liệu (Data Table) hiển thị chi tiết doanh thu đa chiều.
"""

import pandas as pd
from dash import dash_table, html

# Map nhãn tiếng Việt sang key tiếng Anh trong dropdown Group By
GROUP_BY_LABEL_MAP = {
    "Nhóm dịch vụ": "nhom_dv",
    "Dịch vụ chi tiết": "dich_vu",
    "Cụm": "cum",
    "Bưu điện Xã/Phường": "bdx",
    "Mã bưu cục": "buu_cuc",
    "Khách hàng (CMS)": "cms",
    "Loại Khách hàng": "loai_kh",
    "Trạng thái Hợp đồng": "hop_dong",
    "Ngày chấp nhận": "ngay"
}

# Các cột ánh xạ labels hiển thị tiêu đề bảng sang tiếng Việt
COL_LABEL_MAP = {
    'nhom_dv': 'Nhóm dịch vụ', 
    'dich_vu': 'Dịch vụ chi tiết', 
    'cum': 'Cụm', 
    'bdx': 'BĐX', 
    'buu_cuc': 'Mã bưu cục', 
    'cms': 'Khách hàng',
    'loai_kh': 'Loại khách hàng', 
    'hop_dong': 'Trạng thái HĐ', 
    'ngay': 'Ngày',
    'san_luong': 'Sản lượng', 
    'khoi_luong_thuc': 'Khối lượng thực (kg)',
    'cuoc_cb_tong': 'Cước CB', 
    'cuoc_tt_tong': 'Cước TT', 
    'cuoc_tt_gom_vat': 'Cước gồm VAT', 
    'so_kh': 'Số KH',
    
    # So sánh Kỳ trước
    'san_luong_prev': 'Sản lượng kỳ trước', 
    'khoi_luong_thuc_prev': 'Khối lượng kỳ trước',
    'cuoc_cb_tong_prev': 'Cước CB kỳ trước', 
    'cuoc_tt_tong_prev': 'Cước TT kỳ trước',
    'cuoc_tt_gom_vat_prev': 'Cước gồm VAT kỳ trước', 
    'so_kh_prev': 'Số KH kỳ trước',
    'san_luong_pct_change': 'SL kỳ trước (+/- %)', 
    'khoi_luong_thuc_pct_change': 'KL kỳ trước (+/- %)',
    'cuoc_cb_tong_pct_change': 'Cước CB kỳ trước (+/- %)', 
    'cuoc_tt_tong_pct_change': 'Cước TT kỳ trước (+/- %)',
    'cuoc_tt_gom_vat_pct_change': 'Cước gồm VAT kỳ trước (+/- %)', 
    'so_kh_pct_change': 'Số KH kỳ trước (+/- %)',
    
    # So sánh Cùng kỳ năm trước (YoY)
    'san_luong_yoy': 'Sản lượng cùng kỳ', 
    'khoi_luong_thuc_yoy': 'Khối lượng cùng kỳ',
    'cuoc_cb_tong_yoy': 'Cước CB cùng kỳ', 
    'cuoc_tt_tong_yoy': 'Cước TT cùng kỳ',
    'cuoc_tt_gom_vat_yoy': 'Cước gồm VAT cùng kỳ', 
    'so_kh_yoy': 'Số KH cùng kỳ',
    'san_luong_yoy_pct_change': 'SL cùng kỳ (+/- %)', 
    'khoi_luong_thuc_yoy_pct_change': 'KL cùng kỳ (+/- %)',
    'cuoc_cb_tong_yoy_pct_change': 'Cước CB cùng kỳ (+/- %)', 
    'cuoc_tt_tong_yoy_pct_change': 'Cước TT cùng kỳ (+/- %)',
    'cuoc_tt_gom_vat_yoy_pct_change': 'Cước gồm VAT cùng kỳ (+/- %)', 
    'so_kh_yoy_pct_change': 'Số KH cùng kỳ (+/- %)'
}

def render_revenue_datatable(df, groupby_cols, compare_opt):
    """
    Format dữ liệu và khởi tạo DataTable hiển thị kết quả báo cáo.
    """
    if df.empty:
        return html.Div(
            "Không tìm thấy dữ liệu phù hợp với bộ lọc hiện tại.", 
            style={"padding": "20px", "textAlign": "center", "color": "#64748B"}
        )

    # 1. Xác định cấu trúc cột hiển thị
    columns = []
    
    # Thêm các cột groupby đã chọn
    for col in groupby_cols:
        columns.append({"name": COL_LABEL_MAP.get(col, col), "id": col})
        
    # Thêm các cột chỉ số (kỳ hiện tại)
    metrics = ['san_luong', 'khoi_luong_thuc', 'cuoc_cb_tong', 'cuoc_tt_tong', 'cuoc_tt_gom_vat', 'so_kh']
    for col in metrics:
        columns.append({"name": COL_LABEL_MAP.get(col, col), "id": col})
        
    # Thêm các cột so sánh kỳ trước
    if compare_opt in ('prev_period', 'both'):
        for m in metrics:
            columns.append({"name": COL_LABEL_MAP.get(f"{m}_prev", f"{m}_prev"), "id": f"{m}_prev"})
            columns.append({"name": COL_LABEL_MAP.get(f"{m}_pct_change", f"{m}_pct_change"), "id": f"{m}_pct_change"})
            
    # Thêm các cột so sánh YoY
    if compare_opt in ('yoy', 'both'):
        for m in metrics:
            columns.append({"name": COL_LABEL_MAP.get(f"{m}_yoy", f"{m}_yoy"), "id": f"{m}_yoy"})
            columns.append({"name": COL_LABEL_MAP.get(f"{m}_yoy_pct_change", f"{m}_yoy_pct_change"), "id": f"{m}_yoy_pct_change"})

    # 2. Định dạng dữ liệu hiển thị (Bản sao để tránh thay đổi dữ liệu gốc)
    df_display = df.copy()
    
    for col in df_display.columns:
        if col in groupby_cols:
            continue
        if 'pct_change' in col:
            # Định dạng phần trăm (+12.3% hoặc -4.5%)
            import numpy as np
            df_display[col] = df_display[col].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) and x != 0 and np.isfinite(x) else "-")
        elif col in ('san_luong', 'san_luong_prev', 'san_luong_yoy', 'so_kh', 'so_kh_prev', 'so_kh_yoy'):
            # Định dạng số nguyên
            df_display[col] = df_display[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
        elif 'khoi_luong_thuc' in col:
            # Dữ liệu gốc trong DB lưu bằng gram (g), hiển thị đổi sang Kilogram (kg)
            df_display[col] = df_display[col].apply(lambda x: f"{(x / 1000.0):,.1f} kg" if pd.notna(x) else "0.0 kg")
        elif 'cuoc_' in col:
            # Định dạng tiền tệ VND
            df_display[col] = df_display[col].apply(lambda x: f"{x:,.0f} đ" if pd.notna(x) else "0 đ")

    # 3. Khởi tạo đối tượng DataTable
    table = dash_table.DataTable(
        id='revenue-detail-datatable',
        columns=columns,
        data=df_display.to_dict('records'),
        page_size=15,
        sort_action="native",
        filter_action="native",
        export_format="xlsx",
        export_headers="display",
        style_table={'overflowX': 'auto', 'minWidth': '100%'},
        style_header={
            'backgroundColor': '#F1F5F9',
            'fontWeight': 'bold',
            'color': '#1E293B',
            'border': '1px solid #E2E8F0',
            'textAlign': 'left',
            'padding': '12px 10px'
        },
        style_cell={
            'border': '1px solid #E2E8F0',
            'padding': '10px 10px',
            'fontSize': '13px',
            'color': '#334155',
            'fontFamily': 'Inter, sans-serif'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#F8FAFC',
            }
        ]
    )
    return table
