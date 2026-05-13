import sqlite3

conn = sqlite3.connect('mobilidade_renapsi.db')
cursor = conn.cursor()


cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]
    print(f"\n{'='*60}")
    print(f"TABLE: {table_name}")
    print(f"{'='*60}")
    
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    for col in columns:
        col_id, col_name, col_type, not_null, default, pk = col
        print(f"  {col_name:30} {col_type:15} {'NOT NULL' if not_null else ''} {'PK' if pk else ''} {f'DEFAULT {default}' if default else ''}")

conn.close()
