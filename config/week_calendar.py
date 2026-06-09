# -*- coding: utf-8 -*-
"""
Module quản lý lịch tuần, tháng và chu kỳ so sánh cho dự án Doanh thu BCCP.
Tuần tính từ Thứ 6 → Thứ 5 tuần sau.
Riêng năm 2026: Tuần 1 từ 01/01 đến 08/01. Tuần 2 bắt đầu từ Thứ Sáu 09/01.
"""

from datetime import date, timedelta
import calendar

def get_week_list(year: int) -> list[tuple[int, date, date]]:
    """
    Trả về danh sách các tuần trong năm chỉ định.
    Mỗi tuần là tuple (week_num, start_date, end_date).
    Nếu year != 2026, lấy lịch tuần chuẩn tính toán từ năm 2026
    và thay thế năm của các ngày bắt đầu/kết thúc sang year.
    """
    if year == 2026:
        weeks = []
        start_date = date(2026, 1, 1)
        end_of_year = date(2026, 12, 31)
        
        # Tìm ngày Thứ Sáu đầu tiên của năm
        first_friday = start_date
        while first_friday.weekday() != 4:  # 4 là Thứ Sáu
            first_friday += timedelta(days=1)
            
        # Nếu Thứ Sáu đầu tiên rơi vào ngày 1, 2, 3 tháng 1 (tuần đầu quá ngắn):
        # gộp những ngày trước đó vào Tuần 1, Tuần 2 bắt đầu từ Thứ Sáu tiếp theo
        if first_friday.day <= 3:
            week2_start = first_friday + timedelta(days=7)
        else:
            week2_start = first_friday
            
        # Tuần 1 bắt đầu từ 01/01 đến trước ngày bắt đầu Tuần 2
        week1_end = week2_start - timedelta(days=1)
        weeks.append((1, start_date, week1_end))
        
        # Các tuần tiếp theo
        current_start = week2_start
        week_num = 2
        while current_start <= end_of_year:
            current_end = current_start + timedelta(days=6)
            if current_end >= end_of_year:
                current_end = end_of_year
            weeks.append((week_num, current_start, current_end))
            if current_end == end_of_year:
                break
            current_start = current_end + timedelta(days=1)
            week_num += 1
            
        return weeks
    else:
        # Lấy lịch tuần của năm 2026 và đổi năm sang year
        weeks_2026 = get_week_list(2026)
        weeks = []
        for w_num, start_dt, end_dt in weeks_2026:
            try:
                new_start = start_dt.replace(year=year)
            except ValueError:
                new_start = date(year, start_dt.month, start_dt.day)
            try:
                new_end = end_dt.replace(year=year)
            except ValueError:
                new_end = date(year, end_dt.month, end_dt.day)
            weeks.append((w_num, new_start, new_end))
        return weeks

def allocate_weekly_plan(year: int) -> list[tuple[int, date, date, list[tuple[int, int, int, int]]]]:
    """
    Phân bổ tuần trong năm cho các tháng tương ứng dựa trên số ngày của tuần nằm trong mỗi tháng.
    Trả về danh sách tuple:
    [
      (tuan_so, start_date, end_date, [
        (thang, nam_cua_thang, so_ngay_trong_tuan_thuoc_thang, tong_so_ngay_trong_thang)
      ])
    ]
    """
    weeks = get_week_list(year)
    allocation_list = []
    
    for w_num, w_start, w_end in weeks:
        # Tuần có thể nằm trọn trong 1 tháng hoặc vắt qua 2 tháng
        months_distribution = []
        
        current_date = w_start
        # Gom các ngày trong tuần này theo (thang, nam)
        days_per_month = {}
        while current_date <= w_end:
            key = (current_date.month, current_date.year)
            days_per_month[key] = days_per_month.get(key, 0) + 1
            current_date += timedelta(days=1)
            
        for (m, y), days_count in days_per_month.items():
            _, total_days_in_month = calendar.monthrange(y, m)
            months_distribution.append((m, y, days_count, total_days_in_month))
            
        allocation_list.append((w_num, w_start, w_end, months_distribution))
        
    return allocation_list

def get_month_range(year: int, month: int) -> tuple[date, date]:
    """
    Trả về ngày đầu tiên và ngày cuối cùng của tháng.
    """
    first_day = date(year, month, 1)
    _, last_day_num = calendar.monthrange(year, month)
    last_day = date(year, month, last_day_num)
    return first_day, last_day

