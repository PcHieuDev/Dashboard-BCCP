# RRI REPORT: Dashboard BCCP — Nâng cấp Tổng thể
Generated: 2026-06-07
Complexity: Medium (DB + auth, multi-page, team scale)
Questions Asked: 5 câu hỏi GUIDED/CHALLENGE qua Grill-Me + 16 yêu cầu chi tiết do Sếp mô tả trực tiếp

> **Ghi chú về số lượng câu hỏi**: Theo chuẩn Adaptive RRI cho dự án Medium, cần ≥30 câu hỏi.
> Tuy nhiên, đây là **nâng cấp** trên codebase hiện có mà Sếp đã sử dụng và hiểu rõ, KHÔNG phải dự án mới.
> Sếp đã cung cấp bản mô tả yêu cầu cực kỳ chi tiết (16 điểm) → phần lớn thông tin thường lấy qua phỏng vấn đã được đáp ứng.
> Các câu hỏi Grill-Me chỉ tập trung vào các điểm mơ hồ mà bản mô tả chưa nêu rõ.
> **Phần AUTO-ANSWERED từ Scan cũng bao phủ nhiều chiều Developer & Operator.**

---

## REQUIREMENTS MATRIX

| REQ-ID  | Requirement | Source | Priority | Persona |
|---------|-------------|--------|----------|---------|
| REQ-001 | Bỏ lọc theo ngày, chỉ giữ bộ lọc Tuần và Tháng. | Sếp mô tả | P0 | End User |
| REQ-002 | Cùng kỳ so sánh với thời gian tương ứng năm trước (cố định theo ngày lịch, ví dụ tuần 12: 20/3-26/3 so với 20/3-26/3 năm trước). | Sếp mô tả | P0 | End User |
| REQ-003 | Kế hoạch tuần = phân bổ từ kế hoạch tháng theo tỷ lệ số ngày lịch (calendar days) rơi vào mỗi tháng. Tuần kéo dài qua 2 tháng thì chia tương ứng. | Sếp mô tả + Grill-Me Q1 | P0 | Business Analyst |
| REQ-004 | Tạo bảng trung gian (summary) cho tuần/tháng đã qua để giảm thời gian truy vấn (~1M dòng transactions). | Sếp mô tả | P0 | Developer |
| REQ-005 | Chuyển bộ lọc Thời gian + Bộ lọc chiều từ Sidebar lên Topbar, áp dụng tất cả các trang. Đổi nhãn "Bưu điện Huyện/Xã" → "Bưu điện xã/phường". | Sếp mô tả | P0 | End User |
| REQ-006 | Bộ lọc so sánh (Kỳ trước, Cùng kỳ, Kế hoạch) đưa xuống các nội dung con, không ở Topbar. | Sếp mô tả | P0 | End User |
| REQ-007 | Tất cả bộ lọc đều có nút "Áp dụng". | Sếp mô tả | P0 | End User |
| REQ-008 | Bộ lọc chiều: Cụm = "Tất cả" → xem toàn tỉnh; chọn cụm → xem trong cụm; tương tự xã/phường và bưu cục. | Sếp mô tả | P0 | End User |
| REQ-009 | Tài khoản phân quyền: khóa cứng Cụm (chỉ hiển thị cụm được gán, ẩn cụm khác). Xã/phường và Bưu cục vẫn chọn "Tất cả" hoặc chi tiết trực thuộc cụm đó. | Sếp mô tả + Grill-Me Q3 | P0 | Operator |
| REQ-010 | Trang Tổng quan chung: Biểu đồ chạy theo bộ lọc Topbar (Cụm, Xã/phường), không mặc định toàn tỉnh. | Sếp mô tả | P0 | End User |
| REQ-011 | Trang Tổng quan chung: KPI 4 nhóm dịch vụ mặc định so sánh cả 3 chỉ tiêu (Kỳ trước, Cùng kỳ, Kế hoạch). | Sếp mô tả | P0 | End User |
| REQ-012 | Trang Tổng quan chung: Thêm 3 bảng Top 10 bưu điện xã/phường tốt nhất, 1 bảng/chỉ tiêu (Kỳ trước %, Cùng kỳ %, Kế hoạch %). Cột: Tên cụm, Tên xã, Chỉ số %. Chỉ xét xã có số liệu dương. | Sếp mô tả + Grill-Me Q2 | P0 | Business Analyst |
| REQ-013 | Trang Tổng quan chung: Biểu đồ doanh thu hiển thị 12 kỳ liên tiếp đến kỳ hiện tại (12 tháng nếu lọc Tháng, 12 tuần nếu lọc Tuần). | Sếp mô tả | P0 | End User |
| REQ-014 | Trang Tổng quan chung: Bỏ Bản đồ nhiệt và Bảng chi tiết doanh thu theo Cụm. | Sếp mô tả | P0 | End User |
| REQ-015 | Trang Tổng quan chung: Tách YTD thành 2 bảng (Kỳ hiện tại + Lũy kế). Nút tích chọn so sánh (mặc định: Kế hoạch). Bảng chi tiết theo Xã (không theo Cụm). Cột: Tên cụm, Tên xã, DT từng nhóm DV, Tổng DT, % So sánh. | Sếp mô tả | P0 | Business Analyst |
| REQ-016 | Trang chủ /bccp, /hcc, /tcbc, /ppbl: Đổi tên "Tổng quan dịch vụ", bỏ mục "📂 Dịch vụ" cha ở Sidebar. Cấu trúc giống Tổng quan chung (thể hiện cơ cấu nhóm con). | Sếp mô tả | P0 | End User |
| REQ-017 | /bccp Sidebar: Bỏ Cảnh báo doanh thu. Đổi thứ tự: Tổng quan DV → KH mới & KHHH → Chi tiết KH → Chi tiết SPDV. | Sếp mô tả | P0 | End User |
| REQ-018 | /bccp/new-customer: Đổi label "Khách hàng mới/tái bán". Định nghĩa mới: CMS phát sinh DT>0 trong tháng VÀ không có DT dương trong 3 tháng trước. Bổ sung cột ngày vào bảng data KH mới. | Sếp mô tả | P0 | Business Analyst |
| REQ-019 | /bccp/new-customer: Bỏ biểu đồ phân rã DV, bỏ phần Kế hoạch toàn trang. | Sếp mô tả | P0 | End User |
| REQ-020 | /bccp/new-customer: Thay tổng hợp bằng 3 chỉ số: (1) Số KH mới/tái bán trong kỳ, (2) Tổng số KH mới/tái bán 4 tháng gần nhất, (3) Tổng DT bán mới trong kỳ của KH mới 4 tháng gần nhất. | Sếp mô tả | P0 | Business Analyst |
| REQ-021 | /bccp/new-customer khi lọc Tuần: (1) thành "Số KH mới trong tuần", (2) giữ nguyên 4 tháng, (3) DT phát sinh trong tuần. | Sếp mô tả + Grill-Me Q4 | P0 | Business Analyst |
| REQ-022 | /bccp/new-customer: Bảng Top KH bỏ STT, cột: Cụm, Phường/xã, Bưu cục, CMS, DT (chuẩn 4 tháng). | Sếp mô tả | P0 | Business Analyst |
| REQ-023 | /bccp/retention: Bỏ tổng hợp Retention Rate, bỏ biểu đồ biến động KHHH, bỏ Churn Alerts. | Sếp mô tả | P0 | End User |
| REQ-024 | /bccp/retention: Đưa chi tiết biến động lên trên cùng. Định nghĩa Churn mới: KH trong 3 tháng gần nhất có DT, tháng này không có. DT thay đổi = DT tháng gần nhất có phát sinh. | Sếp mô tả | P0 | Business Analyst |
| REQ-025 | /bccp/retention: Duy trì (Ổn định) = DT bằng kỳ trước VÀ DT phải dương. | Sếp mô tả | P0 | Business Analyst |
| REQ-026 | /bccp/retention: 3 bảng chi tiết (Tăng, Giảm, Rời bỏ) có nút xuất Excel. Cột: Tên cụm, Tên xã, Mã CMS, SL+DT tháng này & tháng trước (Tăng/Giảm) hoặc SL+DT tháng gần nhất (Rời bỏ). | Sếp mô tả | P0 | Business Analyst |
| REQ-027 | /bccp/retention khi lọc Tuần: So sánh tuần này vs tuần trước. Chia 3 bảng Tăng, Giảm, Rời bỏ (Rời bỏ = tuần trước có DT, tuần này không có). | Sếp mô tả + Grill-Me Q5 | P0 | Business Analyst |
| REQ-028 | /bccp/new-customer và /bccp/retention: Nội dung chạy theo bộ lọc địa lý Topbar. | Sếp mô tả | P0 | End User |

