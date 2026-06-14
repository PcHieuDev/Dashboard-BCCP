# -*- coding: utf-8 -*-
"""
Module engine truy vấn doanh thu đa chiều (Core Query Engine).
Hỗ trợ đầy đủ bộ lọc: Thời gian, Dịch vụ, Địa lý, Loại KH, Hợp đồng và GROUP BY động.
"""

from datetime import date, datetime
import pandas as pd
import sqlite3
from config.settings import DB_PATH
from config.week_calendar import get_prev_period, get_same_period_prev_year
from analytics.customer_classifier import classify_customers

# Lưu cache phân loại khách hàng để tránh query SQLite nhiều lần
# Key: (db_path, target_month_iso) -> dict[cms, loai_kh]
_CUSTOMER_CLASSIFY_CACHE = {}

def get_cached_classification(conn: sqlite3.Connection, target_month: date) -> dict[str, str]:
    month_key = date(target_month.year, target_month.month, 1).isoformat()
    if month_key not in _CUSTOMER_CLASSIFY_CACHE:
        _CUSTOMER_CLASSIFY_CACHE[month_key] = classify_customers(conn, target_month)
    return _CUSTOMER_CLASSIFY_CACHE[month_key]

def clear_classification_cache():
    global _CUSTOMER_CLASSIFY_CACHE
    _CUSTOMER_CLASSIFY_CACHE.clear()

