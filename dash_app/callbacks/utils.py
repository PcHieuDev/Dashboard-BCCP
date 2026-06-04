# -*- coding: utf-8 -*-
"""
Các hàm tiện ích helper dùng chung cho callbacks (format, sparkline, query cache).
"""

import sys
import base64
import functools
import sqlite3
import pandas as pd
from datetime import date, datetime
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH
from config.week_calendar import get_prev_period, get_same_period_prev_year, get_week_list, get_month_range
from analytics.revenue import query_revenue, query_customer_detail_pivot

# --------------------------------------------------------------------------
# HÀM FORMAT TIỀN TỆ & ĐO LƯỜNG
# --------------------------------------------------------------------------
def format_revenue(val):
    """Định dạng số tiền hiển thị thân thiện (tỷ, triệu, hoặc đồng)."""
    if val is None or pd.isna(val):
        return "0.00 đ"
    if abs(val) >= 1_000_000_000:
        return f"{val / 1_000_000_000:.2f} tỷ"
    elif abs(val) >= 1_000_000:
        return f"{val / 1_000_000:.1f} tr"
    else:
        return f"{val:,.0f} đ"

# --------------------------------------------------------------------------
# TẠO SPARKLINE SVG
# --------------------------------------------------------------------------
def generate_svg_sparkline_src(values: list, color: str) -> str:
    """Tạo chuỗi Data URI Base64 của ảnh SVG sparkline để chèn trực tiếp vào HTML."""
    width = 160
    height = 35
    padding = 2
    
    if not values or len(values) < 2:
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><line x1="0" y1="{height/2}" x2="{width}" y2="{height/2}" stroke="#E2E8F0" stroke-width="1" stroke-dasharray="3"/></svg>'
    else:
        v_min, v_max = min(values), max(values)
        v_range = v_max - v_min if v_max != v_min else 1.0
        
        points = []
        for i, val in enumerate(values):
            x = i * (width / (len(values) - 1))
            y = height - padding - ((val - v_min) / v_range) * (height - 2 * padding)
            points.append((x, y))
            
        polyline_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        fill_points = f"0,{height} " + polyline_points + f" {width},{height}"
        
        try:
            r = int(color.lstrip('#')[0:2], 16)
            g = int(color.lstrip('#')[2:4], 16)
            b = int(color.lstrip('#')[4:6], 16)
            fill_rgba = f"rgba({r},{g},{b},0.1)"
        except Exception:
            fill_rgba = "rgba(100,100,100,0.1)"
            
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" preserveAspectRatio="none">'
            f'<polygon points="{fill_points}" fill="{fill_rgba}" />'
            f'<polyline points="{polyline_points}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round" />'
            f'</svg>'
        )
    
    encoded = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{encoded}"

# --------------------------------------------------------------------------
# CACHING CHO QUERY (Tối ưu hóa tốc độ tải)
# --------------------------------------------------------------------------
@functools.lru_cache(maxsize=128)
def run_query_cached(
    date_from_str: str,
    date_to_str: str,
    date_column: str,
    nhom_dv: tuple | None,
    dich_vu: tuple | None,
    cum: str | None,
    bdx: str | None,
    buu_cuc: str | None,
    loai_kh: tuple | None,
    hop_dong: str | None,
    group_by_primary: str | None,
    group_by_secondary: str | None,
    compare_prev: bool,
    chu_ky: str | None,
    nam: int | None,
    compare_mode: str,
) -> str:
    """
    Thực hiện query dữ liệu từ SQLite và trả về dưới dạng JSON string.
    Sử dụng lru_cache để tăng tốc tối đa.
    """
    conn = sqlite3.connect(str(DB_PATH))
    try:
        df = query_revenue(
            conn=conn,
            date_from=date.fromisoformat(date_from_str),
            date_to=date.fromisoformat(date_to_str),
            date_column=date_column,
            nhom_dv=list(nhom_dv) if nhom_dv is not None else None,
            dich_vu=list(dich_vu) if dich_vu is not None else None,
            cum=cum,
            bdx=bdx,
            buu_cuc=buu_cuc,
            loai_kh=list(loai_kh) if loai_kh is not None else None,
            hop_dong=hop_dong,
            group_by_primary=group_by_primary,
            group_by_secondary=group_by_secondary,
            compare_prev=compare_prev,
            chu_ky=chu_ky,
            nam=nam,
            compare_mode=compare_mode
        )
        return df.to_json(orient='split', date_format='iso')
    finally:
        conn.close()

def get_df_from_cache(*args, **kwargs) -> pd.DataFrame:
    """Gọi cache trả về dữ liệu DataFrame."""
    json_data = run_query_cached(*args, **kwargs)
    # pd.read_json yêu cầu wrapper StringIO trên các phiên bản mới để tránh cảnh báo,
    # tuy nhiên ta vẫn sử dụng read_json trực tiếp hoặc StringIO nếu cần.
    # Để sửa FutureWarning: Wrap json_data trong StringIO
    from io import StringIO
    return pd.read_json(StringIO(json_data), orient='split')

