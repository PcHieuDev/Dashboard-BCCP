# -*- coding: utf-8 -*-
"""
Module phân loại khách hàng theo từng tháng.
Phân loại gồm: Bán mới, Tái bán, Hiện hữu, Vãng lai.
"""

from datetime import date, timedelta
import sqlite3

def get_start_of_month(d: date) -> date:
    return date(d.year, d.month, 1)

def get_end_of_month(d: date) -> date:
    # Ngày cuối tháng = ngày đầu tháng sau - 1 ngày
    if d.month == 12:
        next_month = date(d.year + 1, 1, 1)
    else:
        next_month = date(d.year, d.month + 1, 1)
    return next_month - timedelta(days=1)

def get_start_of_3_months_ago(start_of_month: date) -> date:
    # Lùi 3 tháng
    temp_date = start_of_month
    for _ in range(3):
        # Lùi về ngày cuối của tháng trước
        temp_date = temp_date - timedelta(days=1)
        # Lấy ngày đầu của tháng đó
        temp_date = date(temp_date.year, temp_date.month, 1)
    return temp_date

def classify_customers(conn: sqlite3.Connection, target_date: date) -> dict[str, str]:
    """
    Phân loại tất cả khách hàng có giao dịch trong tháng chứa target_date.
    
    Trả về dict: {cms: loai_kh}
    loai_kh gồm: 'Bán mới', 'Tái bán', 'Hiện hữu', 'Vãng lai'
    """
    start_of_month = get_start_of_month(target_date)
    end_of_month = get_end_of_month(target_date)
    
    # 1. Lấy tất cả CMS có giao dịch trong tháng này
    # Định dạng ngày trong DB là YYYY-MM-DD (ISO)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT cms FROM transactions 
        WHERE ngay_chap_nhan BETWEEN ? AND ?
    """, (start_of_month.isoformat(), end_of_month.isoformat()))
    
    all_cms_in_month = [row[0] for row in cursor.fetchall() if row[0] is not None]
    
    if not all_cms_in_month:
        return {}
        
    classification = {}
    
    # Lọc ra các CMS vãng lai
    non_vanglai_cms = []
    for cms in all_cms_in_month:
        cms_str = str(cms).strip()
        if cms_str.startswith("VANGLAI_") or cms_str == "" or cms_str.lower() == "none":
            classification[cms] = "Vãng lai"
        else:
            non_vanglai_cms.append(cms)
            
    if not non_vanglai_cms:
        return classification
        
    # 2. Tìm ngày giao dịch đầu tiên của các CMS phi vãng lai trong DB
    # Để tối ưu, ta tạo câu lệnh IN
    placeholders = ",".join(["?"] * len(non_vanglai_cms))
    query = f"""
        SELECT cms, MIN(ngay_chap_nhan) FROM transactions 
        WHERE cms IN ({placeholders})
        GROUP BY cms
    """
    cursor.execute(query, non_vanglai_cms)
    first_dates = {row[0]: date.fromisoformat(row[1]) for row in cursor.fetchall() if row[1]}
    
    # 3. Tìm các CMS có phát sinh giao dịch trong 3 tháng liền trước tháng này
    # Khoảng ngày: start_of_3_months_ago -> start_of_month - 1 ngày
    start_of_3_months_ago = get_start_of_3_months_ago(start_of_month)
    end_of_prev_month = start_of_month - timedelta(days=1)
    
    query_prev = f"""
        SELECT DISTINCT cms FROM transactions 
        WHERE ngay_chap_nhan BETWEEN ? AND ?
          AND cms IN ({placeholders})
    """
    cursor.execute(query_prev, [start_of_3_months_ago.isoformat(), end_of_prev_month.isoformat()] + non_vanglai_cms)
    active_in_prev_3_months = {row[0] for row in cursor.fetchall()}
    
    # 4. Phân loại từng CMS
    for cms in non_vanglai_cms:
        first_date = first_dates.get(cms)
        if not first_date:
            classification[cms] = "Hiện hữu"
            continue
            
        if cms not in active_in_prev_3_months:
            # Nếu không có giao dịch trong 3 tháng gần nhất (bao gồm cả KH mới chưa từng giao dịch)
            classification[cms] = "KHM/Tái bán"
        else:
            # Đang hoạt động bình thường (có giao dịch trong 3 tháng gần nhất)
            classification[cms] = "Hiện hữu"
            
    return classification
