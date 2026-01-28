import streamlit as st
import pandas as pd
import base64
import os
import requests
import time
from urllib.parse import quote
from streamlit_lottie import st_lottie 

# Import your logic engine
from logic import (
    filter_and_rank_activities,
    rank_hubs,          
    analyze_vibe,
    compute_plan_risk,
    check_visa_status,
    get_real_weather
)
from viz import create_timeline

# ────────────────────────────────────────────────
# 1. PAGE CONFIG & ASSETS
# ────────────────────────────────────────────────

# Define Asset Paths
LOGO_PATH = "assets/logo.png"
BANNER_PATH_JPG = "assets/banner.jpg"
BANNER_PATH_PNG = "assets/banner.png"
BANNER_PATH_CAPS = "assets/banner.JPG"
FALLBACK_URL = "https://cdn-icons-png.flaticon.com/512/723/723955.png"

# Helper to load images
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return FALLBACK_URL

# Determine which banner exists
if os.path.exists(BANNER_PATH_JPG):
    BANNER_SRC = get_base64_image(BANNER_PATH_JPG)
elif os.path.exists(BANNER_PATH_PNG):
    BANNER_SRC = get_base64_image(BANNER_PATH_PNG)
elif os.path.exists(BANNER_PATH_CAPS):
    BANNER_SRC = get_base64_image(BANNER_PATH_CAPS)
else:
    BANNER_SRC = FALLBACK_URL

# Helper to load Lottie animations (Cached)
@st.cache_data
def load_lottie_url(url: str):
    try:
        r = requests.get(url, timeout=2)
        if r.status_code != 200: return None
        return r.json()
    except: return None

# Determine valid logo/banner assets
APP_ICON = LOGO_PATH if os.path.exists(LOGO_PATH) else "✈️"

# Set page config
st.set_page_config(
    page_title="LayoverAI",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Display top-left logo if available
if os.path.exists(LOGO_PATH):
    try:
        st.logo(LOGO_PATH, icon_image=LOGO_PATH)
    except: pass

# ────────────────────────────────────────────────
# 2. THE "ALIVE" CSS ENGINE (PERMANENT DARK MODE)
# ────────────────────────────────────────────────
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700&family=JetBrains+Mono:wght@400;700&display=swap');

/* --- KEYFRAMES (THE MOTION ENGINE) --- */
@keyframes pulse-border {{
    0% {{ box-shadow: 0 0 0 0 rgba(0, 212, 255, 0.4); border-color: rgba(0, 212, 255, 0.2); }}
    70% {{ box-shadow: 0 0 20px 10px rgba(0, 212, 255, 0); border-color: rgba(0, 212, 255, 0.6); }}
    100% {{ box-shadow: 0 0 0 0 rgba(0, 212, 255, 0); border-color: rgba(0, 212, 255, 0.2); }}
}}

@keyframes shimmer {{
    0% {{ background-position: -1000px 0; }}
    100% {{ background-position: 1000px 0; }}
}}

@keyframes slideDown {{
    from {{ transform: translateY(-50px); opacity: 0; }}
    to {{ transform: translateY(0); opacity: 1; }}
}}

@keyframes slideUp {{
    from {{ transform: translateY(50px); opacity: 0; }}
    to {{ transform: translateY(0); opacity: 1; }}
}}

@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}

@keyframes floatParticles {{
    from {{ background-position: 0 0; }}
    to {{ background-position: 1000px 1000px; }}
}}

/* --- 1. GLOBAL ALIVE BACKGROUND --- */
.stApp {{
    background-color: #050a14 !important; 
    background: linear-gradient(rgba(5, 10, 20, 0.90), rgba(5, 10, 20, 0.95)),
                url("https://unsplash.com/photos/blue-sky-with-stars-during-daytime-6AKLKt-KmdY") center/cover fixed !important;
    color: #ffffff !important;
    font-family: 'Outfit', sans-serif;
}}

/* The Particle Layer */
.stApp::before {{
    content: "";
    position: fixed;
    top: 0; left: 0; width: 200%; height: 200%;
    background-image: 
        radial-gradient(white, rgba(255,255,255,.2) 2px, transparent 3px),
        radial-gradient(white, rgba(255,255,255,.15) 1px, transparent 2px),
        radial-gradient(white, rgba(255,255,255,.1) 2px, transparent 3px);
    background-size: 550px 550px, 350px 350px, 250px 250px;
    background-position: 0 0, 40px 60px, 130px 270px;
    animation: floatParticles 120s linear infinite;
    pointer-events: none;
    z-index: 0;
    opacity: 0.3;
}}

