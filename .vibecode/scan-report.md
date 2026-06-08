TECH_STACK:
  Language: Python 3.13
  Framework: Dash
  Styling: CSS (assets/style.css), dash-bootstrap-components
  Database: SQLite (dashboard.db) -> planned PostgreSQL
  Auth: Flask-Login (RBAC theo Cụm địa lý)
  State: dcc.Store
  Other: pandas, plotly, openpyxl, xlrd

EXISTING_MODULES:
  - dash_app: Main UI dashboard application (components, pages, callbacks, db)
  - etl: Data import and aggregation (importer.py, aggregator.py)
  - analytics: Core logic for revenue, customer classification, and global metrics
  - scripts: Automation and utility scripts (generate_tokens.py, rebuild_summaries.py, sync_mappings.py)
  - config: App configurations, holidays, and week calendar
  - data: Raw CSV mappings and Excel import templates

PATTERNS_DETECTED:
  - Architecture: Separated codebase from OneDrive data to avoid sync locks.
  - Auth: Flask-Login with bypass support and RBAC restricting user views to their Cụm.
  - Data Aggregation: Summary Tables (agg_monthly, plans_weekly) used for high performance UI instead of raw transactions.
  - Business Rules: "Nạp cấp nào, so sánh cấp đó" for 3 levels of plans (BCCP, HCC, PHBC).

REUSABLE_COMPONENTS:
  - dash_app/components: Reusable UI widgets and layout modules.
  - analytics/global_metrics.py: Shared metrics calculations.

GAPS_DETECTED:
  - Deployment: Currently running via local Cloudflare tunnel & SQLite. Pending Phase 5C for internal server deployment and PostgreSQL migration.
  - Pending Data: [RESOLVED] Data for end of May and June 2026 has been added.
  - Data Cleanliness: [RESOLVED] Old backup .csv files have been cleaned up.

CODE_HEALTH:
  Type Safety: Partial (Python type hints likely used but not strict)
  Linting: Not strictly configured
  Tests: Several manual debug/verify scripts exist, but no automated test suite.
  Debug Artifacts: Scripts like `debug_cum.py`, `check_tables.py` present.
  TODO/FIXME: Several pending items documented in project_state.md.

ESTIMATED_SIZE:
  Files: > 50
  Lines of Code: ~3000-5000+
  Components/Modules: 15+
  API Routes/Endpoints: Dash pages & callbacks

COMPLEXITY_ASSESSMENT: Medium
