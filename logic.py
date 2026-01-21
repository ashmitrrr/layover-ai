import sqlite3
import json
import os
from typing import Dict, List, Tuple, Any

import streamlit as st
from sentence_transformers import SentenceTransformer, util


# ==========================================
# CACHING & CORE HELPERS
# ==========================================

@st.cache_resource
def get_model():
    #  model load
    return SentenceTransformer("all-MiniLM-L6-v2")


@st.cache_data(show_spinner=False)
def load_hub_data(hub_id: str):
    """
    New DB Version: Fetches hub data from SQLite database.
    """
    db_path = "layover.db"
    
    # Failsafe: If DB doesn't exist, return None
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
    # still reads from the JSON file because we didn't migrate the meta list
    path = os.path.join("data", "hubs.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _hour_in_window(hour: float, open_h: float, close_h: float) -> bool:
    """
    Robust open-hours check.
    Supports:
      - close_h > 24 (e.g., 26 = 2am next day)
      - wrap-around windows (e.g., 20 -> 4)
    We treat `hour` as local hour in [0, 23].
    """
    # so the hour into a 0..48 space to allow "next-day" close times
    # check both day-0 and day-1 representations
    hour0 = hour
    hour1 = hour + 24

    # close > open (normal or extends beyond 24)
    if close_h >= open_h:
        return (open_h <= hour0 <= close_h) or (open_h <= hour1 <= close_h)
    #  wrap-around (e.g., 20 -> 4)
    return (hour0 >= open_h) or (hour0 <= close_h)

def check_visa_status(hub_id: str, passport: str) -> Tuple[bool, str, str]:
    """
    Checks visa rules from the hub's JSON data.
    Returns: (is_visa_valid, status_title, status_details)
    """
    data = load_hub_data(hub_id)
    if not data:
        return True, "Unknown Policy", "We couldn't fetch visa data for this hub. Assuming valid."
    
    passport_map = {
        "India": "indian",
        "USA": "us",
        "UK": "uk",
        "EU": "eu",
        "Australia": "australian",
        "Japan": "japanese"
    }
    
    key = passport_map.get(passport, "us") # US if unknown
    policy = data.get("visa_policy", {}).get(key, {})
    
    if not policy:
        return True, "Unknown", "No specific data for this passport."

    # if it says "Visa Required", return False (unless user has one)
    # if "Visa Free", "Visa on Arrival", or "Citizen", return True
    p_type = policy.get("type", "").lower()
    
    is_valid = True
    if "required" in p_type and "on arrival" not in p_type:
        is_valid = False
        
    return is_valid, policy.get("type", "Unknown"), policy.get("details", "")

def analyze_vibe(user_query: str) -> Dict[str, Any]:
    """
    Lightweight "AI-feel" intent detection using embeddings + a few anchors.
    Returns:
      { "intents": [("FOOD", 0.78), ...], "labels": ["FOOD","SIGHTS"] }
    """
    model = get_model()
    q = (user_query or "").strip()
    if not q:
        return {"intents": [], "labels": []}

    anchors = [
        ("FOOD", "local food eat hungry snacks dinner lunch halal street food"),
        ("SIGHTS", "sightseeing landmarks skyline view photo explore"),
        ("CULTURE", "culture museum history art heritage mosque temple"),
        ("RELAX", "relax chill spa shower lounge comfort quiet"),
        ("SLEEP", "sleep nap rest hotel pod sleeping"),
        ("SHOPPING", "shopping buy souvenirs duty free mall luxury brands"),
        ("WORK", "work laptop wifi quiet workspace business lounge"),
        ("FITNESS", "gym workout fitness wellbeing run"),
    ]

    q_emb = model.encode(q, convert_to_tensor=True)
    a_texts = [t for _, t in anchors]
    a_embs = model.encode(a_texts, convert_to_tensor=True)

    sims = util.pytorch_cos_sim(q_emb, a_embs)[0].tolist()
    scored = sorted([(anchors[i][0], float(sims[i])) for i in range(len(anchors))],
                    key=lambda x: x[1], reverse=True)

    labels = [k for k, s in scored if s >= 0.35][:3]
    if not labels and scored:
        labels = [scored[0][0]]

    return {"intents": scored[:5], "labels": labels}


def _time_fit_score(min_hours: float, layover_hours: float, overhead_hours: float) -> float:
    """
    Prefer activities that fit comfortably without eating the entire window.
    Uses ratio of min_duration to available free time.
    """
    free = max(0.25, layover_hours - overhead_hours)
    ratio = min_hours / free  # 0..>1

    ideal = 0.40
    spread = 0.35
    score = 1.0 - abs(ratio - ideal) / spread
    return _clamp(score)


def _open_score(act: Dict[str, Any], arrival_hour: int) -> Tuple[float, List[str]]:
    """
    Returns (open_factor, tradeoffs)
    """
    tc = act.get("time_constraints", {})
    if tc.get("is_24h", False):
        return 1.0, []

    open_h = tc.get("opening_hour_24", 0)
    close_h = tc.get("closing_hour_24", 24)
    if not _hour_in_window(arrival_hour, open_h, close_h):
        return 0.0, ["May be closed at your arrival time."]

    # penalize if "closing soon" (within ~2 hours)
    # handle close > 24 by comparing in a 0..48 frame
    arr0 = float(arrival_hour)
    arr1 = arr0 + 24.0

    # Find the close time that is "next after" arrival
    close_candidates = [float(close_h)]
    if close_h < open_h:  # wrap-around close in early morning
        close_candidates.append(float(close_h) + 24.0)
    # Choose the candidate close that is >= arrival representation
    best_close = None
    for arr in [arr0, arr1]:
        for c in close_candidates:
            if c >= arr:
                best_close = c if best_close is None else min(best_close, c)
    if best_close is None:
        best_close = float(close_candidates[-1])

    # Determine remaining time to close
    aligned_arr = arr0 if best_close >= arr0 else arr1
    remaining = best_close - aligned_arr

    tradeoffs = []
    if remaining <= 2.0:
        tradeoffs.append("Closes relatively soon — timing could be tight.")
        return 0.6, tradeoffs
    return 1.0, tradeoffs


def compute_plan_risk(ranked_items: List[Dict[str, Any]], layover_hours: float, visa_valid: bool) -> Tuple[str, str]:
    """
    Simple product-style risk label + reason based on top picks.
    """
    if not ranked_items:
        return "UNKNOWN", "No activities available."

    # top 3
    top = ranked_items[:3]
    any_landside = any(it["activity"]["location"]["zone"] == "LANDSIDE" for it in top)
    tight_flags = 0
    for it in top:
        if it.get("risk_level") in ("MED", "HIGH"):
            tight_flags += 1

    if not visa_valid and any_landside:
        return "HIGH", "Landside options require a visa."

    if any_landside and layover_hours < 6:
        return "HIGH", "City trips on <6h layovers are risky."

    if any_landside and layover_hours < 8:
        return "MED", "Landside plans can be tight — keep buffers."

    if tight_flags >= 2:
        return "MED", "Multiple picks are time-sensitive."

    return "LOW", "Comfortable buffer for your plan."


# ==========================================
# PART 1: ROUTING INTELLIGENCE 
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
    "doh": "MIDDLE_EAST",
    "dxb": "MIDDLE_EAST",
    "ist": "EUROPE_EAST",
    "sin": "SE_ASIA",
    "bkk": "SE_ASIA",
    "hnd": "EAST_ASIA",
    "lhr": "EUROPE_WEST"
}
def _is_late(arrival_hour: int) -> bool:
    return (arrival_hour >= 22) or (arrival_hour <= 5)


