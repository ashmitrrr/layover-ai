import streamlit as st
import pandas as pd
import base64
import os
from logic import filter_and_rank_activities, find_best_hubs
from viz import create_timeline

# ────────────────────────────────────────────────
# 1. SETUP & LOGO CONFIGURATION
# ────────────────────────────────────────────────

LOGO_PATH = "logo.png" 
# Fallback if local file isn't found
FALLBACK_URL = "https://cdn-icons-png.flaticon.com/512/723/723955.png"

def get_base64_image(image_path):
    """Converts a local image to base64 for HTML embedding."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return FALLBACK_URL

# Determine which logo to use
APP_ICON = LOGO_PATH if os.path.exists(LOGO_PATH) else FALLBACK_URL
HEADER_LOGO_SRC = get_base64_image(LOGO_PATH)

st.set_page_config(
    page_title="LayoverAI",
    page_icon=APP_ICON,
    layout="wide"
)

# Sidebar/Nav Logo (Try/Except for older Streamlit versions)
try:
    st.logo(APP_ICON, icon_image=APP_ICON)
except:
    pass

# ────────────────────────────────────────────────
# 2. CUSTOM CSS (Styling + Animations)
# ────────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Outfit:wght@300;400;500;600;700&display=swap');

    /* --- ANIMATIONS --- */
    @keyframes fadeInSlide {{
        0% {{ opacity: 0; transform: translateY(20px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Apply Animation */
    .block-container {{ animation: fadeInSlide 0.8s ease-out; }}
    .streamlit-expanderHeader {{ animation: fadeInSlide 1s ease-out; }}
    .ai-box {{ animation: fadeInSlide 1.2s ease-out; }}

    /* --- BACKGROUND & LAYOUT --- */
    .stApp {{
        background: linear-gradient(rgba(10, 15, 25, 0.92), rgba(10, 15, 25, 0.88)),
                    url("https://wallpapers.com/images/hd/microsoft-flight-simulator-horizon-6mwe1vs8gpmjkhvo.jpg") center/cover fixed;
    }}

    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        max-width: 1280px !important;
    }}

    /* --- HEADER (LOGO ONLY) --- */
    .header-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }}
    
    .header-logo {{
        width: 210px; /* Big Logo Size */
        height: auto;
        filter: drop-shadow(0 0 20px rgba(0, 234, 255, 0.2));
        transition: transform 0.3s ease;
    }}
    .header-logo:hover {{ transform: scale(1.02); }}

    .subtitle {{
        text-align: center;
        font-family: 'Outfit', sans-serif;
        font-size: 1.2rem;
        color: #a0d8ef;
        letter-spacing: 4px;
        text-transform: uppercase;
        margin-top: 15px;
        margin-bottom: 3rem;
        opacity: 0.85;
        font-weight: 500;
    }}

    /* --- INPUTS --- */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {{
        background-color: rgba(20, 30, 45, 0.88) !important;
        color: #e0f7ff !important;
        border: 1px solid #00d4ff44 !important;
        border-radius: 10px;
        font-size: 1.08rem !important;
    }}
    label {{ color: #b0e0ff !important; font-weight: 500 !important; }}

    /* --- BUTTONS --- */
    .stButton > button {{
        background: linear-gradient(135deg, #ff4b5c, #ff6b6b) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.9rem 2.4rem !important;
        font-size: 1.18rem !important;
        font-weight: 700 !important;
        letter-spacing: 1.1px;
        box-shadow: 0 6px 20px rgba(255, 75, 92, 0.4) !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 32px rgba(255, 75, 92, 0.55) !important;
    }}

    /* --- AI NARRATOR BOX --- */
    .ai-box {{
        background: rgba(0, 212, 255, 0.08);
        border-left: 4px solid #00d4ff;
        padding: 1.6rem 2rem;
        border-radius: 10px;
        margin: 2rem 0;
        color: #FFFFFF !important;
        font-size: 1.15rem !important;
        line-height: 1.6;
    }}
    .ai-box b {{ color: #00eaff !important; }}

    /* --- EXPANDER CARDS (Fixed Visibility) --- */
    .streamlit-expanderHeader {{
        background: rgba(30, 45, 65, 0.8) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        border-radius: 10px !important;
        padding: 18px 24px !important;
        margin-bottom: 0.8rem !important;
    }}
    .streamlit-expanderHeader p {{
        color: #FFFFFF !important;
        font-weight: 700 !important;    
        font-size: 1.3rem !important;   
    }}
    .streamlit-expanderContent {{
        background: rgba(15, 20, 30, 0.95) !important;
        border-radius: 0 0 10px 10px !important;
        padding: 24px !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    /* Aggressive Selector for Text Color */
    .streamlit-expanderContent p, 
    .streamlit-expanderContent div, 
    .streamlit-expanderContent li,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {{
        color: #E0E0E0 !important;
        font-size: 1.15rem !important;
        font-weight: 400 !important;
        line-height: 1.6 !important;   
    }}

    /* --- STAT PILLS --- */
    .stat-pill {{
        display: inline-block; padding: 6px 12px; border-radius: 6px;
        background: rgba(255, 255, 255, 0.08); color: #FFFFFF;
        font-size: 0.9rem; font-weight: 600; margin-bottom: 6px;
        width: 100%; text-align: right; border-right: 4px solid;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }}

    /* --- TIMELINE --- */
    .timeline-container {{
        background: rgba(15, 25, 40, 0.75); border-radius: 12px;
        padding: 1.4rem 1.8rem; border: 1px solid rgba(0, 212, 255, 0.14);
        margin-top: 1.8rem;
    }}
    
    h2, h3 {{ color: #FFFFFF !important; font-family: 'Space Mono', monospace; }}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 3. SESSION STATE & HELPERS
# ────────────────────────────────────────────────
if 'hub_index' not in st.session_state: st.session_state.hub_index = 0
if 'show_results' not in st.session_state: st.session_state.show_results = False

CITY_TO_CODE = {
    "delhi": "DEL", "new delhi": "DEL", "del": "DEL",
    "mumbai": "BOM", "bom": "BOM",
    "bangalore": "BLR", "bengaluru": "BLR", "blr": "BLR",
    "london": "LHR", "heathrow": "LHR", "lhr": "LHR",
    "dubai": "DXB", "dxb": "DXB",
    "doha": "DOH", "doh": "DOH",
    "singapore": "SIN", "changi": "SIN", "sin": "SIN",
    "bangkok": "BKK", "suvarnabhumi": "BKK", "bkk": "BKK",
    "tokyo": "HND", "haneda": "HND", "hnd": "HND", "narita": "NRT", "nrt": "NRT",
    "istanbul": "IST", "ist": "IST",
    "sydney": "SYD", "syd": "SYD",
    "melbourne": "MEL", "mel": "MEL",
    "new york": "JFK", "jfk": "JFK", "ny": "JFK",
    "san francisco": "SFO", "sfo": "SFO",
    "paris": "CDG", "cdg": "CDG"
}

def get_airport_code(user_input):
    clean_input = user_input.strip().lower()
    return CITY_TO_CODE.get(clean_input, user_input.upper())

CITY_IMAGES = {
    "doh": ["https://www.qatarairways.com/content/dam/images/renditions/horizontal-3/destinations/qatar/doha/h3-discover-qatar.jpg", "https://i.insider.com/614e388d2fb46b0019be1518?width=700"],
    "dxb": ["https://media.istockphoto.com/id/154918211/photo/city-of-dubai-burj-khalifa.jpg?s=612x612&w=0&k=20&c=IQ1upJGlnISqrBcBpmDS8HTCw-u6j08GkrFwV2QEMQk=", "https://economymiddleeast.com/cdn-cgi/imagedelivery/Xfg_b7GtigYi5mxeAzkt9w/economymiddleeast.com/2024/12/DXB.jpg/w=1200,h=800"],
    "sin": ["https://media.istockphoto.com/id/590050726/photo/singapore-glowing-at-night.jpg?s=612x612&w=0&k=20&c=43tSsy1yC0iOAGL3ZVq3-nl84KnmWTnHGI5mwQtp8zo=", "https://assets.architecturaldigest.in/photos/68c7d8d82cdd24de84422076/master/w_1600%2Cc_limit/2209940368"],
    "bkk": ["https://images.contentstack.io/v3/assets/blt06f605a34f1194ff/blt946ff9e4985c1319/6731c3a64ef1040e96e55bfc/BCC-2024-EXPLORER-BANGKOK-FUN-THINGS-TO-DO-HEADER_MOBILE.jpg?fit=crop&disable=upscale&auto=webp&quality=60&crop=smart", "https://cdn.sanity.io/images/nxpteyfv/goguides/43d4bd7fa049ae9062730f0b5a479ddfbf2cd77a-1600x1066.jpg"],
    "lhr": ["https://cms.inspirato.com/ImageGen.ashx?image=%2Fmedia%2F5682444%2FLondon_Dest_16531610X.jpg&width=1081.5", "https://www.tripsavvy.com/thmb/vKqHGNr-M6zNFu965gNLrnnb8eg=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/GettyImages-143685782-593523f83df78c08ab1fa4d5.jpg"],
    "ist": ["https://hblimg.mmtcdn.com/content/hubble/img/tvdestinationimages/mmt/activities/m_Istanbul_tv_destination_img_1_l_667_1000.jpg", "https://cargofactsevents.com/wp-content/uploads/2025/04/IST-2.jpg"],
    "hnd": ["https://img.freepik.com/free-photo/aerial-view-tokyo-cityscape-with-fuji-mountain-japan_335224-148.jpg?semt=ais_hybrid&w=740&q=80", "https://www.machiya-inn-japan.com/blog/wp-content/uploads/2024/12/Haneda-Airport-Tokyo-International-Airport.jpeg"],
}

city_options = {
    "doh": "Doha (DOH) 🇶🇦", "dxb": "Dubai (DXB) 🇦🇪", "sin": "Singapore (SIN) 🇸🇬",
    "bkk": "Bangkok (BKK) 🇹🇭", "lhr": "London (LHR) 🇬🇧", "ist": "Istanbul (IST) 🇹🇷",
    "hnd": "Tokyo (HND) 🇯🇵"
}
city_keys = list(city_options.keys())

# ────────────────────────────────────────────────
# 4. AI NARRATOR LOGIC
# ────────────────────────────────────────────────
def generate_narrative(activities, hours, user_vibe):
    if not activities: return "I couldn't find any perfect matches, but here are some options."
    
    top_pick = activities[0]['activity']['title']
    second_pick = activities[1]['activity']['title'] if len(activities) > 1 else "exploring the terminal"
    
    if hours < 5: time_msg = "It's a short layover, so we're keeping it tight."
    elif hours < 10: time_msg = "You have a decent amount of time to explore!"
    else: time_msg = "With this much time, you can really relax and see the city."

    vibe_lower = user_vibe.lower()
    if "food" in vibe_lower or "eat" in vibe_lower: vibe_msg = f"Since you're hungry, your priority stop is <b>{top_pick}</b>."
    elif "relax" in vibe_lower or "sleep" in vibe_lower: vibe_msg = f"To help you rest, I've prioritized <b>{top_pick}</b> for maximum comfort."
    elif "shop" in vibe_lower: vibe_msg = f"Get your wallet ready! We're sending you to <b>{top_pick}</b>."
    else: vibe_msg = f"Based on your vibe, <b>{top_pick}</b> is your best bet."

    return f"🤖 <b>SMART TIP:</b> {time_msg} {vibe_msg} Afterwards, if you have time, check out <b>{second_pick}</b>."

# ────────────────────────────────────────────────
# 5. HEADER (LOGO ONLY, INCREASED SIZE)
# ────────────────────────────────────────────────
st.markdown(f"""
    <div class="header-container">
        <img src="{HEADER_LOGO_SRC}" class="header-logo">
    </div>
    <p class="subtitle">TURN YOUR BORING TRANSIT INTO A MINI-VACATION</p>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 6. SEARCH SECTION
