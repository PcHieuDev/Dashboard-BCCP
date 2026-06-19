# Branch Plan: Triển khai tính năng `agg_daily` có cột `BK/E`

Kịch bản phân nhánh và điều phối thực hiện các nhiệm vụ (TIPs) cho dự án Dashboard-BCCP.

---

## 1. Kế hoạch Phân Nhánh (Branching Strategy)
*   **Mô hình**: Single Mode (Dự án quy mô nhỏ, chạy trên một nhánh phát triển độc lập).
*   **Nhánh phát triển**: `feat/agg-daily`
*   **Đường dẫn Worktree đề xuất**: `E:\Projects\worktrees\Dashboard-BCCP\feat-agg-daily`
*   **Thứ tự thực hiện**: Tuyến tính (TIP-001 -> TIP-002 -> TIP-003 -> TIP-004).

---

## 2. Danh Sách Nhiệm Vụ (Task List / TIPs)

| Mã TIP | Tên Nhiệm Vụ | File Ảnh Hưởng | Độ Ưu Tiên |
| :--- | :--- | :--- | :--- |
| **TIP-agg-001** | Đồng bộ cột `BK/E` vào `dim_dichvu` | `data/mapping-spdv.csv`<br>`scripts/sync_mappings.py` | P0 (Cao nhất) |
| **TIP-agg-002** | Tạo bảng `agg_daily` & viết hàm ETL | `etl/aggregator.py` | P0 |
| **TIP-agg-003** | Tích hợp Rebuild số liệu 2025 & 2026 | `scripts/rebuild_summaries.py` | P0 |
| **TIP-agg-004** | Cập nhật Script kiểm tra đối chiếu số liệu | `scripts/verify_sums.py` | P0 |

---

## 3. Quy trình Thi công (Build Execution)
1.  **Contractor** tạo nhánh `feat/agg-daily` và tạo worktree tương ứng tại thư mục `E:\Projects\worktrees\Dashboard-BCCP\feat-agg-daily`.
2.  Chuyển sang vai trò **Builder** trên worktree mới để thực thi từng TIP.
3.  Sau mỗi TIP, Builder thực hiện chạy kiểm thử, viết Completion Report, cập nhật Build Log và thực hiện Commit.
4.  Khi hoàn thành tất cả TIP, Contractor thực hiện Verify (Nghiệm thu) và Merge vào nhánh `main`.
