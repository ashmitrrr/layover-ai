import sqlite3
import json
import os
from typing import Dict, List, Tuple, Any
import streamlit as st
import requests
from sentence_transformers import SentenceTransformer, util

# ==========================================
# 1. CACHING & DATA LOADING
# ==========================================

@st.cache_resource
def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_data(show_spinner=False)
def load_hub_data(hub_id: str):
    db_path = "layover.db"
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row 
    c = conn.cursor()
    c.execute("SELECT full_data FROM hubs WHERE id = ?", (hub_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row['full_data'])
    return None

@st.cache_data(show_spinner=False)
def load_hubs_meta() -> Dict[str, Any]:
    path = os.path.join("data", "hubs.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# ==========================================
# 2. V3 INTELLIGENCE ENGINE (THE BRAIN)
# ==========================================

# 🧠 INTELLIGENCE: Regional Weekend Definitions
WEEKEND_MAP = {
    "doh": ["Friday", "Saturday"],       # Qatar
    "dxb": ["Saturday", "Sunday"],       # UAE (New logic)
    "sin": ["Saturday", "Sunday"],
    "lhr": ["Saturday", "Sunday"],
    "ist": ["Saturday", "Sunday"],
    "bkk": ["Saturday", "Sunday"],
    "hnd": ["Saturday", "Sunday"],
}

class Airport:
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.factors = data.get("intelligence_factors", {})
        self.code = data.get("meta", {}).get("code", "UNKNOWN")
        self.hub_id = data.get("id", "unknown").lower()

    def is_v3_ready(self) -> bool:
        return bool(self.factors)

    def get_immigration_time(self, arrival_hour: int) -> float:
        base_mins = self.factors.get("immigration_avg_mins", 45)
        multiplier = 1.0
        # Rush Hour Immigration (Airport Busy times)
        if 17 <= arrival_hour <= 20:
             multiplier = self.factors.get("risk_multipliers", {}).get("rush_hour", 1.5)
        elif 1 <= arrival_hour <= 5:
             multiplier = self.factors.get("risk_multipliers", {}).get("late_night", 0.8)
        return (base_mins * multiplier) / 60.0

    def get_transit_time_one_way(self, arrival_hour: int, day_of_week: str) -> float:
        base_mins = self.factors.get("transit_to_city_mins", 30)
        
        # 🧠 INTELLIGENCE: Traffic & Weekend Logic
        weekends = WEEKEND_MAP.get(self.hub_id, ["Saturday", "Sunday"])
        is_weekend = day_of_week in weekends
        
        # Rush Hour Definition (7-9 AM and 5-7 PM)
        is_rush_hour = (7 <= arrival_hour <= 9) or (17 <= arrival_hour <= 19)
        
        multiplier = 1.0
        
        if is_weekend:
            multiplier = 0.85  # Traffic is generally lighter on weekends
        elif is_rush_hour:
            multiplier = 1.6   # Rush hour traffic penalty
            
        return (base_mins * multiplier) / 60.0

    def get_security_buffer(self) -> float:
        return self.factors.get("security_check_mins", 45) / 60.0

def calculate_safe_exploration_time(
    airport: Airport, 
    total_layover: float, 
    arrival_hour: int, 
    visa_valid: bool,
    day_of_week: str
) -> Tuple[float, Dict[str, Any]]:
    
    if not airport.is_v3_ready():
        overhead = 2.5 
        return max(0.0, total_layover - overhead), {"method": "V2_STATIC", "overhead_used": overhead}

    imm_time = airport.get_immigration_time(arrival_hour)
    
    # Pass Day & Hour to Transit Calculation
    transit_one_way = airport.get_transit_time_one_way(arrival_hour, day_of_week)
    transit_total = transit_one_way * 2
    
    security_time = airport.get_security_buffer()
    safety_padding = 0.5 
    
    total_overhead = imm_time + transit_total + security_time + safety_padding
    safe_time = max(0.0, total_layover - total_overhead)
    
    return safe_time, {
        "method": "V3_DYNAMIC",
        "immigration_mins": round(imm_time * 60),
        "transit_mins": round(transit_total * 60),
        "security_mins": round(security_time * 60),
        "total_overhead_hours": round(total_overhead, 2),
        "traffic_context": "Weekend (Light)" if transit_one_way < (airport.factors.get("transit_to_city_mins", 30)/60) else "Weekday/Rush"
    }

# ==========================================
# 3. ROUTING INTELLIGENCE
# ==========================================
# ... (No changes to Routing Logic, keeping existing code) ...
AIRPORT_REGIONS = {
    "DEL": "SOUTH_ASIA", "BOM": "SOUTH_ASIA", "BLR": "SOUTH_ASIA",
    "SYD": "OCEANIA", "MEL": "OCEANIA",
    "LHR": "EUROPE_WEST", "CDG": "EUROPE_WEST",
    "DXB": "MIDDLE_EAST", "DOH": "MIDDLE_EAST", "IST": "EUROPE_EAST",
    "SIN": "SE_ASIA", "BKK": "SE_ASIA", "HND": "EAST_ASIA"
}
ROUTE_LOGIC = {
    ("SOUTH_ASIA", "SE_ASIA"): ["SE_ASIA"],
    ("SE_ASIA", "SOUTH_ASIA"): ["SE_ASIA"],
    ("SOUTH_ASIA", "OCEANIA"): ["SE_ASIA"],
    ("OCEANIA", "SOUTH_ASIA"): ["SE_ASIA"],
    ("OCEANIA", "EAST_ASIA"): ["SE_ASIA"],
    ("EAST_ASIA", "OCEANIA"): ["SE_ASIA"],
    ("SOUTH_ASIA", "EAST_ASIA"): ["SE_ASIA", "EAST_ASIA", "HKG"],
    ("EAST_ASIA", "SOUTH_ASIA"): ["SE_ASIA", "EAST_ASIA", "HKG"],
    ("SOUTH_ASIA", "NORTH_AMERICA"): ["MIDDLE_EAST", "EUROPE_WEST"],
    ("NORTH_AMERICA", "SOUTH_ASIA"): ["MIDDLE_EAST", "EUROPE_WEST"],
    ("SOUTH_ASIA", "EUROPE_WEST"): ["MIDDLE_EAST", "EUROPE_EAST"],
    ("EUROPE_WEST", "SOUTH_ASIA"): ["MIDDLE_EAST", "EUROPE_EAST"],
    ("EUROPE_WEST", "OCEANIA"): ["MIDDLE_EAST", "SE_ASIA"],
    ("OCEANIA", "EUROPE_WEST"): ["MIDDLE_EAST", "SE_ASIA"],
}
HUBS_INFO = {
    "doh": "MIDDLE_EAST", "dxb": "MIDDLE_EAST", "ist": "EUROPE_EAST",
    "sin": "SE_ASIA", "bkk": "SE_ASIA", "hnd": "EAST_ASIA", "lhr": "EUROPE_WEST"
}
def rank_hubs(origin, destination, layover_hours, arrival_hour, visa_valid, user_query=""):
    origin, dest = origin.upper().strip(), destination.upper().strip()
    region_a = AIRPORT_REGIONS.get(origin, "UNKNOWN")
    region_b = AIRPORT_REGIONS.get(dest, "UNKNOWN")
    target_regions = ROUTE_LOGIC.get((region_a, region_b), ["MIDDLE_EAST"])
    hubs_meta = load_hubs_meta()
    candidates = []
    for hub_id, hub_region in HUBS_INFO.items():
        if hub_region not in target_regions: continue
        if hub_id.upper() in [origin, dest]: continue
        meta = hubs_meta.get(hub_id, {})
        base = float(meta.get("hub_popularity", 0.5)) * 100
        if layover_hours > 8: base += 10
        candidates.append({
            "hub_id": hub_id,
            "name": meta.get("name", hub_id.upper()),
            "score": round(base, 1),
            "why": ["Strategic location"]
        })
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:5]

# ==========================================
# 4. CORE HELPERS
# ==========================================
def _clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))