def query_revenue(
    conn: sqlite3.Connection,
    date_from: date,
    date_to: date,
    date_column: str = 'ngay_chap_nhan',
    
    # Bộ lọc
    nhom_dv: list[str] | None = None,
    dich_vu: list[str] | None = None,
    cum: str | None = None,
    bdx: str | None = None,
    buu_cuc: str | None = None,
    loai_kh: list[str] | None = None,
    hop_dong: str | None = None,  # 'Có HĐ', 'Không HĐ', None
    
    # Group by
    group_by_primary: str | None = None,  # 'ngay', 'buu_cuc', 'bdx', 'cum', 'nhom_dv', 'dich_vu', 'loai_kh', 'hop_dong', 'cms'
    group_by_secondary: str | None = None,
    
    # So sánh
    compare_prev: bool = False,
    chu_ky: str | None = None,  # 'Ngày', 'Tuần', 'Tháng'
    nam: int = None,
    compare_mode: str = 'prev_period',  # 'prev_period', 'yoy', 'both'
) -> pd.DataFrame:
    """
    Truy vấn doanh thu với bộ lọc đa chiều và tổng hợp động.
    """
    
    # 1. Xây dựng câu SQL truy vấn dữ liệu thô (đã lọc các chiều cơ bản để giảm tải)
    query_parts = [
        """
        SELECT 
            t.cms,
            t.ma_hop_dong,
            t.ma_buu_cuc,
            t.ten_dich_vu,
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
        LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu
        LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
        WHERE (d.nhom_chinh = 'BCCP' OR d.nhom_chinh IS NULL)
        """
    ]
    params = []
    
    # Lọc theo cột ngày
    if date_column == 'thang_du_lieu':
        # thang_du_lieu trong DB lưu dạng T01, T02...
        start_month = f"T{date_from.month:02d}"
        end_month = f"T{date_to.month:02d}"
        query_parts.append("AND t.thang_du_lieu BETWEEN ? AND ?")
        params.extend([start_month, end_month])
        # Lọc theo năm dữ liệu
        if nam is not None:
            query_parts.append("AND t.nam_du_lieu = ?")
            params.append(nam)
    else:
        query_parts.append("AND t.ngay_chap_nhan BETWEEN ? AND ?")
        params.extend([date_from.isoformat(), date_to.isoformat()])
        
    # Lọc theo nhóm dịch vụ
    if nhom_dv:
        placeholders = ",".join(["?"] * len(nhom_dv))
        query_parts.append(f"AND d.nhom_dich_vu IN ({placeholders})")
        params.extend(nhom_dv)
        
    # Lọc theo dịch vụ chi tiết (mã SPDV)
    if dich_vu:
        placeholders = ",".join(["?"] * len(dich_vu))
        query_parts.append(f"AND t.ten_dich_vu IN ({placeholders})")
        params.extend(dich_vu)
        
    # Lọc theo Cụm
    if cum and cum != "Tất cả":
        query_parts.append("AND b.ten_cum = ?")
        params.append(cum)
        
    # Lọc theo BĐX
    if bdx and bdx != "Tất cả":
        query_parts.append("AND b.ten_bdx = ?")
        params.append(bdx)
        
    # Lọc theo Bưu cục
    if buu_cuc and buu_cuc != "Tất cả":
        query_parts.append("AND t.buu_cuc = ?")
        params.append(buu_cuc)
        
    # Lọc theo Hợp đồng
    if hop_dong == "Có HĐ":
        query_parts.append("AND t.ma_hop_dong IS NOT NULL AND t.ma_hop_dong != ''")
    elif hop_dong == "Không HĐ":
        query_parts.append("AND (t.ma_hop_dong IS NULL OR t.ma_hop_dong = '')")
        
    # Thực thi query lấy dữ liệu thô lên Pandas
    sql = "\n".join(query_parts)
    df_raw = pd.read_sql_query(sql, conn, params=params)
    
    if df_raw.empty:
        return create_empty_result_df(group_by_primary, group_by_secondary)
        
    # 2. Phân loại loại khách hàng
    # Xác định các tháng xuất hiện trong dữ liệu để lấy phân loại tương ứng
    months_in_data = set()
    for ngay_str in df_raw['ngay_chap_nhan'].unique():
        if ngay_str:
            dt = date.fromisoformat(ngay_str)
            months_in_data.add(date(dt.year, dt.month, 1))
            
    # Load phân loại khách hàng theo tháng từ cache/DB
    month_classifications = {}
    for m_start in months_in_data:
        month_classifications[m_start] = get_cached_classification(conn, m_start)
        
    # Map phân loại khách hàng vào DataFrame
    def map_loai_kh(row):
        ngay_str = row['ngay_chap_nhan']
        if not ngay_str:
            return "Vãng lai"
        dt = date.fromisoformat(ngay_str)
        m_start = date(dt.year, dt.month, 1)
        cms = row['cms']
        
        # Nếu CMS null hoặc rỗng -> Vãng lai
        if not cms or str(cms).strip().upper() == "NONE" or str(cms).strip().startswith("VANGLAI_"):
            return "Vãng lai"
            
        cls_map = month_classifications.get(m_start, {})
        return cls_map.get(cms, "Hiện hữu")
        
    df_raw['loai_kh'] = df_raw.apply(map_loai_kh, axis=1)
    
    # 3. Lọc theo loại khách hàng sau khi đã mapping
    if loai_kh:
        df_raw = df_raw[df_raw['loai_kh'].isin(loai_kh)]
        if df_raw.empty:
            return create_empty_result_df(group_by_primary, group_by_secondary)
            
    # Tạo thêm các cột hỗ trợ hiển thị
    df_raw['hop_dong'] = df_raw['ma_hop_dong'].apply(lambda x: 'Có HĐ' if x and str(x).strip() else 'Không HĐ')
    
    # Map giá trị hiển thị cho cột group_by
    group_col_mapping = {
        'ngay': 'ngay_chap_nhan',
        'buu_cuc': 'ma_buu_cuc',
        'bdx': 'ten_bdx',
        'cum': 'ten_cum',
        'nhom_dv': 'nhom_dich_vu',
        'dich_vu': 'ten_dich_vu',
        'loai_kh': 'loai_kh',
        'hop_dong': 'hop_dong',
        'cms': 'cms'
    }
    
    # 4. Xác định các cột để GROUP BY
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
        # Mặc định gom theo Nhóm dịch vụ nếu không chọn gì
        group_cols.append('nhom_dich_vu')
        col_names_output.append('nhom_dv')
        
    # 5. Thực hiện Group By và Aggregate
    # Chuẩn hóa giá trị NULL để tránh bị Pandas groupby bỏ qua
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
    
    # Rename các cột groupby về tên chuẩn tiếng anh dễ code ở ngoài view
    rename_dict = {group_cols[i]: col_names_output[i] for i in range(len(group_cols))}
    df_agg = df_agg.rename(columns=rename_dict)
    
    # 6. Nếu có yêu cầu so sánh kỳ trước
    if compare_prev and chu_ky:
        merge_cols = col_names_output
        metrics = ['san_luong', 'khoi_luong_thuc', 'cuoc_cb_tong', 'cuoc_tt_tong', 'cuoc_tt_gom_vat', 'so_kh']
        
        # Helper: query kỳ so sánh
        def _query_compare(cmp_from, cmp_to, nam=None):
            return query_revenue(
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
                nam=nam
            )
        
        # Helper: merge và tính pct_change
        def _merge_with_suffix(df_base, df_cmp, suffix):
            df_m = pd.merge(df_base, df_cmp, on=merge_cols, how='outer', suffixes=('', suffix))
            for m in metrics:
                df_m[m] = df_m[m].fillna(0)
                col_s = f'{m}{suffix}'
                df_m[col_s] = df_m[col_s].fillna(0)
                
                def calc_pct(row, metric_name=m, sfx=suffix):
                    val_now = row[metric_name]
                    val_prev = row[f'{metric_name}{sfx}']
                    if val_prev == 0:
                        return 100.0 if val_now > 0 else 0.0
                    return round((val_now - val_prev) * 100.0 / val_prev, 2)
                    
                df_m[f'{m}{suffix.replace("_prev", "").replace("_yoy", "")}_pct_change' if suffix == '_prev' else f'{m}_yoy_pct_change'] = df_m.apply(calc_pct, axis=1)
            return df_m
        
        df_result = df_agg
        
        if compare_mode in ('prev_period', 'both'):
            prev_from, prev_to = get_prev_period(chu_ky, date_from, date_to)
            df_prev = _query_compare(prev_from, prev_to, nam=None)
            df_result = pd.merge(df_result, df_prev, on=merge_cols, how='outer', suffixes=('', '_prev'))
            for m in metrics:
                df_result[m] = df_result[m].fillna(0)
                df_result[f'{m}_prev'] = df_result[f'{m}_prev'].fillna(0)
                
                def calc_pct_prev(row, metric_name=m):
                    val_now = row[metric_name]
                    val_prev = row[f'{metric_name}_prev']
                    if val_prev == 0:
                        return 100.0 if val_now > 0 else 0.0
                    return round((val_now - val_prev) * 100.0 / val_prev, 2)
                    
                df_result[f'{m}_pct_change'] = df_result.apply(calc_pct_prev, axis=1)
        
        if compare_mode in ('yoy', 'both'):
            yoy_from, yoy_to = get_same_period_prev_year(chu_ky, date_from, date_to)
            # Cho YoY, truyền nam của năm trước
            yoy_nam = (nam - 1) if nam is not None else None
            df_yoy = _query_compare(yoy_from, yoy_to, nam=yoy_nam)
            
            # Nếu chỉ yoy (không both), merge trực tiếp
            if compare_mode == 'yoy':
                df_result = pd.merge(df_result, df_yoy, on=merge_cols, how='outer', suffixes=('', '_yoy'))
            else:
                # both: df_result đã có _prev, merge thêm _yoy
                # Rename df_yoy columns trước khi merge
                yoy_rename = {m: f'{m}_yoy' for m in metrics}
                df_yoy_renamed = df_yoy.rename(columns=yoy_rename)
                df_result = pd.merge(df_result, df_yoy_renamed, on=merge_cols, how='outer')
            
            for m in metrics:
                df_result[m] = df_result[m].fillna(0)
                df_result[f'{m}_yoy'] = df_result[f'{m}_yoy'].fillna(0)
                
                def calc_pct_yoy(row, metric_name=m):
                    val_now = row[metric_name]
                    val_yoy = row[f'{metric_name}_yoy']
                    if val_yoy == 0:
                        return 100.0 if val_now > 0 else 0.0
                    return round((val_now - val_yoy) * 100.0 / val_yoy, 2)
                    
                df_result[f'{m}_yoy_pct_change'] = df_result.apply(calc_pct_yoy, axis=1)
        
        return df_result
        
    return df_agg

