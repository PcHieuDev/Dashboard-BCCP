TECH_STACK:
  Language: Python 3.13
  Framework: Dash (MVC structure with callbacks and components)
  Styling: dash-bootstrap-components, custom CSS in assets/style.css
  Database: SQLite (dashboard.db, synced on OneDrive)
  Auth: Custom RBAC (in dash_app/db/auth.py)
  State: dcc.Store, URL/QueryParams, cache
  Other: pandas, plotly, openpyxl, xlrd>=2.0.1 (read xls)

EXISTING_MODULES:
  - dash_app: Main Dash app configuration and layout (app.py, callbacks, components, pages).
  - analytics: Core business logic (global_metrics.py, revenue.py, retention_metrics.py, new_customer_calculator.py).
  - etl: Data import and aggregation (importer.py, aggregator.py).
  - scripts: Support scripts (rebuild_summaries.py, sync_mappings.py, sync_excel_templates.py).
  - config: App configuration and settings (settings.py, holidays.py).
  - tests: Testing suite (tests/conftest.py, tests/unit/test_plans_consistency.py).

PATTERNS_DETECTED:
  - Clean separation: Backend calculation modules in `analytics/` are separated from Dash layout/callbacks.
  - Aggregation layer: Summary tables like `agg_monthly`, `agg_weekly`, and `plans_weekly` are used to optimize dashboard loading times.
  - Database schema: Recently standardized (ma_buu_cuc instead of buu_cuc/ma_bc, ten_dich_vu instead of san_pham_dv, nhom_dich_vu instead of nhom_dv).

GAPS_DETECTED (CRITICAL):
  - Column Standardization Discrepancy:
    * While database tables (transactions, agg_monthly, agg_weekly, plans, new_customers) and primary UI callbacks (service_callbacks.py, global_callbacks.py) have been migrated to the new columns, multiple deep calculation files in `analytics/` and specific callbacks in `dash_app/callbacks/` still reference the old columns (`t.buu_cuc`, `nc.buu_cuc`, `a.buu_cuc`, `t.san_pham_dv`, `b.ma_bc`).
    * This causes runtime crashes (e.g. SQLite "no such column" or Pandas KeyError) when users query sub-services, view customer retention metrics, or filter by geography (district/commune/post office) on specific tabs.
  - Test coverage:
    * `tests/` directory is partially implemented, but lacks integration tests validating the analytics calculations against the standardized database schema.

CODE_HEALTH:
  Type Safety: Dynamic (DataFrame-heavy)
  Linting: Not strictly configured
  Tests: Partially set up in `tests/` (unit tests for plans)
  Debug Artifacts: Logging is used via `logger` but some print statements exist.
  TODO/FIXME: Slipped column names in analytics files need immediate refactoring.

ESTIMATED_SIZE:
  Files: ~60+ (.py, .md, .bat, .json, .xlsx)
  Complexity: Medium-Large

RESOLVER_PLAN (PROPOSED):
  1. Fix `analytics/global_metrics.py` (replace t.buu_cuc, a.buu_cuc with ma_buu_cuc).
  2. Fix `analytics/revenue.py` (replace t.buu_cuc with t.ma_buu_cuc).
  3. Fix `analytics/retention_metrics.py` (replace t.buu_cuc, nc.buu_cuc with ma_buu_cuc).
  4. Fix `dash_app/callbacks/new_customer_callbacks.py` (replace t.buu_cuc with t.ma_buu_cuc).
  5. Fix `dash_app/callbacks/service_detail_callbacks.py` (replace t.buu_cuc -> t.ma_buu_cuc, b.ma_bc -> b.ma_buu_cuc, t.san_pham_dv -> t.ten_dich_vu).
  6. Fix `etl/importer.py` warning logic (replace t.buu_cuc -> t.ma_buu_cuc, t.san_pham_dv -> t.ten_dich_vu).