# ────────────────────────────────────────────────
with st.container():
    st.markdown("### 🗺️ Flight Vector")
    c1, c2, c3 = st.columns([2, 2, 1.3])
    with c1: origin_input = st.text_input("Origin", "Delhi")
    with c2: dest_input = st.text_input("Destination", "Sydney")
    with c3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔎 FIND HUB"):
            origin_code = get_airport_code(origin_input)
            dest_code = get_airport_code(dest_input)
            suggestions = find_best_hubs(origin_code, dest_code)
            if suggestions and suggestions[0] in city_keys:
                st.session_state.hub_index = city_keys.index(suggestions[0])
                st.toast(f"Route Found: {origin_code} ➝ {dest_code} via {suggestions[0].upper()}", icon="✈️")
                st.rerun()
            else:
                st.warning(f"No match for {origin_code} -> {dest_code}. Select Manually 👇")

    st.markdown("<div style='height: 2.4rem;'></div>", unsafe_allow_html=True)

    st.markdown("### 📍 Transit Hub")
    col_hub, col_vibe = st.columns([1.6, 2.4])
    with col_hub:
        selected_code = st.selectbox(
            "Select Airport",
            city_keys,
            index=st.session_state.hub_index,
            format_func=lambda x: city_options[x]
        )
        if selected_code != city_keys[st.session_state.hub_index]: st.session_state.hub_index = city_keys.index(selected_code)
    with col_vibe: user_query = st.text_input("✨ Vibe Check", "I want local food and sightseeing")

    st.markdown("<div style='height: 1.8rem;'></div>", unsafe_allow_html=True)

    c_time, c_arr, c_visa = st.columns([1,1,1.2])
    with c_time: hours = st.number_input("Duration (Hours)", 2.0, 24.0, 6.0, 0.5)
    with c_arr: arrival_time = st.number_input("Arrival Time (24h)", 0, 23, 14)
    with c_visa:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        visa_valid = st.toggle("I have Visa / Visa-Free", value=True)

    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

    if st.button("🚀 GENERATE ITINERARY"):
        st.session_state.show_results = True

