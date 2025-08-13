import streamlit as st
import altair as alt
import plotly.express as px
import pandas as pd
from utils import load_csv, find_column, validate_required_columns

def show(year: int):
    st.title(f"👥 VCT {year} Player Performance")
    st.markdown("""Explore individual player statistics, performance trends, and comparative analysis across the tournament.""")

    # Load player data
    stats = load_csv([f"vct_{year}", "players_stats", "players_stats.csv"])
    
    if stats.empty:
        st.warning(f"No player data available for {year}. Please check if the data files exist.")
        return

    # Validate required columns
    required_cols = {
        "Player name": ["Player", "player", "player_name", "Player Name"],
        "Combat score": ["Average Combat Score", "ACS", "Rating", "average_combat_score", "Average Combat Score (ACS)"],
        "Team name": ["Team", "Teams", "team", "team_name"]
    }
    
    missing = validate_required_columns(stats, required_cols)
    if missing:
        st.error(f"⚠️ Missing required columns: {'; '.join(missing)}")
        st.info("Available columns: " + ", ".join(stats.columns.tolist()))
        return

    # Get column names
    player_col = find_column(stats, required_cols["Player name"])
    acs_col = find_column(stats, required_cols["Combat score"])
    team_col = find_column(stats, required_cols["Team name"])
    
    try:
        # Player selection
        available_players = sorted(stats[player_col].dropna().unique())
        if not available_players:
            st.error("No players found in the data.")
            return

        col1, col2 = st.columns([2, 1])
        with col1:
            selected_player = st.selectbox("Select Player", available_players, key="player_select")
        with col2:
            show_leaderboard = st.checkbox("Show leaderboard", value=True)

        if show_leaderboard:
            # Top performers leaderboard
            st.subheader("🏆 Performance Leaderboard")
            
            # Calculate average stats per player
            numeric_cols = stats.select_dtypes(include=['number']).columns.tolist()
            
            leaderboard = stats.groupby(player_col)[numeric_cols].mean().round(2)
            
            # Sort by ACS or Rating
            if acs_col in leaderboard.columns:
                leaderboard = leaderboard.sort_values(acs_col, ascending=False)
            elif 'Rating' in leaderboard.columns:
                leaderboard = leaderboard.sort_values('Rating', ascending=False)
            
            # Display top 10
            top_performers = leaderboard.head(10).reset_index()
            
            # Create visualization
            if acs_col:
                fig = px.bar(
                    top_performers, 
                    x=player_col, 
                    y=acs_col,
                    title="Top 10 Players by Average Performance",
                    color=acs_col,
                    color_continuous_scale="Viridis"
                )
                fig.update_layout(xaxis_tickangle=-45, height=500)
                st.plotly_chart(fig, use_container_width=True)

        # Individual player analysis
        st.subheader(f"🔍 {selected_player} Analysis")
        player_data = stats[stats[player_col] == selected_player]
        
        if player_data.empty:
            st.warning(f"No data available for {selected_player}.")
            return

        # Player metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if acs_col:
                avg_acs = player_data[acs_col].mean()
                st.metric("Avg Combat Score", f"{avg_acs:.1f}")
        
        with col2:
            matches_played = len(player_data)
            st.metric("Matches Played", matches_played)
        
        with col3:
            if team_col:
                teams = player_data[team_col].nunique()
                st.metric("Teams Played For", teams)
                
        with col4:
            # Try to find KD ratio or kills/deaths
            kd_cols = ["KD", "K/D", "Kills:Deaths", "kd_ratio"]
            kd_col = find_column(player_data, kd_cols)
            if kd_col:
                avg_kd = player_data[kd_col].mean() if pd.api.types.is_numeric_dtype(player_data[kd_col]) else "N/A"
                st.metric("Avg K/D", f"{avg_kd:.2f}" if avg_kd != "N/A" else "N/A")

        # Performance over time
        if acs_col and len(player_data) > 1:
            st.subheader("📈 Performance Trend")
            
            # Try to find a match identifier or date column
            match_cols = ["Match ID", "Match Name", "match_id", "Tournament", "Stage"]
            match_col = find_column(player_data, match_cols)
            
            if match_col:
                # Create performance chart
                chart_data = player_data.copy()
                chart_data = chart_data.reset_index(drop=True)
                chart_data['Match_Number'] = range(1, len(chart_data) + 1)
                
                chart = (
                    alt.Chart(chart_data)
                    .mark_line(point=True, size=3)
                    .encode(
                        x=alt.X('Match_Number:O', title="Match Number"),
                        y=alt.Y(f"{acs_col}:Q", title="Performance Score"),
                        tooltip=[match_col, acs_col]
                    )
                    .properties(
                        title=f"{selected_player} Performance Over Time",
                        height=400
                    )
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Match identifier not found for trend analysis.")

        # Detailed statistics table
        st.subheader("📋 Detailed Statistics")
        
        # Select relevant columns for display
        display_cols = [player_col]
        if team_col: display_cols.append(team_col)
        if acs_col: display_cols.append(acs_col)
        
        # Add other interesting columns
        interesting_cols = ["Rating", "Kills", "Deaths", "Assists", "Headshot %", "First Kills", "First Deaths"]
        for col in interesting_cols:
            found_col = find_column(player_data, [col, col.lower(), col.replace(' ', '_')])
            if found_col and found_col not in display_cols:
                display_cols.append(found_col)
        
        # Limit to first 10 columns to avoid overwhelming display
        display_cols = display_cols[:10]
        
        st.dataframe(player_data[display_cols], use_container_width=True)
        
        # Player comparison
        if len(available_players) > 1:
            st.subheader("⚖️ Player Comparison")
            
            compare_players = st.multiselect(
                "Select players to compare:",
                available_players,
                default=[selected_player],
                key="compare_players"
            )
            
            if len(compare_players) > 1:
                comparison_data = stats[stats[player_col].isin(compare_players)]
                
                if acs_col:
                    avg_stats = comparison_data.groupby(player_col)[acs_col].mean().reset_index()
                    
                    fig = px.bar(
                        avg_stats,
                        x=player_col,
                        y=acs_col,
                        title="Player Performance Comparison",
                        color=acs_col,
                        color_continuous_scale="Plasma"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
    except Exception as e:
        st.error(f"Error processing player data: {str(e)}")
        st.info("This might be due to unexpected data format. Please check the data structure.")