def _hub_score(
    meta: Dict[str, Any],
    layover_hours: float,
    arrival_hour: int,
    visa_valid: bool
) -> Tuple[float, List[str]]:
    """
    Returns (score 0..100, reasons[])
    """
    # meta fields def
    pop = float(meta.get("hub_popularity", 0.6))                 # 0..1 higher better
    friction = float(meta.get("airport_friction", 0.5))          # 0..1 lower better
    late_strength = float(meta.get("late_night_strength", 0.5))  # 0..1 higher better
    airside = float(meta.get("airside_strength", 0.6))           # 0..1 higher better
    landside = float(meta.get("landside_strength", 0.6))         # 0..1 higher better

    friction_good = 1.0 - _clamp(friction, 0.0, 1.0)

    late = _is_late(arrival_hour)

    # Visa affects which strengths matter
    access_strength = airside if not visa_valid else (0.55 * airside + 0.45 * landside)

    # Short layovers should heavily prefer low friction
    if layover_hours < 5:
        layover_factor = 1.0
        friction_weight = 0.40
    elif layover_hours < 8:
        layover_factor = 0.9
        friction_weight = 0.33
    else:
        layover_factor = 0.8
        friction_weight = 0.25

    late_bonus = late_strength if late else 0.55  # daytime baseline

    # Weighted score (0..1)
    s = (
        0.35 * pop +
        friction_weight * friction_good +
        0.20 * late_bonus +
        0.20 * access_strength
    )
    s = _clamp(s) * 100.0 * layover_factor

    # (“why this hub”)
    reasons = []

    # easy connection
    if friction_good >= 0.75:
        reasons.append("✅ easy connection (low airport friction)")
    elif friction_good >= 0.55:
        reasons.append("✅ decent connection flow")

    # late night
    if late and late_strength >= 0.70:
        reasons.append("✅ strong late-night airport (good after 10pm)")
    elif late and late_strength < 0.50:
        reasons.append("⚠️ late-night options can be limited")

    # visa-aware
    
    if not visa_valid:
        if airside >= 0.80:
            reasons.append("✅ great airside experience if you can't enter the city")
        else:
            reasons.append("⚠️ mostly better landside — but you said no visa")
    else:
        if landside >= 0.85:
            reasons.append("✅ strong city options if you want to go landside")
        else:
            reasons.append("✅ solid airport-first layover")

    return round(s, 1), reasons[:3]


