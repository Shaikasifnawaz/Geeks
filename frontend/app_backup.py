"""
Football Management Dashboard
-----------------------------

Fully self-contained Streamlit app that showcases a professional football
management dashboard with realistic sample data, interactive tables, and
card-driven insights. Run with: `streamlit run app.py`
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import os
import time

import numpy as np
import pandas as pd
import streamlit as st
import requests


# -----------------------------------------------------------------------------
# API Client Configuration
# -----------------------------------------------------------------------------
API_BASE_URL = os.getenv('API_BASE_URL', 'http://127.0.0.1:5001')
LLM_API_BASE_URL = os.getenv('LLM_API_BASE_URL', 'http://127.0.0.1:5000')

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_api_data(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """Fetch data from backend API with loading state."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timeout. Backend is taking too long to respond.")
        return None
    except requests.exceptions.RequestException as e:
        if "404" not in str(e) and "500" not in str(e):
            st.error(f"❌ API Error: {e}")
        return None

def query_llm_api(question: str) -> Optional[Dict]:
    """Query the LLM API with a natural language question."""
    try:
        url = f"{LLM_API_BASE_URL}/query"
        payload = {
            "question": question,
            "model": "gemini-2.5-flash",
            "max_results": 100
        }
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to LLM API. Please ensure the LLM service is running on port 5000.")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ LLM API request timeout. The query might be taking too long to process.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ LLM API Error: {e}")
        return None

def show_loading_spinner(message: str = "Loading data..."):
    """Display loading spinner."""
    return st.spinner(message)

def show_success_message(message: str):
    """Display success message."""
    st.success(f"✅ {message}")

def show_info_message(message: str):
    """Display info message."""
    st.info(f"ℹ️ {message}")

def show_warning_message(message: str):
    """Display warning message."""
    st.warning(f"⚠️ {message}")

def show_error_message(message: str):
    """Display error message."""
    st.error(f"❌ {message}")

def show_no_data_alert(data_type: str = "data"):
    """Display styled no data found alert."""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        ">
            <div style="font-size: 3rem; margin-bottom: 10px;">📭</div>
            <h3 style="margin: 10px 0; color: white;">No {data_type} Found</h3>
            <p style="margin: 5px 0; opacity: 0.9;">We couldn't find any {data_type} in the database.</p>
            <p style="margin: 5px 0; font-size: 0.9rem; opacity: 0.8;">Please ensure the backend API is running and data is loaded.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

@st.cache_data(ttl=300)
def get_teams_data() -> pd.DataFrame:
    """Get teams data from API."""
    with show_loading_spinner("Loading teams data..."):
        data = fetch_api_data('/api/teams')
        if data and 'teams' in data:
            return pd.DataFrame(data['teams'])
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_players_data(team_id: Optional[str] = None) -> pd.DataFrame:
    """Get players data from API."""
    with show_loading_spinner("Loading players data..."):
        params = {'team_id': team_id} if team_id else None
        data = fetch_api_data('/api/players', params=params)
        if data and 'players' in data:
            return pd.DataFrame(data['players'])
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_rankings_data(week: Optional[int] = None) -> pd.DataFrame:
    """Get rankings data from API."""
    with show_loading_spinner("Loading rankings data..."):
        params = {'week': week} if week else None
        data = fetch_api_data('/api/rankings', params=params)
        if data and 'rankings' in data:
            return pd.DataFrame(data['rankings'])
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_seasons_data() -> pd.DataFrame:
    """Get seasons data from API."""
    with show_loading_spinner("Loading seasons data..."):
        data = fetch_api_data('/api/seasons')
        if data and 'seasons' in data:
            return pd.DataFrame(data['seasons'])
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_player_statistics_data(player_id: Optional[str] = None, team_id: Optional[str] = None) -> pd.DataFrame:
    """Get player statistics from API."""
    with show_loading_spinner("Loading player statistics..."):
        params = {}
        if player_id:
            params['player_id'] = player_id
        if team_id:
            params['team_id'] = team_id
        data = fetch_api_data('/api/player-statistics', params=params if params else None)
        if data and 'statistics' in data:
            return pd.DataFrame(data['statistics'])
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_venues_data() -> pd.DataFrame:
    """Get venues data from API."""
    with show_loading_spinner("Loading venues data..."):
        data = fetch_api_data('/api/venues')
        if data and 'venues' in data:
            return pd.DataFrame(data['venues'])
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_coaches_data(team_id: Optional[str] = None) -> pd.DataFrame:
    """Get coaches data from API."""
    with show_loading_spinner("Loading coaches data..."):
        params = {'team_id': team_id} if team_id else None
        data = fetch_api_data('/api/coaches', params=params)
        if data and 'coaches' in data:
            return pd.DataFrame(data['coaches'])
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_conferences_data() -> pd.DataFrame:
    """Get conferences data from API."""
    with show_loading_spinner("Loading conferences data..."):
        data = fetch_api_data('/api/conferences')
        if data and 'conferences' in data:
            return pd.DataFrame(data['conferences'])
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_summary_stats() -> Dict:
    """Get summary statistics from API."""
    with show_loading_spinner("Loading summary statistics..."):
        data = fetch_api_data('/api/stats/summary')
        return data if data else {}


def render_sidebar_nav() -> str:
    """Render sidebar with interactive routing."""

    if "active_panel" not in st.session_state:
        st.session_state.active_panel = SIDEBAR_ITEMS[0][0]
    if "previous_panel" not in st.session_state:
        st.session_state.previous_panel = SIDEBAR_ITEMS[0][0]

    st.sidebar.markdown("<h2 style='color:#4F5F90;margin-bottom:1rem;'>DASHBOARD</h2>", unsafe_allow_html=True)
    current = st.session_state.active_panel
    for panel_id, icon, label in SIDEBAR_ITEMS:
        clicked = st.sidebar.button(
            f"{icon}  {label}",
            use_container_width=True,
            key=f"sidebar-{panel_id}",
        )
        if clicked:
            current = panel_id
            # Clear search when switching panels
            if current != st.session_state.previous_panel:
                if "global_search" in st.session_state:
                    st.session_state.global_search = ""
                st.session_state.previous_panel = current

    st.session_state.active_panel = current
    return current
def render_player_lab(players: pd.DataFrame):
    """Display player laboratory metrics."""

    st.markdown("### Player Lab")
    top_scorer = players.sort_values("Goals", ascending=False).iloc[0]
    best_creator = players.sort_values("Assists", ascending=False).iloc[0]
    cols = st.columns(3)
    with cols[0]:
        metric_card("Top Scorer", f"{top_scorer['Player']}", f"{top_scorer['Goals']} goals", accent="#F1A208")
    with cols[1]:
        metric_card("Chief Creator", f"{best_creator['Player']}", f"{best_creator['Assists']} assists", accent="#59A5D8")
    with cols[2]:
        metric_card("Avg Rating", round(players["Rating"].mean(), 2), "Squad-wide", accent="#4F6AA3")
    st.dataframe(
        players.sort_values("Rating", ascending=False),
        use_container_width=True,
    )