def _hour_in_window(hour, open_h, close_h):
    hour0, hour1 = hour, hour + 24
    if close_h >= open_h:
        return (open_h <= hour0 <= close_h) or (open_h <= hour1 <= close_h)
    return (hour0 >= open_h) or (hour0 <= close_h)

def check_visa_status(hub_id, passport):
    data = load_hub_data(hub_id)
    if not data: return True, "Unknown", "Assuming valid."
    mapping = {"India": "indian", "USA": "us", "UK": "uk", "EU": "eu", "Australia": "australian", "Japan": "japanese"}
    key = mapping.get(passport, "us")
    policy = data.get("visa_policy", {}).get(key, {})
    p_type = policy.get("type", "").lower()
    is_valid = not ("required" in p_type and "on arrival" not in p_type)
    return is_valid, policy.get("type", "Unknown"), policy.get("details", "")

def analyze_vibe(user_query):
    model = get_model()
    q = (user_query or "").strip()
    if not q: return {"intents": [], "labels": []}
    anchors = [
        ("FOOD", "local food eat hungry snacks dinner lunch halal street food"),
        ("SIGHTS", "sightseeing landmarks skyline view photo explore"),
        ("CULTURE", "culture museum history art heritage mosque temple"),
        ("RELAX", "relax chill spa shower lounge comfort quiet"),
        ("SLEEP", "sleep nap rest hotel pod sleeping"),
        ("SHOPPING", "shopping buy souvenirs duty free mall luxury brands"),
    ]
    q_emb = model.encode(q, convert_to_tensor=True)
    a_embs = model.encode([t for _, t in anchors], convert_to_tensor=True)
    sims = util.pytorch_cos_sim(q_emb, a_embs)[0].tolist()
    scored = sorted([(anchors[i][0], float(sims[i])) for i in range(len(anchors))], key=lambda x: x[1], reverse=True)
    labels = [k for k, s in scored if s >= 0.35][:3]
    return {"intents": scored[:5], "labels": labels}

