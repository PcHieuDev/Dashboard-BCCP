# -*- coding: utf-8 -*-
"""
Callbacks cho trang Báo cáo Doanh thu chi tiết Hành chính công (HCC).
"""

import sys
import sqlite3
import functools
import pandas as pd
import dash
from dash import Output, Input, State, html, dcc, dash_table
from pathlib import Path
from datetime import datetime, date

# Setup path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from config.settings import DB_PATH
from config.week_calendar import get_prev_period, get_same_period_prev_year, get_week_list, get_month_range
from analytics.customer_classifier import classify_customers
from analytics.revenue import get_cached_classification, create_empty_result_df
from components.data_table import render_revenue_datatable

def query_hcc_revenue(
    conn: sqlite3.Connection,
    date_from: date,
    date_to: date,
    date_column: str = 'ngay_chap_nhan',
    nhom_dv: list[str] | None = None,
    dich_vu: list[str] | None = None,
    cum: str | None = None,
    bdx: str | None = None,
    buu_cuc: str | None = None,
    loai_kh: list[str] | None = None,
    hop_dong: str | None = None,
    group_by_primary: str | None = None,
    group_by_secondary: str | None = None,
    compare_prev: bool = False,
    chu_ky: str | None = None,
    nam: int = None,
    compare_mode: str = 'prev_period',
) -> pd.DataFrame:
    # 1. SQL query joining dim_dichvu and filtering on nhom_chinh = 'HCC'
    query_parts = [
        """
        SELECT 
            t.cms,
            t.ma_hop_dong,
            t.buu_cuc,
            t.san_pham_dv,
            t.ngay_chap_nhan,
            t.thang_du_lieu,
            t.san_luong,
            t.khoi_luong_thuc,
            t.cuoc_cb_tong,
            t.cuoc_tt_tong,
            t.cuoc_tt_gom_vat,
            d.nhom_dich_vu,
            d.ten_dich_vu as ten_spdv,
            b.ten_buu_cuc,
            b.ten_bdx,
            b.ten_cum
        FROM transactions t
        INNER JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
        LEFT JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
        WHERE 1=1 AND d.nhom_chinh = 'HCC'
        """
    ]
    params = []
    
    if date_column == 'thang_du_lieu':
        start_month = f"T{date_from.month:02d}"
        end_month = f"T{date_to.month:02d}"
        query_parts.append("AND t.thang_du_lieu BETWEEN ? AND ?")
        params.extend([start_month, end_month])
        if nam is not None:
            query_parts.append("AND t.nam_du_lieu = ?")
            params.append(nam)
    else:
        query_parts.append("AND t.ngay_chap_nhan BETWEEN ? AND ?")
        params.extend([date_from.isoformat(), date_to.isoformat()])
        
    if nhom_dv:
        placeholders = ",".join(["?"] * len(nhom_dv))
        query_parts.append(f"AND d.nhom_dich_vu IN ({placeholders})")
        params.extend(nhom_dv)
        
    if dich_vu:
        placeholders = ",".join(["?"] * len(dich_vu))
        query_parts.append(f"AND t.san_pham_dv IN ({placeholders})")
        params.extend(dich_vu)
        
    if cum and cum != "Tất cả":
        query_parts.append("AND b.ten_cum = ?")
        params.append(cum)
        
    if bdx and bdx != "Tất cả":
        query_parts.append("AND b.ten_bdx = ?")
        params.append(bdx)
        
    if buu_cuc and buu_cuc != "Tất cả":
        query_parts.append("AND t.buu_cuc = ?")
        params.append(buu_cuc)
        
    if hop_dong == "Có HĐ":
        query_parts.append("AND t.ma_hop_dong IS NOT NULL AND t.ma_hop_dong != ''")
    elif hop_dong == "Không HĐ":
        query_parts.append("AND (t.ma_hop_dong IS NULL OR t.ma_hop_dong = '')")
        
    sql = "\n".join(query_parts)
    df_raw = pd.read_sql_query(sql, conn, params=params)
    
    if df_raw.empty:
        return create_empty_result_df(group_by_primary, group_by_secondary)
        
    months_in_data = set()
    for ngay_str in df_raw['ngay_chap_nhan'].unique():
        if ngay_str:
            try:
                dt = date.fromisoformat(ngay_str)
                months_in_data.add(date(dt.year, dt.month, 1))
            except ValueError:
                pass
            
    month_classifications = {}
    for m_start in months_in_data:
        month_classifications[m_start] = get_cached_classification(conn, m_start)
        
    def map_loai_kh(row):
        ngay_str = row['ngay_chap_nhan']
        if not ngay_str:
            return "Vãng lai"
        try:
            dt = date.fromisoformat(ngay_str)
            m_start = date(dt.year, dt.month, 1)
        except ValueError:
            return "Vãng lai"
        cms = row['cms']
        if not cms or str(cms).strip().upper() == "NONE" or str(cms).strip().startswith("VANGLAI_"):
            return "Vãng lai"
        cls_map = month_classifications.get(m_start, {})
        return cls_map.get(cms, "Hiện hữu")
        
    df_raw['loai_kh'] = df_raw.apply(map_loai_kh, axis=1)
    
    if loai_kh:
        df_raw = df_raw[df_raw['loai_kh'].isin(loai_kh)]
        if df_raw.empty:
            return create_empty_result_df(group_by_primary, group_by_secondary)
            
    df_raw['hop_dong'] = df_raw['ma_hop_dong'].apply(lambda x: 'Có HĐ' if x and str(x).strip() else 'Không HĐ')
    
    group_col_mapping = {
        'ngay': 'ngay_chap_nhan',
        'buu_cuc': 'buu_cuc',
        'bdx': 'ten_bdx',
        'cum': 'ten_cum',
        'nhom_dv': 'nhom_dich_vu',
        'dich_vu': 'san_pham_dv',
        'loai_kh': 'loai_kh',
        'hop_dong': 'hop_dong',
        'cms': 'cms'
    }
    
    group_cols = []
    col_names_output = []
    
    if group_by_primary:
        col_db = group_col_mapping.get(group_by_primary)
        if col_db:
            group_cols.append(col_db)
            col_names_output.append(group_by_primary)
            
    if group_by_secondary:
        col_db = group_col_mapping.get(group_by_secondary)
        if col_db and col_db not in group_cols:
            group_cols.append(col_db)
            col_names_output.append(group_by_secondary)
            
    if not group_cols:
        group_cols.append('nhom_dich_vu')
        col_names_output.append('nhom_dv')
        
    for col in group_cols:
        df_raw[col] = df_raw[col].fillna("Chưa phân loại")
        
    df_agg = df_raw.groupby(group_cols).agg(
        san_luong=('san_luong', 'sum'),
        khoi_luong_thuc=('khoi_luong_thuc', 'sum'),
        cuoc_cb_tong=('cuoc_cb_tong', 'sum'),
        cuoc_tt_tong=('cuoc_tt_tong', 'sum'),
        cuoc_tt_gom_vat=('cuoc_tt_gom_vat', 'sum'),
        so_kh=('cms', 'nunique')
    ).reset_index()
    
    rename_dict = {group_cols[i]: col_names_output[i] for i in range(len(group_cols))}
    df_agg = df_agg.rename(columns=rename_dict)
    
    if compare_prev and chu_ky:
        merge_cols = col_names_output
        metrics = ['san_luong', 'khoi_luong_thuc', 'cuoc_cb_tong', 'cuoc_tt_tong', 'cuoc_tt_gom_vat', 'so_kh']
        
        def _query_compare(cmp_from, cmp_to, nam_val=None):
            return query_hcc_revenue(
                conn=conn,
                date_from=cmp_from,
                date_to=cmp_to,
                date_column=date_column,
                nhom_dv=nhom_dv,
                dich_vu=dich_vu,
                cum=cum,
                bdx=bdx,
                buu_cuc=buu_cuc,
                loai_kh=loai_kh,
                hop_dong=hop_dong,
                group_by_primary=group_by_primary,
                group_by_secondary=group_by_secondary,
                compare_prev=False,
                nam=nam_val
            )
            
        df_result = df_agg
        
        if compare_mode in ('prev_period', 'both'):
            prev_from, prev_to = get_prev_period(chu_ky, date_from, date_to)
            df_prev = _query_compare(prev_from, prev_to, nam_val=None)
            df_result = pd.merge(df_result, df_prev, on=merge_cols, how='outer', suffixes=('', '_prev'))
            for m in metrics:
                df_result[m] = df_result[m].fillna(0)
                df_result[f'{m}_prev'] = df_result[f'{m}_prev'].fillna(0)
                
                def calc_pct_prev(row_val, metric_name=m):
                    val_now = row_val[metric_name]
                    val_prev = row_val[f'{metric_name}_prev']
                    if val_prev == 0:
                        return 100.0 if val_now > 0 else 0.0
                    return round((val_now - val_prev) * 100.0 / val_prev, 2)
                    
                df_result[f'{m}_pct_change'] = df_result.apply(calc_pct_prev, axis=1)
                
        if compare_mode in ('yoy', 'both'):
            yoy_from, yoy_to = get_same_period_prev_year(chu_ky, date_from, date_to)
            yoy_nam = (nam - 1) if nam is not None else None
            df_yoy = _query_compare(yoy_from, yoy_to, nam_val=yoy_nam)
            
            if compare_mode == 'yoy':
                df_result = pd.merge(df_result, df_yoy, on=merge_cols, how='outer', suffixes=('', '_yoy'))
            else:
                yoy_rename = {m: f'{m}_yoy' for m in metrics}
                df_yoy_renamed = df_yoy.rename(columns=yoy_rename)
                df_result = pd.merge(df_result, df_yoy_renamed, on=merge_cols, how='outer')
                
            for m in metrics:
                df_result[m] = df_result[m].fillna(0)
                df_result[f'{m}_yoy'] = df_result[f'{m}_yoy'].fillna(0)
                
                def calc_pct_yoy(row_val, metric_name=m):
                    val_now = row_val[metric_name]
                    val_yoy = row_val[f'{metric_name}_yoy']
                    if val_yoy == 0:
                        return 100.0 if val_now > 0 else 0.0
                    return round((val_now - val_yoy) * 100.0 / val_yoy, 2)
                    
                df_result[f'{m}_yoy_pct_change'] = df_result.apply(calc_pct_yoy, axis=1)
                
        return df_result
        
    return df_agg

