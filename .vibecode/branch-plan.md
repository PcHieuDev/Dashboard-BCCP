# BRANCH PLAN — Kế hoạch phân chia nhánh và thứ tự thực hiện
Generated: 2026-06-07
Role: Contractor (Chủ thầu)
User (Boss): Sếp

---

## 1. PHÂN CHIA NHÁNH (GIT BRANCHES & WORKTREES)

Để thực hiện công việc sửa lỗi một cách khoa học, tránh xung đột mã nguồn và dễ dàng nghiệm thu, công việc được chia thành 2 nhánh phát triển tương ứng với 2 worktrees độc lập:

| Nhánh phát triển | Worktree Path | File ảnh hưởng | TIPs phụ trách | Thứ tự |
| :--- | :--- | :--- | :--- | :--- |
| **`feat-db-etl`** | `E:\Projects\worktrees\Dashboard-BCCP\feat-db-etl` | `scripts/migrate_to_dashboard_db.py`<br>`etl/importer.py`<br>`etl/aggregator.py` | `TIP-fix-db-etl` | **1 (Thực hiện trước)** |
| **`feat-ui-analytics`** | `E:\Projects\worktrees\Dashboard-BCCP\feat-ui-analytics` | `analytics/global_metrics.py`<br>`dash_app/callbacks/global_callbacks.py`<br>`dash_app/callbacks/sidebar_callbacks.py`<br>`dash_app/callbacks/service_callbacks.py`<br>`dash_app/pages/customer_detail.py`<br>`dash_app/callbacks/customer_callbacks.py`<br>`dash_app/pages/service_detail.py`<br>`dash_app/callbacks/service_detail_callbacks.py`<br>`dash_app/assets/style.css` | `TIP-fix-ui-callbacks` | **2 (Thực hiện sau)** |

---

## 2. QUY TRÌNH THỰC HIỆN VÀ MERGE

1.  **Bước 1: Triển khai nhánh `feat-db-etl`**
    *   Tạo nhánh và worktree `feat-db-etl`.
    *   Nâng cấp cơ sở dữ liệu (ALTER TABLE).
    *   Sửa logic import Excel (`importer.py`) để lưu 6 cột ngày.
    *   Sửa logic tổng hợp (`aggregator.py`) để phân bổ trung bình ngày và lưu nhóm dịch vụ con.
    *   Rebuild dữ liệu và kiểm thử dữ liệu khớp hoàn toàn.
    *   Merge nhánh `feat-db-etl` vào `main`.

2.  **Bước 2: Triển khai nhánh `feat-ui-analytics`**
    *   Sau khi `feat-db-etl` đã merge vào `main`, tạo nhánh và worktree `feat-ui-analytics` từ `main`.
    *   Chỉnh sửa các câu SQL ở Tổng quan chung để quy đổi ngược về nhóm chính.
    *   Sửa logic dồn dòng theo xã và hiển thị cột Tên Xã (bỏ lặp xã).
    *   Cập nhật sidebar, accordion, và highlight.
    *   Tái cấu trúc trang `/bccp/customer` và `/bccp/service-detail`.
    *   Đồng bộ bộ lọc địa lý cho các trang dịch vụ con và sắp xếp thứ tự dịch vụ BCCP.
    *   Merge nhánh `feat-ui-analytics` vào `main`.

3.  **Bước 3: Final Verify**
    *   Kiểm thử tích hợp toàn bộ hệ thống trên nhánh `main`.
