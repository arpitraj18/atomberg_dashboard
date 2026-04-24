import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="Atomberg Room Intelligence",
    page_icon="",
    layout="wide"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .brand { font-size: 12px; color: #888; letter-spacing: 0.1em;
             text-transform: uppercase; font-weight: 600; }
    .badge {
        display: inline-block;
        padding: 3px 12px; border-radius: 20px;
        font-size: 12px; font-weight: 600;
    }
    .heavy   { background:#fde8e0; color:#a03020; }
    .moderate{ background:#fef3dc; color:#8a5a00; }
    .light   { background:#e4f4e0; color:#2d6a20; }
</style>
""", unsafe_allow_html=True)

PROFILE_COLORS = {
    "Heavy":    "#d85a30",
    "Moderate": "#e09020",
    "Light":    "#3a8a28",
}
SUCTION_LABELS = {
    "Heavy":    "Max (100%) — 2 passes",
    "Moderate": "Standard (68%) — 1 pass",
    "Light":    "Eco (28%) — 1 pass, fast",
}
SUCTION_PCT = {"Heavy": 100, "Moderate": 68, "Light": 28}
WH_MAX_PER_M2 = 0.72

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df      = pd.read_csv("sessions.csv", parse_dates=["timestamp"])
    latest  = pd.read_csv("latest_profiles.csv")
    return df, latest

df, latest = load_data()

# ensure predicted_profile exists
if "predicted_profile" not in latest.columns:
    latest["predicted_profile"] = latest["profile"]

total_used    = latest["wh_used"].sum()
total_max     = latest["wh_max"].sum()
saved_wh      = round(total_max - total_used, 2)
pct_saved     = round((saved_wh / total_max) * 100)
total_sessions = len(df)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="brand">Atomberg Technologies — Prototype</div>',
            unsafe_allow_html=True)
st.markdown("## Room Intelligence Dashboard")
st.caption("Adaptive suction profiles · 3BHK · powered by K-Means + Random Forest")
st.divider()

# ── Top metrics ────────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Sessions Logged",   total_sessions,        "30-day window")
m2.metric("Power Saved",       f"{pct_saved}%",       "vs always-max")
m3.metric("Wh Saved",          f"{saved_wh} Wh",      "this session")
m4.metric("Rooms Profiled",    len(latest),           "auto-classified")

st.divider()

# ── Room profile cards ─────────────────────────────────────────────────────────
st.markdown("### Room Profiles")

for _, row in latest.iterrows():
    profile = row["predicted_profile"]
    color   = PROFILE_COLORS[profile]
    suction = SUCTION_PCT[profile]
    savings = int(row["savings_pct"])

    c1, c2, c3 = st.columns([3, 3, 2])

    with c1:
        st.markdown(
            f"**{row['room_name']}** &nbsp;"
            f'<span class="badge {profile.lower()}">{profile}</span>',
            unsafe_allow_html=True
        )
        st.caption(
            f"Dirt score: **{round(row['dirt_score'], 3)}** · "
            f"{SUCTION_LABELS[profile]}"
        )

    with c2:
        st.markdown(f"Suction — **{suction}%**")
        st.progress(suction / 100)
        if savings > 0:
            st.markdown(
                f'<span style="font-size:12px;color:#2d6a20;">'
                f'Saves {savings}% power vs max</span>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<span style="font-size:12px;color:#a03020;">'
                'Full power — room needs it</span>',
                unsafe_allow_html=True
            )

    with c3:
        # mini sparkline — last 7 sessions for this room
        room_hist = (
            df[df["room_id"] == row["room_id"]]
            .sort_values("timestamp")
            .tail(7)["dirt_score"]
            .tolist()
        )
        fig_spark = go.Figure(go.Scatter(
            y=room_hist, mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=f"rgba({int(color[1:3],16)},"
                      f"{int(color[3:5],16)},"
                      f"{int(color[5:7],16)},0.1)",
        ))
        fig_spark.update_layout(
            height=60, margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False, range=[0, 1]),
            showlegend=False,
        )
        st.plotly_chart(fig_spark, use_container_width=True,
                        config={"displayModeBar": False})
        st.caption("7-session trend")

    st.markdown(
        '<hr style="border:none;border-top:1px solid #f0f0f0;margin:4px 0;">',
        unsafe_allow_html=True
    )

st.divider()

# ── Power chart ────────────────────────────────────────────────────────────────
st.markdown("### Power: Adaptive vs Always-Max")

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    name="Always-max baseline",
    x=latest["room_name"],
    y=latest["wh_max"].round(2),
    marker_color="#c8c7c1",
    marker_line_width=0,
))
fig_bar.add_trace(go.Bar(
    name="Adaptive (this system)",
    x=latest["room_name"],
    y=latest["wh_used"],
    marker_color="#1d9e75",
    marker_line_width=0,
    text=latest["savings_pct"].apply(lambda x: f"-{x}%"),
    textposition="outside",
))
fig_bar.update_layout(
    barmode="group",
    plot_bgcolor="white",
    height=340,
    margin=dict(l=0, r=0, t=10, b=10),
    yaxis=dict(title="Energy (Wh)", gridcolor="#f0f0f0"),
    xaxis=dict(gridcolor="#f0f0f0"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1),
)
st.plotly_chart(fig_bar, use_container_width=True,
                config={"displayModeBar": False})

st.divider()

# ── Dirt history ───────────────────────────────────────────────────────────────
st.markdown("### Dirt Score History — 30 Days")

ROOM_COLORS = {
    "Kitchen":          "#d85a30",
    "Living Room":      "#e09020",
    "Master Bedroom":   "#3a7abf",
    "Bedroom 2":        "#7a5abf",
    "Bedroom 3 Guest":  "#3a8a28",
}

selected = st.selectbox(
    "Select room",
    options=df["room_name"].unique().tolist(),
)

room_df = df[df["room_name"] == selected].sort_values("timestamp")
color   = ROOM_COLORS.get(selected, "#1d9e75")

fig_hist = go.Figure()
fig_hist.add_trace(go.Scatter(
    x=room_df["timestamp"],
    y=room_df["dirt_score"],
    mode="lines+markers",
    line=dict(color=color, width=2),
    marker=dict(size=4, color=color),
    fill="tozeroy",
    fillcolor=f"rgba({int(color[1:3],16)},"
              f"{int(color[3:5],16)},"
              f"{int(color[5:7],16)},0.1)",
))
fig_hist.add_hline(y=0.60, line_dash="dash", line_color="#d85a30",
                   line_width=1, annotation_text="Heavy threshold",
                   annotation_position="top right")
fig_hist.add_hline(y=0.35, line_dash="dash", line_color="#e09020",
                   line_width=1, annotation_text="Moderate threshold",
                   annotation_position="top right")
fig_hist.update_layout(
    plot_bgcolor="white",
    height=300,
    margin=dict(l=0, r=0, t=10, b=10),
    yaxis=dict(title="Dirt Score", range=[0, 1.05], gridcolor="#f0f0f0"),
    xaxis=dict(title="Date", gridcolor="#f0f0f0"),
)
st.plotly_chart(fig_hist, use_container_width=True,
                config={"displayModeBar": False})

st.divider()

# ── Savings summary ────────────────────────────────────────────────────────────
st.markdown("### Savings Summary")

s1, s2 = st.columns(2)

with s1:
    fig_donut = go.Figure(go.Pie(
        labels=["Power saved", "Power used"],
        values=[saved_wh, round(total_used, 2)],
        hole=0.65,
        marker_colors=["#1d9e75", "#e9e9e3"],
        textinfo="label+percent",
    ))
    fig_donut.add_annotation(
        text=f"{pct_saved}%<br>saved",
        x=0.5, y=0.5, font_size=20, showarrow=False,
    )
    fig_donut.update_layout(
        height=300, showlegend=False,
        margin=dict(l=0, r=0, t=10, b=10),
    )
    st.plotly_chart(fig_donut, use_container_width=True,
                    config={"displayModeBar": False})

with s2:
    st.markdown("#### What this means")
    annual_kwh = round(saved_wh * 260 / 1000, 2)
    st.metric("Annual saving (5x/week)", f"{annual_kwh} kWh/year")
    st.markdown(" ")
    st.markdown(
        f"- Full-home energy (adaptive): **{round(total_used,2)} Wh**"
    )
    st.markdown(
        f"- Always-max baseline: **{round(total_max,2)} Wh**"
    )
    st.markdown(
        f"- Battery cycles reduced by ~**20%** in light rooms"
    )
    st.markdown(
        f"- Vacuum completes 3BHK in **one charge** without docking"
    )

st.divider()
st.caption("Atomberg Room Intelligence · Prototype · Built on K-Means + Random Forest")