def clear_query_cache():
    """Xóa bộ nhớ đệm truy vấn."""
    run_query_cached.cache_clear()


@functools.lru_cache(maxsize=128)
def run_customer_query_cached(
    date_from_str: str,
    date_to_str: str,
    date_column: str,
    nhom_dv: tuple | None,
    dich_vu: tuple | None,
    cum: str | None,
    bdx: str | None,
    buu_cuc: str | None,
    loai_kh: tuple | None,
    hop_dong: str | None,
    nam: int | None,
) -> str:
    """
    Thực hiện query chi tiết khách hàng xoay chiều (pivot) và trả về JSON string.
    Sử dụng lru_cache để tăng tốc tối đa.
    """
    conn = sqlite3.connect(str(DB_PATH))
    try:
        df = query_customer_detail_pivot(
            conn=conn,
            date_from=date.fromisoformat(date_from_str),
            date_to=date.fromisoformat(date_to_str),
            date_column=date_column,
            nhom_dv=list(nhom_dv) if nhom_dv is not None else None,
            dich_vu=list(dich_vu) if dich_vu is not None else None,
            cum=cum,
            bdx=bdx,
            buu_cuc=buu_cuc,
            loai_kh=list(loai_kh) if loai_kh is not None else None,
            hop_dong=hop_dong,
            nam=nam
        )
        return df.to_json(orient='split', date_format='iso')
    finally:
        conn.close()

def get_customer_df_from_cache(*args, **kwargs) -> pd.DataFrame:
    """Gọi cache trả về dữ liệu DataFrame của chi tiết khách hàng."""
    json_data = run_customer_query_cached(*args, **kwargs)
    from io import StringIO
    return pd.read_json(StringIO(json_data), orient='split')

def clear_customer_query_cache():
    """Xóa bộ nhớ đệm truy vấn chi tiết khách hàng."""
    run_customer_query_cached.cache_clear()


def resolve_filters_and_query_customer(year, period, date_range_start, date_range_end, week_idx, month_val, 
                                     nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong):
    """
    Chuyển đổi các thông số bộ lọc từ UI sang các đối tượng Date và thực hiện truy vấn chi tiết khách hàng qua Cache.
    """
    date_column = 'ngay_chap_nhan'
    if period == "Ngày":
        date_from = date.fromisoformat(date_range_start) if date_range_start else date(year, 1, 1)
        date_to = date.fromisoformat(date_range_end) if date_range_end else date(year, 1, 31)
    elif period == "Tuần":
        weeks = get_week_list(year)
        if week_idx is not None and 0 <= week_idx < len(weeks):
            w_num, w_start, w_end = weeks[week_idx]
            date_from, date_to = w_start, w_end
        else:
            date_from, date_to = date(year, 1, 1), date(year, 1, 7)
    else: # Tháng
        date_column = 'thang_du_lieu'
        date_from, date_to = get_month_range(year, month_val)
        
    # Chuẩn hóa giá trị bộ lọc
    from flask_login import current_user
    if current_user and current_user.is_authenticated and current_user.role == 'user' and current_user.assigned_cum:
        cum_filter = current_user.assigned_cum
    else:
        cum_filter = None if cum == "Tất cả" else cum
    bdx_filter = None if bdx == "Tất cả" else bdx
    bc_filter = None if buu_cuc == "Tất cả" else buu_cuc
    if not hop_dong or (isinstance(hop_dong, list) and len(hop_dong) != 1) or hop_dong == "Tất cả":
        hd_filter = None
    elif isinstance(hop_dong, list):
        hd_filter = hop_dong[0]
    else:
        hd_filter = hop_dong
    
    # Chuyển đổi list thành tuple để làm key cho lru_cache
    nhom_dv_tuple = tuple(nhom_dv) if nhom_dv else None
    spdv_tuple = tuple(spdv) if spdv else None
    loai_kh_tuple = tuple(loai_kh) if loai_kh else None
    
    df = get_customer_df_from_cache(
        date_from.isoformat(),
        date_to.isoformat(),
        date_column,
        nhom_dv_tuple,
        spdv_tuple,
        cum_filter,
        bdx_filter,
        bc_filter,
        loai_kh_tuple,
        hd_filter,
        year
    )
    
    return date_from, date_to, date_column, df

