import sqlite3
import json
import os

# Path to your DB
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "layover.db")

def check_database():
    if not os.path.exists(DB_PATH):
        print("❌ Database file not found!")
        return

    print(f"📂 Reading database: {DB_PATH}\n")
    print(f"{'HUB':<6} | {'ACTIVITIES':<12} | {'V3 LOGIC':<10} | {'SAMPLE PLACE'}")
    print("-" * 65)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        c.execute("SELECT id, full_data FROM hubs")
        rows = c.fetchall()

        for row in rows:
            hub_id = row['id'].upper()
            data = json.loads(row['full_data'])
            
            # Count activities
            activities = data.get("activities", [])
            count = len(activities)
            
            # Check for V3 Intelligence
            has_intel = "✅ YES" if "intelligence_factors" in data else "❌ NO"
            
            # Get first place name as a sample
            sample = activities[0]["title"] if count > 0 else "None"
            if len(sample) > 25: sample = sample[:22] + "..."

            print(f"{hub_id:<6} | {count:<12} | {has_intel:<10} | {sample}")

    except Exception as e:
        print(f"❌ Error reading DB: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database()