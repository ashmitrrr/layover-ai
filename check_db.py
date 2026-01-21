import sqlite3
import json
conn = sqlite3.connect("layover.db")
c = conn.cursor()
c.execute("SELECT id, name, code FROM hubs")
rows = c.fetchall()

print(f"--- Found {len(rows)} Airports in Database ---")
for row in rows:
    print(f"  {row[1]} ({row[2]}) - ID: {row[0]}")

conn.close()