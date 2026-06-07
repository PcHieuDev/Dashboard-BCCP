# TIP-topbar-001: Tạo topbar.py component + CSS

## HEADER
- TIP-ID: TIP-topbar-001
- Branch: feat/topbar-auth
- Project: Dashboard BCCP v2.0
- Module: Components / UI
- Depends on: None
- Priority: P0
- Estimated effort: 45 min

## CONTEXT
- Working directory: E:\Projects\worktrees\Dashboard-BCCP\feat-topbar-auth
- Key files to reference:
  - `dash_app/components/sidebar.py` → xem cách tạo bộ lọc hiện tại (sẽ chuyển lên topbar)
  - `dash_app/assets/style.css` → styles hiện có
  - `config/week_calendar.py` → `get_week_list(year)` cho danh sách tuần
- Patterns to follow: Xem context.md mục 2 — Naming conventions

## TASK
Tạo component Topbar chứa toàn bộ bộ lọc, thay thế bộ lọc trong Sidebar.

## SPECIFICATIONS

### File mới: `dash_app/components/topbar.py`

Hàm `create_topbar_layout(filter_opts: dict)` → trả về `html.Div`

Layout ngang (dbc.Row + dbc.Col), chia 2 nhóm:

**Nhóm 1 — Thời gian:**
| Component | ID (GIỮ NGUYÊN) | Mô tả |
|-----------|-----------------|-------|
| Dropdown Năm | `sidebar-year` | Giá trị từ filter_opts["years"] |
| Dropdown Chu kỳ | `sidebar-period` | Chỉ 2 options: "Tuần", "Tháng". Mặc định "Tháng" |
| Container Tuần | `week-container` | Chứa Dropdown `sidebar-week-select` |
| Container Tháng | `month-container` | Chứa Dropdown `sidebar-month-select` |

**Nhóm 2 — Địa lý:**
| Component | ID (GIỮ NGUYÊN) | Mô tả |
|-----------|-----------------|-------|
| Dropdown Cụm | `sidebar-cum` | Options từ filter_opts["cum"], placeholder "Tất cả" |
| Dropdown Xã/phường | `sidebar-bdx` | Label đổi thành "Bưu điện xã/phường". Options từ filter_opts["bdx"] |
| Dropdown Bưu cục | `sidebar-buu-cuc` | Options từ filter_opts["buu_cuc"] |

**Nút Áp dụng:**
| Component | ID | Mô tả |
|-----------|-----|-------|
| Button | `btn-apply-filter` | "🔍 Áp dụng", dbc.Button color="primary" |

### Styling
- Container: nền `#F8FAFC`, viền dưới `1px solid #E2E8F0`, padding `12px 20px`
- Không cố định (sticky) — cuộn cùng trang
- Responsive: trên màn hình nhỏ các filter xuống dòng
- Label nhỏ trên mỗi dropdown (font-size 11px, color #64748B)
- Dropdown width: vừa đủ nội dung, min-width 120px

### CSS bổ sung vào `dash_app/assets/style.css`
```css
.topbar-container { ... }
.topbar-filter-group { ... }
.topbar-label { ... }
.topbar-apply-btn { ... }
```

## ACCEPTANCE CRITERIA
- Given: App khởi chạy
- When: Render topbar component
- Then:
  - Topbar hiển thị ngang, 2 nhóm filter + nút Áp dụng
  - Các ID component giữ nguyên (sidebar-year, sidebar-period, etc.)
  - Label "Bưu điện xã/phường" đúng
  - Chu kỳ chỉ có "Tuần" và "Tháng" (BỎ "Ngày")
  - CSS đẹp, nền nhẹ, không sticky

## CONSTRAINTS
- KHÔNG tạo callbacks ở TIP này — chỉ layout + CSS
- GIỮ NGUYÊN tất cả ID component để tương thích với callbacks hiện có
- KHÔNG xóa sidebar.py — sẽ sửa ở TIP-topbar-003
- BỎ hoàn toàn DatePickerRange (lọc theo ngày)
