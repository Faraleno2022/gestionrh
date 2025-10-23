import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check if utilisateurs table exists
if any('utilisateurs' in t[0] for t in tables):
    cursor.execute("SELECT COUNT(*) FROM utilisateurs")
    count = cursor.fetchone()[0]
    print(f"\nTable 'utilisateurs' exists with {count} rows")
else:
    print("\n❌ Table 'utilisateurs' NOT FOUND!")

conn.close()