def create_empty_result_df(group1: str | None, group2: str | None) -> pd.DataFrame:
    cols = []
    if group1:
        cols.append(group1)
    if group2:
        cols.append(group2)
    if not cols:
        cols.append('nhom_dv')
        
    metrics = ['san_luong', 'khoi_luong_thuc', 'cuoc_cb_tong', 'cuoc_tt_tong', 'cuoc_tt_gom_vat', 'so_kh']
    for m in metrics:
        cols.append(m)
    return pd.DataFrame(columns=cols)


def query_revenue_cached(
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
    """
    Wrapper của query_revenue tích hợp st.cache_data của Streamlit.
    Nếu không cài streamlit, sẽ truy vấn trực tiếp mà không cache.
    """
    try:
        import streamlit as st
        
        @st.cache_data(ttl=3600)
        def _cached_run(
            _db_path: str,
            date_from: date,
            date_to: date,
            date_column: str,
            nhom_dv_tuple: tuple[str] | None,
            dich_vu_tuple: tuple[str] | None,
            cum: str | None,
            bdx: str | None,
            buu_cuc: str | None,
            loai_kh_tuple: tuple[str] | None,
            hop_dong: str | None,
            group_by_primary: str | None,
            group_by_secondary: str | None,
            compare_prev: bool,
            chu_ky: str | None,
            nam: int | None,
            compare_mode: str,
        ) -> pd.DataFrame:
            conn = sqlite3.connect(_db_path)
            try:
                nhom_dv_list = list(nhom_dv_tuple) if nhom_dv_tuple is not None else None
                dich_vu_list = list(dich_vu_tuple) if dich_vu_tuple is not None else None
                loai_kh_list = list(loai_kh_tuple) if loai_kh_tuple is not None else None
                
                return query_revenue(
                    conn=conn,
                    date_from=date_from,
                    date_to=date_to,
                    date_column=date_column,
                    nhom_dv=nhom_dv_list,
                    dich_vu=dich_vu_list,
                    cum=cum,
                    bdx=bdx,
                    buu_cuc=buu_cuc,
                    loai_kh=loai_kh_list,
                    hop_dong=hop_dong,
                    group_by_primary=group_by_primary,
                    group_by_secondary=group_by_secondary,
                    compare_prev=compare_prev,
                    chu_ky=chu_ky,
                    nam=nam,
                    compare_mode=compare_mode
                )
            finally:
                conn.close()

        nhom_dv_tuple = tuple(nhom_dv) if nhom_dv is not None else None
        dich_vu_tuple = tuple(dich_vu) if dich_vu is not None else None
        loai_kh_tuple = tuple(loai_kh) if loai_kh is not None else None

        return _cached_run(
            str(DB_PATH),
            date_from,
            date_to,
            date_column,
            nhom_dv_tuple,
            dich_vu_tuple,
            cum,
            bdx,
            buu_cuc,
            loai_kh_tuple,
            hop_dong,
            group_by_primary,
            group_by_secondary,
            compare_prev,
            chu_ky,
            nam,
            compare_mode
        )
    except ImportError:
        conn = sqlite3.connect(str(DB_PATH))
        try:
            return query_revenue(
                conn=conn,
                date_from=date_from,
                date_to=date_to,
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
                compare_prev=compare_prev,
                chu_ky=chu_ky,
                nam=nam,
                compare_mode=compare_mode
            )
        finally:
            conn.close()


def create_empty_result_df_for_customer() -> pd.DataFrame:
    """Trả về DataFrame rỗng có cấu trúc cột cơ bản để tránh crash DataTable."""
    return pd.DataFrame(columns=['ten_cum', 'ten_bdx', 'buu_cuc', 'cms', 'san_luong', 'cuoc_tt_tong'])


def query_customer_detail_pivot(
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
    nam: int = None,
) -> pd.DataFrame:
    """
    Truy vấn doanh thu chi tiết theo khách hàng (CMS), xoay (pivot) chỉ tiêu theo nhóm dịch vụ.
    """
    # 1. Truy vấn dữ liệu thô từ DB, áp dụng toàn bộ bộ lọc có thể tối ưu trong SQL
    query_parts = [
        """
        SELECT 
            t.cms,
            t.ma_hop_dong,
            t.ma_buu_cuc,
            t.ten_dich_vu,
            t.ngay_chap_nhan,
            t.thang_du_lieu,
            t.san_luong,
            t.khoi_luong_thuc,
            t.cuoc_tt_tong,
            t.cuoc_tt_gom_vat,
            d.nhom_dich_vu,
            b.ten_buu_cuc,
            b.ten_bdx,
            b.ten_cum
        FROM transactions t
        LEFT JOIN dim_dichvu d ON t.ten_dich_vu = d.ma_dich_vu
        LEFT JOIN dim_buucuc b ON t.ma_buu_cuc = b.ma_buu_cuc
        WHERE (d.nhom_chinh = 'BCCP' OR d.nhom_chinh IS NULL)
        """
    ]
    params = []
    
    # Lọc theo cột ngày
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
        
    # Lọc theo nhóm dịch vụ
    if nhom_dv:
        placeholders = ",".join(["?"] * len(nhom_dv))
        query_parts.append(f"AND d.nhom_dich_vu IN ({placeholders})")
        params.extend(nhom_dv)
        
    # Lọc theo dịch vụ chi tiết (mã SPDV)
    if dich_vu:
        placeholders = ",".join(["?"] * len(dich_vu))
        query_parts.append(f"AND t.ten_dich_vu IN ({placeholders})")
        params.extend(dich_vu)
        
    # Lọc theo Cụm
    if cum and cum != "Tất cả":
        query_parts.append("AND b.ten_cum = ?")
        params.append(cum)
        
    # Lọc theo BĐX
    if bdx and bdx != "Tất cả":
        query_parts.append("AND b.ten_bdx = ?")
        params.append(bdx)
        
    # Lọc theo Bưu cục
    if buu_cuc and buu_cuc != "Tất cả":
        query_parts.append("AND t.buu_cuc = ?")
        params.append(buu_cuc)
        
    # Lọc theo Hợp đồng (lọc SQL để tối ưu)
    if hop_dong == "Có HĐ":
        query_parts.append("AND t.ma_hop_dong IS NOT NULL AND t.ma_hop_dong != ''")
    elif hop_dong == "Không HĐ":
        query_parts.append("AND (t.ma_hop_dong IS NULL OR t.ma_hop_dong = '')")
        
    sql = "\n".join(query_parts)
    df_raw = pd.read_sql_query(sql, conn, params=params)
    
    if df_raw.empty:
        return create_empty_result_df_for_customer()
        
    # 2. Phân loại loại khách hàng
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
    
    # Lọc theo loại khách hàng sau khi đã mapping
    if loai_kh:
        df_raw = df_raw[df_raw['loai_kh'].isin(loai_kh)]
        if df_raw.empty:
            return create_empty_result_df_for_customer()
            
    # 3. Chuẩn hóa các trường
    df_raw['cms'] = df_raw['cms'].fillna("Vãng lai").astype(str).str.strip()
    df_raw.loc[df_raw['cms'] == '', 'cms'] = "Vãng lai"
    df_raw['nhom_dich_vu'] = df_raw['nhom_dich_vu'].fillna("Chưa phân loại")
    df_raw['hop_dong'] = df_raw['ma_hop_dong'].apply(lambda x: 'Có HĐ' if x and str(x).strip() else 'Không HĐ')
    df_raw['khoi_luong_thuc'] = df_raw['khoi_luong_thuc'].fillna(0) / 1000.0
    
    # 4. Gộp nhóm lấy số liệu chi tiết khách hàng phẳng
    df_raw['ten_cum'] = df_raw['ten_cum'].fillna("Chưa phân loại")
    df_raw['ten_bdx'] = df_raw['ten_bdx'].fillna("Chưa phân loại")
    df_raw['buu_cuc'] = df_raw['buu_cuc'].fillna("Chưa phân loại")
    
    df_grouped = df_raw.groupby(['ten_cum', 'ten_bdx', 'buu_cuc', 'cms'], as_index=False).agg(
        san_luong=('san_luong', 'sum'),
        cuoc_tt_tong=('cuoc_tt_tong', 'sum')
    )
    
    # Sắp xếp
    df_grouped = df_grouped.sort_values(by=['ten_cum', 'ten_bdx', 'buu_cuc', 'cms'])
    
    return df_grouped


