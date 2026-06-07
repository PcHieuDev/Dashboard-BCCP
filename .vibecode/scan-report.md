# SCAN REPORT: Dashboard BCCP — Sửa lỗi & Tối ưu giao diện (5 yêu cầu)
Generated: 2026-06-07
Type: Focus Scan on Bug Fixing & UX Refinement
Role: Contractor (Chủ thầu)

---

## 1. PHÂN TÍCH CHI TIẾT 5 LỖI & YÊU CẦU

### Yêu cầu 1: Lỗi chuyển trang và sidebar accordion
*   **Hiện trạng:** Khi chuyển giữa các trang (ví dụ về trang chủ `/` hoặc sang trang dịch vụ khác `/hcc`), accordion "Bưu chính chuyển phát" không tự động thu gọn mà vẫn mở. Đồng thời nút accordion này luôn ở trạng thái "sáng" (nền xám nhạt, chữ đen đậm).
*   **Nguyên nhân gốc rễ:** 
    1.  Trong `dash_app/callbacks/sidebar_callbacks.py`, khi chuyển về `/`, callback trả về `active_accordion = None`. Tuy nhiên, component `dbc.Accordion` của Dash Bootstrap Components khi nhận giá trị `active_item=None` thông qua callback có thể không kích hoạt đóng client-side nếu trạng thái mở rộng được kiểm soát uncontrolled hoặc do CSS ghi đè.
    2.  Trong `dash_app/assets/style.css`, class `.sidebar-accordion .accordion-button:not(.collapsed)` quy định nền `#E2E8F0` (xám) và chữ `#0F172A` (tối đậm) cho bất kỳ accordion nào đang mở, khiến người dùng có cảm giác accordion này luôn "sáng" và lấn át các menu con.
*   **Giải pháp:** 
    *   Cần kiểm tra thuộc tính `persistence` của `dbc.Accordion` hoặc cấu trúc lại callback để đảm bảo đóng khi `active_item=None`.
    *   Tối ưu lại CSS của `.accordion-button` để khi accordion mở nhưng không chứa trang con đang active thì không được tô màu sáng nổi bật.

### Yêu cầu 2: Trùng lặp xã ở bảng chi tiết xã
*   **Hiện trạng:** Bảng "Chi tiết doanh thu theo Bưu cục Xã" hiển thị một xã nhiều lần (ví dụ: "Bưu điện xã Anh Sơn" xuất hiện 3-4 lần).
*   **Nguyên nhân gốc rễ:** 
    *   Các hàm `get_period_detail_by_xa` và `get_ytd_detail_by_xa` trong `analytics/global_metrics.py` (dành cho trang chính) và các hàm `query_sub_service_data` / `query_sub_service_data_ytd` trong `dash_app/callbacks/service_callbacks.py` (dành cho các trang dịch vụ con) đang gom nhóm SQL theo cột `buu_cuc` (mã bưu cục `ma_bc`).
    *   Khi join với danh mục `dim_buucuc` (có 654 bưu cục nhưng thực tế chỉ có 141 xã `ma_bdx` độc bản), nhiều bưu cục cùng thuộc một xã sẽ trả về nhiều dòng có cùng tên xã `ten_bdx`.
*   **Giải pháp:** 
    *   Thực hiện gom nhóm (groupby) và cộng dồn (sum) dữ liệu doanh thu/sản lượng theo mã xã `ma_bdx` và tên xã `ten_bdx` trước khi trả về DataFrame hiển thị.

### Yêu cầu 3: Trang dịch vụ con (/hcc, /tcbc, /ppbl) không cập nhật dữ liệu
*   **Hiện trạng:** Khi thay đổi bộ lọc và nhấn áp dụng, dữ liệu ở các trang dịch vụ con không hoạt động, không cập nhật.
*   **Nguyên nhân gốc rễ:**
    1.  Các hàm truy vấn dữ liệu trong `service_callbacks.py` (như `query_sub_service_data`) đang đọc doanh thu từ bảng `agg_monthly` và `agg_weekly`.
    2.  Thực tế kiểm tra database chỉ ra rằng `agg_monthly` và `agg_weekly` chỉ chứa các nhóm dịch vụ chính là `'BCCP'` và `'HCC'`, hoàn toàn không chứa dữ liệu của các dịch vụ `'TCBC'` và `'PPBL'`.
    3.  Dữ liệu thực tế của HCC, TCBC, PPBL được lưu trong các bảng riêng biệt: `transactions_hcc`, `transactions_tcbc`, `transactions_ppbl` và không được đồng bộ đầy đủ vào bảng aggregate.
