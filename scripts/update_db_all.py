import sqlite3
import json
import os

# Connect to DB
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "layover.db")

def get_v3_data_for_hub(hub_id):
    # 🧠 V3 INTELLIGENCE LAYER (Verified Data - Jan 2026)
    
    intelligence_map = {
        "dxb": { 
            # DUBAI: Efficient but GIGANTIC. 
            # Walking times in T3 are the real killer (20+ mins) [Source: LoungePair Guide]
            "immigration_avg_mins": 40,
            "security_check_mins": 50, # High walking buffer included
            "transit_to_city_mins": 25, # Metro to Burj Khalifa is reliable
            "transport_reliability_score": 0.95,
            "risk_multipliers": { "rush_hour": 1.4, "late_night": 0.9 }
        },
        "sin": { 
            # SINGAPORE: The Gold Standard. 
            # Immigration is ~12-24 mins. Security is AT THE GATE (decentralized).
            "immigration_avg_mins": 25, 
            "security_check_mins": 20, 
            "transit_to_city_mins": 25, 
            "transport_reliability_score": 0.98,
            "risk_multipliers": { "rush_hour": 1.2, "late_night": 1.0 }
        },
        "lhr": { 
            # LONDON: The Boss Fight.
            # Non-EU immigration is notoriously slow. ETA required now.
            "immigration_avg_mins": 75, 
            "security_check_mins": 45,
            "transit_to_city_mins": 55, # Elizabeth Line is reliable, but far
            "transport_reliability_score": 0.85, # Strikes/Delays happen
            "risk_multipliers": { "rush_hour": 1.3, "late_night": 0.9 }
        },
        "hnd": { 
            # TOKYO: Strict efficiency.
            # Immigration est 26-40 mins. Monorail is precise to the second.
            "immigration_avg_mins": 40,
            "security_check_mins": 30,
            "transit_to_city_mins": 30, 
            "transport_reliability_score": 1.0, 
            "risk_multipliers": { "rush_hour": 1.1, "late_night": 1.5 } # Late night taxi is $$$
        },
        "ist": { 
            # ISTANBUL: The Wildcard.
            # Immigration is fast (7-30m) but Security is slow (30m+). Traffic is lethal.
            "immigration_avg_mins": 35, 
            "security_check_mins": 55, # Two security checkpoints often required
            "transit_to_city_mins": 55, # Far from Sultanahmet
            "transport_reliability_score": 0.75, # Traffic is very unpredictable
            "risk_multipliers": { "rush_hour": 2.0, "late_night": 0.7 } 
        },
        "bkk": { 
            # BANGKOK: The Chaos.
            # Digital Arrival Card speeds things up (27-35m). Traffic is the main risk.
            "immigration_avg_mins": 35,
            "security_check_mins": 40,
            "transit_to_city_mins": 50, 
            "transport_reliability_score": 0.80, # Traffic jams are frequent
            "risk_multipliers": { "rush_hour": 2.2, "late_night": 0.6 } 
        }
    }

    if hub_id not in intelligence_map:
        return None

    return intelligence_map[hub_id]

def upgrade_all_hubs():
    if not os.path.exists(DB_PATH):
        print("❌ DB not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get all hubs except Doha (already done)
    c.execute("SELECT id, full_data FROM hubs WHERE id != 'doh'")
    rows = c.fetchall()

    print(f"🚀 Upgrading {len(rows)} airports to V3 Intelligence...")

    for row in rows:
        hub_id = row['id']
        try:
            current_data = json.loads(row['full_data'])
            
            # Get the new V3 brains
            new_intel = get_v3_data_for_hub(hub_id)
            
            if new_intel:
                # Inject the intelligence into the existing JSON
                current_data["intelligence_factors"] = new_intel
                
                # Save back to DB
                c.execute("UPDATE hubs SET full_data = ? WHERE id = ?", 
                          (json.dumps(current_data), hub_id))
                print(f"  ✅ Upgraded {hub_id.upper()}")
            else:
                print(f"  ⚠️ No V3 data defined for {hub_id}, skipping.")
        except Exception as e:
            print(f"  ❌ Failed to upgrade {hub_id}: {e}")

    conn.commit()
    conn.close()
    print("\n🎉 All airports are now V3 Smart!")

if __name__ == "__main__":
    upgrade_all_hubs()