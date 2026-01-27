import sqlite3
import json
import os

DB_NAME = "layover.db"
DATA_DIR = "data"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS hubs (
            id TEXT PRIMARY KEY,
            name TEXT,
            code TEXT,
            full_data JSON
        )
    ''')
    
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json') and f != "hubs.json"]
    
    count = 0
    print(f"Starting migration for {len(files)} hubs...")

    for filename in files:
        hub_id = filename.replace('.json', '')
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                
                name = data.get("name", hub_id)
                code = data.get("code", hub_id.upper())

                c.execute('INSERT OR REPLACE INTO hubs (id, name, code, full_data) VALUES (?, ?, ?, ?)',
                          (hub_id, name, code, json.dumps(data)))
                
                print(f" Migrated: {name} ({code})")
                count += 1
            except Exception as e:
                print(f" Failed to process {filename}: {e}")

    conn.commit()
    conn.close()
    print(f"\n Success! {count} hubs saved to '{DB_NAME}'.")

if __name__ == "__main__":
    init_db()