@functools.lru_cache(maxsize=128)
def run_hcc_query_cached(
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
    conn = sqlite3.connect(str(DB_PATH))
    try:
        df = query_hcc_revenue(
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

def get_hcc_df_from_cache(*args, **kwargs) -> pd.DataFrame:
    json_data = run_hcc_query_cached(*args, **kwargs)
    from io import StringIO
    return pd.read_json(StringIO(json_data), orient='split')

def resolve_filters_and_query_hcc(year, period, date_range_start, date_range_end, week_idx, month_val, 
                                  compare_mode, nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
                                  group_by_primary='nhom_dv', group_by_secondary=None, compare_prev=False):
    # Chuẩn hóa compare_mode
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
        
    # Chuẩn hóa địa lý và bộ lọc
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
        
    nhom_dv_tuple = tuple(nhom_dv) if nhom_dv else None
    spdv_tuple = tuple(spdv) if spdv else None
    loai_kh_tuple = tuple(loai_kh) if loai_kh else None
    
    df = get_hcc_df_from_cache(
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

def register_hcc_revenue_callbacks(app):
    """
    Đăng ký callback cập nhật bảng Doanh thu chi tiết HCC.
    """
    
    @app.callback(
        Output("hcc-revenue-table-container", "children"),
        [Input("url", "pathname"),
         Input("hcc-revenue-g1", "value"),
         Input("hcc-revenue-g2", "value"),
         Input("hcc-revenue-compare-opt", "value"),
         # Bộ lọc từ Sidebar
         Input("sidebar-year", "value"),
         Input("sidebar-period", "value"),
         Input("sidebar-date-range", "start_date"),
         Input("sidebar-date-range", "end_date"),
         Input("sidebar-week-select", "value"),
         Input("sidebar-month-select", "value"),
         Input("sidebar-nhom-dv", "value"),
         Input("sidebar-cum", "value"),
         Input("sidebar-bdx", "value"),
         Input("sidebar-buu-cuc", "value"),
         Input("sidebar-loai-kh", "value"),
         Input("sidebar-hop-dong", "value")]
    )
    def update_hcc_revenue_table(pathname, g1, g2, compare_opt, year, period, start_date, end_date, week_idx, month_val,
                                 nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        if pathname != "/hcc/revenue":
            return dash.no_update
        spdv = None
            
        g2_actual = None if g2 == "None" else g2
        compare_prev = compare_opt != "none"
        compare_mode = compare_opt if compare_prev else "prev_period"
        
        # 1. Truy vấn dữ liệu có cache dựa vào các bộ lọc
        _, _, _, df = resolve_filters_and_query_hcc(
            year, period, start_date, end_date, week_idx, month_val, compare_mode,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary=g1, group_by_secondary=g2_actual, compare_prev=compare_prev
        )
        
        # 2. Xử lý nhóm cột và hiển thị
        groupby_cols = [g1]
        if g2_actual:
            groupby_cols.append(g2_actual)
            
        # 3. Trả về bảng DataTable được định dạng (reuse hàm từ components.data_table)
        table = render_revenue_datatable(df, groupby_cols, compare_opt)
        # Sửa ID của DataTable để tránh xung đột
        if isinstance(table, dash_table.DataTable if hasattr(dash_table, 'DataTable') else object):
            table.id = "hcc-revenue-detail-datatable"
        return table

    @app.callback(
        Output("hcc-revenue-download", "data"),
        [Input("hcc-revenue-btn-export-excel", "n_clicks")],
        [State("url", "pathname"),
         State("hcc-revenue-g1", "value"),
         State("hcc-revenue-g2", "value"),
         State("hcc-revenue-compare-opt", "value"),
         State("sidebar-year", "value"),
         State("sidebar-period", "value"),
         State("sidebar-date-range", "start_date"),
         State("sidebar-date-range", "end_date"),
         State("sidebar-week-select", "value"),
         State("sidebar-month-select", "value"),
         State("sidebar-nhom-dv", "value"),
         State("sidebar-cum", "value"),
         State("sidebar-bdx", "value"),
         State("sidebar-buu-cuc", "value"),
         State("sidebar-loai-kh", "value"),
         State("sidebar-hop-dong", "value")],
        prevent_initial_call=True
    )
    def export_hcc_revenue_table(btn_excel, pathname, g1, g2, compare_opt, year, period, start_date, end_date, week_idx, month_val,
                                 nhom_dv, cum, bdx, buu_cuc, loai_kh, hop_dong):
        ctx = dash.callback_context
        if not ctx.triggered or pathname != "/hcc/revenue":
            return dash.no_update
        spdv = None
            
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id != "hcc-revenue-btn-export-excel":
            return dash.no_update
            
        g2_actual = None if g2 == "None" else g2
        compare_prev = compare_opt != "none"
        compare_mode = compare_opt if compare_prev else "prev_period"
        
        # 1. Truy vấn dữ liệu có cache dựa vào các bộ lọc
        date_from, date_to, _, df = resolve_filters_and_query_hcc(
            year, period, start_date, end_date, week_idx, month_val, compare_mode,
            nhom_dv, spdv, cum, bdx, buu_cuc, loai_kh, hop_dong,
            group_by_primary=g1, group_by_secondary=g2_actual, compare_prev=compare_prev
        )
        
        groupby_cols = [g1]
        if g2_actual:
            groupby_cols.append(g2_actual)
            
        # 2. Tạo thông tin bộ lọc gửi đi
        filter_info = {
            "Năm dữ liệu": year,
            "Chu kỳ báo cáo": period,
            "Khoảng thời gian": f"{date_from.strftime('%d/%m/%Y')} - {date_to.strftime('%d/%m/%Y')}",
            "Nhóm dịch vụ": ", ".join(nhom_dv) if nhom_dv else "Tất cả",
            "Cụm địa lý": cum,
            "Mã bưu điện": bdx if bdx != "Tất cả" else "Tất cả",
            "Phân loại KH": ", ".join(loai_kh) if loai_kh else "Tất cả",
            "Trạng thái HĐ": ", ".join(hop_dong) if isinstance(hop_dong, list) and hop_dong else (hop_dong if isinstance(hop_dong, str) and hop_dong else 'Tất cả')
        }
        
        # 3. Tạo file xuất tương ứng
        from callbacks.export_helpers import generate_excel_report
        excel_bytes = generate_excel_report(df, groupby_cols, compare_opt, filter_info)
        filename = f"BaoCaoDoanhThu_HCC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return dcc.send_bytes(excel_bytes, filename)
