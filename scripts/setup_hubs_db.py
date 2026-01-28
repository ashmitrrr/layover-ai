import sqlite3
import json

# ==============================================================================
#  TRANSIT TRAVELLER V3.5 - MASTER HUB DATA
#  Includes: Seoul (ICN), Amsterdam (AMS), Paris (CDG)
#  Features: 10+ Passports, 10+ Activities, Deep "Local" Intelligence
# ==============================================================================

NEW_HUBS_DATA = {
    # -------------------------------------------------------------------------
    # 🇰🇷 SEOUL INCHEON (ICN) - The "Activity" King
    # -------------------------------------------------------------------------
    "icn": {
        "id": "icn",
        "name": "Seoul Incheon",
        "timezone": "Asia/Seoul",
        "intelligence_factors": {
            "efficiency": 0.95, 
            "safety": 0.98, 
            "transit_ease": 0.95, 
            "transit_to_city_mins": 45,
            "security_check_mins": 20
        },
        "visa_policy": {
            "indian": { "type": "Conditional Entry", "details": "Visa-free entry ONLY if participating in the official 'Free Transit Tour'. Otherwise, visa required to exit landside. Airside transit is visa-free.", "allowed_hours": 72 },
            "us": { "type": "Visa Free (K-ETA)", "details": "Visa-free for 90 days. K-ETA (Electronic Travel Authorization) must be approved before flight.", "allowed_hours": 2160 },
            "uk": { "type": "Visa Free (K-ETA)", "details": "Visa-free for 90 days. K-ETA required.", "allowed_hours": 2160 },
            "eu": { "type": "Visa Free (K-ETA)", "details": "Visa-free for 90 days. K-ETA required.", "allowed_hours": 2160 },
            "australian": { "type": "Visa Free (K-ETA)", "details": "Visa-free for 90 days. K-ETA required.", "allowed_hours": 2160 },
            "canadian": { "type": "Visa Free (K-ETA)", "details": "Visa-free for 6 months. K-ETA required.", "allowed_hours": 4320 },
            "japanese": { "type": "Visa Free", "details": "Visa-free for 90 days. K-ETA temporarily waived (check current status).", "allowed_hours": 2160 },
            "chinese": { "type": "Visa Required", "details": "Visa required to enter Seoul. Visa-free transit ONLY for Jeju-bound passengers or holders of US/EU/Aus visas transiting to those countries.", "allowed_hours": 0 },
            "russian": { "type": "Visa Free (K-ETA)", "details": "Visa-free for 60 days. K-ETA required.", "allowed_hours": 1440 },
            "brazilian": { "type": "Visa Free (K-ETA)", "details": "Visa-free for 90 days. K-ETA required.", "allowed_hours": 2160 }
        },
        "activities": [
            {
                "id": "icn_tour_temple",
                "title": "Free Transit Tour (Temple)",
                "type": "CULTURE",
                "description": "Official government-run tour to Heungryunsa Temple. Includes free bus and guide. You MUST register at the transit desk.",
                "location": { "zone": "LANDSIDE", "lat": 37.44, "lon": 126.45 },
                "time_constraints": { "min_duration_hours": 2.0, "best_time": "DAY", "opening_hour_24": 8, "closing_hour_24": 15 },
                "cost_tier": "FREE",
                "founders_tip": "Go immediately to the 'Transit Tour' desk in T1 or T2. These fill up fast."
            },
            {
                "id": "icn_nap_zone",
                "title": "Nap Zone (Relax & Fly)",
                "type": "SLEEP",
                "description": "Free designated quiet zones with padded lie-flat benches. Dark, quiet, and perfect for saving money on hotels.",
                "location": { "zone": "AIRSIDE", "lat": 37.46, "lon": 126.44 },
                "time_constraints": { "min_duration_hours": 1.0, "is_24h": True },
                "cost_tier": "FREE",
                "founders_tip": "Located on 4F of Terminal 1 (East & West) and T2. Bring a hoodie; AC can be cold."
            },
            {
                "id": "icn_showers",
                "title": "Free Shower Suites",
                "type": "RELAX",
                "description": "Clean shower rooms available for transit passengers. Towels and soap provided. A lifesaver after a long haul.",
                "location": { "zone": "AIRSIDE", "lat": 37.46, "lon": 126.44 },
                "time_constraints": { "min_duration_hours": 0.5, "opening_hour_24": 7, "closing_hour_24": 21 },
                "cost_tier": "FREE",
                "founders_tip": "Free for transit passengers (show boarding pass). Non-transit pays ~3,000 KRW."
            },
            {
                "id": "icn_culture_center",
                "title": "K-Culture Experience Center",
                "type": "CULTURE",
                "description": "Make traditional Korean crafts (Hanji paper, fans) and try on Hanbok clothes for free. Quick cultural immersion without leaving the terminal.",
                "location": { "zone": "AIRSIDE", "lat": 37.46, "lon": 126.44 },
                "time_constraints": { "min_duration_hours": 0.5, "opening_hour_24": 7, "closing_hour_24": 22 },
                "cost_tier": "FREE",
                "founders_tip": "Located in T1 (near Gate 25) and T2 (Gate 248). Great for kids and solos."
            },
            {
                "id": "icn_matina",
                "title": "Matina Lounge (Best Food)",
                "type": "FOOD",
                "description": "Widely considered the best food buffet of any Priority Pass lounge. Huge spread of Korean fried chicken, bibimbap, and soups.",
                "location": { "zone": "AIRSIDE", "lat": 37.46, "lon": 126.44 },
                "time_constraints": { "min_duration_hours": 1.5, "opening_hour_24": 7, "closing_hour_24": 21 },
                "cost_tier": "MEDIUM",
                "founders_tip": "There is often a line, but it moves fast. The spicy rice cakes (tteokbokki) are legit."
            },
            {
                "id": "icn_ice_forest",
                "title": "Ice Forest (Skating)",
                "type": "ADVENTURE",
                "description": "An indoor ice skating rink inside the Transportation Center. Uses synthetic ice so you don't get wet/cold.",
                "location": { "zone": "LANDSIDE", "lat": 37.45, "lon": 126.46 },
                "time_constraints": { "min_duration_hours": 1.5, "opening_hour_24": 10, "closing_hour_24": 20 },
                "cost_tier": "CHEAP",
                "founders_tip": "Located in the Transportation Center (B1). Rent skates for a few dollars."
            },
            {
                "id": "icn_paradise_city",
                "title": "Paradise City (Cimer Spa)",
                "type": "RELAX",
                "description": "Ultra-luxury resort complex just 5 mins via Maglev train (free). 'Cimer' is a world-class spa/pool club.",
                "location": { "zone": "LANDSIDE", "lat": 37.43, "lon": 126.46 },
                "time_constraints": { "min_duration_hours": 4.0, "best_time": "DAY" },
                "cost_tier": "HIGH",
                "founders_tip": "Take the free Maglev train from the Transportation Center to Paradise City station."
            },
            {
                "id": "icn_capsule",
                "title": "Darakhyu Capsule Hotel",
                "type": "SLEEP",
                "description": "Rent a smart capsule bed by the hour (min 3 hours). Perfect for deep sleep without leaving the airport building.",
                "location": { "zone": "LANDSIDE", "lat": 37.45, "lon": 126.46 },
                "time_constraints": { "min_duration_hours": 3.0, "is_24h": True },
                "cost_tier": "MEDIUM",
                "founders_tip": "Book in advance online. They are almost always full for walk-ins."
            },
            {
                "id": "icn_hongdae",
                "title": "Hongdae (AREX Train)",
                "type": "SIGHTS",
                "description": "Take the Express Train to Hongik Univ station (50 mins). Youth culture, busking, fashion, and endless street food.",
                "location": { "zone": "LANDSIDE", "lat": 37.55, "lon": 126.92 },
                "time_constraints": { "min_duration_hours": 6.0, "best_time": "EVENING" },
                "cost_tier": "MEDIUM",
                "founders_tip": "Only do this if you have 6+ hours. The vibe is best after 5 PM."
            },
            {
                "id": "icn_robot_cafe",
                "title": "Robot Coffee Bar (Beat)",
                "type": "FOOD",
                "description": "Get your coffee served by a robotic arm. A fun, futuristic photo-op and decent caffeine hit.",
                "location": { "zone": "AIRSIDE", "lat": 37.46, "lon": 126.44 },
                "time_constraints": { "min_duration_hours": 0.5, "is_24h": True },
                "cost_tier": "LOW",
                "founders_tip": "Located in T2. Fun for a quick Instagram video."
            }
        ]
    },

    # -------------------------------------------------------------------------
    # 🇳🇱 AMSTERDAM SCHIPHOL (AMS) - The "Culture" King
    # -------------------------------------------------------------------------
    "ams": {
        "id": "ams",
        "name": "Amsterdam Schiphol",
        "timezone": "Europe/Amsterdam",
        "intelligence_factors": {
            "efficiency": 0.85, 
            "safety": 0.90, 
            "transit_ease": 0.90, 
            "transit_to_city_mins": 15,
            "security_check_mins": 25
        },
        "visa_policy": {
            "indian": { "type": "Visa Free (Airside Only)", "details": "No transit visa needed if holding valid US/UK/Can/Japan visa. Otherwise, ATV required. Schengen visa MANDATORY to exit landside.", "allowed_hours": 0 },
            "us": { "type": "Visa Free", "details": "90 days visa-free entry (Schengen).", "allowed_hours": 2160 },
            "uk": { "type": "Visa Free", "details": "90 days visa-free entry.", "allowed_hours": 2160 },
            "eu": { "type": "Freedom of Movement", "details": "ID card sufficient.", "allowed_hours": 9999 },
            "australian": { "type": "Visa Free", "details": "90 days visa-free entry.", "allowed_hours": 2160 },
            "canadian": { "type": "Visa Free", "details": "90 days visa-free entry.", "allowed_hours": 2160 },
            "japanese": { "type": "Visa Free", "details": "90 days visa-free entry.", "allowed_hours": 2160 },
            "chinese": { "type": "ATV Required (Conditional)", "details": "ATV required unless holding US/EU visa. Schengen visa required to exit.", "allowed_hours": 0 },
            "brazilian": { "type": "Visa Free", "details": "90 days visa-free entry.", "allowed_hours": 2160 },
            "russian": { "type": "Schengen Visa Required", "details": "Strict rules apply. ATV usually required.", "allowed_hours": 0 }
        },
        "activities": [
            {
                "id": "ams_rijks",
                "title": "Rijksmuseum Schiphol",
                "type": "CULTURE",
                "description": "A legitimate annex of the famous Rijksmuseum located INSIDE the terminal. See Dutch Golden Age art for free.",
                "location": { "zone": "AIRSIDE", "lat": 52.31, "lon": 4.76 },
                "time_constraints": { "min_duration_hours": 0.75, "opening_hour_24": 7, "closing_hour_24": 20 },
                "cost_tier": "FREE",
                "founders_tip": "Located on Holland Boulevard between Lounge 2 and 3. Don't miss the gift shop."
            },
            {
                "id": "ams_library",
                "title": "Airport Library",
                "type": "RELAX",
                "description": "The world's first airport library. Read books, listen to music, and relax in giant oversized chairs.",
                "location": { "zone": "AIRSIDE", "lat": 52.31, "lon": 4.76 },
                "time_constraints": { "min_duration_hours": 0.5, "is_24h": True },
                "cost_tier": "FREE",
                "founders_tip": "Best spot to charge your phone in silence. Often overlooked by crowds."
            },
            {
                "id": "ams_panorama",
                "title": "Panorama Terrace",
                "type": "SIGHTS",
                "description": "Open-air observation deck to watch planes. Features a real KLM Fokker 100 you can walk inside.",
                "location": { "zone": "LANDSIDE", "lat": 52.31, "lon": 4.76 },
                "time_constraints": { "min_duration_hours": 1.5, "opening_hour_24": 7, "closing_hour_24": 21 },
                "cost_tier": "FREE",
                "founders_tip": "Located Landside (Departure Hall 1). You need to exit immigration to see this."
            },
            {
                "id": "ams_canal",
                "title": "Canal Express (City)",
                "type": "SIGHTS",
                "description": "Take the train (15m) to Centraal Station. Walk 2 mins to catch a 1-hour canal boat cruise.",
                "location": { "zone": "LANDSIDE", "lat": 52.37, "lon": 4.90 },
                "time_constraints": { "min_duration_hours": 4.5, "best_time": "DAY" },
                "cost_tier": "MEDIUM",
                "founders_tip": "Trains leave from directly underneath the terminal. Buy tickets in the main plaza."
            },
            {
                "id": "ams_yotel",
                "title": "YOTELAIR (Shower/Sleep)",
                "type": "SLEEP",
                "description": "Book a cabin for 4 hours to nap or just pay for a shower cabin. Clean, modern, airside.",
                "location": { "zone": "AIRSIDE", "lat": 52.31, "lon": 4.76 },
                "time_constraints": { "min_duration_hours": 2.0, "is_24h": True },
                "cost_tier": "MEDIUM",
                "founders_tip": "Lounge 2. Much cheaper than a missed flight from exhaustion."
            },
            {
                "id": "ams_baby",
                "title": "Baby Care Lounge",
                "type": "RELAX",
                "description": "Private booths for feeding, bathing, and letting babies sleep. One of the best family facilities in the world.",
                "location": { "zone": "AIRSIDE", "lat": 52.31, "lon": 4.76 },
                "time_constraints": { "min_duration_hours": 1.0, "opening_hour_24": 6, "closing_hour_24": 22 },
                "cost_tier": "FREE",
                "founders_tip": "Hidden on Holland Boulevard. A lifesaver for parents."
            },
            {
                "id": "ams_nemo",
                "title": "NEMO Science Museum",
                "type": "ADVENTURE",
                "description": "Green ship-shaped building near Centraal Station. Great roof terrace with free city views.",
                "location": { "zone": "LANDSIDE", "lat": 52.37, "lon": 4.91 },
                "time_constraints": { "min_duration_hours": 5.0, "best_time": "DAY" },
                "cost_tier": "MEDIUM",
                "founders_tip": "The roof terrace is free to access even without a museum ticket."
            },
            {
                "id": "ams_bubbles",
                "title": "Bubbles Seafood & Wine",
                "type": "FOOD",
                "description": "High-end seafood bar airside. Oysters, champagne, and herring. Proper dining experience.",
                "location": { "zone": "AIRSIDE", "lat": 52.31, "lon": 4.76 },
                "time_constraints": { "min_duration_hours": 1.0, "best_time": "ANY" },
                "cost_tier": "HIGH",
                "founders_tip": "Lounge 2. Try the traditional Dutch herring if you are brave."
            },
            {
                "id": "ams_sheraton",
                "title": "Sheraton Fitness (Day Pass)",
                "type": "RELAX",
                "description": "Buy a day pass to use the gym, sauna, and steam room at the Sheraton connected to the terminal.",
                "location": { "zone": "LANDSIDE", "lat": 52.31, "lon": 4.76 },
                "time_constraints": { "min_duration_hours": 2.0, "is_24h": False },
                "cost_tier": "MEDIUM",
                "founders_tip": "Walkway from Schiphol Plaza. No need for a taxi."
            },
            {
                "id": "ams_xpres",
                "title": "XpresSpa",
                "type": "RELAX",
                "description": "Quick massages, manicures, and facials. Good for killing 30-45 mins.",
                "location": { "zone": "AIRSIDE", "lat": 52.31, "lon": 4.76 },
                "time_constraints": { "min_duration_hours": 0.5, "opening_hour_24": 7, "closing_hour_24": 21 },
                "cost_tier": "MEDIUM",
                "founders_tip": "Located in Lounge 2 and Lounge 3."
            }
        ]
    },

    # -------------------------------------------------------------------------
    # 🇫🇷 PARIS CHARLES DE GAULLE (CDG) - The "Food" King
    # -------------------------------------------------------------------------
    "cdg": {
        "id": "cdg",
        "name": "Paris Charles de Gaulle",
        "timezone": "Europe/Paris",
        "intelligence_factors": {
            "efficiency": 0.60, 
            "safety": 0.80, 
            "transit_ease": 0.50, 
            "transit_to_city_mins": 55,
            "security_check_mins": 45
        },
        "visa_policy": {
            "indian": { "type": "ATV Required (Usually)", "details": "Airport Transit Visa required even for airside, UNLESS holding a valid US/Canada/UK/Schengen visa. Schengen Visa required to exit landside.", "allowed_hours": 0 },
            "us": { "type": "Visa Free", "details": "90 days visa-free (Schengen).", "allowed_hours": 2160 },
            "uk": { "type": "Visa Free", "details": "90 days visa-free.", "allowed_hours": 2160 },
            "eu": { "type": "Freedom of Movement", "details": "ID card sufficient.", "allowed_hours": 9999 },
            "australian": { "type": "Visa Free", "details": "90 days visa-free.", "allowed_hours": 2160 },
            "canadian": { "type": "Visa Free", "details": "90 days visa-free.", "allowed_hours": 2160 },
            "japanese": { "type": "Visa Free", "details": "90 days visa-free.", "allowed_hours": 2160 },
            "chinese": { "type": "ATV Required (Conditional)", "details": "ATV required unless holding US/EU/UK visa.", "allowed_hours": 0 },
            "brazilian": { "type": "Visa Free", "details": "90 days visa-free.", "allowed_hours": 2160 },
            "russian": { "type": "Schengen Visa Required", "details": "Strict rules.", "allowed_hours": 0 }
        },
        "activities": [
            {
                "id": "cdg_lounge_instant",
                "title": "Instant Paris Lounge",
                "type": "RELAX",
                "description": "A stylish Yotel-like lounge in Terminal 2E (Gate L). Offers comfortable beds and a library vibe. Accessible to transit passengers.",
                "location": { "zone": "AIRSIDE", "lat": 49.00, "lon": 2.55 },
                "time_constraints": { "min_duration_hours": 3.0, "is_24h": True },
                "cost_tier": "MEDIUM",
                "founders_tip": "Best option if you are stuck in T2E and can't enter France."
            },
            {
                "id": "cdg_museum",
                "title": "Espace Musées (Art)",
                "type": "CULTURE",
                "description": "A genuine art museum in Terminal 2E (Hall M). Features rotating exhibits from the Louvre or Rodin museums.",
                "location": { "zone": "AIRSIDE", "lat": 49.00, "lon": 2.55 },
                "time_constraints": { "min_duration_hours": 1.0, "opening_hour_24": 7, "closing_hour_24": 22 },
                "cost_tier": "FREE",
                "founders_tip": "Often empty. A quiet place to escape the chaos of CDG."
            },
            {
                "id": "cdg_disney",
                "title": "Disneyland Paris (TGV)",
                "type": "ADVENTURE",
                "description": "Take the high-speed TGV train from T2 station. It takes ONLY 10 minutes to reach Disneyland gates.",
                "location": { "zone": "LANDSIDE", "lat": 48.87, "lon": 2.78 },
                "time_constraints": { "min_duration_hours": 6.0, "best_time": "DAY" },
                "cost_tier": "HIGH",
                "founders_tip": "The TGV is fast (10 mins), RER is slow (45 mins). Buy TGV tickets in advance. Doable on a 7h layover!"
            },
            {
                "id": "cdg_roissy",
                "title": "Roissy-en-France Village",
                "type": "FOOD",
                "description": "A charming, authentic French village 10 mins away by taxi. Cobblestone streets, bistros, no tourists.",
                "location": { "zone": "LANDSIDE", "lat": 49.00, "lon": 2.52 },
                "time_constraints": { "min_duration_hours": 4.5, "best_time": "DINNER" },
                "cost_tier": "CHEAP",
                "founders_tip": "Skip the hour-long train to Paris. Eat real French Onion Soup here instead."
            },
            {
                "id": "cdg_aeroville",
                "title": "Aéroville Mall",
                "type": "SHOPPING",
                "description": "Huge modern shopping mall with a cinema and massive food court. 15 min free shuttle or taxi.",
                "location": { "zone": "LANDSIDE", "lat": 48.99, "lon": 2.53 },
                "time_constraints": { "min_duration_hours": 4.0, "opening_hour_24": 10, "closing_hour_24": 20 },
                "cost_tier": "MEDIUM",
                "founders_tip": "The 'Europa Corp' cinema here has lie-flat beds. Great for sleeping while watching a movie."
            },
            {
                "id": "cdg_laduree",
                "title": "Ladurée (Macarons)",
                "type": "FOOD",
                "description": "Iconic luxury macarons. Several carts and shops airside. The ultimate quick Paris treat.",
                "location": { "zone": "AIRSIDE", "lat": 49.00, "lon": 2.55 },
                "time_constraints": { "min_duration_hours": 0.2, "opening_hour_24": 6, "closing_hour_24": 21 },
                "cost_tier": "MEDIUM",
                "founders_tip": "Located in almost every terminal. Buy a box for the plane."
            },
            {
                "id": "cdg_ps4",
                "title": "Gaming Corners (PS4)",
                "type": "ADVENTURE",
                "description": "Free PlayStation 4 terminals scattered around the terminals. Good for killing 30 mins.",
                "location": { "zone": "AIRSIDE", "lat": 49.00, "lon": 2.55 },
                "time_constraints": { "min_duration_hours": 0.5, "is_24h": True },
                "cost_tier": "FREE",
                "founders_tip": "Look for the brightly colored 'Arcade' zones."
            },
            {
                "id": "cdg_air_museum",
                "title": "Air & Space Museum",
                "type": "CULTURE",
                "description": "Musée de l'Air et de l'Espace at Le Bourget. See an actual Concorde and 747. 20 min taxi.",
                "location": { "zone": "LANDSIDE", "lat": 48.94, "lon": 2.43 },
                "time_constraints": { "min_duration_hours": 5.0, "best_time": "DAY", "opening_hour_24": 10, "closing_hour_24": 17 },
                "cost_tier": "MEDIUM",
                "founders_tip": "Closed Mondays. A must for aviation geeks."
            },
            {
                "id": "cdg_notre_dame",
                "title": "Notre Dame (RER B)",
                "type": "SIGHTS",
                "description": "Take RER B express straight to 'Saint-Michel Notre-Dame'. Fastest route to the city center (40-50 mins).",
                "location": { "zone": "LANDSIDE", "lat": 48.85, "lon": 2.35 },
                "time_constraints": { "min_duration_hours": 7.0, "best_time": "DAY" },
                "cost_tier": "LOW",
                "founders_tip": "Only do this if the RER is running normally (check strikes!)."
            },
            {
                "id": "cdg_sheraton",
                "title": "Sheraton Paris Airport",
                "type": "SLEEP",
                "description": "Located *inside* T2 (landside), right above the TGV station. Soundproof rooms for serious sleep.",
                "location": { "zone": "LANDSIDE", "lat": 49.00, "lon": 2.55 },
                "time_constraints": { "min_duration_hours": 4.0, "is_24h": True },
                "cost_tier": "HIGH",
                "founders_tip": "Expensive but zero hassle. Walk straight from the plane (after immigration)."
            }
        ]
    }
}

def update_db():
    print("🚀 Initializing LayoverAI Database Injector...")
    conn = sqlite3.connect("layover.db")
    c = conn.cursor()
    
    # Ensure table exists
    c.execute('''CREATE TABLE IF NOT EXISTS hubs 
                 (id TEXT PRIMARY KEY, full_data JSON)''')
    
    # Upsert data
    for hub_id, data in NEW_HUBS_DATA.items():
        json_str = json.dumps(data)
        c.execute("INSERT OR REPLACE INTO hubs (id, full_data) VALUES (?, ?)", (hub_id, json_str))
        print(f"   ✅ Injected: {data['name']} ({len(data['activities'])} activities, {len(data['visa_policy'])} visa rules)")
    
    conn.commit()
    conn.close()
    print("\n✨ SUCCESS: Database updated with V3.5 content.")

if __name__ == "__main__":
    update_db()