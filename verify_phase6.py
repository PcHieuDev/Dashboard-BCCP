import sys
sys.stdout.reconfigure(encoding='utf-8')
import os; os.chdir(r'E:\Projects\Dashboard-BCCP')
sys.path.insert(0, r'E:\Projects\Dashboard-BCCP')

print("=== TEST 1: Import modules ===")
try:
    from config.settings import DB_PATH
    print(f'[PASS] DB_PATH = {DB_PATH}')
    from analytics.global_metrics import get_revenue_by_cum
    print('[PASS] Import global_metrics OK')
except Exception as e:
    print(f'[FAIL] Import error: {e}')

print("\n=== TEST 2: dim_dichvu HCC grouping ===")
import sqlite3, pandas as pd
conn = sqlite3.connect(str(DB_PATH))
df = pd.read_sql_query("SELECT nhom_chinh, COUNT(*) as cnt FROM dim_dichvu GROUP BY nhom_chinh", conn)
print(df.to_string())

print("\n=== TEST 3: HCC001-HCC004 nhom_chinh ===")
df2 = pd.read_sql_query("SELECT ma_dich_vu, ten_dich_vu, nhom_chinh FROM dim_dichvu WHERE ma_dich_vu IN ('HCC001','HCC002','HCC003','HCC004')", conn)
print(df2.to_string())

print("\n=== TEST 4: Backup file ===")
import glob
backups = glob.glob(r'E:\Projects\Dashboard-BCCP\data\dim_dichvu_backup_*.csv')
print(f'Backup files: {len(backups)}')
for b in backups:
    print(f'  -> {b}')

print("\n=== TEST 5: New routes file list ===")
import os
pages = os.listdir(r'E:\Projects\Dashboard-BCCP\dash_app\pages')
callbacks = os.listdir(r'E:\Projects\Dashboard-BCCP\dash_app\callbacks')
print('Pages:', pages)
print('hcc_revenue.py exists:', 'hcc_revenue.py' in pages)
print('hcc_revenue_callbacks.py exists:', 'hcc_revenue_callbacks.py' in callbacks)

conn.close()
print("\n=== ALL TESTS COMPLETE ===")