def rank_hubs(
    origin: str,
    destination: str,
    layover_hours: float,
    arrival_hour: int,
    visa_valid: bool,
    user_query: str = ""
) -> List[Dict[str, Any]]:
    """
    Returns top hubs with scores + why.
    Output: [{ "hub_id": "sin", "name": "...", "code": "...", "score": 88.2, "why": [...] }, ...]
    """
    origin = origin.upper().strip()
    dest = destination.upper().strip()

    region_a = AIRPORT_REGIONS.get(origin, "UNKNOWN")
    region_b = AIRPORT_REGIONS.get(dest, "UNKNOWN")

    target_regions = ROUTE_LOGIC.get((region_a, region_b), [])
    if not target_regions:
        target_regions = ["MIDDLE_EAST"]

    hubs_meta = load_hubs_meta()

    candidates = []
    for hub_id, hub_region in HUBS_INFO.items():
        if hub_region not in target_regions:
            continue
        # don't recommend origin/destination as "hub"
        if hub_id.upper() == origin or hub_id.upper() == dest:
            continue

        meta = hubs_meta.get(hub_id, {})
        score, why = _hub_score(meta, layover_hours, arrival_hour, visa_valid)

        candidates.append({
            "hub_id": hub_id,
            "name": meta.get("name", hub_id.upper()),
            "code": meta.get("code", hub_id.upper()),
            "score": score,
            "why": why
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:5]


def find_best_hubs(origin, destination):
    ranked = rank_hubs(origin, destination, layover_hours=8, arrival_hour=14, visa_valid=True, user_query="")
    return [r["hub_id"] for r in ranked[:3]]

    region_a = AIRPORT_REGIONS.get(origin, "UNKNOWN")
    region_b = AIRPORT_REGIONS.get(dest, "UNKNOWN")

    target_regions = ROUTE_LOGIC.get((region_a, region_b), [])
    if not target_regions:
        target_regions = ["MIDDLE_EAST"]

    suggested_hubs = []
    for code, region in HUBS_INFO.items():
        if region in target_regions:
            if code.upper() != dest and code.upper() != origin:
                suggested_hubs.append(code)

    return suggested_hubs[:3]


# ==========================================
# PART 2: ACTIVITY EMBEDDINGS (cached per hub)
# ==========================================

@st.cache_data(show_spinner=False)
def _hub_activity_texts_and_embeddings(hub_id: str) -> Tuple[List[Dict[str, Any]], Any]:
    """
    Returns (activities, embeddings_tensor) cached per hub.
    """
    data = load_hub_data(hub_id)
    if not data:
        return [], None

    acts = data.get("activities", [])
    model = get_model()

    texts = []
    for act in acts:
        act_text = f"{act.get('title','')} {act.get('type','')} {act.get('description','')} {act.get('founders_tip','')}"
        texts.append(act_text)

    embs = model.encode(texts, convert_to_tensor=True) if texts else None
    return acts, embs


# ==========================================
# PART 3: ACTIVITY RANKING 
# ==========================================

def filter_and_rank_activities(hub_id, layover_hours, arrival_hour, user_query, visa_valid=False):
    data = load_hub_data(hub_id)
    if not data:
        return []

    all_activities, all_embs = _hub_activity_texts_and_embeddings(hub_id)
    if not all_activities:
        return []

    q_lower = (user_query or "").lower()
    vibe = analyze_vibe(user_query)
    detected = set(vibe.get("labels", []))

    valid = []
    
    explicitly_wants_sleep = any(w in q_lower for w in ["sleep", "nap", "bed", "rest", "hotel", "shower"])

    for idx, act in enumerate(all_activities):
        zone = act["location"]["zone"]

        # 1) Visa/Location Check
        if zone == "LANDSIDE" and not visa_valid:
            continue

        # 2) Duration Check with overhead
        overhead = 2.5 if zone == "LANDSIDE" else 0.5
        min_dur = act["time_constraints"]["min_duration_hours"]
        if (min_dur + overhead) > layover_hours:
            continue

        # 3) Opening Hours Check
        tc = act.get("time_constraints", {})
        if not tc.get("is_24h", False):
            open_h = tc.get("opening_hour_24", 0)
            close_h = tc.get("closing_hour_24", 24)
            if not _hour_in_window(arrival_hour, open_h, close_h):
                continue

        valid.append(act)


    def _append_failsafe_if_missing(act_type: str, payload: Dict[str, Any]):
        if not any(a.get("type") == act_type for a in valid):
            valid.append(payload)

    if any(w in q_lower for w in ["food", "hungry", "eat"]):
        _append_failsafe_if_missing("FOOD", {
            "title": "Terminal Food Court",
            "type": "FOOD",
            "description": "Various international dining options available in the transit area. Quick and convenient.",
            "founders_tip": "Check the terminal map for the nearest food court. Usually open 24/7.",
            "location": {"zone": "AIRSIDE", "lat": 0, "lon": 0},
            "time_constraints": {"min_duration_hours": 1, "is_24h": True},
            "cost_tier": "VARIES"
        })

    if any(w in q_lower for w in ["shop", "buy"]):
        _append_failsafe_if_missing("SHOPPING", {
            "title": "Duty Free Shopping",
            "type": "SHOPPING",
            "description": "Perfumes, chocolates, and electronics available airside.",
            "founders_tip": "Great for killing 30–60 minutes.",
            "location": {"zone": "AIRSIDE", "lat": 0, "lon": 0},
            "time_constraints": {"min_duration_hours": 1, "is_24h": True},
            "cost_tier": "VARIES"
        })

    if explicitly_wants_sleep:
        # rest zone if they ASKED for it or sleep
        if not any(a.get("type") in ["SLEEP", "RELAX"] for a in valid):
            valid.append({
                "title": "Quiet Rest Zone",
                "type": "RELAX",
                "description": "Designated quiet areas with reclining chairs near the gates.",
                "founders_tip": "Bring an eye mask and earplugs!",
                "location": {"zone": "AIRSIDE", "lat": 0, "lon": 0},
                "time_constraints": {"min_duration_hours": 1, "is_24h": True},
                "cost_tier": "FREE"
            })

    if not valid:
        return []

    # --- MULTI-FACTOR SCORING ---
    model = get_model()
    q_emb = model.encode(user_query, convert_to_tensor=True)

    scored = []

    emb_map = {}
    if all_embs is not None:
        for act, idx in zip(all_activities, range(len(all_activities))):
            emb_map[id(act)] = all_embs[idx]

    for act in valid:
        zone = act["location"]["zone"]
        min_dur = act["time_constraints"]["min_duration_hours"]
        overhead = 2.5 if zone == "LANDSIDE" else 0.5
        act_type = (act.get("type") or "").upper()

        # 1. Semantic Score
        if id(act) in emb_map:
            a_emb = emb_map[id(act)]
        else:
            a_text = f"{act.get('title','')} {act.get('type','')} {act.get('description','')} {act.get('founders_tip','')}"
            a_emb = model.encode(a_text, convert_to_tensor=True)

        semantic = float(util.pytorch_cos_sim(q_emb, a_emb).item())
        semantic = _clamp((semantic + 1) / 2)

        # 2. Intent Match fixed
        intent_match = 0.0
        if act_type in detected:
            intent_match = 1.0
        elif act_type == "RELAX" and ("SLEEP" in detected or "RELAX" in detected):
            intent_match = 0.9
        elif act_type == "SHOPPING" and "SHOPPING" in detected:
            intent_match = 1.0
        
        if (act_type in ["SIGHTS", "CULTURE"]) and ("SIGHTS" in detected or "CULTURE" in detected):
            intent_match = 1.0

        # 3. Smart Friction (The Fix: Less penalty for long layovers)
        buffer_left = layover_hours - (min_dur + overhead)
        
        if zone == "AIRSIDE":
            friction = 1.0
        else:
            # LANDSIDE LOGIC
            # If we have visa AND plenty of time (8h+), going landside is NOT friction.
            if visa_valid and layover_hours >= 8.0:
                 friction = 1.0  # Treat as easy access
            elif visa_valid and layover_hours >= 6.0:
                 friction = 0.85 # Slight penalty
            else:
                 friction = 0.55 # High friction (tight connection)

        # Risk Calculation
        risk_level = "LOW"
        if zone == "LANDSIDE":
            if layover_hours < 6 or buffer_left < 1.25:
                risk_level = "HIGH"
                friction = 0.30 # Severe penalty for risky connections
            elif layover_hours < 8 or buffer_left < 2.0:
                risk_level = "MED"

        # 4. Open Factor
        open_factor, open_tradeoffs = _open_score(act, arrival_hour)
        time_fit = _time_fit_score(min_dur, layover_hours, overhead)

        # 5. Sleep Penalty 
        sleep_penalty = 1.0
        if act_type == "SLEEP":
            if not explicitly_wants_sleep and "SLEEP" not in detected:
                sleep_penalty = 0.6 # 40% score reduction

        # 6. Weighted Final Score (The Fix: New Weights)
        final = (
            0.40 * semantic +
            0.25 * intent_match +  # Huge boost from 0.03 to 0.25
            0.15 * time_fit +
            0.10 * friction +
            0.10 * open_factor
        )
        
        final = final * sleep_penalty # Apply the demotion
        final = _clamp(final)

        # Explainability
        reasons = []
        tradeoffs = []

        if intent_match >= 0.9:
            reasons.append("Matches your vibe exactly.")
        elif semantic >= 0.65:
            reasons.append("Good semantic match.")

        if zone == "AIRSIDE":
            reasons.append("Low friction: stays inside airport.")
        elif friction >= 0.85:
            reasons.append("You have plenty of time to explore the city.")
        else:
            tradeoffs.append("Requires extra buffer for immigration.")

        if sleep_penalty < 1.0:
            tradeoffs.append("This is a sleep-only option (ranked lower).")

        if open_tradeoffs:
            tradeoffs.extend(open_tradeoffs)

        scored.append({
            "activity": act,
            "score": round(final * 100, 1),
            "risk_level": risk_level,
            "explain": {
                "reasons": reasons[:3],
                "tradeoffs": tradeoffs[:3],
                "detected_intents": list(detected)
            }
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored