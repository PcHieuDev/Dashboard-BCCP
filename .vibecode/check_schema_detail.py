import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
conn = sqlite3.connect(r'E:/OneDrive/z.Database-TTKD-Data/dashboard.db')
c = conn.cursor()

# 1. Schema chi tiết cho các bảng quan trọng
for t in ['plans', 'plans_new_customer', 'dim_dichvu', 'transactions_hcc', 'transactions_phbc', 'agg_weekly', 'new_customers']:
    print(f"\n=== {t} ===")
    cols = c.execute(f"PRAGMA table_info({t})").fetchall()
    for col in cols:
        print(f"  {col[1]:30s} {col[2]:15s} {'NOT NULL' if col[3] else ''}")
    cnt = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  → {cnt} rows")

# 2. Kiểm tra dữ liệu thực tế của plans
print("\n=== plans sample ===")
rows = c.execute("SELECT * FROM plans LIMIT 3").fetchall()
for r in rows:
    print(f"  {r}")

# 3. Kiểm tra dữ liệu theo năm
print("\n=== transactions years & months ===")
rows = c.execute("SELECT nam_du_lieu, thang_du_lieu, COUNT(*) FROM transactions GROUP BY nam_du_lieu, thang_du_lieu ORDER BY nam_du_lieu, thang_du_lieu").fetchall()
for r in rows:
    print(f"  {r}")

# 4. Kiểm tra agg_weekly structure
print("\n=== agg_weekly sample ===")
rows = c.execute("SELECT * FROM agg_weekly LIMIT 3").fetchall()
for r in rows:
    print(f"  {r}")

# 5. Kiểm tra new_customers columns
print("\n=== new_customers sample ===")
rows = c.execute("SELECT * FROM new_customers LIMIT 3").fetchall()
for r in rows:
    print(f"  {r}")

# 6. dim_buucuc count
cnt = c.execute("SELECT COUNT(DISTINCT ten_bdx) FROM dim_buucuc").fetchone()[0]
print(f"\n=== dim_buucuc: {cnt} distinct ten_bdx ===")
cnt2 = c.execute("SELECT COUNT(DISTINCT ten_cum) FROM dim_buucuc").fetchone()[0]
print(f"  {cnt2} distinct ten_cum")

conn.close()
