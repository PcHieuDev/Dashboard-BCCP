# TIP-cb-003: Sửa sparkline column + division zero + StringIO + dead cursor

## HEADER
- TIP-ID: TIP-cb-003
- Branch: fix/critical-callbacks
- Module: kpi_callbacks.py, service_detail_callbacks.py, db/connection.py, service_callbacks.py
- Depends on: TIP-cb-001
- Priority: P1
- Estimated effort: 20 phút

## CONTEXT
- Bug refs: H-06 (sparkline cột sai), H-11 (division zero), M-12 (StringIO), M-13 (dead cursor)

## TASK
1. kpi_callbacks.py: Tìm get_trend_series, sửa filter `nhom_dv` sang tên cột thực tế (có thể là nhom_dich_vu - xác nhận bằng cách đọc query_revenue)
2. service_detail_callbacks.py ~dòng 186-191: Thêm `elif curr > 0: return 100.0` vào hàm calc_change
3. db/connection.py dòng ~106: `pd.read_json(json_data, ...)` → `pd.read_json(StringIO(json_data), ...)`, thêm `from io import StringIO` nếu chưa có
4. service_callbacks.py: Xóa 2 dòng `cursor = conn.cursor()` trong query_sub_service_data và query_sub_service_data_ytd

## ACCEPTANCE CRITERIA
Given: Dashboard KPI có filter nhóm dịch vụ
When: Sparkline render
Then: Không rỗng (có dữ liệu)

Given: Dịch vụ mới (prev=0, curr>0)
When: service_detail render
Then: Hiển thị +100%

## CONSTRAINTS
- KHÔNG refactor hàm nào
- Surgical
