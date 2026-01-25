import streamlit as st
import pandas as pd
import base64
import os

from logic import (
    filter_and_rank_activities,
    rank_hubs,          
    analyze_vibe,
    compute_plan_risk,
    check_visa_status
)
from viz import create_timeline

# ────────────────────────────────────────────────
# 1. SETUP & LOGO CONFIGURATION
# ────────────────────────────────────────────────

LOGO_PATH = "assets/logo.png"
FALLBACK_URL = "https://cdn-icons-png.flaticon.com/512/723/723955.png"


def get_base64_image(image_path):
    """Converts a local image to base64 for HTML embedding."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return FALLBACK_URL


APP_ICON = LOGO_PATH if os.path.exists(LOGO_PATH) else FALLBACK_URL
HEADER_LOGO_SRC = get_base64_image(LOGO_PATH)

st.set_page_config(
    page_title="LayoverAI",
    page_icon=APP_ICON,
    layout="wide"
)

try:
    st.logo(APP_ICON, icon_image=APP_ICON)
except Exception:
    pass

# ────────────────────────────────────────────────
# 2. CUSTOM CSS (Styling + Animations)
# ────────────────────────────────────────────────

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Outfit:wght@300;400;500;600;700&display=swap');
@keyframes fadeInSlide {{
    0% {{ opacity: 0; transform: translateY(20px); }}
    100% {{ opacity: 1; transform: translateY(0); }}
}}
.block-container {{ animation: fadeInSlide 0.8s ease-out; }}
.streamlit-expanderHeader {{ animation: fadeInSlide 1s ease-out; }}
.ai-box {{ animation: fadeInSlide 1.2s ease-out; }}

.stApp {{
    background: linear-gradient(rgba(10, 15, 25, 0.92), rgba(10, 15, 25, 0.88)),
                url("https://wallpapers.com/images/hd/microsoft-flight-simulator-horizon-6mwe1vs8gpmjkhvo.jpg") center/cover fixed;
}}
.block-container {{
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
    max-width: 1280px !important;
}}
.header-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-top: 1rem;
    margin-bottom: 1rem;
}}
.header-logo {{
    width: 250px;
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

.ai-box {{
    background: rgba(0, 212, 255, 0.08);
    border-left: 4px solid #00d4ff;
    padding: 1.6rem 2rem;
    border-radius: 10px;
    margin: 1.5rem 0;
    color: #FFFFFF !important;
    font-size: 1.15rem !important;
    line-height: 1.6;
}}
.ai-box b {{ color: #00eaff !important; }}

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
/* NEW: Pink gradient when the dropdown is OPEN - NUCLEAR OPTION */
details[open] > summary,
details[open] .streamlit-expanderHeader {{
    background: linear-gradient(135deg, #ff4b5c, #ff6b6b) !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(255, 75, 92, 0.4) !important;
    color: #FFFFFF !important;
}}

/* Force all text inside the header to be white */
details[open] > summary p,
details[open] > summary span,
details[open] .streamlit-expanderHeader p,
details[open] .streamlit-expanderHeader span {{
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}}

/* Fix the little arrow icon color */
details[open] > summary svg {{
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
}}
.streamlit-expanderContent {{
    background: rgba(15, 20, 30, 0.95) !important;
    border-radius: 0 0 10px 10px !important;
    padding: 24px !important;
    border: 1px solid rgba(255, 255, 255, 0.1);
}}
.streamlit-expanderContent p,
.streamlit-expanderContent div,
.streamlit-expanderContent li,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {{
    color: #E0E0E0 !important;
    font-size: 1.15rem !important;
    font-weight: 400 !important;
    line-height: 1.6 !important;
}}


.stat-pill {{
    display: inline-block; padding: 6px 12px; border-radius: 6px;
    background: rgba(255, 255, 255, 0.08); color: #FFFFFF;
    font-size: 0.9rem; font-weight: 600; margin-bottom: 6px;
    width: 100%; text-align: right; border-right: 4px solid;
    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
}}

.meta-pill {{
    display: inline-block;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(0, 212, 255, 0.10);
    border: 1px solid rgba(0, 212, 255, 0.25);
    color: #e8fbff;
    font-size: 0.92rem;
    font-weight: 600;
    margin-right: 8px;
    margin-bottom: 8px;
}}
.risk-pill {{
    display: inline-block;
    padding: 7px 12px;
    border-radius: 999px;
    color: #fff;
    font-size: 0.92rem;
    font-weight: 800;
    margin-right: 8px;
    margin-bottom: 8px;
}}
.risk-low {{ background: rgba(46, 204, 113, 0.25); border: 1px solid rgba(46, 204, 113, 0.45); }}
.risk-med {{ background: rgba(241, 196, 15, 0.25); border: 1px solid rgba(241, 196, 15, 0.45); }}
.risk-high {{ background: rgba(231, 76, 60, 0.25); border: 1px solid rgba(231, 76, 60, 0.45); }}

.timeline-container {{
    background: rgba(15, 25, 40, 0.75); border-radius: 12px;
    padding: 1.4rem 1.8rem; border: 1px solid rgba(0, 212, 255, 0.14);
    margin-top: 1.8rem;
}}
h2, h3 {{ color: #FFFFFF !important; font-family: 'Space Mono', monospace; }}
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

#  hub ranking state
if "ranked_hubs" not in st.session_state:
    st.session_state.ranked_hubs = []
if "show_hub_dropdown" not in st.session_state:
    st.session_state.show_hub_dropdown = False

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
    "doh": [
        "https://www.qatarairways.com/content/dam/images/renditions/horizontal-3/destinations/qatar/doha/h3-discover-qatar.jpg",
        "https://i.insider.com/614e388d2fb46b0019be1518?width=700",
    ],
    "dxb": [
        "https://media.istockphoto.com/id/154918211/photo/city-of-dubai-burj-khalifa.jpg?s=612x612&w=0&k=20&c=IQ1upJGlnISqrBcBpmDS8HTCw-u6j08GkrFwV2QEMQk=",
        "https://economymiddleeast.com/cdn-cgi/imagedelivery/Xfg_b7GtigYi5mxeAzkt9w/economymiddleeast.com/2024/12/DXB.jpg/w=1200,h=800",
    ],
    "sin": [
        "https://media.istockphoto.com/id/590050726/photo/singapore-glowing-at-night.jpg?s=612x612&w=0&k=20&c=43tSsy1yC0iOAGL3ZVq3-nl84KnmWTnHGI5mwQtp8zo=",
        "https://assets.architecturaldigest.in/photos/68c7d8d82cdd24de84422076/master/w_1600%2Cc_limit/2209940368",
    ],
    "bkk": [
        "https://images.contentstack.io/v3/assets/blt06f605a34f1194ff/blt946ff9e4985c1319/6731c3a64ef1040e96e55bfc/BCC-2024-EXPLORER-BANGKOK-FUN-THINGS-TO-DO-HEADER_MOBILE.jpg?fit=crop&disable=upscale&auto=webp&quality=60&crop=smart",
        "https://cdn.sanity.io/images/nxpteyfv/goguides/43d4bd7fa049ae9062730f0b5a479ddfbf2cd77a-1600x1066.jpg",
    ],
    "lhr": [
        "https://cms.inspirato.com/ImageGen.ashx?image=%2Fmedia%2F5682444%2FLondon_Dest_16531610X.jpg&width=1081.5",
        "https://www.tripsavvy.com/thmb/vKqHGNr-M6zNFu965gNLrnnb8eg=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/GettyImages-143685782-593523f83df78c08ab1fa4d5.jpg",
    ],
    "ist": [
        "https://hblimg.mmtcdn.com/content/hubble/img/tvdestinationimages/mmt/activities/m_Istanbul_tv_destination_img_1_l_667_1000.jpg",
        "https://cargofactsevents.com/wp-content/uploads/2025/04/IST-2.jpg",
    ],
    "hnd": [
        "https://img.freepik.com/free-photo/aerial-view-tokyo-cityscape-with-fuji-mountain-japan_335224-148.jpg?semt=ais_hybrid&w=740&q=80",
        "https://www.machiya-inn-japan.com/blog/wp-content/uploads/2024/12/Haneda-Airport-Tokyo-International-Airport.jpeg",
    ],
}

city_options = {
    "doh": "Doha (DOH) 🇶🇦",
    "dxb": "Dubai (DXB) 🇦🇪",
    "sin": "Singapore (SIN) 🇸🇬",
    "bkk": "Bangkok (BKK) 🇹🇭",
    "lhr": "London (LHR) 🇬🇧",
    "ist": "Istanbul (IST) 🇹🇷",
    "hnd": "Tokyo (HND) 🇯🇵",
}
city_keys = list(city_options.keys())

# ────────────────────────────────────────────────
# 4. HELPERS from v1
# ────────────────────────────────────────────────
def generate_narrative(ranked_items, hours, user_vibe, visa_valid, arrival_time):
    if not ranked_items:
        return "I couldn't find any safe matches for this window — try changing the vibe or picking a different hub."

    top = ranked_items[0]["activity"]["title"]
    second = ranked_items[1]["activity"]["title"] if len(ranked_items) > 1 else "exploring the terminal"

    if hours < 5:
        time_msg = "It's a short layover, so we're keeping things efficient."
    elif hours < 10:
        time_msg = "You have a decent amount of time to explore."
    else:
        time_msg = "With this much time, you can really take it slow."

    late = (arrival_time >= 22) or (arrival_time <= 5)
    night_msg = "But heads up — it's a late arrival, so a lot of city spots may be closed. I'm prioritising options that are open late / 24h." if late else ""

    visa_msg = "Since you have visa access, landside city options can be included too." if visa_valid else \
               "Because you don’t have visa access, I’m sticking to airside options so you don’t get trapped by immigration rules."

    vibe_lower = (user_vibe or "").lower()
    if any(w in vibe_lower for w in ["food", "eat", "hungry"]):
        vibe_msg = f"Since you're hungry, your priority stop is <b>{top}</b>."
    elif any(w in vibe_lower for w in ["relax", "sleep", "nap", "rest"]):
        vibe_msg = f"To help you recharge, I’ve prioritised <b>{top}</b>."
    elif any(w in vibe_lower for w in ["shop", "shopping", "buy"]):
        vibe_msg = f"Retail therapy time — <b>{top}</b> is your best bet."
    else:
        vibe_msg = f"Based on your vibe, <b>{top}</b> is your strongest match."

    return f"""
    🤖 <b>LayoverAI TIP:</b> {time_msg} {visa_msg} {night_msg}
    {vibe_msg} Afterwards, if you have time, check out <b>{second}</b>.
    """

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

# ────────────────────────────────────────────────
# 5. HEADER
# ────────────────────────────────────────────────
st.markdown(
    f"""