h1, h2, h3, h4, h5, h6, p, span, div, label {{ color: #ffffff !important; z-index: 1; }}

/* --- 2. GLASS SHIMMER CONTAINERS --- */
.glass-panel {{
    background: linear-gradient(to right, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.03) 40%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.03) 60%, rgba(255,255,255,0.03) 100%);
    background-size: 2000px 100%;
    animation: shimmer 6s infinite linear;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    position: relative;
    z-index: 1;
}}

.banner-box {{
    border-radius: 16px; 
    overflow: hidden; 
    border: 2px solid rgba(0, 212, 255, 0.2); 
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    animation: pulse-border 3s infinite;
}}

/* --- 3. ANIMATIONS --- */
.entry-0 {{ animation: slideDown 0.8s ease-out forwards; }}
.entry-1 {{ animation: fadeIn 1.2s ease-out forwards; opacity: 0; animation-delay: 0.3s; }}
.entry-2 {{ animation: slideUp 0.8s ease-out forwards; opacity: 0; animation-delay: 0.6s; }}
.entry-3 {{ animation: slideUp 0.8s ease-out forwards; opacity: 0; animation-delay: 0.9s; }}

/* --- 4. UI ELEMENTS --- */
.hero-title {{
    font-size: 3.5rem;
    font-weight: 700;
    background: linear-gradient(90deg, #FFFFFF 0%, #00D4FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0px;
    letter-spacing: -1px;
}}
.hero-slogan {{
    font-size: 1.2rem;
    color: #8daec4 !important;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-weight: 500;
    margin-bottom: 20px;
}}

/* Force Dark Inputs */
div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {{
    background-color: rgba(0, 0, 0, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}}
div[data-baseweb="base-input"] input {{ color: #ffffff !important; }}
label {{ color: #00d4ff !important; font-size: 0.8rem !important; text-transform: uppercase !important; letter-spacing: 1px !important; font-weight: 600 !important; }}

/* Fix Dropdowns */
ul[data-baseweb="menu"] {{
    background-color: rgba(10, 15, 25, 0.98) !important;
    border: 1px solid rgba(0, 212, 255, 0.2) !important;
    backdrop-filter: blur(16px);
}}
li[data-baseweb="option"] {{ color: #ffffff !important; }}
li[data-baseweb="option"][aria-selected="true"] {{ background-color: rgba(0, 212, 255, 0.2) !important; }}

/* Buttons */
.stButton > button {{
    background: linear-gradient(135deg, #00d4ff 0%, #005bea 100%) !important;
    color: #ffffff !important;
    border: none !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    width: 100%;
}}
.stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 0 20px rgba(0, 212, 255, 0.4) !important; }}

/* Expanders */
.streamlit-expanderHeader {{
    background-color: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    transition: all 0.3s ease !important;
}}
.streamlit-expanderHeader:hover {{
    border-color: #00d4ff !important;
    background-color: rgba(0, 212, 255, 0.08) !important;
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.2) !important;
    transform: translateY(-2px);
}}
.streamlit-expanderContent {{
    background-color: rgba(0, 0, 0, 0.4) !important;
    border: 1px solid rgba(0, 212, 255, 0.1) !important;
    border-radius: 0 0 8px 8px !important;
}}

/* HUD Pills */
.hud-stat {{ display: inline-flex; align-items: center; background: rgba(0, 212, 255, 0.1); border: 1px solid rgba(0, 212, 255, 0.2); color: #00d4ff !important; padding: 6px 16px; border-radius: 20px; font-size: 0.95rem; font-weight: 600; margin-right: 12px; }}
.ai-box {{ background: rgba(0, 212, 255, 0.05); border-left: 3px solid #00d4ff; padding: 20px; border-radius: 0 12px 12px 0; font-family: 'Outfit', sans-serif; line-height: 1.6; margin-bottom: 30px; }}
.ai-box b {{ color: #00eaff !important; }}
.stat-pill {{ display: inline-block; padding: 4px 10px; border-radius: 4px; background: rgba(255, 255, 255, 0.05); color: #FFFFFF; font-size: 0.8rem; font-weight: 600; margin-bottom: 4px; width: 100%; text-align: right; border-right: 3px solid; }}
.risk-pill {{ display: inline-block; padding: 5px 12px; border-radius: 20px; color: #fff; font-size: 0.85rem; font-weight: 700; margin-right: 8px; margin-bottom: 8px; }}
.risk-low {{ background: rgba(0, 255, 157, 0.15); border: 1px solid #00ff9d; color: #00ff9d !important; }}
.risk-med {{ background: rgba(255, 200, 0, 0.15); border: 1px solid #ffc800; color: #ffc800 !important; }}
.risk-high {{ background: rgba(255, 50, 50, 0.15); border: 1px solid #ff3232; color: #ff3232 !important; }}
.map-btn {{ display: inline-block; margin-top: 10px; background: rgba(0, 0, 0, 0.3); color: #00d4ff !important; text-decoration: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; border: 1px solid rgba(0, 212, 255, 0.3); transition: all 0.2s; }}
.map-btn:hover {{ background: rgba(0, 212, 255, 0.1); border-color: #00d4ff; }}
</style>
""",
    unsafe_allow_html=True
)

# ────────────────────────────────────────────────
# 3. SESSION STATE & HELPERS
# ────────────────────────────────────────────────
if "hub_index" not in st.session_state:
    st.session_state.hub_index = 0
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "refine_mode" not in st.session_state:
    st.session_state.refine_mode = "DEFAULT"
if "ranked_hubs" not in st.session_state:
    st.session_state.ranked_hubs = []
if "show_hub_dropdown" not in st.session_state:
    st.session_state.show_hub_dropdown = False

# EXTENDED CITY MAPPING (Global Coverage)
CITY_TO_CODE = {
    # INDIA & S. ASIA
    "delhi": "DEL", "del": "DEL", "new delhi": "DEL",
    "mumbai": "BOM", "bom": "BOM", "bombay": "BOM",
    "bangalore": "BLR", "blr": "BLR", "bengaluru": "BLR",
    "chennai": "MAA", "maa": "MAA",
    "hyderabad": "HYD", "hyd": "HYD",
    
    # MIDDLE EAST
    "dubai": "DXB", "dxb": "DXB",
    "doha": "DOH", "doh": "DOH", "qatar": "DOH",
    "abu dhabi": "AUH", "auh": "AUH",
    
    # EUROPE
    "london": "LHR", "lhr": "LHR", "heathrow": "LHR",
    "paris": "CDG", "cdg": "CDG", "charles de gaulle": "CDG",
    "amsterdam": "AMS", "ams": "AMS", "schiphol": "AMS",
    "frankfurt": "FRA", "fra": "FRA",
    "istanbul": "IST", "ist": "IST",
    "munich": "MUC", "muc": "MUC",
    "zurich": "ZRH", "zrh": "ZRH",
    "madrid": "MAD", "mad": "MAD",
    "rome": "FCO", "fco": "FCO",
    
    # SE ASIA & EAST ASIA
    "singapore": "SIN", "sin": "SIN", "changi": "SIN",
    "bangkok": "BKK", "bkk": "BKK",
    "tokyo": "HND", "hnd": "HND", "haneda": "HND", "narita": "NRT", "nrt": "NRT",
    "seoul": "ICN", "icn": "ICN", "incheon": "ICN",
    "hong kong": "HKG", "hkg": "HKG",
    "shanghai": "PVG", "pvg": "PVG",
    "beijing": "PEK", "pek": "PEK",
    
    # AUSTRALIA & OCEANIA
    "sydney": "SYD", "syd": "SYD",
    "melbourne": "MEL", "mel": "MEL",
    "brisbane": "BNE", "bne": "BNE",
    "perth": "PER", "per": "PER",
    "auckland": "AKL", "akl": "AKL",
    
    # NORTH AMERICA (USA & CANADA)
    "new york": "JFK", "jfk": "JFK", "nyc": "JFK", "newark": "EWR", "ewr": "EWR",
    "los angeles": "LAX", "lax": "LAX",
    "san francisco": "SFO", "sfo": "SFO",
    "chicago": "ORD", "ord": "ORD",
    "miami": "MIA", "mia": "MIA",
    "dallas": "DFW", "dfw": "DFW",
    "seattle": "SEA", "sea": "SEA",
    "vancouver": "YVR", "yvr": "YVR",
    "toronto": "YYZ", "yyz": "YYZ",
    "montreal": "YUL", "yul": "YUL",
    "calgary": "YYC", "yyc": "YYC"
}

def get_airport_code(user_input):
    clean_input = user_input.strip().lower()
    return CITY_TO_CODE.get(clean_input, user_input.upper())

# RELIABLE UNSPLASH IMAGES (No Hotlink Blocks)
CITY_IMAGES = {

"doh": ["https://www.qatarairways.com/content/dam/images/renditions/horizontal-3/destinations/qatar/doha/h3-discover-qatar.jpg", "https://i.insider.com/614e388d2fb46b0019be1518?width=700"],
"dxb": ["https://media.istockphoto.com/id/154918211/photo/city-of-dubai-burj-khalifa.jpg?s=612x612&w=0&k=20&c=IQ1upJGlnISqrBcBpmDS8HTCw-u6j08GkrFwV2QEMQk=", "https://economymiddleeast.com/cdn-cgi/imagedelivery/Xfg_b7GtigYi5mxeAzkt9w/economymiddleeast.com/2024/12/DXB.jpg/w=1200,h=800"],
"sin": ["https://media.istockphoto.com/id/590050726/photo/singapore-glowing-at-night.jpg?s=612x612&w=0&k=20&c=43tSsy1yC0iOAGL3ZVq3-nl84KnmWTnHGI5mwQtp8zo=", "https://assets.architecturaldigest.in/photos/68c7d8d82cdd24de84422076/master/w_1600%2Cc_limit/2209940368"],
"bkk": ["https://images.contentstack.io/v3/assets/blt06f605a34f1194ff/blt946ff9e4985c1319/6731c3a64ef1040e96e55bfc/BCC-2024-EXPLORER-BANGKOK-FUN-THINGS-TO-DO-HEADER_MOBILE.jpg?fit=crop&disable=upscale&auto=webp&quality=60&crop=smart", "https://cdn.sanity.io/images/nxpteyfv/goguides/43d4bd7fa049ae9062730f0b5a479ddfbf2cd77a-1600x1066.jpg"],
"lhr": ["https://cms.inspirato.com/ImageGen.ashx?image=%2Fmedia%2F5682444%2FLondon_Dest_16531610X.jpg&width=1081.5", "https://www.tripsavvy.com/thmb/vKqHGNr-M6zNFu965gNLrnnb8eg=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/GettyImages-143685782-593523f83df78c08ab1fa4d5.jpg"],
"ist": ["https://hblimg.mmtcdn.com/content/hubble/img/tvdestinationimages/mmt/activities/m_Istanbul_tv_destination_img_1_l_667_1000.jpg", "https://cargofactsevents.com/wp-content/uploads/2025/04/IST-2.jpg"],
"hnd": ["https://img.freepik.com/free-photo/aerial-view-tokyo-cityscape-with-fuji-mountain-japan_335224-148.jpg?semt=ais_hybrid&w=740&q=80", "https://www.machiya-inn-japan.com/blog/wp-content/uploads/2024/12/Haneda-Airport-Tokyo-International-Airport.jpeg"],
"ams": ["https://cdn.audleytravel.com/1050/749/79/15985180-canal-cruise-in-amsterdam-netherlands.webp", "https://worldwidetravel.tips/wp-content/uploads/2020/12/Netherlands-Amsterdam-Airport-Schiphol-_120.jpg"],
"icn": ["https://ik.imgkit.net/3vlqs5axxjf/external/http://images.ntmllc.com/v4/destination/South-Korea/Seoul/219740_SCN_Seoul_iStock521707831_ZC35CD.jpg?tr=w-1200%2Cfo-auto", "https://wheelchairtravel.org/content/images/wp-content/uploads/2015/11/seoul_airport-feature.jpg"],
"cdg": ["https://www.chooseparisregion.org/sites/default/files/news/6---Tour-Eiffel_AdobeStock_644956457_1920_72dpi.jpg", "https://www.chooseparisregion.org/sites/default/files/territories/Paris-CDG-Airport-Area.jpg"]

}

city_options = {
    "doh": "Doha (DOH) 🇶🇦",
    "dxb": "Dubai (DXB) 🇦🇪",
    "sin": "Singapore (SIN) 🇸🇬",
    "bkk": "Bangkok (BKK) 🇹🇭",
    "lhr": "London (LHR) 🇬🇧",
    "ist": "Istanbul (IST) 🇹🇷",
    "hnd": "Tokyo (HND) 🇯🇵",
    "ams": "Amsterdam (AMS) 🇳🇱",
    "icn": "Seoul (ICN) 🇰🇷",
    "cdg": "Paris (CDG) 🇫🇷"
}
city_keys = list(city_options.keys())

def render_risk_pill(level: str) -> str:
    level = (level or "").upper()
    if level == "LOW":
        return '<span class="risk-pill risk-low">✅ LOW RISK</span>'
    if level == "MED":
        return '<span class="risk-pill risk-med">⚠️ MEDIUM RISK</span>'
    if level == "HIGH":
        return '<span class="risk-pill risk-high">🚨 HIGH RISK</span>'
    return '<span class="risk-pill risk-med">ℹ️ RISK UNKNOWN</span>'

def apply_refinement(base_query: str, mode: str) -> str:
    q = (base_query or "").strip()
    mode = (mode or "DEFAULT").upper()
    if mode == "ONLY_AIRSIDE":
        return f"{q}. Prefer airside only, inside airport, no city trips."
    if mode == "MORE_CHILL":
        return f"{q}. Prefer relaxing, quiet, lounge, spa, comfy."
    if mode == "MORE_CULTURE":
        return f"{q}. Prefer culture, museums, heritage, landmarks, history."
    if mode == "MAX_SIGHTS":
        return f"{q}. Prefer sightseeing, viewpoints, iconic spots, photo locations."
    if mode == "CHEAPER":
        return f"{q}. Prefer cheap, free, budget friendly."
    return q

def generate_narrative(ranked_items, hours, user_vibe, visa_valid, arrival_time):
    if not ranked_items:
        return "I scanned the airport, but I couldn't find any safe matches for this specific window. It might be too tight to explore comfortably."

    top_pick = ranked_items[0]
    act = top_pick["activity"]
    meta = top_pick.get("explain", {}).get("v3_meta", {})
    overhead = meta.get("total_overhead_hours", 2.5)
    safe_time = max(0.0, hours - overhead)
    
    is_night = (arrival_time >= 21 or arrival_time <= 4)
    
    if is_night:
        if hours >= 14:
            time_msg = f"You land late ({arrival_time}:00), but with {hours} hours, you're set. **Sleep first**, then you have a full day to explore tomorrow."
        elif hours >= 7:
            time_msg = f"You land at {arrival_time}:00 and fly out in the morning. Honestly? **Skip the city.** It's not worth the immigration hassle to see closed buildings. Head to an airside hotel or lounge and get some real sleep."
        else:
            time_msg = f"It's a short overnight stop ({arrival_time}:00 arrival). The city is asleep. Stick to the airport terminal."
            
    elif meta.get("method") == "V3_DYNAMIC" and safe_time < 2.0:
        time_msg = f"Okay, real talk: You have {hours} hours, but airport logistics are eating most of it. We need to be super efficient."
    else:
        time_msg = f"Logistics look smooth. You'll have about <b>{int(safe_time)}h {int((safe_time*60)%60)}m</b> of actual fun time."

    vibe_lower = (user_vibe or "").lower()
    if not vibe_lower:
        vibe_msg = f"I've picked <b>{act['title']}</b> as your best bet."
    elif any(w in vibe_lower for w in ["sleep", "rest", "hotel"]):
        vibe_msg = f"Since you want to rest, <b>{act['title']}</b> is the smartest choice."
    else:
        vibe_msg = f"Based on your vibe, <b>{act['title']}</b> is a solid match."

    return f"""
    🤖 <b>LayoverAI:</b> {time_msg}
    <br><br>
    {vibe_msg}
    """

def render_safe_time_breakdown(ranked_activities, total_layover_hours):
    if not ranked_activities: return
    
    first_item = ranked_activities[0]
    meta = first_item.get("explain", {}).get("v3_meta", {})
    
    def fmt_mins(m): return f"{m} mins"
    def fmt_hours(h): return f"{int(h)}h {int((h*60)%60)}m"
    
    if meta.get("method") != "V3_DYNAMIC":
        st.info(f"🛡️ **Safe Buffer:** We reserved 2.5 hours for airport logistics, leaving you {total_layover_hours - 2.5}h to explore.")
        return

    imm = meta.get("immigration_mins", 0)
    transit = meta.get("transit_mins", 0)
    sec = meta.get("security_mins", 0)
    overhead = meta.get("total_overhead_hours", 0)
    safe_val = max(0.0, total_layover_hours - overhead)
    
    st.markdown(f"""
    <div class="entry-2" style="background: rgba(0, 212, 255, 0.05); border: 1px solid rgba(0, 212, 255, 0.1); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; font-size: 1.1rem; font-weight: 700; color: #fff; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
            <span>⏱️ Total Layover</span>
            <span>{fmt_hours(total_layover_hours)}</span>
        </div>
        <div style="display: flex; justify-content: space-between; color: #b0e0ff; padding: 4px 0;">
            <span>🛂 Immigration Processing (Avg)</span>
            <span class="deduction">-{fmt_mins(imm)}</span>
        </div>
        <div style="display: flex; justify-content: space-between; color: #b0e0ff; padding: 4px 0;">
            <span>🚆 City Transit (Round Trip)</span>
            <span class="deduction">-{fmt_mins(transit)}</span>
        </div>
        <div style="display: flex; justify-content: space-between; color: #b0e0ff; padding: 4px 0;">
            <span>🛡️ Security & Buffer</span>
            <span class="deduction">-{fmt_mins(sec)}</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 1.2rem; font-weight: 700; color: #00ff9d; margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
            <span>Safe Exploration Time</span>
            <span>{fmt_hours(safe_val)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 4. HEADER & BANNER (THE HUD)
# ────────────────────────────────────────────────
c_head1, c_head2 = st.columns([2, 1])
with c_head1:
    st.markdown('<h1 class="hero-title">LayoverAI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-slogan">AI Powered Transit & Layover Intelligence</p>', unsafe_allow_html=True)
    st.markdown("<em>Turn Your Boring Transit Into A Mini-Vacation</em>", unsafe_allow_html=True)

with c_head2:
    st.markdown(f"""
        <div class="banner-box">
            <img src="{BANNER_SRC}" style="width: 100%; height: auto; display: block;">
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 5. COMMAND DECK (SEARCH)
# ────────────────────────────────────────────────
st.markdown('<div class="glass-panel">', unsafe_allow_html=True)

c1, c2, c3 = st.columns([2, 2, 1.3])
with c1:
    origin_input = st.text_input("Origin", "Delhi", key="ui_origin")
with c2:
    dest_input = st.text_input("Destination", "Sydney", key="ui_dest")
with c3:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    find_clicked = st.button("Find Hub 🔎", key="btn_find_hub")

if find_clicked:
    origin_code = get_airport_code(origin_input)
    dest_code = get_airport_code(dest_input)
    ranked = rank_hubs(origin_code, dest_code, 6.0, 14, True, "")
    st.session_state.ranked_hubs = ranked
    st.session_state.show_hub_dropdown = True

    if ranked:
        best = ranked[0]["hub_id"]
        if best in city_keys:
            st.session_state.hub_index = city_keys.index(best)
            st.toast(f"Route: {origin_code} ➝ {dest_code} via {best.upper()}", icon="✈️")
    else:
        st.warning("No direct hub match. Select manually below.")

if st.session_state.show_hub_dropdown and st.session_state.ranked_hubs:
    hub_score = {x["hub_id"]: x["score"] for x in st.session_state.ranked_hubs if "hub_id" in x}
    hub_ids = [h for h in hub_score.keys() if h in city_options]
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    chosen = st.selectbox(
        "AI Recommended Hubs",
        hub_ids,
        format_func=lambda h: f"{city_options.get(h, h.upper())} ({hub_score.get(h,0)}% Match)",
        key="hub_reco_dropdown"
    )
    if chosen in city_keys:
        st.session_state.hub_index = city_keys.index(chosen)

# Row 2: Hub + Vibe
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
col_hub, col_vibe = st.columns([1.6, 2.4])
with col_hub:
    selected_code = st.selectbox(
        "Select Airport",
        city_keys,
        index=st.session_state.hub_index,
        format_func=lambda x: city_options[x],
        key="ui_selected_hub"
    )
    st.session_state.hub_index = city_keys.index(selected_code)
with col_vibe:
    user_query = st.text_input("Vibe Check", "I want local food and sightseeing", key="ui_user_query")

# Row 3: Details
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
c_time, c_arr, c_day, c_visa = st.columns([1, 1, 1, 1.3])

with c_time:
    hours = st.number_input("Duration (Hours)", 2.0, 24.0, 6.0, 0.5, key="ui_hours")
with c_arr:
    arrival_time = st.number_input("Arrival Time (24h)", 0, 23, 14, key="ui_arrival_time")
with c_day:
    day_of_week = st.selectbox("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=0, key="ui_day")
with c_visa:
    passport_options = ["India", "USA", "UK", "EU", "Australia", "Japan"]
    selected_passport = st.selectbox("My Passport", passport_options, key="ui_passport")
    
    auto_visa, v_title, v_desc = check_visa_status(selected_code, selected_passport)
    visa_valid = auto_visa
    lower_title = v_title.lower()
    
    if "required" in lower_title and "eta" not in lower_title and "evisa" not in lower_title:
            st.markdown(f'<span style="color:#ff4b4b; font-weight:bold;">🛑 {v_title}</span>', unsafe_allow_html=True)
    elif any(x in lower_title for x in ["eta", "evisa", "conditional", "varies", "on arrival"]):
            st.markdown(f'<span style="color:#ffc800; font-weight:bold;">⚠️ {v_title}</span>', unsafe_allow_html=True)
    else:
            st.markdown(f'<span style="color:#00ff9d; font-weight:bold;">✅ {v_title}</span>', unsafe_allow_html=True)

    if not auto_visa:
            has_visa = st.checkbox("I have a valid Visa", key="ui_manual_visa")
            if has_visa: visa_valid = True

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
if st.button("🚀 GENERATE ITINERARY", key="btn_generate"):
    st.session_state.show_results = True

st.markdown('</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 6. RESULTS DASHBOARD
# ────────────────────────────────────────────────
if st.session_state.show_results:
    current_hub_name = city_options[selected_code]

    # Loading Theatre
    lottie_url = "https://assets5.lottiefiles.com/packages/lf20_x62chJ.json"
    lottie_json = load_lottie_url(lottie_url)
    
    if lottie_json:
        placeholder = st.empty()
        with placeholder.container():
            st_lottie(lottie_json, height=200, key="loading")
            st.markdown("<h3 style='text-align:center;'>Crunching Logistics...</h3>", unsafe_allow_html=True)
    
    time.sleep(1.5)
    if lottie_json: placeholder.empty()

    # Weather
    weather = get_real_weather(selected_code)
    weather_html = ""
    if weather:
        weather_html = f"""<div class="hud-stat">{weather['icon']} {weather['temp']}°C {weather['condition']}</div>"""
    
    # Situation Room
    st.markdown(f"""
<div class="entry-0" style="display:flex; align-items:center; justify-content:space-between; margin: 2rem 0 1.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px;">
    <div>
        <h2 style="margin:0; font-size: 2.2rem;">Exploring {current_hub_name}</h2>
        <div style="margin-top: 5px; display: flex; align-items: center;">
            {weather_html}
            <div class="hud-stat" style="margin-left: 10px;">📅 {day_of_week}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

    # Images
    st.markdown('<div class="entry-1">', unsafe_allow_html=True)
    img_c1, img_c2 = st.columns(2)
    city_img_url, airport_img_url = CITY_IMAGES.get(selected_code, CITY_IMAGES["doh"])
    with img_c1: st.image(city_img_url, use_container_width=True)
    with img_c2: st.image(airport_img_url, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Refine
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    r1, r2, r3, r4, r5 = st.columns(5)
    with r1: 
        if st.button("😌 More Chill"): st.session_state.refine_mode = "MORE_CHILL"; st.rerun()
    with r2: 
        if st.button("🏛️ Culture"): st.session_state.refine_mode = "MORE_CULTURE"; st.rerun()
    with r3: 
        if st.button("🛃 Airside"): st.session_state.refine_mode = "ONLY_AIRSIDE"; st.rerun()
    with r4: 
        if st.button("💸 Cheaper"): st.session_state.refine_mode = "CHEAPER"; st.rerun()
    with r5: 
        if st.button("📸 Sights"): st.session_state.refine_mode = "MAX_SIGHTS"; st.rerun()

    enriched_query = apply_refinement(user_query, st.session_state.refine_mode)

    # Logic
    ranked_activities = filter_and_rank_activities(
        selected_code, hours, arrival_time, enriched_query, visa_valid, day_of_week
    )

    # Safe Time
    render_safe_time_breakdown(ranked_activities, hours)
    
    # Warning
    st.markdown('<div class="entry-3">', unsafe_allow_html=True)
    is_late_night = (arrival_time >= 21 or arrival_time <= 4)
    is_long_sleep = (hours >= 7 and hours < 14) 
    is_full_day = (hours >= 14) 
    
    if is_late_night and is_long_sleep:
        st.info("🌙 **Sleep First:** You have a decent overnight break, but the city is closed. Prioritise an airport hotel!")
    elif is_late_night and is_full_day:
        st.success("🌙 **Overnight + Day:** You arrive late, but have the whole next day. Get a hotel, then explore!")
    elif is_late_night:
        st.warning("🌙 **Late Night:** Most city spots are closed. Stick to Airside options.")

    # Narrative
    if ranked_activities:
        narrative = generate_narrative(ranked_activities, hours, user_query, visa_valid, arrival_time)
        st.markdown(f'<div class="ai-box">{narrative}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Recommendations
    if not ranked_activities:
        st.error("No matches found. Try increasing duration or changing the vibe.")
    else:
        st.markdown('<div class="entry-3">', unsafe_allow_html=True)
        risk_level, risk_reason = compute_plan_risk(ranked_activities, hours, visa_valid)
        st.markdown(f"{render_risk_pill(risk_level)} <span class='meta-pill'>🧩 {risk_reason}</span>", unsafe_allow_html=True)
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1.6, 1])

        with col_left:
            st.markdown("### Top Recommendations")
            for item in ranked_activities:
                act = item["activity"]
                score = item["score"]
                risk = item.get("risk_level", "LOW")
                explain = item.get("explain", {}) or {}

                icon = {"FOOD": "🍜", "RELAX": "💆", "SHOPPING": "🛍️"}.get(act.get("type"), "📍")
                risk_tag = {"LOW": "✅", "MED": "⚠️", "HIGH": "🚨"}.get(risk, "ℹ️")

                with st.expander(f"{icon} {act['title']}  —  {score}% Match", expanded=(score > 75)):
                    c_desc, c_stats = st.columns([2.5, 1])
                    with c_desc:
                        st.markdown(f"**{act.get('description','')}**")
                        if "founders_tip" in act:
                            st.info(f"💡 {act['founders_tip']}")
                        
                        map_query = quote(f"{act['title']} {city_options[selected_code]}")
                        map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
                        st.markdown(f'<a href="{map_url}" target="_blank" class="map-btn">📍 Navigate ↗</a>', unsafe_allow_html=True)

                        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
                        for r in explain.get("reasons", []): st.caption(f"✅ {r}")
                        for t in explain.get("tradeoffs", []): st.caption(f"⚠️ {t}")

                    with c_stats:
                        zone_tag = "🛃 AIRSIDE" if act["location"]["zone"] == "AIRSIDE" else "🏙️ LANDSIDE"
                        cost_tag = f"💰 {act.get('cost_tier', 'MEDIUM')}"
                        time_tag = f"⏱️ {act['time_constraints']['min_duration_hours']}h+"
                        
                        st.markdown(f"""
                            <div style="display: flex; flex-direction: column; gap: 6px; align-items: flex-end;">
                                <span class="stat-pill" style="border-right-color: #00D4FF;">{zone_tag}</span>
                                <span class="stat-pill" style="border-right-color: #FFD700;">{cost_tag}</span>
                                <span class="stat-pill" style="border-right-color: #FF4B4B;">{time_tag}</span>
                            </div>
                        """, unsafe_allow_html=True)

        with col_right:
            st.markdown("### Map View")
            map_data = [{"lat": a["activity"]["location"]["lat"], "lon": a["activity"]["location"]["lon"]} 
                        for a in ranked_activities if a["activity"]["location"].get("lat", 0) != 0]
            if map_data: st.map(pd.DataFrame(map_data), zoom=10)
            else: st.info("No coordinates available.")

        st.markdown("<div style='height: 3.0rem;'></div>", unsafe_allow_html=True)
        st.markdown("### ⏳ Suggested Timeframe")
        timeline_fig = create_timeline(ranked_activities, arrival_time, hours)
        if timeline_fig:
            st.markdown('<div class="glass-panel" style="padding:10px;">', unsafe_allow_html=True)
            st.plotly_chart(timeline_fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)