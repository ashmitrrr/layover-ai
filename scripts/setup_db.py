import sqlite3
import json

# Data for the 3 New Hubs
# This includes the specific tours, lounges, and "V3" details.
NEW_HUBS_DATA = {
    "icn": {
        "id": "icn",
        "name": "Seoul Incheon",
        "timezone": "Asia/Seoul",
        "intelligence_factors": {"efficiency": 0.95, "safety": 0.98, "transit_ease": 0.95, "transit_to_city_mins": 45},
        "visa_policy": {
            "us": {"type": "Visa Free (90 Days)", "details": "K-ETA required."},
            "indian": {"type": "Visa Required (Transit Free)", "details": "Visa-free entry ONLY if part of official Transit Tour group."},
            "eu": {"type": "Visa Free", "details": "K-ETA required."}
        },
        "activities": [
            {"id": "icn_tour", "title": "Free Transit Tour (Temple)", "type": "CULTURE", "description": "Official 1-hour tour to Heungryunsa Temple. Free for transit passengers.", "location": {"zone": "LANDSIDE", "lat": 37.44, "lon": 126.45}, "time_constraints": {"min_duration_hours": 2.0, "best_time": "DAY", "opening_hour_24": 8, "closing_hour_24": 15}, "cost_tier": "FREE", "founders_tip": "Go to the 'Transit Tour' desk in Terminal 1 or 2 immediately."},
            {"id": "icn_nap", "title": "Nap Zone & Shower", "type": "RELAX", "description": "Designated quiet zones with lie-flat beds and free shower facilities.", "location": {"zone": "AIRSIDE", "lat": 37.46, "lon": 126.44}, "time_constraints": {"min_duration_hours": 1.0, "best_time": "ANY", "is_24h": True}, "cost_tier": "FREE", "founders_tip": "Located on 4F of Terminal 1. Quiet and dark."},
            {"id": "icn_skate", "title": "Ice Forest (Skating)", "type": "ADVENTURE", "description": "Indoor ice skating rink inside the Transportation Center.", "location": {"zone": "LANDSIDE", "lat": 37.45, "lon": 126.46}, "time_constraints": {"min_duration_hours": 1.5, "best_time": "DAY", "opening_hour_24": 10, "closing_hour_24": 20}, "cost_tier": "CHEAP", "founders_tip": "Rent skates for cheap. Synthetic ice."}
        ]
    },
    "ams": {
        "id": "ams",
        "name": "Amsterdam Schiphol",
        "timezone": "Europe/Amsterdam",
        "intelligence_factors": {"efficiency": 0.85, "safety": 0.9, "transit_ease": 0.9, "transit_to_city_mins": 15},
        "visa_policy": {
            "us": {"type": "Visa Free", "details": "Schengen rules apply."},
            "indian": {"type": "Schengen Visa Required", "details": "Cannot exit airside without Schengen visa."},
            "eu": {"type": "Freedom of Movement", "details": ""}
        },
        "activities": [
            {"id": "ams_museum", "title": "Rijksmuseum Schiphol", "type": "CULTURE", "description": "Annex of the famous Rijksmuseum with Dutch Golden Age paintings inside the terminal.", "location": {"zone": "AIRSIDE", "lat": 52.31, "lon": 4.76}, "time_constraints": {"min_duration_hours": 1.0, "best_time": "DAY", "is_24h": True}, "cost_tier": "FREE", "founders_tip": "Located on Holland Boulevard between Piers E and F."},
            {"id": "ams_library", "title": "Airport Library", "type": "RELAX", "description": "World's first airport library. Read books and relax in oversized chairs.", "location": {"zone": "AIRSIDE", "lat": 52.31, "lon": 4.76}, "time_constraints": {"min_duration_hours": 0.5, "best_time": "ANY", "is_24h": True}, "cost_tier": "FREE", "founders_tip": "Great place to charge your phone in silence."},
            {"id": "ams_city", "title": "Canal Express", "type": "SIGHTS", "description": "Take the train (15 mins) to Centraal Station for a quick canal walk.", "location": {"zone": "LANDSIDE", "lat": 52.37, "lon": 4.90}, "time_constraints": {"min_duration_hours": 4.5, "best_time": "DAY", "opening_hour_24": 6, "closing_hour_24": 23}, "cost_tier": "MEDIUM", "founders_tip": "Trains leave from directly below the terminal every 10 mins."}
        ]
    },
    "cdg": {
        "id": "cdg",
        "name": "Paris Charles de Gaulle",
        "timezone": "Europe/Paris",
        "intelligence_factors": {"efficiency": 0.6, "safety": 0.8, "transit_ease": 0.5, "transit_to_city_mins": 55},
        "visa_policy": {
            "us": {"type": "Visa Free", "details": "Schengen rules apply."},
            "indian": {"type": "Schengen Visa Required", "details": "Strict transit zone rules."},
            "eu": {"type": "Freedom of Movement", "details": ""}
        },
        "activities": [
            {"id": "cdg_lounge", "title": "Instant Paris Lounge", "type": "RELAX", "description": "Yotel-style lounge in Terminal 2E. Accessible without a visa.", "location": {"zone": "AIRSIDE", "lat": 49.00, "lon": 2.55}, "time_constraints": {"min_duration_hours": 3.0, "best_time": "ANY", "is_24h": True}, "cost_tier": "MEDIUM", "founders_tip": "Best option if stuck in T2."},
            {"id": "cdg_museum", "title": "Espace Musées", "type": "CULTURE", "description": "Free art museum in Terminal 2E (Hall M). Rotating exhibits.", "location": {"zone": "AIRSIDE", "lat": 49.00, "lon": 2.55}, "time_constraints": {"min_duration_hours": 1.0, "best_time": "DAY", "opening_hour_24": 7, "closing_hour_24": 22}, "cost_tier": "FREE", "founders_tip": "Look for it near Duty Free in Hall M."},
            {"id": "cdg_village", "title": "Roissy-en-France", "type": "FOOD", "description": "Charming authentic French village 10 mins away. Real food, no city traffic.", "location": {"zone": "LANDSIDE", "lat": 49.00, "lon": 2.52}, "time_constraints": {"min_duration_hours": 4.5, "best_time": "DINNER", "opening_hour_24": 11, "closing_hour_24": 23}, "cost_tier": "CHEAP", "founders_tip": "Skip Eiffel Tower if short on time. Go here for onion soup."}
        ]
    }
}

def update_db():
    conn = sqlite3.connect("layover.db")
    c = conn.cursor()
    
    # Ensure table exists
    c.execute('''CREATE TABLE IF NOT EXISTS hubs 
                 (id TEXT PRIMARY KEY, full_data JSON)''')
    
    # Upsert data
    print("🚀 Injecting new hubs into Database...")
    for hub_id, data in NEW_HUBS_DATA.items():
        json_str = json.dumps(data)
        c.execute("INSERT OR REPLACE INTO hubs (id, full_data) VALUES (?, ?)", (hub_id, json_str))
        print(f"   ✅ Added/Updated: {data['name']}")
    
    conn.commit()
    conn.close()
    print("✨ Database update complete.")

if __name__ == "__main__":
    update_db()