<div class="header-container">
    <img src="{HEADER_LOGO_SRC}" class="header-logo">
</div>
<p class="subtitle">TURN YOUR BORING TRANSIT INTO A MINI-VACATION</p>
""",
    unsafe_allow_html=True,
)

st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# 6. SEARCH SECTION
# ────────────────────────────────────────────────
with st.container():
    st.markdown("### Flight Vector")
    c1, c2, c3 = st.columns([2, 2, 1.3])

    with c1:
        origin_input = st.text_input("Origin", "Delhi", key="ui_origin")
    with c2:
        dest_input = st.text_input("Destination", "Sydney", key="ui_dest")
    with c3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        find_clicked = st.button("FIND HUB", key="btn_find_hub")

    # no dropdown rendering 
    if find_clicked:
        origin_code = get_airport_code(origin_input)
        dest_code = get_airport_code(dest_input)

        _hours = st.session_state.get("ui_hours", 6.0)
        _arrival = st.session_state.get("ui_arrival_time", 14)
        _visa = st.session_state.get("ui_visa_valid", True)
        _vibe = st.session_state.get("ui_user_query", "I want local food and sightseeing")

        ranked = rank_hubs(origin_code, dest_code, _hours, _arrival, _visa, _vibe)

        st.session_state.ranked_hubs = ranked
        st.session_state.show_hub_dropdown = True

        if ranked:
            best = ranked[0]["hub_id"]
            if best in city_keys:
                st.session_state.hub_index = city_keys.index(best)
                st.toast(f"Route Found: {origin_code} ➝ {dest_code} via {best.upper()}", icon="✈️")
        else:
            st.warning(f"No match for {origin_code} -> {dest_code}. Select Manually 👇")
    

    # dropdown renders outside butn
    if st.session_state.show_hub_dropdown and st.session_state.ranked_hubs:
        st.markdown("### Best Transit Hubs")

        # hub_id -> score
        hub_score = {
            item["hub_id"]: float(item.get("score", 0))
            for item in st.session_state.ranked_hubs
            if isinstance(item, dict) and "hub_id" in item
        }

        # Keep only hub_ids that exist in UI list
        hub_ids = [h for h in hub_score.keys() if h in city_options]

        # Dropdown label w score
        def fmt_hub(h):
            return f"{city_options.get(h, h.upper())}  —  {hub_score.get(h, 0):.0f}%"

        chosen = st.selectbox(
            "AI Recommended Hubs",
            hub_ids,
            format_func=fmt_hub,
            key="hub_reco_dropdown"
        )

        if chosen in city_keys:
            st.session_state.hub_index = city_keys.index(chosen)
        #  why selected hub
    selected_obj = next((x for x in st.session_state.ranked_hubs if x.get("hub_id") == chosen), None)
    if selected_obj:
        why = selected_obj.get("why", [])
        if why:
            with st.expander("Why this hub?", expanded=False):
                for w in why:
                    st.markdown(f"- ✅ {w}")



    st.markdown("<div style='height: 2.4rem;'></div>", unsafe_allow_html=True)

    st.markdown("### 📍 Transit Hub")
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
        user_query = st.text_input(
            "✨ Vibe Check",
            "I want local food and sightseeing",
            key="ui_user_query"
        )

    st.markdown("<div style='height: 1.8rem;'></div>", unsafe_allow_html=True)

    c_time, c_arr, c_visa = st.columns([1, 1, 1.2])
    with c_time:
        hours = st.number_input("Duration (Hours)", 2.0, 24.0, 6.0, 0.5, key="ui_hours")
    with c_arr:
        arrival_time = st.number_input("Arrival Time (24h)", 0, 23, 14, key="ui_arrival_time")
    with c_visa:
        # 1. Passport Dropdown
        passport_options = ["India", "USA", "UK", "EU", "Australia", "Japan"]
        selected_passport = st.selectbox("My Passport", passport_options, key="ui_passport")
        
        # 2. visa Status Live
        auto_visa, v_title, v_desc = check_visa_status(selected_code, selected_passport)
        
        # 3. Store result for the ranking logic
        visa_valid = auto_visa

        lower_title = v_title.lower()

        # 5. TLL
        if "required" in lower_title and "eta" not in lower_title and "evisa" not in lower_title:
             st.error(f"🛑 {v_title}")   # Red: Hard Visa Required
        elif any(x in lower_title for x in ["eta", "evisa", "conditional", "varies", "on arrival"]):
             st.warning(f"⚠️ {v_title}") # Yellow: Caution needed
        else:
             st.success(f"✅ {v_title}") # Green: Visa Free
            
        st.caption(f"ℹ️ {v_desc}")
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

    if st.button("🚀 GENERATE ITINERARY", key="btn_generate"):
        st.session_state.show_results = True

# ────────────────────────────────────────────────
# 7. RESULTS 
# ────────────────────────────────────────────────
if st.session_state.show_results:
    current_hub_name = city_options[selected_code]
    st.markdown(
        f"<h2 style='text-align:center; margin: 4rem 0 2rem 0;'>Exploring {current_hub_name}</h2>",
        unsafe_allow_html=True,
    )

    img_c1, img_c2 = st.columns(2)
    city_img_url, airport_img_url = CITY_IMAGES.get(selected_code, CITY_IMAGES["doh"])

    with img_c1:
        st.image(city_img_url, use_container_width=True)
    with img_c2:
        st.image(airport_img_url, use_container_width=True)

    st.markdown("<div style='height: 2.2rem;'></div>", unsafe_allow_html=True)

    vibe_info = analyze_vibe(user_query)
    detected_labels = vibe_info.get("labels", [])

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    r1, r2, r3, r4, r5 = st.columns([1, 1, 1, 1, 1])
    with r1:
        if st.button("😌 More chill", key="ref_chill"):
            st.session_state.refine_mode = "MORE_CHILL"
            st.rerun()
    with r2:
        if st.button("🏛️ More culture", key="ref_culture"):
            st.session_state.refine_mode = "MORE_CULTURE"
            st.rerun()
    with r3:
        if st.button("🛃 Only airside", key="ref_airside"):
            st.session_state.refine_mode = "ONLY_AIRSIDE"
            st.rerun()
    with r4:
        if st.button("💸 Cheaper", key="ref_cheap"):
            st.session_state.refine_mode = "CHEAPER"
            st.rerun()
    with r5:
        if st.button("📸 Max sights", key="ref_sights"):
            st.session_state.refine_mode = "MAX_SIGHTS"
            st.rerun()

    enriched_query = apply_refinement(user_query, st.session_state.refine_mode)

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    with st.spinner("Matching your vibe to the schedule..."):
        ranked_activities = filter_and_rank_activities(
            selected_code, hours, arrival_time, enriched_query, visa_valid
        )

        late = (arrival_time >= 22) or (arrival_time <= 5)
        if late:
            st.warning("Late arrival detected — many city attractions may be closed. Results are prioritised for open-late / 24h options.")

        if late and len(ranked_activities) < 4:
            st.info("Not many safe late-night options at this hub — consider relaxing airside (lounges, rest zones, food courts).")

    if not ranked_activities:
        st.error("No suitable activities match your time / visa constraints. Try a longer layover?")
    else:
        risk_level, risk_reason = compute_plan_risk(ranked_activities, hours, visa_valid)
        st.markdown(
            f"{render_risk_pill(risk_level)} <span class='meta-pill'>🧩 {risk_reason}</span>",
            unsafe_allow_html=True
        )

        narrative = generate_narrative(ranked_activities, hours, user_query, visa_valid, arrival_time)
        st.markdown(f'<div class="ai-box">{narrative}</div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 2.0rem;'></div>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1.6, 1])

        with col_left:
            st.markdown("###  Top Recommendations")

            for item in ranked_activities:
                act = item["activity"]
                score = item["score"]
                risk = item.get("risk_level", "LOW")
                explain = item.get("explain", {}) or {}

                icon = {"FOOD": "🍜", "RELAX": "💆", "SHOPPING": "🛍️"}.get(act.get("type"), "📍")
                risk_tag = {"LOW": "✅", "MED": "⚠️", "HIGH": "🚨"}.get(risk, "ℹ️")

                with st.expander(f"{icon} {act['title']}  —  {score}% Match  {risk_tag}", expanded=(score > 75)):
                    c_desc, c_stats = st.columns([2.5, 1])

                    with c_desc:
                        st.markdown(f"<p>{act.get('description','')}</p>", unsafe_allow_html=True)
                        if "founders_tip" in act:
                            st.info(f"💡 {act['founders_tip']}")

                        reasons = explain.get("reasons", [])
                        tradeoffs = explain.get("tradeoffs", [])

                        if reasons:
                            st.markdown("**Why this matched**")
                            for r in reasons:
                                st.markdown(f"- ✅ {r}")

                        if tradeoffs:
                            st.markdown("**Tradeoffs**")
                            for t in tradeoffs:
                                st.markdown(f"- ⚠️ {t}")

                    with c_stats:
                        zone_tag = "🛃 AIRSIDE" if act["location"]["zone"] == "AIRSIDE" else "🏙️ LANDSIDE"
                        cost_tag = f"💰 {act.get('cost_tier', 'MEDIUM')}"
                        time_tag = f"⏱️ {act['time_constraints']['min_duration_hours']}h+"

                        st.markdown(
                            f"""
<div style="display: flex; flex-direction: column; gap: 6px; align-items: flex-end;">
    <span class="stat-pill" style="border-right-color: #00D4FF;">{zone_tag}</span>
    <span class="stat-pill" style="border-right-color: #FFD700;">{cost_tag}</span>
    <span class="stat-pill" style="border-right-color: #FF4B4B;">{time_tag}</span>
</div>
""",
                            unsafe_allow_html=True,
                        )

        with col_right:
            st.markdown("###  Map View")
            map_data = [
                {"lat": a["activity"]["location"]["lat"], "lon": a["activity"]["location"]["lon"]}
                for a in ranked_activities
                if a["activity"]["location"].get("lat", 0) != 0
            ]
            if map_data:
                st.map(pd.DataFrame(map_data), zoom=10)
            else:
                st.info("Map coordinates not available for this hub.")

        st.markdown("<div style='height: 3.0rem;'></div>", unsafe_allow_html=True)

        st.markdown("### ⏳ Suggested Timeframe")
        timeline_fig = create_timeline(ranked_activities, arrival_time, hours)
        if timeline_fig:
            st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
            st.plotly_chart(timeline_fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