def compute_plan_risk(ranked_items, layover_hours, visa_valid):
    if not ranked_items: return "UNKNOWN", "No activities."
    first_meta = ranked_items[0].get("explain", {}).get("v3_meta", {})
    if first_meta.get("method") == "V3_DYNAMIC":
        safe_time = layover_hours - first_meta.get("total_overhead_hours", 0)
        any_landside = any(it["activity"]["location"]["zone"] == "LANDSIDE" for it in ranked_items[:3])
        if any_landside and safe_time < 1.0: return "HIGH", "Extremely tight window."
        if any_landside and safe_time < 2.0: return "MED", "City trip rushed."
        return "LOW", "Comfortable buffer."
    return "LOW", "Standard buffer."

def _open_score(act, arrival_hour, layover_hours):
    tc = act.get("time_constraints", {})
    if tc.get("is_24h", False): return 1.0, []
    open_h = tc.get("opening_hour_24", 0)
    close_h = tc.get("closing_hour_24", 24)
    if layover_hours >= 10.0:
        wait_time = (open_h - arrival_hour) % 24
        if 0 < wait_time < layover_hours:
            return 1.0, [f"Opens at {open_h}:00 (you have time to wait)."]
        elif wait_time > layover_hours:
             return 0.0, ["Closed during your entire window."]
    if not _hour_in_window(arrival_hour, open_h, close_h):
        time_until_open = (open_h - arrival_hour) % 24
        if time_until_open <= 1.0 and (layover_hours - time_until_open) > 3.0:
             return 0.8, [f"Opens soon ({open_h}:00)."]
        return 0.0, ["Closed at arrival time."]
    arr0 = float(arrival_hour)
    close_candidates = [float(close_h)]
    if close_h < open_h: close_candidates.append(float(close_h) + 24.0)
    best_close = min([c for c in close_candidates if c >= arr0] + [999])
    if best_close != 999 and (best_close - arr0) <= 2.0:
        return 0.6, ["Closes soon."]
    return 1.0, []

