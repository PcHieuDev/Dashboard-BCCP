# TIP-008 Completion Report
- **Status**: DONE
- **Issues Found**: None
- **Resolution**: 
  - Thay đổi UI trong `kpi_cards.py` từ thẻ Hành chính công sang thẻ "📰 Phát hành báo chí" (ID: `kpi-phbc-value`, màu `#F97316`).
  - Cập nhật `kpi_callbacks.py`: Thêm hàm helper `_get_phbc_revenue` truy vấn trực tiếp bảng `transactions_phbc`.
  - Điều chỉnh biến `bccp_cur` bằng `tot_cur` (do dữ liệu HCC đã được đẩy sang nhóm khác). Đưa giá trị `phbc` render lên KPI grid.
