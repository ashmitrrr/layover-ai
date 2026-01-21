import sqlite3
import json
import os

DB_NAME = "layover.db"
DATA_DIR = "data"

def init_db():
    # 1. Connect to (or create) the database
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 2. Create a table to store our Hubs
    # We store the ID, Name, Code, and the full data bundle as a JSON column
    c.execute('''
        CREATE TABLE IF NOT EXISTS hubs (
            id TEXT PRIMARY KEY,
            name TEXT,
            code TEXT,
            full_data JSON
        )
    ''')
    
    # 3. Read existing JSON files and insert them
    # We skip 'hubs.json' because that's just metadata, not a full hub file
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json') and f != "hubs.json"]
    
    count = 0
    print(f"Starting migration for {len(files)} hubs...")

    for filename in files:
        hub_id = filename.replace('.json', '')
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                
                # Extract metadata for the columns, keep the rest in JSON
                name = data.get("name", hub_id)
                code = data.get("code", hub_id.upper())
                
                # Insert into DB (REPLACE ensures we update if we run it twice)
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