# ────────────────────────────────────────────────
# 7. RESULTS
# ────────────────────────────────────────────────
if st.session_state.show_results:
    current_hub_name = city_options[selected_code]
    st.markdown(f"<h2 style='text-align:center; margin: 4rem 0 2rem 0;'>Exploring {current_hub_name}</h2>", unsafe_allow_html=True)

    img_c1, img_c2 = st.columns(2)
    city_img_url, airport_img_url = CITY_IMAGES.get(selected_code, CITY_IMAGES["doh"])
    
    # Updated to use_container_width (Fixes deprecated warning)
    with img_c1: st.image(city_img_url, use_container_width=True) 
    with img_c2: st.image(airport_img_url, use_container_width=True) 

    st.markdown("<div style='height: 2.5rem;'></div>", unsafe_allow_html=True)

    with st.spinner("Matching your vibe to the schedule..."):
        ranked_activities = filter_and_rank_activities(selected_code, hours, arrival_time, user_query, visa_valid)

    if not ranked_activities:
        st.error("No suitable activities match your time / visa constraints. Try a longer layover?")
    else:
        # NARRATIVE BOX (FIXED)
        narrative = generate_narrative(ranked_activities, hours, user_query)
        st.markdown(f'<div class="ai-box">{narrative}</div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1.6, 1])
        with col_left:
            st.markdown("###  Top Recommendations")
            for item in ranked_activities:
                act = item['activity']
                score = item['score']
                
                # RESTORED ICONS
                icon = {"FOOD":"🍜","RELAX":"💆","SHOPPING":"🛍️"}.get(act['type'], "📍")
                
                with st.expander(f"{icon} {act['title']}  —  {score}% Match", expanded=(score > 75)):
                    c_desc, c_stats = st.columns([2.5, 1])
                    with c_desc:
                        st.markdown(f"<p>{act['description']}</p>", unsafe_allow_html=True)
                        if 'founders_tip' in act: st.info(f"💡 {act['founders_tip']}")
                    
                    # RESTORED PILLS
                    with c_stats:
                        zone_tag = "🛃 AIRSIDE" if act['location']['zone'] == "AIRSIDE" else "🏙️ LANDSIDE"
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
            st.markdown("###  Map View")
            map_data = [{"lat": a['activity']['location']['lat'], "lon": a['activity']['location']['lon']} for a in ranked_activities if a['activity']['location'].get('lat', 0) != 0]
            if map_data: st.map(pd.DataFrame(map_data), zoom=10)
            else: st.info("Map coordinates not available for this hub.")

        st.markdown("<div style='height: 3.5rem;'></div>", unsafe_allow_html=True)

        st.markdown("### ⏳ Suggested Timeframe")
        timeline_fig = create_timeline(ranked_activities, arrival_time, hours)
        if timeline_fig:
            st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
            st.plotly_chart(timeline_fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)