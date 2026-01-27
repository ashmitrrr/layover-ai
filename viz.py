import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

def create_timeline(activities, arrival_hour, total_layover_hours):
    """
    Smart Scheduler that strictly fits activities into the available time window.
    Accounts for Arrival Logistics, Travel Time, and Departure Buffer.
    """
    if not activities:
        return None

    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = base_date + timedelta(hours=arrival_hour)

    departure_time = start_time + timedelta(hours=total_layover_hours)
    hard_stop_time = departure_time - timedelta(hours=2)  # reserve 2h buffer

    schedule_data = []
    current_clock = start_time

    # Determine if we will go landside at all (based on top recommendations)
    top_zone_list = [it["activity"]["location"]["zone"] for it in activities[:4]]
    any_landside = any(z == "LANDSIDE" for z in top_zone_list)

    # Arrival logistics
    immigration_duration = 1.5 if any_landside else 0.75
    schedule_data.append(dict(
        Task="Arrival & Logistics 🛬",
        Start=current_clock,
        Finish=current_clock + timedelta(hours=immigration_duration),
        Type="Logistics",
    ))
    current_clock += timedelta(hours=immigration_duration)

    # Transit to city (only if we are doing landside)
    if any_landside:
        transit_time = 1.0
        schedule_data.append(dict(
            Task="Transit to City 🚆",
            Start=current_clock,
            Finish=current_clock + timedelta(hours=transit_time),
            Type="Logistics",
        ))
        current_clock += timedelta(hours=transit_time)

    # Greedy schedule
    for item in activities:
        act = item["activity"]
        duration = act["time_constraints"]["min_duration_hours"]
        potential_finish = current_clock + timedelta(hours=duration)

        # If any landside included, reserve return transit before hard stop
        buffer_needed_to_return = 1.0 if any_landside else 0.0

        if potential_finish + timedelta(hours=buffer_needed_to_return) <= hard_stop_time:
            schedule_data.append(dict(
                Task=act["title"],
                Start=current_clock,
                Finish=potential_finish,
                Type=act.get("type", "OTHER"),
            ))
            current_clock = potential_finish
        else:
            continue

    # Return transit
    if any_landside:
        schedule_data.append(dict(
            Task="Return Transit 🚆",
            Start=current_clock,
            Finish=current_clock + timedelta(hours=1.0),
            Type="Logistics",
        ))
        current_clock += timedelta(hours=1.0)

    # Boarding
    schedule_data.append(dict(
        Task="Security & Boarding 🛫",
        Start=current_clock,
        Finish=departure_time,
        Type="Logistics",
    ))

    df = pd.DataFrame(schedule_data)

    fig = px.timeline(
        df, x_start="Start", x_end="Finish", y="Task", color="Type", height=350
    )
    fig.update_layout(
        paper_bgcolor="rgba(255, 255, 255, 0.05)",
        plot_bgcolor="rgba(255, 255, 255, 0.05)",
        font=dict(color="#E0E0E0", size=14, family="Outfit"),
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color="white")
        )
    )
    fig.update_xaxes(tickformat="%H:%M", gridcolor="rgba(255, 255, 255, 0.1)")
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(255, 255, 255, 0.1)")
    return fig

# v3 update 

def render_timeline_v3(blocks):
    if not blocks:
        return None

    rows = []
    start = 0

    for b in blocks:
        minutes = int(b.get("minutes", 0))
        label = b.get("label", "Block")
        end = start + max(0, minutes)

        rows.append({
            "Task": label,
            "Start": start,
            "Finish": end,
            "Minutes": minutes
        })

        start = end

    df = pd.DataFrame(rows)

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        hover_data=["Minutes"]
    )

    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Minutes from arrival")
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))

    return fig
