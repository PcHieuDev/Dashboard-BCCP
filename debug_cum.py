import sys; sys.stdout.reconfigure(encoding='utf-8')
import sqlite3, pandas as pd
from config.settings import DB_PATH
conn = sqlite3.connect(DB_PATH)
df_years = pd.read_sql_query("SELECT DISTINCT nam_du_lieu FROM transactions", conn)
print('Years in DB:', df_years)
df_bccp = pd.read_sql_query("""
    SELECT b.ten_cum, d.nhom_chinh, SUM(t.cuoc_tt_tong) as dt
    FROM transactions t
    INNER JOIN dim_dichvu d ON t.san_pham_dv = d.ma_dich_vu
    INNER JOIN dim_buucuc b ON t.buu_cuc = b.ma_bc
    GROUP BY b.ten_cum, d.nhom_chinh
""", conn)
print('BCCP & HCC matched data by Cụm:')
print(df_bccp)

print('BCCP & HCC matched data by Cụm:')
print(df_bccp)
