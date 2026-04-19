import streamlit as st
import sqlite3
import pandas as pd
import pickle
import plotly.graph_objects as go
from inference_math import calculate_time_left, calculate_deterministic_score, calculate_pcw, calculate_final_score

DB_PATH = '../db/nba_data.db'
MODEL_PATH = 'hoeffding_model.pkl'

@st.cache_resource
def load_model():
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)

def get_teams():
    try:
        conn = sqlite3.connect(DB_PATH)
        teams_query = "SELECT DISTINCT team_abbreviation_home FROM game_summary UNION SELECT DISTINCT team_abbreviation_away FROM game_summary"
        teams = pd.read_sql(teams_query, conn)
        conn.close()
        return sorted(teams.iloc[:, 0].dropna().tolist())
    except Exception as e:
        st.error(f"Error fetching teams: {e}")
        return ['LAL', 'BOS']

def get_historical_results(home_team, away_team):
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
        SELECT wl_home FROM game_summary 
        WHERE team_abbreviation_home = ? AND team_abbreviation_away = ?
        ORDER BY game_date DESC LIMIT 5
        """
        df = pd.read_sql(query, conn, params=(home_team, away_team))
        conn.close()
        return df['wl_home'].tolist()
    except Exception as e:
        return []

def main():
    st.set_page_config(page_title="NBA Win Probability Dashboard", layout="wide", initial_sidebar_state="expanded")
    
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>NBA Live Win Probability</h1>", unsafe_allow_html=True)
    st.markdown("<hr/>", unsafe_allow_html=True)
    
    try:
        model = load_model()
    except FileNotFoundError:
        st.error("Model not found. Please run 'train_model.py' to generate 'hoeffding_model.pkl'.")
        return

    teams = get_teams()
    
    st.sidebar.header("Matchup Configuration")
    home_team = st.sidebar.selectbox("Home Team", teams, index=teams.index('LAL') if 'LAL' in teams else 0)
    away_team = st.sidebar.selectbox("Away Team", teams, index=teams.index('BOS') if 'BOS' in teams else 1)
    
    # Deterministic Score
    hist_results = get_historical_results(home_team, away_team)
    det_home = calculate_deterministic_score(hist_results)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Historical Baseline")
    st.sidebar.write(f"**Last 5 Matchups (1=Home Win)**: {hist_results if hist_results else 'No history'}")
    st.sidebar.write(f"**Deterministic Score ($Det_{{Home}}$)**: {det_home:.3f}")
    
    # Live Game State Inputs
    st.header("Live Game State Inputs")
    col3, col4, col5 = st.columns(3)
    with col3:
        quarter = st.selectbox("Quarter", [1, 2, 3, 4], index=0)
    with col4:
        minutes = st.slider("Minutes Left", 0, 12, 12)
    with col5:
        seconds = st.slider("Seconds Left", 0, 59, 0)
        
    # State management for Score
    if 'home_score' not in st.session_state:
        st.session_state.home_score = 0
    if 'away_score' not in st.session_state:
        st.session_state.away_score = 0

    st.markdown(f"""
        <div style='text-align: center; font-size: 5rem; font-weight: bold; letter-spacing: 0.1em; margin: 20px 0;'>
            <span style='color: blue;'>{st.session_state.home_score}</span>
            <span style='color: gray; margin: 0 40px;'>-</span>
            <span style='color: red;'>{st.session_state.away_score}</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='text-align: center; color: gray; font-size: 1.2rem;'>Home Score Controls &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Away Score Controls</p>", unsafe_allow_html=True)
    
    sc1, sc2, sc3, sc4, sc_space, sc5, sc6, sc7, sc8 = st.columns([1,1,1,1,0.5,1,1,1,1])
    with sc1:
        if st.button("Home +1"): st.session_state.home_score += 1; st.rerun()
    with sc2:
        if st.button("Home +2"): st.session_state.home_score += 2; st.rerun()
    with sc3:
        if st.button("Home +3"): st.session_state.home_score += 3; st.rerun()
    with sc4:
        if st.button("Home -1"): st.session_state.home_score = max(0, st.session_state.home_score - 1); st.rerun()
    with sc5:
        if st.button("Away +1"): st.session_state.away_score += 1; st.rerun()
    with sc6:
        if st.button("Away +2"): st.session_state.away_score += 2; st.rerun()
    with sc7:
        if st.button("Away +3"): st.session_state.away_score += 3; st.rerun()
    with sc8:
        if st.button("Away -1"): st.session_state.away_score = max(0, st.session_state.away_score - 1); st.rerun()
        
    st.markdown("<hr/>", unsafe_allow_html=True)
    
    # Computations
    time_left = calculate_time_left(quarter, minutes, seconds)
    point_diff = st.session_state.home_score - st.session_state.away_score
    
    c1, c2 = st.columns(2)
    c1.metric("Time Left (Seconds)", time_left)
    c2.metric("Point Differential", point_diff)
    
    # Model Inference
    x = {'time_left': time_left, 'point_diff': point_diff}
    proba = model.predict_proba_one(x)
    pbp_home = proba.get(1, 0.5) if isinstance(proba, dict) else 0.5
    
    # PCW Blending
    pcw = calculate_pcw(time_left)
    final_home, final_away = calculate_final_score(pcw, det_home, pbp_home)
    
    st.header("Live Win Probability")
    st.markdown(f"""
        <h3 style='text-align: center;'>
            <span style='color: blue;'>{home_team} Win Probability: {final_home*100:.1f}%</span>
            <br/><br/>
            <span style='color: red;'>{away_team} Win Probability: {final_away*100:.1f}%</span>
        </h3>
    """, unsafe_allow_html=True)
    
    # Plotly Stacked Bar Chart
    fig = go.Figure(data=[
        go.Bar(name=home_team, y=['Win Probability'], x=[final_home], orientation='h', marker_color='blue', text=f"{home_team} {final_home*100:.1f}%", textposition='inside'),
        go.Bar(name=away_team, y=['Win Probability'], x=[final_away], orientation='h', marker_color='red', text=f"{away_team} {final_away*100:.1f}%", textposition='inside')
    ])
    fig.update_layout(
        barmode='stack', 
        xaxis=dict(range=[0, 1], tickformat='.0%', showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False),
        height=150, 
        margin=dict(l=20, r=20, t=10, b=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig)

if __name__ == "__main__":
    main()