def render_fixture_desk(fixtures: pd.DataFrame):
    """Upcoming fixture focus."""

    st.markdown("### Fixture Desk")
    st.dataframe(
        fixtures,
        use_container_width=True,
        column_config={
            "Date": st.column_config.DateColumn(format="MMM DD, YYYY"),
            "Opponent": st.column_config.TextColumn("Opponent"),
            "Venue": st.column_config.TextColumn("Venue"),
            "Importance": st.column_config.TextColumn("Importance"),
        },
    )


def render_analytics_lab(players: pd.DataFrame, matches: pd.DataFrame):
    """Analytics hub."""

    st.markdown("### Analytics Lab")
    st.write("Goals per match:", round(matches["Goals For"].mean(), 2))
    st.write("Shots on target per match:", round(matches["Shots on Target"].mean(), 1))
    st.write("Average rating:", round(players["Rating"].mean(), 2))


def render_scouting_feed(matches: pd.DataFrame):
    """Simple scouting feed using match data."""

    st.markdown("### Scouting Feed")
    st.write(matches[["Opponent", "Result", "Goals For", "Goals Against"]].tail(5))


def render_medical_room(players: pd.DataFrame):
    """Medical room summary."""

    st.markdown("### Medical Room")
    medical = players[players["Status"] != "Fit"]
    if medical.empty:
        st.success("All players are match ready.")
    else:
        st.dataframe(medical[["Player", "Position", "Status"]])


def render_settings_panel():
    """Placeholder settings panel."""

    st.markdown("### Controls")
    st.info("Use this panel to configure dashboard preferences.")