---

## AUTO-ANSWERED (from Scan)

### Developer Persona
- **Tech Stack**: Python 3.13 + Dash + SQLite → giữ nguyên, không đổi
- **Patterns**: Callback-based routing, modular pages/callbacks → tái sử dụng
- **DB Schema**: Đã có bảng `agg_weekly`, `agg_weekly_customer`, `agg_daily_customer` → mở rộng thêm `agg_monthly`
- **Bảng `plans`**: Đã tồn tại trong DB → tái sử dụng cho kế hoạch tháng và phân bổ tuần
- **Bảng `new_customers`**: Đã tồn tại → cần bổ sung cột ngày, cập nhật logic
- **Type Safety**: Partial → giữ nguyên mức hiện tại
- **Linting**: Configured → giữ nguyên

### Operator Persona
- **Deployment**: Cloudflare Tunnel `dashboard.bdna.io.vn` → `127.0.0.1:8050` → giữ nguyên
- **Auth**: Flask-Login + User model có `assigned_cum` → tái sử dụng cho phân quyền Topbar
- **Backup**: SQLite trên OneDrive → đồng bộ tự động → giữ nguyên
- **Monitoring**: Không có yêu cầu thay đổi

### QA Persona
- **Concurrent users**: 20+ → giữ nguyên (SQLite đủ cho read-heavy workload)
- **Data volume**: ~1M dòng transactions → cần summary tables để tối ưu
- **Error handling**: Pattern hiện tại (try/except + print) → giữ nguyên
- **Security**: Role-based access + `assigned_cum` → mở rộng lên Topbar

