import json
import os
from sentence_transformers import SentenceTransformer, util

# Load AI Model (Cache it)
print("Loading AI Model...")
model = SentenceTransformer('all-MiniLM-L6-v2') 

# ==========================================
# PART 1: ROUTING INTELLIGENCE (The Missing Part)
# ==========================================

AIRPORT_REGIONS = {
    # South Asia
    "DEL": "SOUTH_ASIA", "BOM": "SOUTH_ASIA", "BLR": "SOUTH_ASIA", "MAA": "SOUTH_ASIA", "HYD": "SOUTH_ASIA",
    # Oceania
    "SYD": "OCEANIA", "MEL": "OCEANIA", "BNE": "OCEANIA", "AKL": "OCEANIA", "PER": "OCEANIA",
    # Europe
    "LHR": "EUROPE_WEST", "CDG": "EUROPE_WEST", "FRA": "EUROPE_WEST", "AMS": "EUROPE_WEST", "MUC": "EUROPE_WEST",
    # North America
    "JFK": "NORTH_AMERICA", "EWR": "NORTH_AMERICA", "SFO": "NORTH_AMERICA", "LAX": "NORTH_AMERICA", "ORD": "NORTH_AMERICA", "YYZ": "NORTH_AMERICA",
    # Middle East
    "DXB": "MIDDLE_EAST", "DOH": "MIDDLE_EAST", "AUH": "MIDDLE_EAST", "IST": "EUROPE_EAST",
    # SE Asia
    "SIN": "SE_ASIA", "BKK": "SE_ASIA", "KUL": "SE_ASIA", "HAN": "SE_ASIA", "SGN": "SE_ASIA",
    # East Asia
    "HND": "EAST_ASIA", "NRT": "EAST_ASIA", "ICN": "EAST_ASIA", "KIX": "EAST_ASIA", "HKG": "EAST_ASIA"
}

# Where should you stop based on A -> B?
ROUTE_LOGIC = {
    # India <-> SE Asia (Short Haul) -> Stop in SE Asia
    ("SOUTH_ASIA", "SE_ASIA"): ["SE_ASIA"],
    ("SE_ASIA", "SOUTH_ASIA"): ["SE_ASIA"],

    # India <-> Australia -> Stop in SE Asia
    ("SOUTH_ASIA", "OCEANIA"): ["SE_ASIA"],
    ("OCEANIA", "SOUTH_ASIA"): ["SE_ASIA"],
    
    # Australia <-> East Asia -> Stop in SE Asia
    ("OCEANIA", "EAST_ASIA"): ["SE_ASIA"],
    ("EAST_ASIA", "OCEANIA"): ["SE_ASIA"],

    # India <-> East Asia (Japan/Korea) -> Stop in SE Asia or East Asia
    ("SOUTH_ASIA", "EAST_ASIA"): ["SE_ASIA", "EAST_ASIA", "HKG"],
    ("EAST_ASIA", "SOUTH_ASIA"): ["SE_ASIA", "EAST_ASIA", "HKG"],
    
    # India <-> USA/Europe -> Stop in Middle East or Europe
    ("SOUTH_ASIA", "NORTH_AMERICA"): ["MIDDLE_EAST", "EUROPE_WEST"], 
    ("NORTH_AMERICA", "SOUTH_ASIA"): ["MIDDLE_EAST", "EUROPE_WEST"],
    ("SOUTH_ASIA", "EUROPE_WEST"): ["MIDDLE_EAST", "EUROPE_EAST"],   
    ("EUROPE_WEST", "SOUTH_ASIA"): ["MIDDLE_EAST", "EUROPE_EAST"],

    # Europe <-> Oceania -> Stop in Middle East or SE Asia (The Kangaroo Route)
    ("EUROPE_WEST", "OCEANIA"): ["MIDDLE_EAST", "SE_ASIA"],
    ("OCEANIA", "EUROPE_WEST"): ["MIDDLE_EAST", "SE_ASIA"],
}

# The Hubs we support
HUBS_INFO = {
    "doh": "MIDDLE_EAST",
    "dxb": "MIDDLE_EAST",
    "ist": "EUROPE_EAST",
    "sin": "SE_ASIA",
    "bkk": "SE_ASIA",
    "hnd": "EAST_ASIA",
    "lhr": "EUROPE_WEST"
}

def find_best_hubs(origin, destination):
    """
    Returns a list of hub codes (e.g., ['doh', 'dxb']) based on the route.
    """
    origin = origin.upper().strip()
    dest = destination.upper().strip()
    
    region_a = AIRPORT_REGIONS.get(origin, "UNKNOWN")
    region_b = AIRPORT_REGIONS.get(dest, "UNKNOWN")
    
    # 1. Find optimal regions for layover
    target_regions = ROUTE_LOGIC.get((region_a, region_b), [])
    
    # Fallback: If unknown route (e.g. South America), suggest Middle East
    if not target_regions:
        target_regions = ["MIDDLE_EAST"]
        
    # 2. Filter our supported hubs
    suggested_hubs = []
    for code, region in HUBS_INFO.items():
        if region in target_regions:
            # Don't suggest the layover if it IS the destination/origin
            if code.upper() != dest and code.upper() != origin:
                suggested_hubs.append(code)
            
    # Return Top 3
    return suggested_hubs[:3]


