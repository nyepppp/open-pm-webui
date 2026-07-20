import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'webui.db')
print(f"DB path: {db_path}, exists: {os.path.exists(db_path)}")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'pm_work%' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f"pm_work* tables: {tables}")

if 'pm_workflows' in tables:
    cur.execute("PRAGMA table_info(pm_workflows)")
    cols = [(r[1], r[2]) for r in cur.fetchall()]
    print(f"pm_workflows columns: {cols}")
    cur.execute("SELECT COUNT(*) FROM pm_workflows")
    print(f"pm_workflows row count: {cur.fetchone()[0]}")
    cur.execute("SELECT id, name, status FROM pm_workflows LIMIT 5")
    for row in cur.fetchall():
        print(f"  row: {row}")

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'pm_workflow%' ORDER BY name")
print(f"pm_workflow* tables: {[r[0] for r in cur.fetchall()]}")

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'pm_%' ORDER BY name")
print(f"All pm_* tables: {[r[0] for r in cur.fetchall()]}")

conn.close()
