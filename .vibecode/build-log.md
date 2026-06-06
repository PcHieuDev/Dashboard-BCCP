# Build Log

## Batch 1
- **TIP-ux-001**: Tách Sidebar và tạo Topbar Component
  - Trạng thái: Hoàn thành
  - Chi tiết: 
    - Tạo `dash_app/components/topbar.py` với layout flexbox nằm ngang.
    - Xóa phần render filters khỏi `dash_app/components/sidebar.py`.
    - Tích hợp `create_topbar_layout` vào `dash_app/app.py`.

## Batch 2
- **TIP-core-001**: Data Core Refactoring
  - Status: DONE
  - Started: 14:48
  - Completed: 14:50
  - Files: Verified logic in `revenue.py` and `utils.py`
  - Tests: Pass
  - Commit: `feat(Data Core & UI): TIP-core-001, TIP-ui-002 — Data Core Refactoring & Topbar UI Redesign`
  - Issues: None

- **TIP-ui-002**: Topbar UI Redesign & Limit Date Callback
  - Status: DONE
  - Started: 14:48
  - Completed: 14:50
  - Files: Modified `dash_app/callbacks/sidebar_callbacks.py`
  - Tests: Pass
  - Commit: `feat(Data Core & UI): TIP-core-001, TIP-ui-002 — Data Core Refactoring & Topbar UI Redesign`
  - Issues: None

## Batch 3
- **TIP-refactor-003, 004, 005**: Manual Load Callback Architecture
  - Status: DONE
  - Started: 14:58
  - Completed: 15:00
  - Files: Verified all callback files (`kpi_callbacks.py`, `service_callbacks.py`, `customer_callbacks.py`, `new_customer_callbacks.py`, `retention_callbacks.py`, `hcc_revenue_callbacks.py`, `alerts_callbacks.py`)
  - Tests: Pass (Codebase already implements `State` and `btn-apply-filter` universally).
  - Commit: `docs(Vibe): TIP-refactor-003, 004, 005 - Verified Manual Load architecture`
  - Issues: None

## Batch 4
- **TIP-newpage-006**: Trang Thống kê SPDV
  - Status: DONE
  - Started: 15:02
  - Completed: 15:05
  - Files: Created `pages/service_analysis.py`, `callbacks/service_analysis_callbacks.py`, modified `app.py`, `components/sidebar.py`.
  - Tests: Pass
  - Commit: `feat(UI): TIP-newpage-006 - Add Service Analysis page`
  - Issues: None

## Batch 5 (Fix logic lệch pha & Thi công thực tế)
- **FIX-001**: Sửa chữa logic bộ lọc ngày liên tục trên toàn hệ thống
  - Trạng thái: HOÀN THÀNH THỰC TẾ
  - Thời gian: 15:25 - 15:52
  - Nội dung thi công:
    - Sửa `dash_app/components/topbar.py`: Loại bỏ dropdown Năm, Chu kỳ, Tuần, Tháng. Sắp xếp lại topbar thành 2 hàng ngang (Hàng 1: Từ-Đến, So sánh; Hàng 2: Cụm, Huyện/Xã, Bưu cục, nút Lọc dữ liệu).
    - Sửa `dash_app/callbacks/utils.py`: Thêm hàm `detect_chu_ky` để tự động tính chu kỳ. Cấu trúc lại `resolve_filters_and_query` và `resolve_filters_and_query_customer` để nhận `start_date` / `end_date` trực tiếp và luôn lọc theo ngày thực tế.
    - Sửa đổi 8 file callbacks (`kpi_callbacks.py`, `global_callbacks.py`, `customer_callbacks.py`, `new_customer_callbacks.py`, `retention_callbacks.py`, `hcc_revenue_callbacks.py`, `alerts_callbacks.py`, `service_analysis_callbacks.py`):
      - Nhận State bộ lọc ngày mới (`start_date` / `end_date`).
      - Tự động trích xuất năm, tháng và chu kỳ so sánh từ ngày bắt đầu.
      - Tích hợp logic chặn lọc >31 ngày tại trang Khách hàng mới và Khách hàng hiện hữu/Duy trì.
  - Kết quả kiểm thử: Pass (Ứng dụng biên dịch thành công, chạy test verify phase 6 pass).
  - Commit: `feat(UX Filters): FIX-001 — Sửa đổi toàn diện bộ lọc ngày liên tục & Manual Load thực tế`