# ==========================================
# PART 2: ACTIVITY RANKING
# ==========================================

def load_hub_data(hub_id):
    path = os.path.join("data", f"{hub_id}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

def filter_and_rank_activities(hub_id, layover_hours, arrival_hour, user_query, visa_valid=False):
    data = load_hub_data(hub_id)
    if not data:
        return []

    valid_activities = []
    
    # --- PHASE 1: HARD FILTERS ---
    for act in data['activities']:
        # 1. Visa/Location Check
        if act['location']['zone'] == 'LANDSIDE' and not visa_valid:
            continue 
            
        # 2. Duration Check (Overhead: 2.5h for Landside, 0.5h for Airside)
        overhead = 2.5 if act['location']['zone'] == 'LANDSIDE' else 0.5
        if (act['time_constraints']['min_duration_hours'] + overhead) > layover_hours:
            continue
            
        # 3. Opening Hours Check
        if not act['time_constraints']['is_24h']:
            open_time = act['time_constraints']['opening_hour_24']
            close_time = act['time_constraints']['closing_hour_24']
            if arrival_hour > (close_time - 1) or arrival_hour < (open_time - 1):
                continue

        valid_activities.append(act)

    # --- PHASE 1.5: THE FAILSAFE INJECTOR ---
    query_lower = user_query.lower()
    
    # Failsafe: FOOD
    if "food" in query_lower or "hungry" in query_lower or "eat" in query_lower:
        has_food = any(a['type'] == 'FOOD' for a in valid_activities)
        if not has_food:
            valid_activities.append({
                "title": "Terminal Food Court",
                "type": "FOOD",
                "description": "Various international dining options available in the transit area. Quick and convenient.",
                "founders_tip": "Check the terminal map for the nearest food court. Usually open 24/7.",
                "location": {"zone": "AIRSIDE", "lat": 0, "lon": 0},
                "time_constraints": {"min_duration_hours": 1, "is_24h": True},
                "cost_tier": "VARIES"
            })

    # Failsafe: SHOPPING
    if "shop" in query_lower or "buy" in query_lower:
        has_shop = any(a['type'] == 'SHOPPING' for a in valid_activities)
        if not has_shop:
            valid_activities.append({
                "title": "Duty Free Shopping",
                "type": "SHOPPING",
                "description": "Perfumes, chocolates, and electronics available airside.",
                "founders_tip": "Great for killing 30-60 minutes.",
                "location": {"zone": "AIRSIDE", "lat": 0, "lon": 0},
                "time_constraints": {"min_duration_hours": 1, "is_24h": True},
                "cost_tier": "VARIES"
            })

    # Failsafe: SLEEP
    if "sleep" in query_lower or "nap" in query_lower or "rest" in query_lower:
        has_sleep = any(a['type'] == 'SLEEP' for a in valid_activities)
        if not has_sleep:
            valid_activities.append({
                "title": "Quiet Rest Zone",
                "type": "RELAX",
                "description": "Designated quiet areas with reclining chairs near the gates.",
                "founders_tip": "Bring an eye mask and earplugs!",
                "location": {"zone": "AIRSIDE", "lat": 0, "lon": 0},
                "time_constraints": {"min_duration_hours": 1, "is_24h": True},
                "cost_tier": "FREE"
            })

    if not valid_activities:
        return []

    # --- PHASE 2: AI RANKING ---
    user_embedding = model.encode(user_query, convert_to_tensor=True)
    
    scored_results = []
    
    keywords = {
        "FOOD": ["food", "eat", "hungry", "lunch", "dinner", "snack"],
        "RELAX": ["relax", "sleep", "nap", "shower", "lounge", "tired"],
        "SHOPPING": ["shop", "buy", "mall", "souvenir"],
        "CULTURE": ["culture", "museum", "history", "temple"],
        "SIGHTS": ["sight", "view", "photo", "landmark"],
    }

    for act in valid_activities:
        act_text = f"{act['title']} {act['type']} {act['description']} {act.get('founders_tip', '')}"
        act_embedding = model.encode(act_text, convert_to_tensor=True)
        
        raw_score = util.pytorch_cos_sim(user_embedding, act_embedding).item()
        
        # CATEGORY BOOSTING
        boost = 0.0
        act_type = act.get('type', '').upper()
        if act_type in keywords:
            for word in keywords[act_type]:
                if word in query_lower:
                    boost = 0.25 
                    break
        
        # Penalize Risky Landside Trips
        overhead = 2.5 if act['location']['zone'] == 'LANDSIDE' else 0.5
        time_buffer = layover_hours - (act['time_constraints']['min_duration_hours'] + overhead)
        if act['location']['zone'] == 'LANDSIDE' and time_buffer < 1.5:
            boost -= 0.2 
            
        final_score = min(1.0, raw_score + boost)
        
        scored_results.append({
            "activity": act,
            "score": round(final_score * 100, 1)
        })
        
    scored_results.sort(key=lambda x: x['score'], reverse=True)
    return scored_results