# Context — Phase 11: PRD Fixes & Tối ưu

**Ngày tạo**: 2026-06-04
**Branch**: feat/phase11-fixes
**Worktree**: E:\Projects\worktrees\Dashboard-BCCP\feat-phase11-fixes

## Yêu cầu sửa lỗi từ Sếp
1. `/bccp`: Top 10 CMS sai số liệu (300 triệu/khách), Tuần 53 bị lỗi hiển thị, bỏ Area Chart.
2. `/bccp/customer`: Gộp 2 bộ lọc, bỏ 1 nút Xuất Excel bị trùng, xóa cột (Trạng thái HĐ, Bưu cục) ở bảng CMS, chỉ giữ sản lượng và cước.
3. `/bccp/new-customer`: Bỏ dropdown lọc theo Bưu điện Huyện/Xã (chỉ lọc theo cụm), bảng BĐX tự hiển thị. Các bảng cần có filter native.
4. `/bccp/retention`: Sếp chốt định nghĩa **Khách hàng Hiện hữu (KHHH)** là *khách hàng có giao dịch trong tháng (có CMS) và KHÔNG phải là khách hàng mới*. Do đó, không cần quét 3 tháng liên tiếp nữa, dùng thẳng bảng `new_customers` để loại trừ. Điều này sẽ giúp trang tải siêu tốc mà không cần script tạo bảng trung gian.

## File cần quan tâm
- `analytics/retention_metrics.py`: Sửa định nghĩa `get_khhh_list` cực nhanh.
- `dash_app/callbacks/kpi_callbacks.py`: Fix lỗi Top 10 CMS, bỏ Area chart.
- `dash_app/pages/...`: Sửa giao diện, loại bỏ element dư thừa.
- `dash_app/callbacks/utils.py`: Hàm `get_bccp_weeks`.

## Thứ tự thi công
- TIP-11-001: `/bccp` Fixes (Top 10 CMS, Tuần 53, Bỏ Area Chart)
- TIP-11-002: `/bccp/customer` Fixes (Gộp bộ lọc, Columns, Export)
- TIP-11-003: `/bccp/new-customer` Fixes (Bỏ lọc BĐX, Native Filter)
- TIP-11-004: `/bccp/retention` Tối ưu Performance (Logic KHHH mới)
