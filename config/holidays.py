# -*- coding: utf-8 -*-
"""
Quản lý ngày lễ Việt Nam cho dự án Doanh thu BCCP.
"""

from datetime import date, timedelta
from typing import Set

# Ngày lễ cố định (dương lịch) - áp dụng mọi năm
_FIXED_HOLIDAYS = {
    (1, 1): "Tết Dương lịch",
    (4, 30): "Ngày Giải phóng miền Nam",
    (5, 1): "Quốc tế Lao động",
    (9, 2): "Quốc khánh",
    (9, 3): "Nghỉ bù Quốc khánh",
}

# Ngày lễ thay đổi theo năm (lịch âm chuyển sang dương lịch)
_VARIABLE_HOLIDAYS = {
    2025: {
        date(2025, 4, 7): "Giỗ Tổ Hùng Vương",
        date(2025, 1, 25): "Tết Nguyên Đán (nghỉ trước)",
        date(2025, 1, 26): "Tết Nguyên Đán (nghỉ trước)",
        date(2025, 1, 27): "Tết Nguyên Đán (nghỉ trước)",
        date(2025, 1, 28): "Tết Nguyên Đán (29 Tết)",
        date(2025, 1, 29): "Tết Nguyên Đán (Mùng 1)",
        date(2025, 1, 30): "Tết Nguyên Đán (Mùng 2)",
        date(2025, 1, 31): "Tết Nguyên Đán (Mùng 3)",
        date(2025, 2, 1): "Tết Nguyên Đán (Mùng 4)",
        date(2025, 2, 2): "Tết Nguyên Đán (nghỉ bù)",
    },
    2026: {
        date(2026, 4, 26): "Giỗ Tổ Hùng Vương",
        date(2026, 2, 14): "Tết Nguyên Đán (nghỉ trước)",
        date(2026, 2, 15): "Tết Nguyên Đán (nghỉ trước)",
        date(2026, 2, 16): "Tết Nguyên Đán (29 Tết)",
        date(2026, 2, 17): "Tết Nguyên Đán (Mùng 1)",
        date(2026, 2, 18): "Tết Nguyên Đán (Mùng 2)",
        date(2026, 2, 19): "Tết Nguyên Đán (Mùng 3)",
        date(2026, 2, 20): "Tết Nguyên Đán (Mùng 4)",
        date(2026, 2, 21): "Tết Nguyên Đán (nghỉ bù)",
        date(2026, 2, 22): "Tết Nguyên Đán (nghỉ bù)",
    },
    2027: {
        date(2027, 4, 15): "Giỗ Tổ Hùng Vương",
        date(2027, 2, 3): "Tết Nguyên Đán (nghỉ trước)",
        date(2027, 2, 4): "Tết Nguyên Đán (nghỉ trước)",
        date(2027, 2, 5): "Tết Nguyên Đán (29 Tết)",
        date(2027, 2, 6): "Tết Nguyên Đán (Mùng 1)",
        date(2027, 2, 7): "Tết Nguyên Đán (Mùng 2)",
        date(2027, 2, 8): "Tết Nguyên Đán (Mùng 3)",
        date(2027, 2, 9): "Tết Nguyên Đán (Mùng 4)",
        date(2027, 2, 10): "Tết Nguyên Đán (nghỉ bù)",
        date(2027, 2, 11): "Tết Nguyên Đán (nghỉ bù)",
    },
}

def get_holidays(year: int) -> Set[date]:
    holidays = set()
    for (month, day), _ in _FIXED_HOLIDAYS.items():
        holidays.add(date(year, month, day))
    if year in _VARIABLE_HOLIDAYS:
        holidays.update(_VARIABLE_HOLIDAYS[year].keys())
    return holidays

def get_holiday_name(d: date) -> str | None:
    key = (d.month, d.day)
    if key in _FIXED_HOLIDAYS:
        return _FIXED_HOLIDAYS[key]
    if d.year in _VARIABLE_HOLIDAYS:
        if d in _VARIABLE_HOLIDAYS[d.year]:
            return _VARIABLE_HOLIDAYS[d.year][d]
    return None

def is_holiday(d: date) -> bool:
    return get_holiday_name(d) is not None

def is_working_day(d: date, cms_type: str = "T") -> bool:
    if cms_type.upper().startswith("C"):
        return True
    if d.weekday() >= 5:  # T7 hoặc CN
        return False
    if is_holiday(d):
        return False
    return True