def get_week_for_date(d: date) -> tuple[int, date, date]:
    """
    Trả về thông tin tuần chứa ngày d: (week_num, start_date, end_date)
    """
    weeks = get_week_list(d.year)
    for w_num, w_start, w_end in weeks:
        if w_start <= d <= w_end:
            return w_num, w_start, w_end
    # Fallback nếu ngoài tầm
    return 1, date(d.year, 1, 1), date(d.year, 1, 7)

def get_prev_period(chu_ky: str, date_from: date, date_to: date) -> tuple[date, date]:
    """
    Tính toán khoảng thời gian của kỳ trước liền kề để so sánh.
    
    Args:
        chu_ky: 'Ngày', 'Tuần' hoặc 'Tháng'
        date_from: Ngày bắt đầu kỳ hiện tại
        date_to: Ngày kết thúc kỳ hiện tại
        
    Returns:
        (prev_from, prev_to): Khoảng ngày kỳ trước
    """
    if chu_ky == 'Ngày':
        delta_days = (date_to - date_from).days + 1
        prev_to = date_from - timedelta(days=1)
        prev_from = prev_to - timedelta(days=delta_days - 1)
        return prev_from, prev_to
        
    elif chu_ky == 'Tuần':
        # Tìm tuần chứa date_from trong năm
        year = date_from.year
        weeks = get_week_list(year)
        
        # Tìm index của tuần hiện tại
        current_idx = -1
        for i, (w_num, w_start, w_end) in enumerate(weeks):
            if w_start <= date_from <= w_end:
                current_idx = i
                break
                
        if current_idx > 0:
            # Tuần trước cùng năm
            _, prev_start, prev_end = weeks[current_idx - 1]
            return prev_start, prev_end
        else:
            # Tuần 1 của năm -> so với tuần cuối của năm ngoái
            prev_year_weeks = get_week_list(year - 1)
            _, prev_start, prev_end = prev_year_weeks[-1]
            return prev_start, prev_end
            
    elif chu_ky == 'Tháng':
        # Tính lùi 1 tháng
        if date_from.month == 1:
            prev_month = 12
            prev_year = date_from.year - 1
        else:
            prev_month = date_from.month - 1
            prev_year = date_from.year
            
        return get_month_range(prev_year, prev_month)
        
    # Mặc định fallback lùi số ngày tương ứng
    delta_days = (date_to - date_from).days + 1
    prev_to = date_from - timedelta(days=1)
    prev_from = prev_to - timedelta(days=delta_days - 1)
    return prev_from, prev_to

def get_same_period_prev_year(chu_ky: str, date_from: date, date_to: date) -> tuple[date, date]:
    """
    Tính toán khoảng thời gian cùng kỳ năm trước để so sánh YoY.
    
    Args:
        chu_ky: 'Ngày', 'Tuần' hoặc 'Tháng'
        date_from: Ngày bắt đầu kỳ hiện tại
        date_to: Ngày kết thúc kỳ hiện tại
        
    Returns:
        (prev_from, prev_to): Khoảng ngày cùng kỳ năm trước
    """
    if chu_ky == 'Ngày':
        # Lùi đúng 1 năm
        prev_from = date_from.replace(year=date_from.year - 1)
        prev_to = date_to.replace(year=date_to.year - 1)
        return prev_from, prev_to
        
    elif chu_ky == 'Tuần':
        # Tìm tuần cùng số thứ tự năm trước
        year = date_from.year
        weeks = get_week_list(year)
        
        # Tìm index của tuần hiện tại
        current_idx = -1
        for i, (w_num, w_start, w_end) in enumerate(weeks):
            if w_start <= date_from <= w_end:
                current_idx = i
                break
                
        prev_year_weeks = get_week_list(year - 1)
        if current_idx >= 0 and current_idx < len(prev_year_weeks):
            _, prev_start, prev_end = prev_year_weeks[current_idx]
            return prev_start, prev_end
        else:
            # Fallback: lấy tuần cuối năm trước
            _, prev_start, prev_end = prev_year_weeks[-1]
            return prev_start, prev_end
            
    elif chu_ky == 'Tháng':
        # Cùng tháng năm trước
        return get_month_range(date_from.year - 1, date_from.month)
        
    # Mặc định fallback lùi 1 năm
    prev_from = date_from.replace(year=date_from.year - 1)
    prev_to = date_to.replace(year=date_to.year - 1)
    return prev_from, prev_to
