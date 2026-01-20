import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

def create_timeline(activities, arrival_hour, total_layover_hours):
    """
    A Smart Scheduler that strictly fits activities into the available time window.
    It accounts for Arrival Logistics, Travel Time (Teleportation prevention), and Departure Buffer.
    """
    if not activities:
        return None

    # --- 1. SETUP THE CLOCK ---
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Arrival Time
    start_time = base_date + timedelta(hours=arrival_hour)
    
    # Hard Stop (When you MUST be back at the gate)
    # We reserve 2 hours for security/boarding
    departure_time = start_time + timedelta(hours=total_layover_hours)
    hard_stop_time = departure_time - timedelta(hours=2) 

    schedule_data = []
    current_clock = start_time
    
    # --- 2. ARRIVAL LOGISTICS (immigration/customs) ---
    # If going Landside, this takes longer (1.5h). If Airside, shorter (45m).
    first_activity_zone = activities[0]['activity']['location']['zone']
    immigration_duration = 1.5 if first_activity_zone == 'LANDSIDE' else 0.75
    
    schedule_data.append(dict(
        Task="Arrival & Logistics 🛬", 
        Start=current_clock, 
        Finish=current_clock + timedelta(hours=immigration_duration), 
        Type="Logistics",
        Color="Gray"
    ))
    current_clock += timedelta(hours=immigration_duration)

    # --- 3. TRANSIT TO CITY (Preventing Teleportation) ---
    # If the first activity is in the city, we need travel time.
    if first_activity_zone == 'LANDSIDE':
        transit_time = 1.0 # Approx 1 hour to city center
        schedule_data.append(dict(
            Task="Transit to City 🚆", 
            Start=current_clock, 
            Finish=current_clock + timedelta(hours=transit_time), 
            Type="Logistics",
            Color="Gray"
        ))
        current_clock += timedelta(hours=transit_time)

    # --- 4. THE GREEDY SCHEDULER (Fixing the Time Warp) ---
    # We loop through recommendations and only add them if they fit.
    
    for item in activities: 
        act = item['activity']
        duration = act['time_constraints']['min_duration_hours']
        
        # Predicted finish time for this activity
        potential_finish = current_clock + timedelta(hours=duration)
        
        # TRANSIT BACK CHECK
        # If we are in the city, we need to reserve 1 hour to get back BEFORE the hard stop.
        buffer_needed_to_return = 1.0 if act['location']['zone'] == 'LANDSIDE' else 0
        
        # Does it fit?
        if potential_finish + timedelta(hours=buffer_needed_to_return) <= hard_stop_time:
            # IT FITS! Add it.
            schedule_data.append(dict(
                Task=act['title'], 
                Start=current_clock, 
                Finish=potential_finish, 
                Type=act['type'],
                Color="Red" 
            ))
            current_clock = potential_finish
        else:
            # IT DOESN'T FIT. Skip it. 
            # (We don't break, because a smaller activity further down the list might fit!)
            continue

    # --- 5. TRANSIT BACK (If needed) ---
    if first_activity_zone == 'LANDSIDE':
        schedule_data.append(dict(
            Task="Return Transit 🚆", 
            Start=current_clock, 
            Finish=current_clock + timedelta(hours=1.0), 
            Type="Logistics",
            Color="Gray"
        ))
        current_clock += timedelta(hours=1.0)

    # --- 6. DEPARTURE PREP ---
    schedule_data.append(dict(
        Task="Security & Boarding 🛫", 
        Start=current_clock, 
        Finish=departure_time, # Fill whatever gap is left until flight
        Type="Logistics",
        Color="Gray"
    ))

    df = pd.DataFrame(schedule_data)

    # --- GENERATE CHART ---
    fig = px.timeline(
        df, x_start="Start", x_end="Finish", y="Task", color="Type", height=350
    )
    
    # Styling (Same Glass UI as before)
    fig.update_layout(
        paper_bgcolor='rgba(255, 255, 255, 0.05)', 
        plot_bgcolor='rgba(255, 255, 255, 0.05)',
        font=dict(color="#E0E0E0", size=14, family="Outfit"),
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white"))
    )
    fig.update_xaxes(tickformat="%H:%M", gridcolor='rgba(255, 255, 255, 0.1)')
    fig.update_yaxes(autorange="reversed", gridcolor='rgba(255, 255, 255, 0.1)')
    
    return fig