*   **Giải pháp:** 
    *   Cấu trúc lại logic query trong `service_callbacks.py` để trỏ đúng vào các bảng transactions của từng dịch vụ con tương ứng (`transactions_hcc`, `transactions_tcbc`, `transactions_ppbl`) khi tính toán, thay vì dùng chung bảng `agg_monthly`/`agg_weekly` của BCCP.

### Yêu cầu 4: Trang `/bccp/customer` (Bộ lọc & Bảng hiển thị & Sidebar highlight)
*   **Hiện trạng:** 
    1.  Bộ lọc nâng cao không có nút Lọc riêng biệt.
    2.  Sidebar vẫn highlight bôi đậm accordion "Bưu chính chuyển phát" mà không sáng ở liên kết con "Chi tiết khách hàng" đang chọn.
    3.  Bảng hiển thị dưới chưa đúng các cột yêu cầu.
*   **Nguyên nhân gốc rễ:**
    *   Trang này chưa được gộp bộ lọc nâng cao và bảng hiển thị chưa cập nhật theo thiết kế mới (đang thiếu cột tên cụm, tên xã, bưu cục chấp nhận, mã CMS, sản lượng, doanh thu không VAT).
    *   Định dạng CSS hoạt động của liên kết con `.sidebar-menu-item.active.active-bccp` bị ghi đè hoặc không có hiệu lực trực quan.
*   **Giải pháp:**
    *   Loại bỏ nút "Lọc" nâng cao, kết hợp các trường lọc và đưa kết quả trực tiếp về bộ lọc tổng. Gộp "Nhóm dịch vụ" và "Chiều phân tích" vào 1 nơi trong bộ lọc nâng cao.
    *   Cập nhật cấu trúc bảng hiển thị ở `customer_detail.py` và `customer_callbacks.py` để select đúng các trường: cụm, xã, bưu cục, mã CMS, sản lượng, doanh thu không VAT.
    *   Tối ưu CSS để highlight rõ ràng link con đang active.

### Yêu cầu 5: Trang `/bccp/service-detail`
*   **Hiện trạng:** Cần thêm biểu đồ doanh thu & sản lượng theo mã SPDV; đưa bảng thống kê xuống dưới và thêm cột sản lượng; bỏ biểu đồ cơ cấu tỷ trọng doanh thu theo nhóm dịch vụ.
*   **Nguyên nhân gốc rễ:** Thiết kế cũ chưa đáp ứng các yêu cầu này.
*   **Giải pháp:**
    *   Chỉnh sửa layout trong `pages/service_detail.py`.
    *   Chỉnh sửa callback trong `callbacks/service_detail_callbacks.py` để vẽ thêm 2 biểu đồ cột (doanh thu và sản lượng theo mã SPDV), bổ sung cột sản lượng vào bảng thống kê mã SPDV và gỡ bỏ biểu đồ cơ cấu tỷ trọng.

---

## 2. CÁC FILE LIÊN QUAN TRỰC TIẾP

1.  **Sidebar & Điều hướng:**
    *   `dash_app/components/sidebar.py`
    *   `dash_app/callbacks/sidebar_callbacks.py`
    *   `dash_app/assets/style.css`
2.  **Bảng bưu cục xã & Trùng lặp xã:**
    *   `analytics/global_metrics.py`
    *   `dash_app/callbacks/service_callbacks.py`
3.  **Trang dịch vụ con:**
    *   `dash_app/callbacks/service_callbacks.py`
    *   `dash_app/pages/service_overview.py`
4.  **Chi tiết khách hàng (`/bccp/customer`):**
    *   `dash_app/pages/customer_detail.py`
    *   `dash_app/callbacks/customer_callbacks.py`
5.  **Chi tiết sản phẩm dịch vụ (`/bccp/service-detail`):**
    *   `dash_app/pages/service_detail.py`
    *   `dash_app/callbacks/service_detail_callbacks.py`