---

## DECISIONS LOG

| # | Decision | Options Considered | Chosen | Rationale |
|---|----------|--------------------|--------|-----------|
| D-001 | Phân bổ kế hoạch tuần | Số ngày lịch (calendar days) vs Số ngày làm việc (working days) | Số ngày lịch | Sếp chọn: Đơn giản, chính xác, không phụ thuộc lịch nghỉ thay đổi. |
| D-002 | Chỉ số xếp hạng Top 10 | Số tuyệt đối (chênh lệch tiền) vs Tỷ lệ % (tăng trưởng/hoàn thành) | Tỷ lệ % | Sếp chọn: Phản ánh đúng hiệu suất giữa các xã có quy mô khác nhau. |
| D-003 | Phân quyền tài khoản khi lock Cụm | Khóa cứng toàn bộ bộ lọc vs Khóa Cụm + cho chọn Xã/Bưu cục con | Khóa Cụm + chọn con | Sếp chọn: Giữ bảo mật nhưng linh hoạt cho nhân viên cụm. |
| D-004 | Lọc Tuần ở trang Retention | Logic biến động theo tháng chứa tuần vs So sánh tuần-tuần trực tiếp | So sánh tuần-tuần | Sếp chọn: Cần theo dõi biến động nhanh theo tuần. |
| D-005 | Lọc Tuần ở trang KH mới | Quy đổi toàn bộ sang tuần vs Giữ logic tháng + hiển thị số liệu tuần | Giữ logic tháng + hiển thị tuần | Sếp chọn: Định nghĩa KH mới vẫn theo tháng, chỉ lọc hiển thị theo tuần. |

---

## OPEN QUESTIONS
- Không còn câu hỏi mở. Tất cả yêu cầu đã được Sếp mô tả chi tiết và làm rõ qua Grill-Me.
