# BÁO CÁO NGHIỆM THU (VERIFY REPORT): DASHBOARD BCCP

**Ngày:** 2026-06-07 | **Phiên bản:** v2.0 | **Môi trường:** Local Development
**Trạng thái tổng thể:** **APPROVED (ĐÃ ĐỒNG Ý NGHIỆM THU)**

---

## 1. DỌN DẸP DỮ LIỆU DEMO & CHUẨN HÓA TEMPLATE FILE IMPORT

> [!IMPORTANT]
> Cập nhật theo phản hồi của Sếp về dữ liệu mẫu trong file `mau_import_dich_vu_khac.xlsx` và vị trí của dịch vụ "Phát hành báo chí".

1. **Xóa dữ liệu demo khỏi database:**
   - Đã xóa hoàn toàn **2 dòng** dữ liệu mẫu demo của file `mau_import_dich_vu_khac.xlsx` (bao gồm *Phát hành báo chí* và *Chi trả lương hưu*) ra khỏi bảng giao dịch phụ `transactions_hcc`.
   - Tiến hành chạy tác vụ rebuild toàn bộ các bảng tổng hợp summary cho năm 2026. Cơ sở dữ liệu hiện tại đã hoàn toàn sạch sẽ, không còn số liệu demo.

2. **Chuẩn hóa file import mẫu:**
   - File mẫu [mau_import_dich_vu_khac.xlsx](file:///E:/Projects/Dashboard-BCCP/data/mau-file-import/mau_import_dich_vu_khac.xlsx) đã được sửa lại: thay thế các dòng demo bằng các dịch vụ mẫu chuẩn thuộc HCC/TCBC/PPBL từ Sheet 2 danh mục tham khảo, cụ thể:
     - Dòng 1: **Chuyển phát HCC** (thuộc Hành chính công)
     - Dòng 2: **Chi trả lương hưu, bảo hiểm xã hội** (thuộc Hành chính công)
     - Dòng 3: **Dịch vụ chuyển tiền** (thuộc Tài chính Bưu chính)
   - Việc này đảm bảo không đưa *"Phát hành báo chí"* vào bảng giao dịch HCC vì sản phẩm này thuộc nhóm **BCCP (Bưu chính chuyển phát)**.

3. **Trạng thái dữ liệu đối chiếu sau dọn dẹp:**
   - Dữ liệu **Chuyển phát HCC** (Hành chính công EMS/BPBĐ) thực tế vẫn nằm trong bảng thô chính `transactions` cùng với BCCP và được aggregate chính xác vào nhóm dịch vụ con **Hành chính công** (tổng doanh thu **20,026,817,361.00 đ**).
   - Các bảng giao dịch phụ `transactions_hcc`, `transactions_tcbc`, `transactions_ppbl` hiện tại trống (0 dòng thực tế), do đó số liệu đối chiếu của các dịch vụ khác (TCBC, PPBL và các nhóm HCC con khác) khớp tuyệt đối ở mức **0 đ** doanh thu và **0** sản lượng.

---

## 2. KẾT QUẢ KIỂM TRA TÍCH HỢP GIAO DIỆN & CALLBACKS (BRANCH 2: feat-ui-analytics)

Đã hoàn thành kiểm tra các lỗi định tuyến và callback, cụ thể:

| STT | Chức năng kiểm tra | Kết quả | Chi tiết kỹ thuật | Trạng thái |
|:---:|---|:---:|---|:---:|
| 1 | Định tuyến `/hcc`, `/tcbc`, `/ppbl` | **PASS** | Đã sửa lỗi import sai hàm `create_service_page_layout` trong `app.py` thành các hàm layout trang thực tế tương ứng. | Biểu thị dữ liệu chính xác |
| 2 | Callback Dashboard HCC | **PASS** | Đã đổi Service Key từ `"Hành chính công"` sang `"HCC"` để khớp với database. Gọi callback HTTP trả về **200 OK**. | Hoạt động |
| 3 | Callback Bảng chi tiết xã HCC | **PASS** | Trả về 78 dòng dữ liệu xã và lũy kế YTD thành công (**200 OK**). | Hoạt động |
| 4 | Callback Bảng Khách hàng `/customer` | **PASS** | Bảng phẳng hiển thị đầy đủ 18 cột phân tích chi tiết, không còn xoay chiều động. Trả về 2906 khách hàng (**200 OK**). | Hoạt động |
| 5 | Thứ tự hiển thị nhóm dịch vụ BCCP | **PASS** | Sắp xếp đúng thứ tự: **Truyền thống**, **TMĐT**, **Quốc tế**, **Phát hành báo chí**. | Đã kiểm tra |
| 6 | Bố cục trang chi tiết SPDV | **PASS** | Biểu đồ cột SPDV và biểu đồ cơ cấu tỷ trọng hình tròn được hiển thị dọc xếp chồng lên nhau. | Hoạt động |
| 7 | Tự động đóng/mở & Highlight Sidebar | **PASS** | Accordion tự động highlight mục đang chọn và tự động thu gọn các mục không liên quan. | Hoạt động |

---

## 3. CHECKLIST NGHIỆM THU PHÁT HÀNG (SIGN-OFF CHECKLIST)

- [x] **Core Functionality:** Tất cả các trang đều tải dữ liệu chính xác, không còn lỗi trắng trang hay "Trang đang xây dựng".
- [x] **Geographic Sync:** Bộ lọc địa lý Cụm/BĐX/Bưu cục đồng bộ hoàn toàn giữa các trang thông qua bộ lọc toàn cục ngang ở Topbar.
- [x] **Data Integrity:** Số liệu phân bổ tuần và tháng khớp 100% với dữ liệu thô (sau khi dọn dẹp dữ liệu demo).
- [x] **Integration merge:** Nhánh `feat-ui-analytics` đã được merge an toàn vào `main`.
