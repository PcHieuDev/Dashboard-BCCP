# TIP-fix-002: Sửa Biểu đồ Cơ cấu BCCP (Bug #3)

## Header
- **TIP-ID**: TIP-fix-002
- **Branch**: feat/ui-fixes
- **Module**: analytics/revenue, callbacks/kpi
- **Dependencies**: Không
- **Priority**: P0 (dữ liệu sai)
- **Estimated effort**: Small-Medium

## Bối cảnh & Root Cause
Biểu đồ "Cơ cấu doanh thu" tại `/bccp` hiển thị cả HCC, TCBC, PPBL dù đang xem trang BCCP.

### Root Cause xác định:
- `analytics/revenue.py` → `query_revenue()` JOIN `dim_spdv` (bảng legacy)
- `dim_spdv.nhom_dich_vu` chứa các giá trị: `"BCCP"`, `"HCC"`, `"TCBC"`, `"PPBL"` (là nhóm chính, không phải nhóm DV chi tiết)
- Query KHÔNG có filter `WHERE nhom_chinh = 'BCCP'` hoặc `WHERE d.nhom_dich_vu = 'BCCP'`
- → biểu đồ GROUP BY `nhom_dich_vu` từ dim_spdv → ra đủ 4 nhóm chính

### Xác minh trước khi sửa:
Thợ cần chạy để kiểm tra dim_spdv:
```python
import sqlite3
conn = sqlite3.connect(r'E:\OneDrive\z.Database-TTKD-Data\dashboard.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dim_spdv'")
print('dim_spdv exists:', c.fetchone())
c.execute("PRAGMA table_info(dim_spdv)")
print('Columns:', c.fetchall())
c.execute("SELECT DISTINCT nhom_dich_vu FROM dim_spdv LIMIT 20")
print('nhom_dich_vu values:', c.fetchall())
conn.close()
```

## Phương án sửa

### Option A (Khuyến nghị): Thêm filter trong `query_revenue()`
Trong `analytics/revenue.py`, thêm điều kiện vào WHERE:
```python
# Luôn chỉ lấy dữ liệu BCCP khi query từ bảng transactions (bảng BCCP)
query_parts.append("AND d.nhom_dich_vu = 'BCCP'")
# HOẶC nếu dim_spdv có nhóm chi tiết hơn:
query_parts.append("AND d.nhom_chinh = 'BCCP'")
```

### Option B: Filter ở kpi_callbacks.py trước khi vẽ chart
Nếu không muốn thay đổi analytics layer, filter trong callback:
```python
# Trước khi vẽ pie chart
if 'nhom_dv' in df_cur.columns:
    # Chỉ giữ các nhóm DV thuộc BCCP
    bccp_nhom_dv = ['Truyền thống', 'TMĐT', 'Quốc tế', 'Phát hành báo chí']
    df_pie = df_cur[df_cur['nhom_dv'].isin(bccp_nhom_dv)].groupby("nhom_dv")["cuoc_tt_tong"].sum().reset_index()
```

### Option C (Tốt nhất): JOIN dim_dichvu thay vì dim_spdv
Thay `LEFT JOIN dim_spdv d ON t.san_pham_dv = d.ma_spdv` bằng:
```sql
LEFT JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
WHERE d.nhom_chinh = 'BCCP' OR d.nhom_chinh IS NULL
```

> Thợ cần xác minh `dim_dichvu.ma_dich_vu` có khớp với `transactions.san_pham_dv` không trước khi dùng Option C

## Acceptance Criteria
```gherkin
Given người dùng xem trang /bccp, chọn tháng 5/2026
When biểu đồ Cơ cấu doanh thu render
Then legend chỉ hiển thị: Truyền thống, TMĐT, Quốc tế, Phát hành báo chí
And KHÔNG có HCC, TCBC, PPBL trong legend

Given tổng doanh thu trong Donut
Then khớp với KPI card "Tổng doanh thu" ở trên
```

## Ghi chú
- Sau khi sửa, label trong biểu đồ sẽ là nhóm DV BCCP chi tiết (Truyền thống, TMĐT, Quốc tế, PHBC)
- Cần cập nhật `color_discrete_map` trong biểu đồ nếu đang map theo tên cũ