# --------------------------------------------------------------------------
# GIẢI QUYẾT BỘ LỌC VÀ TRUY VẤN
# --------------------------------------------------------------------------
def resolve_filters_and_query(year, period, date_range_start, date_range_end, week_idx, month_val, 
                              compare_mode, nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
                              group_by_primary='nhom_dv', group_by_secondary=None, compare_prev=False):
    """
    Chuyển đổi các thông số bộ lọc từ UI sang các đối tượng Date và thực hiện truy vấn qua Cache.
    """
    # Chuẩn hóa compare_mode nếu là list/tuple (từ checklist)
    if isinstance(compare_mode, (list, tuple)):
        has_prev = 'prev_period' in compare_mode
        has_yoy = 'yoy' in compare_mode
        if has_prev and has_yoy:
            compare_mode_str = 'both'
        elif has_prev:
            compare_mode_str = 'prev_period'
        elif has_yoy:
            compare_mode_str = 'yoy'
        else:
            compare_mode_str = 'none'
    else:
        compare_mode_str = compare_mode if compare_mode else 'none'

    date_column = 'ngay_chap_nhan'
    if period == "Ngày":
        date_from = date.fromisoformat(date_range_start) if date_range_start else date(year, 1, 1)
        date_to = date.fromisoformat(date_range_end) if date_range_end else date(year, 1, 31)
    elif period == "Tuần":
        weeks = get_week_list(year)
        if week_idx is not None and 0 <= week_idx < len(weeks):
            w_num, w_start, w_end = weeks[week_idx]
            date_from, date_to = w_start, w_end
        else:
            date_from, date_to = date(year, 1, 1), date(year, 1, 7)
    else: # Tháng
        date_column = 'thang_du_lieu'
        date_from, date_to = get_month_range(year, month_val)
        
    # Chuẩn hóa giá trị bộ lọc
    from flask_login import current_user
    if current_user and current_user.is_authenticated and current_user.role == 'user' and current_user.assigned_cum:
        cum_filter = current_user.assigned_cum
    else:
        cum_filter = None if cum == "Tất cả" else cum
    bdx_filter = None if bdx == "Tất cả" else bdx
    bc_filter = None if buu_cuc == "Tất cả" else buu_cuc
    if not hop_dong or (isinstance(hop_dong, list) and len(hop_dong) != 1) or hop_dong == "Tất cả":
        hd_filter = None
    elif isinstance(hop_dong, list):
        hd_filter = hop_dong[0]
    else:
        hd_filter = hop_dong
    
    # Chuyển đổi list thành tuple để làm key cho lru_cache
    nhom_dv_tuple = tuple(nhom_dv) if nhom_dv else None
    spdv_tuple = tuple(spdv) if spdv else None
    loai_kh_tuple = tuple(loai_kh) if loai_kh else None
    
    df = get_df_from_cache(
        date_from.isoformat(),
        date_to.isoformat(),
        date_column,
        nhom_dv_tuple,
        spdv_tuple,
        cum_filter,
        bdx_filter,
        bc_filter,
        loai_kh_tuple,
        hd_filter,
        group_by_primary,
        group_by_secondary,
        compare_prev,
        period,
        year,
        compare_mode_str
    )
    
    return date_from, date_to, date_column, df


def get_bccp_weeks(year):
    """
    Tính ranh giới các tuần BCCP cho năm.
    Tuần BCCP: Thứ 6 tuần trước -> Thứ 5 tuần này.
    Tuần 1 bắt đầu từ 01/01.
    Returns: list of (week_number, start_date, end_date)
    """
    from datetime import date, timedelta
    
    weeks = []
    current_date = date(year, 1, 1)
    
    # Tìm Thứ 5 đầu tiên kể từ 01/01 (weekday() == 3)
    days_to_thursday = (3 - current_date.weekday()) % 7
    first_thursday = current_date + timedelta(days=days_to_thursday)
    
    week_num = 1
    weeks.append((week_num, current_date, first_thursday))
    
    current_date = first_thursday + timedelta(days=1) # Thứ 6
    while current_date.year == year:
        next_thursday = current_date + timedelta(days=6)
        if next_thursday.year > year:
            next_thursday = date(year, 12, 31)
        weeks.append((week_num + 1, current_date, next_thursday))
        week_num += 1
        current_date = next_thursday + timedelta(days=1)
        if current_date.year > year:
            break
            
    return weeks


def get_bccp_week_number(d, year):
    """Lấy số tuần BCCP của một ngày trong năm"""
    from datetime import date
    if isinstance(d, str):
        try:
            d = date.fromisoformat(d)
        except ValueError:
            d = pd.to_datetime(d).date()
    elif isinstance(d, pd.Timestamp):
        d = d.date()
        
    weeks = get_bccp_weeks(year)
    for w_num, start_d, end_d in weeks:
        if start_d <= d <= end_d:
            return 1 if w_num == 53 else w_num
    
    last_w = weeks[-1][0] if weeks else 1
    return 1 if last_w == 53 else last_w

