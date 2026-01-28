import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "layover.db")
JSON_PATH = os.path.join(BASE_DIR, "data", "doh.json") # Checks for doh.json

def get_fallback_rich_data():
    # Only used if doha.json is MISSING or empty
    return [
        {"title": "Souq Waqif", "type": "CULTURE", "location": {"lat": 25.2867, "lon": 51.5333, "zone": "LANDSIDE"}, "time_constraints": {"min_duration_hours": 3, "is_24h": False, "opening_hour_24": 9, "closing_hour_24": 23}, "cost_tier": "LOW", "founders_tip": "If you only do ONE city thing in Doha, do this."},
        {"title": "The Orchard (Indoor Garden)", "type": "RELAX", "location": {"lat": 25.2744, "lon": 51.6083, "zone": "AIRSIDE"}, "time_constraints": {"min_duration_hours": 0.75, "is_24h": True}, "cost_tier": "FREE", "founders_tip": "Best 'no-friction' option when city stuff is closed."},
        {"title": "Museum of Islamic Art (MIA)", "type": "CULTURE", "location": {"lat": 25.2948, "lon": 51.5393, "zone": "LANDSIDE"}, "time_constraints": {"min_duration_hours": 2.5, "is_24h": False, "opening_hour_24": 9, "closing_hour_24": 19}, "cost_tier": "MEDIUM", "founders_tip": "Iconic architecture, great for photos."},
        {"title": "Katara Cultural Village", "type": "CULTURE", "location": {"lat": 25.3548, "lon": 51.5311, "zone": "LANDSIDE"}, "time_constraints": {"min_duration_hours": 3, "is_24h": True}, "cost_tier": "MEDIUM", "founders_tip": "Huge arts complex with amphitheater and beach."},
        {"title": "The Pearl Qatar", "type": "SIGHTS", "location": {"lat": 25.37, "lon": 51.55, "zone": "LANDSIDE"}, "time_constraints": {"min_duration_hours": 3, "is_24h": True}, "cost_tier": "HIGH", "founders_tip": "Man-made island. Luxury vibes."},
        {"title": "Villaggio Mall", "type": "SHOPPING", "location": {"lat": 25.26, "lon": 51.44, "zone": "LANDSIDE"}, "time_constraints": {"min_duration_hours": 2.5, "is_24h": False, "opening_hour_24": 9, "closing_hour_24": 23}, "cost_tier": "MEDIUM", "founders_tip": "Venetian-themed mall with indoor canal."},
        {"title": "National Museum of Qatar", "type": "CULTURE", "location": {"lat": 25.28, "lon": 51.54, "zone": "LANDSIDE"}, "time_constraints": {"min_duration_hours": 2.5, "is_24h": False, "opening_hour_24": 9, "closing_hour_24": 19}, "cost_tier": "MEDIUM", "founders_tip": "The 'Desert Rose' building."},
        {"title": "Msheireb Downtown", "type": "SIGHTS", "location": {"lat": 25.28, "lon": 51.52, "zone": "LANDSIDE"}, "time_constraints": {"min_duration_hours": 2, "is_24h": True}, "cost_tier": "FREE", "founders_tip": "Modern smart city district."},
        {"title": "Al Mourjan Business Lounge", "type": "RELAX", "location": {"lat": 25.27, "lon": 51.60, "zone": "AIRSIDE"}, "time_constraints": {"min_duration_hours": 3, "is_24h": True}, "cost_tier": "HIGH", "founders_tip": "One of the best lounges in the world."},
        {"title": "Vitality Wellbeing & Fitness Centre", "type": "RELAX", "location": {"lat": 25.27, "lon": 51.60, "zone": "AIRSIDE"}, "time_constraints": {"min_duration_hours": 2, "is_24h": True}, "cost_tier": "MEDIUM", "founders_tip": "Swimming pool inside the airport."}
    ]

def upgrade_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    hub_id = "doh"

    # 1. READ FROM DATABASE (To preserve Intelligence Factors)
    c.execute("SELECT full_data FROM hubs WHERE id = ?", (hub_id,))
    row = c.fetchone()
    if not row:
        print("❌ Error: Doha not found in DB. Run update_db_all.py first.")
        return

    db_data = json.loads(row['full_data'])
    
    # 2. TRY TO READ FROM JSON FILE (The "Lot" of data)
    final_activities = []
    if os.path.exists(JSON_PATH):
        print(f"📂 Found local file: {JSON_PATH}")
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                json_file_data = json.load(f)
                # Check if it's a list or a dict with "activities" key
                if isinstance(json_file_data, list):
                    final_activities = json_file_data
                elif "activities" in json_file_data:
                    final_activities = json_file_data["activities"]
                
                print(f"   ✅ Loaded {len(final_activities)} activities from JSON file.")
        except Exception as e:
            print(f"   ⚠️ Error reading JSON: {e}")
    
    # 3. FALLBACK IF JSON FAILED
    if not final_activities:
        print("⚠️ No JSON data found. Using fallback Rich List.")
        final_activities = get_fallback_rich_data()

    # 4. MERGE & UPDATE
    # Keep the DB's intelligence_factors, overwrite the activities
    db_data["activities"] = final_activities
    
    c.execute("UPDATE hubs SET full_data = ? WHERE id = ?", (json.dumps(db_data), hub_id))
    conn.commit()
    conn.close()
    
    print(f"🎉 Success! Database updated with {len(final_activities)} activities for Doha.")

if __name__ == "__main__":
    upgrade_data()