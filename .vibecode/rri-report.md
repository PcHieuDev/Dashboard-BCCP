# RRI Report: Yêu cầu chi tiết cho bảng `agg_daily` và cột `BK/E`

Tài liệu ghi nhận kết quả Phỏng vấn ngược làm rõ yêu cầu (Reverse Requirements Interview - RRI) giữa Sếp và Contractor.

---

## 1. Kết Quả Phỏng Vấn Nghiệp Vụ (Q&A)

| Câu hỏi RRI | Quyết định của Sếp (Đáp án) | Ý nghĩa kỹ thuật / Logic áp dụng |
| :--- | :--- | :--- |
| **Q1**: Phân loại `BK/E` cho dịch vụ phụ (TCBC, PPBL, PHBC)? | **Phương án A**: Mặc định là `'Khác'`. | Các dòng dữ liệu từ 4 bảng phụ nếu không tìm thấy mã trong file mapping sẽ được gán giá trị mặc định là `'Khác'`. |
| **Q2**: Xử lý mã dịch vụ mới hoặc trống cột `BK/E`? | **Phương án A + Ghi Log**: Gán mặc định là `'Khác'` + Ghi cảnh báo trong log import. | Hệ thống tự động gán `'Khác'` để tiến trình chạy mượt, đồng thời in cảnh báo trong log để Sếp biết cần bổ sung mapping và chạy import đè. |
| **Q3**: Cột số lượng khách hàng phát sinh (`so_kh_phat_sinh`)? | **Có**. | Thêm cột `so_kh_phat_sinh` vào bảng `agg_daily`. Logic đếm: `COUNT(DISTINCT cms)` cho các khách hàng hợp lệ (không null/rỗng/vãng lai). |
| **Q4**: Cập nhật giao diện Dashboard chính? | **Chưa nâng cấp**. | Không chỉnh sửa giao diện Dash App (UI) trong đợt này. Chỉ bổ sung bảng, cấu trúc DB và logic ETL chạy ngầm. |
| **Q5**: Phạm vi năm dữ liệu tổng hợp? | **Rebuild toàn bộ từ đầu năm 2025**. | Script `rebuild_summaries.py` sẽ thực hiện quét và tổng hợp dữ liệu ngày cho cả năm 2025 và 2026. |

---

## 2. Phạm Vi Thực Hiện (Scope of Work)

### 📌 Trong phạm vi (In-Scope)
*   **Database**: Bổ sung bảng `agg_daily` có cột `bk_e`. Cập nhật bảng `dim_dichvu` để thêm cột `bk_e`.
*   **Đồng bộ Mapping**: Cập nhật `sync_mappings.py` để import cột `BK/E` từ file `001-mapping-spdv-new.csv` mới vào bảng `dim_dichvu`.
*   **Tiến trình ETL**: 
    *   Hàm khởi tạo summary tables bổ sung tạo bảng `agg_daily` và index.
    *   Viết hàm `rebuild_daily` gộp doanh thu, sản lượng, và đếm số khách hàng phát sinh theo Ngày + Bưu cục + Nhóm dịch vụ con + BK/E cho mảng BCCP và các mảng dịch vụ phụ.
    *   Tích hợp vào `rebuild_summaries.py` chạy cho cả 2025 và 2026.
*   **Đối chiếu số liệu**: Cập nhật `verify_sums.py` để kiểm tra đối chiếu tính đúng đắn của bảng ngày so với bảng thô.

### 🚫 Ngoài phạm vi (Out-of-Scope)
*   Không thay đổi giao diện Dash App (UI).
*   Không sửa đổi bất kỳ tệp tin nào thuộc dự án Chatbot.
