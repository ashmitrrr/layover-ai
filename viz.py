import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def create_timeline(activities, arrival_hour, total_layover_hours):
    """
    V3 SMART SCHEDULER:
    - Driven by 'logic.py' calculation engine (Single Source of Truth).
    - Visualizes hard deadlines (Latest Return Time).
    - Explicitly shows Logistics vs. Fun vs. Buffer.
    """
    if not activities:
        return None

    # 1. SETUP CLOCK & CANVAS
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    arrival_time = base_date + timedelta(hours=arrival_hour)
    departure_time = arrival_time + timedelta(hours=total_layover_hours)
    
    # 2. EXTRACT INTELLIGENCE FROM ENGINE (The "Brain" Link)
    # We look at the first recommended activity to get the route's logistics metadata
    top_pick = activities[0]
    meta = top_pick.get("explain", {}).get("v3_meta", {})
    
    # Fallback defaults if engine data is missing (Safety Net)
    imm_mins = meta.get("immigration_mins", 60)
    transit_mins_one_way = meta.get("transit_mins", 60) // 2
    sec_mins = meta.get("security_mins", 60)
    
    # Check if we are even going Landside
    top_zone = top_pick["activity"]["location"]["zone"]
    is_landside = (top_zone == "LANDSIDE")

    # 3. BUILD THE SCHEDULE BLOCKS
    schedule = []
    cursor = arrival_time

    # --- BLOCK A: ARRIVAL & IMMIGRATION ---
    if is_landside:
        schedule.append(dict(
            Task="🛂 Immigration & Customs",
            Start=cursor,
            Finish=cursor + timedelta(minutes=imm_mins),
            Type="Logistics",
            Color="#7f8c8d" # Grey
        ))
        cursor += timedelta(minutes=imm_mins)
        
        # --- BLOCK B: TRANSIT TO CITY ---
        schedule.append(dict(
            Task="🚆 Transit to City",
            Start=cursor,
            Finish=cursor + timedelta(minutes=transit_mins_one_way),
            Type="Logistics",
            Color="#3498db" # Blue
        ))
        cursor += timedelta(minutes=transit_mins_one_way)

    # --- BLOCK C: ACTIVITIES (The Fun Stuff) ---
    # Calculate the "Hard Return Time" (When you MUST start heading back)
    # Formula: Departure - (Security + Transit Back + 15m Boarding Buffer)
    transit_back_mins = transit_mins_one_way if is_landside else 0
    safe_return_time = departure_time - timedelta(minutes=sec_mins + transit_back_mins + 15)
    
    for item in activities[:3]: # Only map top 3 to keep it readable
        act = item["activity"]
        duration_mins = act["time_constraints"]["min_duration_hours"] * 60
        
        # Will this activity fit before we have to leave?
        if cursor + timedelta(minutes=duration_mins) <= safe_return_time:
            schedule.append(dict(
                Task=f"📍 {act['title']}",
                Start=cursor,
                Finish=cursor + timedelta(minutes=duration_mins),
                Type="Activity",
                Color="#00d4ff" # Cyan/Neon
            ))
            cursor += timedelta(minutes=duration_mins)
        else:
            # If it doesn't fit, we stop scheduling activities
            break

    # --- BLOCK D: BUFFER / FREE TIME ---
    # Any time left between now and the "Must Leave" time is pure safety buffer
    if cursor < safe_return_time:
        schedule.append(dict(
            Task="☕ Safe Buffer / Free Time",
            Start=cursor,
            Finish=safe_return_time,
            Type="Buffer",
            Color="#2ecc71" # Green
        ))
        cursor = safe_return_time

    # --- BLOCK E: RETURN TRANSIT ---
    if is_landside:
        schedule.append(dict(
            Task="🚆 Return Transit",
            Start=cursor,
            Finish=cursor + timedelta(minutes=transit_mins_one_way),
            Type="Logistics",
            Color="#3498db"
        ))
        cursor += timedelta(minutes=transit_mins_one_way)

    # --- BLOCK F: SECURITY & BOARDING ---
    schedule.append(dict(
        Task="🛡️ Security & Gate",
        Start=cursor,
        Finish=departure_time,
        Type="Logistics",
        Color="#e74c3c" # Red/Warning color for "Don't Miss This"
    ))

    # 4. RENDER WITH PLOTLY
    df = pd.DataFrame(schedule)
    
    fig = px.timeline(
        df, 
        x_start="Start", 
        x_end="Finish", 
        y="Task", 
        color="Type",
        color_discrete_map={
            "Logistics": "#7f8c8d",
            "Activity": "#00d4ff",
            "Buffer": "#2ecc71"
        },
        height=350
    )

    # 5. VISUAL INTELLIGENCE (The "Smart" Cues)
    
    # Add "MUST RETURN" Vertical Line
    fig.add_vline(
        x=safe_return_time.timestamp() * 1000, # Plotly needs ms timestamp for lines
        line_width=2, 
        line_dash="dash", 
        line_color="#ff4b4b",
        annotation_text="🚨 MUST RETURN", 
        annotation_position="top right",
        annotation_font_color="#ff4b4b"
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255, 255, 255, 0.05)",
        font=dict(color="#E0E0E0", size=13, family="Outfit"),
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
        hovermode="x"
    )
    
    fig.update_xaxes(
        tickformat="%H:%M", 
        gridcolor="rgba(255, 255, 255, 0.1)",
        title=None
    )
    
    fig.update_yaxes(
        autorange="reversed", 
        gridcolor="rgba(255, 255, 255, 0.1)",
        title=None
    )

    return fig