def render_news_and_fixtures(matches: pd.DataFrame, fixtures: pd.DataFrame):
    """Bottom cards for recent results and upcoming fixtures."""

    news_col, fixture_col = st.columns([2, 1.2], gap="large")
    with news_col:
        st.markdown('<div class="dashboard-card"><h4>Recent Football Notes</h4>', unsafe_allow_html=True)
        for _, row in matches.tail(3).iterrows():
            st.markdown(
                f"""
                <div class="news-entry">
                    <strong>{row['Opponent']}</strong><br/>
                    <span>{row['Date'].strftime('%b %d, %Y')} • {row['Venue']} • {row['Result']} ({row['Goals For']}-{row['Goals Against']})</span><br/>
                    <span>Possession {row['Possession %']}% · {row['Shots on Target']} shots on target</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with fixture_col:
        st.markdown('<div class="dashboard-card"><h4>Upcoming Fixtures</h4>', unsafe_allow_html=True)
        for _, row in fixtures.head(4).iterrows():
            st.markdown(
                f"""
                <div class="news-entry fixtures">
                    <strong>{row['Opponent']}</strong>
                    <span>{row['Date'].strftime('%b %d, %Y')} • {row['Venue']}</span><br/>
                    <span>Importance: {row['Importance']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Page configuration and reusable styles
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Football Management Dashboard",
    page_icon="⚽",
    layout="wide",
)

THEME_COLORS = {
    "primary": "#4F6AA3",
    "secondary": "#F1A208",
    "accent": "#59A5D8",
    "light": "#F4F6FB",
    "danger": "#E63946",
}

st.markdown(
    f"""
    <style>
        html, body {{
            background-color: {THEME_COLORS["light"]};
            overflow-y: auto;
        }}
        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 1400px;
        }}
        .main {{
            background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(244,246,251,1));
        }}
        
        /* Section spacing */
        .section-spacing {{
            margin-top: 2rem;
            margin-bottom: 2rem;
        }}
        
        /* Card improvements */
        .metric-card {{
            border-radius: 16px;
            padding: 1.5rem;
            background: white;
            box-shadow: 0 4px 20px rgba(79, 106, 163, 0.1);
            border-left: 5px solid {THEME_COLORS["primary"]};
            margin-bottom: 1rem;
            min-height: 120px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(79, 106, 163, 0.15);
        }}
        .metric-title {{
            font-size: 0.85rem;
            color: #7a83a7;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05rem;
            font-weight: 600;
        }}
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {THEME_COLORS["primary"]};
            line-height: 1.2;
        }}
        .subtext {{
            font-size: 0.8rem;
            color: #8c94b8;
            margin-top: 0.3rem;
        }}
        
        /* Dashboard cards */
        .dashboard-card {{
            background: white;
            border-radius: 16px;
            padding: 1.8rem;
            box-shadow: 0 4px 20px rgba(79, 106, 163, 0.12);
            margin-bottom: 1.5rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .dashboard-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(79, 106, 163, 0.18);
        }}
        .dashboard-card h4 {{
            margin: 0 0 1rem 0;
            color: #4F5F90;
            font-size: 1.25rem;
            font-weight: 600;
        }}
        .dashboard-card p {{
            color: #6c757d;
            margin-bottom: 0.5rem;
            line-height: 1.6;
        }}
        
        /* Header improvements */
        .dashboard-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #E6E8F4;
        }}
        .breadcrumb {{
            color: #9FA8C8;
            font-size: 0.85rem;
            font-weight: 500;
        }}
        .header-title {{
            font-size: 2rem;
            color: #4F5F90;
            margin-top: 0.3rem;
            font-weight: 700;
        }}
        
        /* Search pill */
        .search-pill {{
            background: white;
            border-radius: 999px;
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.5rem 1.2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: box-shadow 0.2s;
        }}
        .search-pill:hover {{
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }}
        .search-pill input {{
            border: none;
            outline: none;
            background: transparent;
            width: 250px;
            font-size: 0.95rem;
        }}
        
        /* Sidebar improvements */
        div[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #1F2A44 0%, #2A3B5C 100%);
            color: white;
            padding-top: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }}
        div[data-testid="stSidebar"] button {{
            border-radius: 12px;
            border: 1px solid transparent;
            background: rgba(255,255,255,0.08);
            color: rgba(255,255,255,0.95);
            font-weight: 500;
            margin-bottom: 0.5rem;
            padding: 0.8rem 1rem;
            transition: all 0.2s;
        }}
        div[data-testid="stSidebar"] button:hover {{
            background: rgba(255,255,255,0.15);
            border-color: rgba(255,255,255,0.3);
            transform: translateX(4px);
        }}
        
        /* Table improvements */
        .dataframe {{
            border-radius: 12px;
            overflow: hidden;
        }}
        
        /* News and fixtures */
        .news-entry {{
            padding: 1rem 1.2rem;
            margin-bottom: 1rem;
            border-left: 5px solid #4F5F90;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(79,106,163,.08);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .news-entry:hover {{
            transform: translateX(4px);
            box-shadow: 0 4px 15px rgba(79,106,163,.12);
        }}
        .news-entry.fixtures {{
            border-left: 5px solid #F1A208;
        }}
        .news-entry strong {{
            color: #4F6AA3;
            font-size: 1.05rem;
        }}
        .news-entry span {{
            color: #7a83a7;
            font-size: 0.85rem;
        }}
        
        /* Loading spinner customization */
        .stSpinner > div {{
            border-top-color: {THEME_COLORS["primary"]} !important;
        }}
        
        /* Success/Error messages */
        .stSuccess, .stError, .stWarning, .stInfo {{
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin: 1rem 0;
        }}
        
        /* Chat widget */
        .chat-widget {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999;
            font-family: "Segoe UI", sans-serif;
        }}
        .chat-button {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, {THEME_COLORS["secondary"]} 0%, #FF9A3C 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
            font-size: 1.5rem;
            transition: transform 0.2s;
        }}
        .chat-button:hover {{
            transform: scale(1.1);
        }}
        .chat-window {{
            position: absolute;
            bottom: 75px;
            right: 0;
            width: 340px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 12px 40px rgba(15, 76, 129, 0.3);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 400px;
        }}
        .chat-header {{
            padding: 1rem 1.2rem;
            background: {THEME_COLORS["primary"]};
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .chat-body {{
            flex: 1;
            max-height: calc(100% - 100px);
            padding: 1rem;
            background: {THEME_COLORS["light"]};
            overflow-y: auto;
        }}
        .chat-message {{
            margin-bottom: 0.8rem;
        }}
        .chat-input {{
            padding: 0.8rem;
            background: white;
            border-top: 1px solid #e0e0e0;
        }}
        .chat-input input {{
            width: calc(100% - 60px);
            padding: 0.6rem;
            border: 1px solid #ddd;
            border-radius: 18px;
            outline: none;
        }}
        .chat-input button {{
            width: 50px;
            padding: 0.6rem;
            background: {THEME_COLORS["primary"]};
            color: white;
            border: none;
            border-radius: 18px;
            cursor: pointer;
            margin-left: 5px;
        }}
        .close-chat {{
            cursor: pointer;
            font-size: 1.2rem;
        }}
    </style>
    
    <script>
    function toggleChatWindow() {{
        var chatWindow = document.getElementById("chat-window");
        if (chatWindow) {{
            if (chatWindow.style.display === "none" || chatWindow.style.display === "") {{
                chatWindow.style.display = "block";
            }} else {{
                chatWindow.style.display = "none";
            }}
        }}
    }}
    
    function scrollToBottom() {{
        var chatBody = document.getElementById("chat-body");
        if (chatBody) {{
            chatBody.scrollTop = chatBody.scrollHeight;
        }}
    }}
    
    // Ensure chat window is hidden on page load
    document.addEventListener('DOMContentLoaded', function() {{
        var chatWindow = document.getElementById("chat-window");
        if (chatWindow) {{
            chatWindow.style.display = "none";
        }}
    }});
    
    // Scroll to bottom when page loads or updates
    window.addEventListener('load', scrollToBottom);
    window.addEventListener('resize', scrollToBottom);
    
    // Scroll to bottom after Streamlit updates
    document.addEventListener('DOMContentLoaded', function() {{
        const observer = new MutationObserver(scrollToBottom);
        const chatBody = document.getElementById("chat-body");
        if (chatBody) {{
            observer.observe(chatBody, {{ childList: true, subtree: true }});
        }}
    }});
    </script>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Data generation helpers
# -----------------------------------------------------------------------------
def generate_team_profile() -> dict:
    """Return static metadata that describes the club."""

    return {
        "name": "Riverdale Rovers FC",
        "coach": "Marcus Ellington",
        "formation": "4-3-3",
        "league_position": 2,
        "points": 48,
        "matches_played": 20,
        "goals_scored": 42,
        "goals_conceded": 21,
        "clean_sheets": 8,
        "logo_path": (
            Path(__file__).with_name("club_logo.png")
            if Path("club_logo.png").exists()
            else "https://via.placeholder.com/200x200.png?text=Club+Badge"
        ),
    }


def generate_player_stats() -> pd.DataFrame:
    """Craft sample player statistics for the season."""

    rng = np.random.default_rng(2025)
    players: List[dict] = []
    roster = [
        ("Liam Harper", "GK"),
        ("Noah Winter", "RB"),
        ("Ezra Quinn", "CB"),
        ("Rafael Costa", "CB"),
        ("Leo Müller", "LB"),
        ("Ethan Cruz", "CM"),
        ("Jude Marlow", "CM"),
        ("Caleb Onuoha", "CM"),
        ("Mason Ibarra", "RW"),
        ("Kai Nakamura", "ST"),
        ("Leo Williams", "LW"),
        ("Oscar Neal", "CB"),
        ("Rowan Ortiz", "DM"),
        ("Theo Sanchez", "AM"),
        ("Nico Duarte", "ST"),
    ]

    for name, position in roster:
        matches = rng.integers(10, 21)
        goals = rng.integers(0, 12) if position not in {"GK", "CB", "RB", "LB"} else rng.integers(0, 5)
        assists = rng.integers(0, 9) if position not in {"GK", "CB"} else rng.integers(0, 3)
        rating = np.round(rng.uniform(6.5, 8.5), 2)
        players.append(
            {
                "Player": name,
                "Position": position,
                "Age": rng.integers(20, 33),
                "Matches": matches,
                "Goals": goals,
                "Assists": assists,
                "Minutes": matches * rng.integers(60, 95),
                "Rating": rating,
                "Status": rng.choice(["Fit", "Rotation", "Minor Knock"]),
            }
        )

    return pd.DataFrame(players)


def generate_match_results() -> pd.DataFrame:
    """Create past match performance data for charts and tables."""

    rng = np.random.default_rng(7)
    opponents = [
        "Norwich United",
        "Cardiff Blues",
        "Oxford City",
        "Brighton Albion",
        "Leeds Miners",
        "Portsmouth FC",
        "Wolves Athletic",
        "Derby County",
        "Reading Royals",
        "Sheffield Steel",
    ]

    records: List[dict] = []
    start_date = date.today() - timedelta(weeks=len(opponents))

    for idx, opponent in enumerate(opponents):
        goals_for = rng.integers(0, 4)
        goals_against = rng.integers(0, 3)
        result = (
            "Win"
            if goals_for > goals_against
            else "Loss"
            if goals_for < goals_against
            else "Draw"
        )

        records.append(
            {
                "Match": f"Matchday {idx + 1}",
                "Date": pd.to_datetime(start_date + timedelta(days=idx * 3)),
                "Opponent": opponent,
                "Venue": rng.choice(["Home", "Away"]),
                "Goals For": goals_for,
                "Goals Against": goals_against,
                "Result": result,
                "Possession %": np.round(rng.uniform(45, 63), 1),
                "Shots on Target": rng.integers(3, 12),
            }
        )

    return pd.DataFrame(records)


def generate_upcoming_fixtures() -> pd.DataFrame:
    """Define upcoming match schedule with importance labels."""

    fixtures = [
        ("Dec 02, 2025", "Huddersfield Town", "Home", "High"),
        ("Dec 09, 2025", "Bristol Rovers", "Away", "Medium"),
        ("Dec 16, 2025", "Coventry City", "Home", "High"),
        ("Dec 23, 2025", "Swansea FC", "Away", "Low"),
        ("Jan 06, 2026", "Ipswich Wanderers", "Home", "High"),
    ]
    parsed = [
        {
            "Date": pd.to_datetime(entry[0]),
            "Opponent": entry[1],
            "Venue": entry[2],
            "Importance": entry[3],
        }
        for entry in fixtures
    ]
    return pd.DataFrame(parsed)


# -----------------------------------------------------------------------------
# Rendering utilities
# -----------------------------------------------------------------------------
def metric_card(label: str, value: str | int | float, subtext: str = "", accent: str | None = None):
    """Display a custom metric card."""

    accent_color = accent or THEME_COLORS["primary"]
    st.markdown(
        f"""
        <div class="metric-card" style="border-left-color:{accent_color};">
            <div class="metric-title">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="subtext">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


SIDEBAR_ITEMS = [
    ("team_dashboard", "🏠", "Dashboard"),
    ("teams", "🏟️", "Teams"),
    ("players", "👥", "Players"),
    ("seasons", "📅", "Season & Schedule"),
    ("rankings", "🏆", "Rankings"),
    ("player_stats", "📊", "Player Statistics"),
    ("venues", "🏟️", "Venues"),
    ("coaches", "🧑‍🏫", "Coaches"),
    ("help", "❓", "Help"),
]


def _summary_stats(team: dict, players: pd.DataFrame, matches: pd.DataFrame) -> dict:
    """Aggregate values used across cards."""

    return {
        "top_scorer": players.sort_values("Goals", ascending=False).iloc[0],
        "best_creator": players.sort_values("Assists", ascending=False).iloc[0],
        "avg_rating": round(players["Rating"].mean(), 2),
        "fit_pct": round(players["Status"].eq("Fit").mean() * 100, 1),
        "win_rate": round(matches["Result"].eq("Win").mean() * 100, 1),
        "goal_diff": int(matches["Goals For"].sum() - matches["Goals Against"].sum()),
    }


def render_dashboard_template(
    team: dict,
    players: pd.DataFrame,
    matches: pd.DataFrame,
    fixtures: pd.DataFrame,
    active_panel: str,
):
    """Compose dashboard layout conditioned on selected component."""

    stats = _summary_stats(team, players, matches)
    avg_possession = round(matches["Possession %"].mean(), 1)
    avg_shots = round(matches["Shots on Target"].mean(), 1)

    st.markdown(
        """
        <div class="dashboard-header">
            <div>
                <div class="breadcrumb">Dashboard &gt; NCAA Football Analytics Hub</div>
                <div class="header-title">NCAA Football Control Room</div>
            </div>
            <div class="search-pill">
                <span style="color:#94A0C0;font-size:1rem;">🔍</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Working search input integrated with the styled pill
    global_search = st.text_input("", placeholder="Search teams, players, venues, rankings...", key="global_search", label_visibility="collapsed")
    
    if global_search:
        st.markdown(f"### 🔍 Search Results for '{global_search}'")
        
        # Search across all data
        col1, col2 = st.columns(2)
        
        with col1:
            # Search teams
            teams_df = get_teams_data()
            if not teams_df.empty:
                team_results = teams_df[
                    teams_df['name'].str.contains(global_search, case=False, na=False) |
                    teams_df['market'].str.contains(global_search, case=False, na=False)
                ]
                if not team_results.empty:
                    st.markdown("**Teams:**")
                    st.dataframe(team_results[['name', 'market', 'conference_name']].head(5), use_container_width=True)
            
            # Search players
            players_df = get_players_data()
            if not players_df.empty:
                player_results = players_df[
                    players_df['first_name'].str.contains(global_search, case=False, na=False) |
                    players_df['last_name'].str.contains(global_search, case=False, na=False)
                ]
                if not player_results.empty:
                    st.markdown("**Players:**")
                    st.dataframe(player_results[['first_name', 'last_name', 'position', 'team_name']].head(5), use_container_width=True)
        
        with col2:
            # Search venues
            venues_df = get_venues_data()
            if not venues_df.empty:
                venue_results = venues_df[
                    venues_df['name'].str.contains(global_search, case=False, na=False) |
                    venues_df['city'].str.contains(global_search, case=False, na=False)
                ]
                if not venue_results.empty:
                    st.markdown("**Venues:**")
                    st.dataframe(venue_results[['name', 'city', 'state']].head(5), use_container_width=True)
        
        st.markdown("---")

    if active_panel == "teams":
        render_teams_explorer(team, players)
        return
    if active_panel == "players":
        render_players_explorer(players, team)
        return
    if active_panel == "seasons":
        render_seasons_viewer(matches, fixtures)
        return
    if active_panel == "rankings":
        render_rankings_panel(matches)
        return
    if active_panel == "player_stats":
        render_player_statistics(players)
        return
    if active_panel == "venues":
        render_venues_directory(team)
        return
    if active_panel == "coaches":
        render_coaches_table(team)
        return
    if active_panel == "help":
        render_help_panel()
        return

    # legacy/other panels (kept for compatibility)
    if active_panel == "player_lab":
        render_player_lab(players)
        return
    if active_panel == "fixture_desk":
        render_fixture_desk(fixtures)
        return
    if active_panel == "analytics_lab":
        render_analytics_lab(players, matches)
        return
    if active_panel == "scouting":
        render_scouting_feed(matches)
        return
    if active_panel == "medical":
        render_medical_room(players)
        return
    if active_panel == "settings":
        render_settings_panel()
        return

    # Get summary stats from API
    summary = get_summary_stats()
    
    # Use API data for cards if available, otherwise use mock data
    teams_count = summary.get('teams', 0) if summary else 0
    players_count = summary.get('players', 0) if summary else len(players)
    coaches_count = summary.get('coaches', 0) if summary else 0
    venues_count = summary.get('venues', 0) if summary else 0
    
    stat_cards = [
        ("Total Teams", teams_count, "In database", "#4F6AA3"),
        ("Total Players", players_count, "All teams", "#F1A208"),
        ("Coaches", coaches_count, "Staff members", "#59A5D8"),
        ("Venues", venues_count, "Stadiums", "#FF6F91"),
    ]
    cols = st.columns(4)
    for col, (title, value, note, accent) in zip(cols, stat_cards):
        with col:
            metric_card(title, value, note, accent=accent)

    mid_cols = st.columns([2.4, 1.2], gap="large")
    with mid_cols[0]:
        chart_data = matches.set_index("Match")[["Goals For", "Goals Against"]]
        st.markdown(
            """
            <div class="dashboard-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="color:#9FA8C8;font-size:0.8rem;">Detailed Chart 01</div>
                        <h4>Goal Rhythm</h4>
                    </div>
                    <span style="color:#9FA8C8;font-size:0.8rem;">Matchdays</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        st.line_chart(chart_data, height=220)
        st.markdown("</div>", unsafe_allow_html=True)

    with mid_cols[1]:
        st.markdown(
            f"""
            <div class="dashboard-card">
                <div style="color:#9FA8C8;font-size:0.8rem;">Average Charts</div>
                <h4>Team Pulse</h4>
                <div style="margin-top:0.8rem;">
                    <p>Possession Control</p>
                    <div style="background:#E6E8F4;border-radius:999px;">
                        <div style="width:{avg_possession}%;background:#4F6AA3;height:8px;border-radius:999px;"></div>
                    </div>
                    <p style="margin-top:0.7rem;">Shots on Target</p>
                    <div style="background:#E6E8F4;border-radius:999px;">
                        <div style="width:{min(avg_shots*12,100)}%;background:#F1A208;height:8px;border-radius:999px;"></div>
                    </div>
                    <p style="margin-top:0.7rem;">Goal Differential</p>
                    <div style="background:#E6E8F4;border-radius:999px;">
                        <div style="width:{min(max(stats['goal_diff'],0)*6+50,100)}%;background:#59A5D8;height:8px;border-radius:999px;"></div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    profile_cols = st.columns([1.6, 1, 1], gap="large")
    with profile_cols[0]:
        st.markdown(
            """
            <div class="dashboard-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="color:#9FA8C8;font-size:0.8rem;">Profile Strength</div>
                        <h4>Squad Cohesion</h4>
                    </div>
                    <div style="width:92px;height:92px;border-radius:50%;border:8px solid #E6E8F4;display:flex;align-items:center;justify-content:center;">
                        <div style="width:74px;height:74px;border-radius:50%;border:8px solid #F1A208;display:flex;align-items:center;justify-content:center;color:#4F5F90;font-weight:700;">
                            75%
                        </div>
                    </div>
                </div>
                <p>Rovers push aggressive wide overloads while keeping midfield rotations tidy.</p>
                <p style="color:#9FA8C8;font-size:0.8rem;">Coach {team['coach']} • Formation {team['formation']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with profile_cols[1]:
        monthly = (
            matches.assign(Month=matches["Date"].dt.to_period("M"))
            .groupby("Month")["Goals For"]
            .sum()
            .to_timestamp()
        )
        st.markdown(
            """
            <div class="dashboard-card">
                <div style="color:#9FA8C8;font-size:0.8rem;">Detailed Chart 02</div>
                <h4>Finishing Spread</h4>
            """,
            unsafe_allow_html=True,
        )
        st.bar_chart(monthly, height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    with profile_cols[2]:
        st.markdown(
            f"""
            <div class="dashboard-card">
                <div style="color:#9FA8C8;font-size:0.8rem;">Key Notes</div>
                <h4>Matchday Brief</h4>
                <ul style="color:#6c757d;font-size:0.85rem;padding-left:1.2rem;">
                    <li>Top scorer: {stats["top_scorer"]["Player"]} ({stats["top_scorer"]["Goals"]} goals)</li>
                    <li>Chief creator: {stats["best_creator"]["Player"]} ({stats["best_creator"]["Assists"]} assists)</li>
                    <li>Fit players: {stats["fit_pct"]}% squad availability</li>
                    <li>Goal differential: {stats["goal_diff"]:+d}</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_news_and_fixtures(matches, fixtures)


# -----------------------------------------------------------------------------
# Sidebar navigation and chat widget helpers
# -----------------------------------------------------------------------------

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Initialize chat input state
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""

def render_chat_widget():
    """Inject floating chat widget with functional LLM integration."""
    
    # Add a button to clear chat history
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
    
    # Chat container - using JavaScript to toggle visibility
    st.markdown(
        """
        <div class="chat-widget">
            <div class="chat-button" onclick="toggleChatWindow()">💬</div>
            <div class="chat-window" id="chat-window" style="display: none;">
                <div class="chat-header">
                    <span>🏈 NCAAFB Assistant</span>
                    <span class="close-chat" onclick="toggleChatWindow()">×</span>
                </div>
                <div class="chat-body" id="chat-body">
        """,
        unsafe_allow_html=True
    )
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(
                f"""
                <div class="chat-message user-message">
                    <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                        <div style="background: #4F6AA3; color: white; border-radius: 18px 18px 4px 18px; padding: 12px 16px; max-width: 80%;">
                            <div style="font-weight: 500; font-size: 0.85rem; margin-bottom: 4px;">You</div>
                            <div>{message["content"]}</div>
                        </div>
                        <div style="width: 30px; height: 30px; background: #4F6AA3; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-left: 8px; flex-shrink: 0;">
                            <span>👤</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="chat-message bot-message">
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                        <div style="width: 30px; height: 30px; background: #F1A208; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 8px; flex-shrink: 0;">
                            <span>🤖</span>
                        </div>
                        <div style="background: #f0f2f6; color: #333; border-radius: 18px 18px 18px 4px; padding: 12px 16px; max-width: 80%;">
                            <div style="font-weight: 500; font-size: 0.85rem; margin-bottom: 4px; color: #F1A208;">NCAAFB Assistant</div>
                            <div>{message["content"]}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    st.markdown(
        """
                </div>
                <div class="chat-input">
        """,
        unsafe_allow_html=True
    )
    
    # Chat input form
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "",
            placeholder="Ask about teams, players, rankings, etc...",
            key="chat_input_field",
            label_visibility="collapsed"
        )
        submit_button = st.form_submit_button("Send")
        
        if submit_button and user_input:
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # Show loading indicator
            with st.spinner("Thinking..."):
                # Query LLM API
                response = query_llm_api(user_input)
                
                if response:
                    # Add bot response to chat history
                    bot_response = response.get("answer", "Sorry, I couldn't process that request.")
                    st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
                else:
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": "Sorry, I'm having trouble connecting to the assistant. Please make sure the LLM service is running."
                    })
            
            # Rerun to update the UI
            st.rerun()
    
    st.markdown(
        """
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
            }
        }
        
        // Ensure chat window is hidden on page load
        document.addEventListener('DOMContentLoaded', function() {
            var chatWindow = document.getElementById("chat-window");
            if (chatWindow) {
                chatWindow.style.display = "none";
            }
        });
        
        // Scroll to bottom when page loads or updates
        window.addEventListener('load', scrollToBottom);
        window.addEventListener('resize', scrollToBottom);
        
        // Scroll to bottom after Streamlit updates
        document.addEventListener('DOMContentLoaded', function() {
            const observer = new MutationObserver(scrollToBottom);
            const chatBody = document.getElementById("chat-body");
            if (chatBody) {
                observer.observe(chatBody, { childList: true, subtree: true });
            }
        });
        </script>
        """,
        unsafe_allow_html=True
    )


# -- Lightweight renderers for the requested panels
def render_teams_explorer(team: dict, players: pd.DataFrame):
    st.markdown("<div class='section-spacing'>", unsafe_allow_html=True)
    st.markdown("### 🏟️ Teams Explorer")
    st.markdown("<p style='color: #7a83a7; margin-bottom: 1.5rem;'>Browse teams and view team-level details</p>", unsafe_allow_html=True)
    
    teams_df = get_teams_data()
    
    if teams_df.empty:
        show_no_data_alert("Teams")
        return
    
    show_success_message(f"Loaded {len(teams_df)} teams")
    
    # Display teams table
    display_cols = ['name', 'market', 'alias', 'conference_name', 'division_name', 'founded', 'championships_won']
    available_cols = [col for col in display_cols if col in teams_df.columns]
    st.dataframe(teams_df[available_cols], use_container_width=True, height=400)
    
    st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
    # Team selector
    team_names = teams_df['name'].tolist() if 'name' in teams_df.columns else []
    if team_names:
        sel = st.selectbox("🎯 Select team to view details", team_names)
        if sel:
            detail = teams_df[teams_df["name"] == sel].iloc[0].to_dict()
            team_id = detail.get('team_id')
            
            st.markdown(
                f"""
                <div class='dashboard-card' style='margin-top: 1rem;'>
                    <h4 style='color: #4F6AA3; font-size: 1.4rem;'>{detail.get('name', 'N/A')}</h4>
                    <p style='color: #7a83a7; font-size: 1.05rem;'>{detail.get('market', 'N/A')} ({detail.get('alias', 'N/A')})</p>
                """,
                unsafe_allow_html=True
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if detail.get('conference_name'):
                    st.write(f"🏆 **Conference:** {detail['conference_name']}")
                if detail.get('division_name'):
                    st.write(f"🛡️ **Division:** {detail['division_name']}")
            with col2:
                if detail.get('venue_name'):
                    st.write(f"🏟️ **Venue:** {detail['venue_name']}")
                if detail.get('founded'):
                    st.write(f"📅 **Founded:** {detail['founded']}")
                if detail.get('championships_won') is not None:
                    st.write(f"🏆 **Championships:** {detail['championships_won']}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("👥 Show Roster", use_container_width=True) and team_id:
                roster = get_players_data(team_id=team_id)
                if not roster.empty:
                    display_cols = ['first_name', 'last_name', 'position', 'height', 'weight', 'status']
                    available_cols = [col for col in display_cols if col in roster.columns]
                    st.dataframe(roster[available_cols], use_container_width=True, height=350)
                else:
                    show_info_message("No players found for this team")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_players_explorer(players: pd.DataFrame, team: dict):
    st.markdown("<div class='section-spacing'>", unsafe_allow_html=True)
    st.markdown("### 👥 Players Explorer")
    st.markdown("<p style='color: #7a83a7; margin-bottom: 1.5rem;'>Search, filter and view player profiles</p>", unsafe_allow_html=True)
    
    pv = get_players_data()
    
    if pv.empty:
        show_no_data_alert("Players")
        return
    
    show_success_message(f"Loaded {len(pv)} players")
    
    # Filter by team if needed
    teams_df = get_teams_data()
    if not teams_df.empty and 'team_id' in teams_df.columns:
        st.markdown("<div style='margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
        team_filter = st.selectbox("🏟️ Filter by team (optional)", ["All"] + teams_df['name'].tolist())
        st.markdown("</div>", unsafe_allow_html=True)
        if team_filter != "All":
            selected_team = teams_df[teams_df['name'] == team_filter]
            if not selected_team.empty:
                team_id = selected_team.iloc[0]['team_id']
                pv = get_players_data(team_id=team_id)
    
    if pv.empty:
        show_info_message("No players found for the selected filter")
        return
    
    # Display columns
    display_cols = ['first_name', 'last_name', 'position', 'height', 'weight', 'status', 'team_name']
    available_cols = [col for col in display_cols if col in pv.columns]
    
    st.dataframe(pv[available_cols].sort_values(["position", "last_name"]), use_container_width=True, height=500)
    st.markdown("</div>", unsafe_allow_html=True)


def render_seasons_viewer(matches: pd.DataFrame, fixtures: pd.DataFrame):
    st.markdown("<div class='section-spacing'>", unsafe_allow_html=True)
    st.markdown("### 📅 Seasons & Schedule")
    st.markdown("<p style='color: #7a83a7; margin-bottom: 1.5rem;'>View season information and rankings</p>", unsafe_allow_html=True)
    
    seasons_df = get_seasons_data()
    
    if seasons_df.empty:
        show_no_data_alert("Seasons")
    else:
        show_success_message(f"Loaded {len(seasons_df)} seasons")
        st.dataframe(seasons_df, use_container_width=True, height=300)
    
    # Show rankings for selected season
    if not seasons_df.empty:
        st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
        season_options = seasons_df.apply(lambda x: f"{x['year']} - {x['type_code']}", axis=1).tolist()
        selected_season = st.selectbox("🏆 Select season to view rankings", season_options)
        if selected_season:
            selected_row = seasons_df[seasons_df.apply(lambda x: f"{x['year']} - {x['type_code']}" == selected_season, axis=1)]
            if not selected_row.empty:
                season_id = selected_row.iloc[0]['season_id']
                rankings = get_rankings_data()
                if not rankings.empty and 'season_id' in rankings.columns:
                    season_rankings = rankings[rankings['season_id'] == season_id]
                    if not season_rankings.empty:
                        st.markdown("### Rankings for Selected Season")
                        display_cols = ['week', 'rank', 'team_name', 'points', 'wins', 'losses']
                        available_cols = [col for col in display_cols if col in season_rankings.columns]
                        st.dataframe(season_rankings[available_cols].sort_values('rank'), use_container_width=True, height=400)
                    else:
                        show_info_message("No rankings available for this season")
                else:
                    show_info_message("No rankings data available")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_rankings_panel(matches: pd.DataFrame):
    st.markdown("<div class='section-spacing'>", unsafe_allow_html=True)
    st.markdown("### 🏆 Weekly Rankings")
    st.markdown("<p style='color: #7a83a7; margin-bottom: 1.5rem;'>View team rankings by week</p>", unsafe_allow_html=True)
    
    rankings_df = get_rankings_data()
    
    if rankings_df.empty:
        show_no_data_alert("Rankings")
        return
    
    show_success_message(f"Loaded {len(rankings_df)} ranking entries")
    
    # Week selector - dynamically from API data
    if 'week' in rankings_df.columns:
        weeks = sorted(rankings_df['week'].dropna().unique(), reverse=True)
        if weeks:
            st.markdown("<div style='margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
            selected_week = st.selectbox("📅 Select week", weeks, key="week_selector")
            st.markdown("</div>", unsafe_allow_html=True)
            rankings_df = rankings_df[rankings_df['week'] == selected_week]
    
    if rankings_df.empty:
        show_info_message("No rankings found for selected week")
        return
    
    # Display rankings in a card
    st.markdown(
        f"""
        <div class='dashboard-card' style='margin-bottom: 1.5rem;'>
            <h4>Week {selected_week if 'week' in rankings_df.columns else 'N/A'} Rankings</h4>
            <p style='color: #7a83a7;'>Total teams ranked: {len(rankings_df)}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Display rankings
    display_cols = ['poll_name', 'week', 'team_market', 'team_name', 'rank', 'prev_rank', 'points', 'wins', 'losses']
    available_cols = [col for col in display_cols if col in rankings_df.columns]
    
    rankings_display = rankings_df[available_cols].sort_values('rank')
    st.dataframe(rankings_display, use_container_width=True, height=450)
    
    # Chart
    if 'rank' in rankings_df.columns and 'points' in rankings_df.columns:
        st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
        st.markdown("#### 📊 Points Distribution")
        chart_data = rankings_display.set_index('rank')['points']
        st.line_chart(chart_data, height=300)
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_player_statistics(players: pd.DataFrame):
    st.markdown("<div class='section-spacing'>", unsafe_allow_html=True)
    st.markdown("### 📊 Player Statistics & Leaderboards")
    st.markdown("<p style='color: #7a83a7; margin-bottom: 1.5rem;'>Top performers and statistical leaders</p>", unsafe_allow_html=True)
    
    stats_df = get_player_statistics_data()
    
    if stats_df.empty:
        show_no_data_alert("Player Statistics")
        return
    
    show_success_message(f"Loaded statistics for {len(stats_df)} players")
    
    # Display statistics
    display_cols = ['first_name', 'last_name', 'position', 'team_name', 'season_year', 
                    'games_played', 'rushing_yards', 'rushing_touchdowns', 
                    'receiving_yards', 'receiving_touchdowns']
    available_cols = [col for col in display_cols if col in stats_df.columns]
    
    if available_cols:
        # Convert numeric columns for sorting
        if 'rushing_yards' in stats_df.columns:
            stats_df['rushing_yards'] = pd.to_numeric(stats_df['rushing_yards'], errors='coerce')
        if 'receiving_yards' in stats_df.columns:
            stats_df['receiving_yards'] = pd.to_numeric(stats_df['receiving_yards'], errors='coerce')
        if 'games_played' in stats_df.columns:
            stats_df['games_played'] = pd.to_numeric(stats_df['games_played'], errors='coerce')
        
        # Sort by rushing_yards if available, otherwise by first available numeric column
        sort_col = 'rushing_yards' if 'rushing_yards' in stats_df.columns else available_cols[0]
        st.dataframe(stats_df[available_cols].sort_values(sort_col, ascending=False, na_position='last'), use_container_width=True, height=400)
        
        # Top performers in cards
        st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
        st.markdown("### 🌟 Top Performers")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(
                """
                <div class='dashboard-card'>
                    <h4>🏃 Top Rushing Yards</h4>
                """,
                unsafe_allow_html=True
            )
            if 'rushing_yards' in stats_df.columns:
                stats_df['rushing_yards'] = pd.to_numeric(stats_df['rushing_yards'], errors='coerce')
                top_rushing = stats_df.nlargest(5, 'rushing_yards', keep='all')
                if not top_rushing.empty:
                    display = top_rushing[['first_name', 'last_name', 'rushing_yards']].copy()
                    display['Player'] = display['first_name'] + ' ' + display['last_name']
                    display = display[display['rushing_yards'].notna()]
                    if not display.empty:
                        st.table(display[['Player', 'rushing_yards']])
                    else:
                        show_info_message("No rushing yards data available")
                else:
                    show_info_message("No rushing yards data available")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(
                """
                <div class='dashboard-card'>
                    <h4>🎯 Top Receiving Yards</h4>
                """,
                unsafe_allow_html=True
            )
            if 'receiving_yards' in stats_df.columns:
                stats_df['receiving_yards'] = pd.to_numeric(stats_df['receiving_yards'], errors='coerce')
                top_receiving = stats_df.nlargest(5, 'receiving_yards', keep='all')
                if not top_receiving.empty:
                    display = top_receiving[['first_name', 'last_name', 'receiving_yards']].copy()
                    display['Player'] = display['first_name'] + ' ' + display['last_name']
                    display = display[display['receiving_yards'].notna()]
                    if not display.empty:
                        st.table(display[['Player', 'receiving_yards']])
                    else:
                        show_info_message("No receiving yards data available")
                else:
                    show_info_message("No receiving yards data available")
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_venues_directory(team: dict):
    st.markdown("<div class='section-spacing'>", unsafe_allow_html=True)
    st.markdown("### 🏟️ Venue Directory")
    st.markdown("<p style='color: #7a83a7; margin-bottom: 1.5rem;'>Explore stadiums and venues across the league</p>", unsafe_allow_html=True)
    
    venues_df = get_venues_data()
    
    if venues_df.empty:
        show_no_data_alert("Venues")
        return
    
    show_success_message(f"Loaded {len(venues_df)} venues")
    
    # Display venues table
    display_cols = ['name', 'city', 'state', 'country', 'capacity', 'surface', 'roof_type']
    available_cols = [col for col in display_cols if col in venues_df.columns]
    
    if available_cols:
        st.dataframe(venues_df[available_cols], use_container_width=True, height=400)
    else:
        st.dataframe(venues_df, use_container_width=True, height=400)
    
    # Map view
    if 'latitude' in venues_df.columns and 'longitude' in venues_df.columns:
        st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class='dashboard-card'>
                <h4>🗺️ Venue Locations Map</h4>
                <p style='color: #7a83a7;'>Geographic distribution of venues</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        map_data = venues_df[['latitude', 'longitude', 'name']].copy()
        map_data = map_data.rename(columns={"latitude": "lat", "longitude": "lon"})
        
        # Convert to numeric and drop non-numeric values
        map_data['lat'] = pd.to_numeric(map_data['lat'], errors='coerce')
        map_data['lon'] = pd.to_numeric(map_data['lon'], errors='coerce')
        map_data = map_data.dropna(subset=['lat', 'lon'])
        
        if not map_data.empty:
            st.map(map_data)
        else:
            show_info_message("No location data available for mapping")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_coaches_table(team: dict):
    st.markdown("<div class='section-spacing'>", unsafe_allow_html=True)
    st.markdown("### 🧑‍🏫 Coaches & Staff")
    st.markdown("<p style='color: #7a83a7; margin-bottom: 1.5rem;'>Coaching staff across all teams</p>", unsafe_allow_html=True)
    
    coaches_df = get_coaches_data()
    
    if coaches_df.empty:
        show_no_data_alert("Coaches")
        return
    
    show_success_message(f"Loaded {len(coaches_df)} coaches")
    
    # Filter by team if needed
    teams_df = get_teams_data()
    if not teams_df.empty and 'team_id' in teams_df.columns:
        st.markdown("<div style='margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
        team_filter = st.selectbox("🏟️ Filter by team (optional)", ["All"] + teams_df['name'].tolist(), key="coach_team_filter")
        st.markdown("</div>", unsafe_allow_html=True)
        if team_filter != "All":
            selected_team = teams_df[teams_df['name'] == team_filter]
            if not selected_team.empty:
                team_id = selected_team.iloc[0]['team_id']
                coaches_df = get_coaches_data(team_id=team_id)
    
    if coaches_df.empty:
        show_info_message("No coaches found for the selected filter")
        return
    
    # Display coaches in styled card
    st.markdown(
        f"""
        <div class='dashboard-card' style='margin-bottom: 1.5rem;'>
            <h4>📊 Coaching Staff Overview</h4>
            <p style='color: #7a83a7;'>Total coaches: {len(coaches_df)}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Display coaches
    display_cols = ['full_name', 'position', 'team_name']
    available_cols = [col for col in display_cols if col in coaches_df.columns]
    st.dataframe(coaches_df[available_cols], use_container_width=True, height=400)
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_help_panel():
    st.markdown("<div class='section-spacing'>", unsafe_allow_html=True)
    st.markdown("### ❓ Help & Documentation")
    st.markdown("<p style='color: #7a83a7; margin-bottom: 1.5rem;'>Resources and information</p>", unsafe_allow_html=True)
    
    # Test LLM API connectivity
    llm_status = "✅ Connected"
    try:
        llm_health_url = f"{LLM_API_BASE_URL}/health"
        llm_response = requests.get(llm_health_url, timeout=5)
        if llm_response.status_code != 200:
            llm_status = "❌ Disconnected"
    except:
        llm_status = "❌ Disconnected"
    
    # Help cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div class='dashboard-card'>
                <h4>🚀 Quick Start</h4>
                <p><strong>1. Backend API:</strong></p>
                <code style='background: #f4f6fb; padding: 0.5rem; border-radius: 6px; display: block; margin: 0.5rem 0;'>python backend/data_api.py --port 5001</code>
                <p style='margin-top: 1rem;'><strong>2. LLM API:</strong></p>
                <code style='background: #f4f6fb; padding: 0.5rem; border-radius: 6px; display: block; margin: 0.5rem 0;'>python backend/llm_api.py --port 5000</code>
                <p style='margin-top: 1rem;'><strong>3. Frontend:</strong></p>
                <code style='background: #f4f6fb; padding: 0.5rem; border-radius: 6px; display: block; margin: 0.5rem 0;'>streamlit run frontend/app.py</code>
                <p style='margin-top: 1rem;'><strong>Or use the all-in-one launcher:</strong></p>
                <code style='background: #f4f6fb; padding: 0.5rem; border-radius: 6px; display: block; margin: 0.5rem 0;'>python run_all.py</code>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"""
            <div class='dashboard-card'>
                <h4>📚 Resources</h4>
                <p>🎯 <strong>SportsRadar:</strong><br/>
                <a href='https://console.sportradar.com/signup' target='_blank'>Sign up for API access</a></p>
                <p>📄 <strong>Streamlit Docs:</strong><br/>
                <a href='https://docs.streamlit.io/library/api-reference' target='_blank'>API Reference</a></p>
                <p>🤖 <strong>Chat Assistant:</strong><br/>
                Click the chat icon (💬) in the bottom right to ask questions about teams, players, rankings, and more!</p>
                <p>📡 <strong>LLM Status:</strong> {llm_status}</p>
                <p>💡 <strong>Chat Examples:</strong><br/>
                - "Show me the top 5 teams by wins"<br/>
                - "Which players are from Alabama?"<br/>
                - "What are the current rankings?"</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='dashboard-card'>
            <h4>📡 API Endpoints</h4>
            <p style='color: #7a83a7;'>This application fetches data from the following endpoints:</p>
            <ul style='color: #6c757d; line-height: 2;'>
                <li><code>/rankings/weekly</code> - Weekly team rankings</li>
                <li><code>/teams/{team_id}/roster</code> - Team rosters</li>
                <li><code>/players/{player_id}/profile</code> - Player profiles</li>
                <li><code>/seasons</code> - Season information</li>
                <li><code>/season/{year}/schedule</code> - Season schedules</li>
            </ul>
            <p style='color: #7a83a7; margin-top: 1rem;'><strong>LLM API Endpoints:</strong></p>
            <ul style='color: #6c757d; line-height: 2;'>
                <li><code>POST /query</code> - Natural language queries</li>
                <li><code>GET /health</code> - Health check</li>
                <li><code>GET /schema</code> - Database schema</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# App layout and navigation flow
# -----------------------------------------------------------------------------
def main():
    """Entry point that orchestrates sidebar navigation and section rendering."""
    
    # Check API connection with styled error
    health_check = fetch_api_data('/health')
    if not health_check:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #E63946 0%, #F1A208 100%);
                border-radius: 12px;
                padding: 30px;
                margin: 20px 0;
                text-align: center;
                color: white;
                box-shadow: 0 4px 15px rgba(230, 57, 70, 0.4);
            ">
                <div style="font-size: 4rem; margin-bottom: 15px;">⚠️</div>
                <h2 style="margin: 10px 0; color: white;">Cannot Connect to Backend API</h2>
                <p style="margin: 10px 0; opacity: 0.95; font-size: 1.1rem;">API endpoint: {API_BASE_URL}</p>
                <p style="margin: 15px 0; font-size: 0.95rem; opacity: 0.9;">Please ensure the backend server is running</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <div class='dashboard-card' style='margin-top: 1.5rem;'>
                <h4>🚀 Quick Fix</h4>
                <p>Start the backend API with:</p>
                <code style='background: #f4f6fb; padding: 0.8rem; border-radius: 8px; display: block; margin: 1rem 0; font-size: 1rem;'>python backend/data_api.py --port 5001</code>
                <p style='color: #7a83a7; margin-top: 1rem;'>Then refresh this page</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        return
    
    # Check LLM API connection
    try:

        llm_health_url = f"{LLM_API_BASE_URL}/health"
        llm_response = requests.get(llm_health_url, timeout=5)
        llm_healthy = llm_response.status_code == 200
    except:
        llm_healthy = False
    
    if not llm_healthy:
        st.sidebar.warning("⚠️ LLM Assistant unavailable. Start the LLM API service for chat functionality.")
    
    # Generate sample data for dashboard (still using mock for matches/fixtures as they're not in DB)
    team = generate_team_profile()
    players = generate_player_stats()  # Keep for dashboard compatibility
    matches = generate_match_results()
    fixtures = generate_upcoming_fixtures()

    active_panel = render_sidebar_nav()

    render_dashboard_template(team, players, matches, fixtures, active_panel)
    render_chat_widget()


if __name__ == "__main__":
    main()