# ==========================================
# 5. WEATHER INTELLIGENCE
# ==========================================
HUB_COORDS = {
    "doh": {"lat": 25.26, "lon": 51.56},
    "dxb": {"lat": 25.25, "lon": 55.36},
    "sin": {"lat": 1.36, "lon": 103.99},
    "lhr": {"lat": 51.47, "lon": -0.45},
    "ist": {"lat": 41.27, "lon": 28.72},
    "bkk": {"lat": 13.69, "lon": 100.75},
    "hnd": {"lat": 35.54, "lon": 139.77},
}
def get_real_weather(hub_id):
    coords = HUB_COORDS.get(hub_id)
    if not coords: return None
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=temperature_2m,weather_code,is_day"
        r = requests.get(url, timeout=2)
        data = r.json()
        current = data.get("current", {})
        temp = current.get("temperature_2m", 25)
        code = current.get("weather_code", 0)
        is_day = current.get("is_day", 1)
        condition, icon = "Clear", "☀️"
        if code in [1, 2, 3]: condition, icon = "Partly Cloudy", "⛅"
        elif code in [45, 48]: condition, icon = "Foggy", "🌫️"
        elif code in [51, 53, 55, 61, 63, 65]: condition, icon = "Rain", "🌧️"
        elif code >= 95: condition, icon = "Storm", "⛈️"
        if is_day == 0 and icon == "☀️": icon = "🌙"
        return {"temp": round(temp), "condition": condition, "icon": icon}
    except: return None

# ==========================================
# 6. MAIN RANKER (UPDATED)
# ==========================================
def filter_and_rank_activities(hub_id, layover_hours, arrival_hour, user_query, visa_valid=False, day_of_week="Monday"):
    data = load_hub_data(hub_id)
    if not data: return []

    # 1. Initialize V3 Logic with Day of Week
    airport = Airport(data)
    safe_landside_hours, calc_meta = calculate_safe_exploration_time(airport, layover_hours, arrival_hour, visa_valid, day_of_week)
    
    all_activities = data.get("activities", [])
    if not all_activities: return []

    q_lower = (user_query or "").lower()
    vibe = analyze_vibe(user_query)
    detected = set(vibe.get("labels", []))
    
    is_zombie_hours = (arrival_hour >= 22 or arrival_hour <= 5)
    sleep_mode = is_zombie_hours and (layover_hours < 12.0)

    model = get_model()
    texts = [f"{a.get('title','')} {a.get('type','')} {a.get('description','')}" for a in all_activities]
    all_embs = model.encode(texts, convert_to_tensor=True)
    q_emb = model.encode(user_query, convert_to_tensor=True)
    
    scored = []
    
    for idx, act in enumerate(all_activities):
        zone = act["location"]["zone"]
        min_dur = act["time_constraints"]["min_duration_hours"]
        act_type = (act.get("type") or "").upper()

        if zone == "LANDSIDE":
            if not visa_valid: continue
            if min_dur > safe_landside_hours: continue
        else:
            if min_dur > (layover_hours - 1.0): continue

        open_factor, open_reasons = _open_score(act, arrival_hour, layover_hours)
        if open_factor == 0.0: continue

        a_emb = all_embs[idx]
        semantic = float(util.pytorch_cos_sim(q_emb, a_emb).item())
        semantic = _clamp((semantic + 1) / 2)
        intent_match = 1.0 if act_type in detected else 0.0
        
        friction = 1.0 if zone == "AIRSIDE" else 0.7
        if zone == "LANDSIDE" and safe_landside_hours < 2.0: friction = 0.4
            
        if sleep_mode:
            if zone == "LANDSIDE" and act_type in ["SIGHTS", "CULTURE", "SHOPPING"]:
                friction *= 0.3
                open_reasons.append("It's late/early. City vibe will be dead.")
            if zone == "AIRSIDE" and act_type in ["SLEEP", "RELAX"]:
                intent_match += 0.5 
            if zone == "LANDSIDE" and act_type == "FOOD":
                friction *= 0.8 

        final = (0.45 * semantic) + (0.25 * intent_match) + (0.15 * friction) + (0.15 * open_factor)
        
        reasons = []
        if intent_match > 0.8: reasons.append(f"Matches '{act_type}' vibe.")
        if sleep_mode and zone == "AIRSIDE": reasons.append("Best option for a short overnight stay.")
            
        scored.append({
            "activity": act,
            "score": round(final * 100, 1),
            "risk_level": "LOW" if friction > 0.6 else "MED",
            "explain": {
                "reasons": reasons,
                "tradeoffs": open_reasons,
                "v3_meta": calc_meta
            }
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored