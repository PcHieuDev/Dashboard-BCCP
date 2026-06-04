# TIP-fix-003: Thêm Nút Lọc + Fix Default Giá trị Bộ lọc (Bug #1)

## Header
- **TIP-ID**: TIP-fix-003
- **Branch**: feat/ui-fixes
- **Module**: components/sidebar, callbacks/* (nhiều file)
- **Dependencies**: Không
- **Priority**: P1 (UX improvement)
- **Estimated effort**: Large

## Bối cảnh
Hiện tại tất cả bộ lọc là `Input` → callback tự động trigger mỗi khi người dùng thay đổi
bất kỳ giá trị nào → tốn tài nguyên, UX kém khi chọn nhiều bộ lọc liên tiếp.

Sếp cũng phản ánh: khi chọn bộ lọc "Ngày", hệ thống trả về ngày không đúng kỳ vọng.

## Phần 1: Thêm nút "Lọc"

### 1a. Thêm nút vào `components/sidebar.py`
Thêm nút "🔍 Áp dụng bộ lọc" vào cuối phần bộ lọc sidebar (trước phần menu dịch vụ):
```python
html.Div([
    dbc.Button(
        "🔍 Áp dụng bộ lọc",
        id="btn-apply-filter",
        color="primary",
        className="w-100 mt-3",
        style={"fontWeight": "bold"}
    )
], id="apply-filter-container", style={"padding": "0 15px 15px 15px"})
```

### 1b. Cập nhật TẤT CẢ callbacks chính (7 files)
Với mỗi callback nhận bộ lọc sidebar, thực hiện:

**Bước 1**: Thêm `Input("btn-apply-filter", "n_clicks")` làm trigger đầu tiên
**Bước 2**: Chuyển tất cả bộ lọc sidebar từ `Input` → `State`
**Bước 3**: Giữ nguyên các `Input` nội bộ của trang (VD: `Input("tabs-navigation", "value")`)

#### Danh sách callbacks cần cập nhật:
| File | Hàm | Ghi chú |
|------|-----|---------|
| `callbacks/kpi_callbacks.py` | `update_kpi_cards` | 14 inputs → State |
| `callbacks/customer_callbacks.py` | callback chính | Kiểm tra inputs |
| `callbacks/new_customer_callbacks.py` | callback chính | |
| `callbacks/retention_callbacks.py` | callback chính | |
| `callbacks/alerts_callbacks.py` | callback chính | |
| `callbacks/global_callbacks.py` | callback chính | |
| `callbacks/service_callbacks.py` | callback chính | |

#### Pattern chuẩn cho mỗi callback:
```python
@app.callback(
    [Output(...)],
    [Input("btn-apply-filter", "n_clicks"),  # ← Trigger DUY NHẤT
     Input("tabs-navigation", "value")],      # ← Giữ nếu cần
    [State("sidebar-year", "value"),          # ← Tất cả bộ lọc → State
     State("sidebar-period", "value"),
     State("sidebar-date-range", "start_date"),
     State("sidebar-date-range", "end_date"),
     State("sidebar-week-select", "value"),
     State("sidebar-month-select", "value"),
     State("sidebar-compare-mode", "value"),
     State("sidebar-nhom-dv", "value"),
     State("sidebar-cum", "value"),
     State("sidebar-bdx", "value"),
     State("sidebar-buu-cuc", "value"),
     State("sidebar-loai-kh", "value"),
     State("sidebar-hop-dong", "value")]
)
def callback_name(n_clicks, tab_val, year, period, ...):
    ...
```

> ⚠️ **Lưu ý quan trọng**: Callback cascade (ẩn/hiện bộ lọc, cascade Cụm→BĐX→Bưu cục) KHÔNG cần thêm nút Lọc — chúng phải vẫn chạy realtime để UX mượt. Chỉ callbacks **tính toán data/chart** mới cần nút Lọc.

## Phần 2: Fix Default giá trị khi đổi Chu kỳ

### Vấn đề
Khi người dùng chuyển từ "Tháng" sang "Ngày":
- `sidebar-date-range` không reset về ngày hôm nay đúng cách
- Hoặc khi đổi Năm, DatePicker không cập nhật range tương ứng

### Sửa callback `toggle_period_filters` trong `sidebar_callbacks.py`:
Callback hiện tại chỉ ẩn/hiện container, không set default value.
Cần thêm Output để set giá trị mặc định:

```python
@app.callback(
    [Output("filter-container-day", "style"),
     Output("filter-container-week", "style"),
     Output("filter-container-month", "style"),
     Output("sidebar-date-range", "start_date"),    # MỚI
     Output("sidebar-date-range", "end_date"),       # MỚI
     Output("sidebar-month-select", "value")],       # MỚI
    [Input("sidebar-period", "value"),
     Input("sidebar-year", "value")]
)
def toggle_period_filters(period, year):
    from datetime import date
    today = date.today()
    
    if period == "Ngày":
        # Default: ngày hôm nay
        return (
            {"display": "block"}, {"display": "none"}, {"display": "none"},
            today.isoformat(), today.isoformat(), None
        )
    elif period == "Tuần":
        return (
            {"display": "none"}, {"display": "block"}, {"display": "none"},
            None, None, None
        )
    else:  # Tháng (default)
        # Default: tháng hiện tại
        return (
            {"display": "none"}, {"display": "none"}, {"display": "block"},
            None, None, today.month
        )
```

> ⚠️ Thợ cần đọc `sidebar_callbacks.py` để biết tên hàm/ID chính xác trước khi sửa.
> Nếu callback đã có Output cho start_date/end_date thì chỉ cần thêm logic, không thêm Output.

## Phần 3: Lưu ý thêm nút Lọc vào sidebar cascade callbacks
Callbacks cascade (Cụm→BĐX→Bưu cục) trong `sidebar_callbacks.py` KHÔNG cần nút Lọc.
Chỉ thêm nút Lọc vào ID `btn-apply-filter` ở layout.

## Acceptance Criteria
```gherkin
Given người dùng thay đổi bộ lọc Cụm
When họ chưa bấm "Áp dụng bộ lọc"
Then biểu đồ và bảng KHÔNG cập nhật

Given người dùng bấm "Áp dụng bộ lọc"
Then tất cả biểu đồ và bảng cập nhật theo bộ lọc hiện tại

Given người dùng chuyển Chu kỳ → "Ngày"
Then DatePicker tự động set về ngày hôm nay

Given người dùng chuyển Chu kỳ → "Tháng"
Then dropdown tháng tự động chọn tháng hiện tại

Given người dùng thay đổi Năm khi đang ở chế độ Tháng
When bộ lọc tháng vẫn ở tháng 12 (từ năm ngoái)
Then hệ thống vẫn giữ giá trị tháng đã chọn (không reset)
```

## Thứ tự thi công
1. Thêm nút vào `sidebar.py`
2. Sửa `kpi_callbacks.py` (test xem nút hoạt động)
3. Sửa các callbacks còn lại (global, customer, alerts, service, new_customer, retention)
4. Sửa `sidebar_callbacks.py` để fix default period values
5. Test toàn bộ
