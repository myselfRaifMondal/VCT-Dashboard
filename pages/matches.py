import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from utils import load_csv, find_column, validate_required_columns

def parse_numeric_value(value):
    """Parse string values like '0.2k', '1.5k' to numeric."""
    if pd.isna(value) or value == '':
        return 0
    
    try:
        if isinstance(value, str):
            value = value.lower().strip()
            if 'k' in value:
                return float(value.replace('k', '')) * 1000
            else:
                return float(value)
        return float(value)
    except (ValueError, TypeError):
        return 0

def show(year: int):
    st.title(f"📊 VCT {year} Match Details")
    st.markdown("""Analyze match results, team performance, and economic patterns across tournaments.""")

    # Load match data (this is actually player-level data)
    summary = load_csv([f"vct_{year}", "matches", "overview.csv"])
    econ = load_csv([f"vct_{year}", "matches", "eco_rounds.csv"])

    if summary.empty:
        st.warning(f"No match data available for {year}. Please check if the data files exist.")
        return

    # Validate required columns for player-level data
    required_summary_cols = {
        "Team name": ["Team", "team", "Team A", "Team B"],  
        "Match identifier": ["Match ID", "Match Name", "match_id", "match_name"],
        "Map name": ["Map", "map", "map_name", "Map Name"],
        "Player name": ["Player", "player", "Player Name"]
    }
    
    missing = validate_required_columns(summary, required_summary_cols)
    if missing:
        st.error(f"⚠️ Missing required columns in match data: {'; '.join(missing)}")
        st.info("Available columns: " + ", ".join(summary.columns.tolist()))
        return

    # Get column names
    match_col = find_column(summary, required_summary_cols["Match identifier"])
    map_col = find_column(summary, required_summary_cols["Map name"])
    team_col = find_column(summary, required_summary_cols["Team name"])
    player_col = find_column(summary, required_summary_cols["Player name"])
    
    try:
        # Extract team names from available columns
        teams = set()
        team_cols = [col for col in summary.columns if 'team' in col.lower()]
        for col in team_cols:
            teams.update(summary[col].dropna().unique())
        
        # If no team columns found, try to extract from Team column
        if not teams and 'Team' in summary.columns:
            teams = set(summary['Team'].dropna().unique())
            
        teams = sorted(list(teams))
        
        if not teams:
            st.error("No team data found in the match summary.")
            return

        # Team selection
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_team = st.selectbox("Select Team", teams, key="team_select")
        with col2:
            show_overview = st.checkbox("Show tournament overview", value=True)

        if show_overview:
            # Tournament overview metrics
            st.subheader("📈 Tournament Overview")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_matches = summary[match_col].nunique() if match_col else len(summary)
                st.metric("Total Matches", total_matches)
            with col2:
                total_maps = len(summary)
                st.metric("Maps Played", total_maps)
            with col3:
                unique_teams = len(teams)
                st.metric("Teams", unique_teams)
            with col4:
                if map_col:
                    unique_maps = summary[map_col].nunique()
                    st.metric("Unique Maps", unique_maps)

        # Team-specific analysis
        st.subheader(f"🔍 {selected_team} Analysis")
        
        # Filter data for selected team (handle player-level data)
        team_data = summary[summary[team_col] == selected_team] if team_col else pd.DataFrame()
        
        if team_data.empty:
            st.warning(f"No data found for {selected_team}.")
        else:
            # Create match summary from player data - safely handle columns
            agg_dict = {player_col: 'count'}  # Number of players
            
            # Only add numeric columns to aggregation
            numeric_cols = team_data.select_dtypes(include=[np.number]).columns
            for col in ['Rating', 'Average Combat Score']:
                if col in numeric_cols:
                    agg_dict[col] = 'mean'
            
            match_summary = team_data.groupby([match_col, map_col]).agg(agg_dict).reset_index()
            
            # Rename columns safely
            new_names = [match_col, map_col, 'Players']
            if 'Rating' in agg_dict:
                new_names.append('Avg Rating')
            if 'Average Combat Score' in agg_dict:
                new_names.append('Avg ACS')
            
            match_summary.columns = new_names[:len(match_summary.columns)]
            
            # Display match results
            st.subheader("Recent Matches")
            st.dataframe(match_summary.head(10), use_container_width=True)
            
            # Performance metrics - safely handle potential non-numeric columns
            col1, col2 = st.columns(2)
            with col1:
                if 'Rating' in team_data.columns:
                    try:
                        # Ensure the column is numeric
                        rating_values = pd.to_numeric(team_data['Rating'], errors='coerce')
                        if not rating_values.isna().all():
                            avg_rating = rating_values.mean()
                            st.metric("Average Team Rating", f"{avg_rating:.2f}")
                        else:
                            st.metric("Average Team Rating", "N/A")
                    except Exception:
                        st.metric("Average Team Rating", "N/A")
                    
            with col2:
                if 'Average Combat Score' in team_data.columns:
                    try:
                        # Ensure the column is numeric
                        acs_values = pd.to_numeric(team_data['Average Combat Score'], errors='coerce')
                        if not acs_values.isna().all():
                            avg_acs = acs_values.mean()
                            st.metric("Average Combat Score", f"{avg_acs:.1f}")
                        else:
                            st.metric("Average Combat Score", "N/A")
                    except Exception:
                        st.metric("Average Combat Score", "N/A")
            
            # Map performance
            if map_col and not team_data[map_col].isna().all():
                map_performance = team_data.groupby(map_col).size().reset_index()
                map_performance.columns = ["Map", "Times Played"]
                
                fig = px.bar(
                    map_performance, 
                    x="Map", 
                    y="Times Played", 
                    title=f"{selected_team} - Map Frequency",
                    color="Times Played",
                    color_continuous_scale="Blues"
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

        # Economic analysis (if available)
        if not econ.empty:
            st.subheader("💰 Economic Analysis")
            
            econ_cols = {
                "Team name": ["Team", "team", "team_name"],
                "Round type": ["Type", "type", "round_type", "Round Type"],
                "Remaining credits": ["Remaining Credits", "remaining_credits", "credits"]
            }
            
            team_col_econ = find_column(econ, econ_cols["Team name"])
            type_col = find_column(econ, econ_cols["Round type"])
            credits_col = find_column(econ, econ_cols["Remaining credits"])
            
            if all([team_col_econ, type_col]):
                team_econ = econ[econ[team_col_econ] == selected_team]
                
                if not team_econ.empty:
                    # Count round types instead of averaging string values
                    round_type_counts = team_econ[type_col].value_counts().reset_index()
                    round_type_counts.columns = ["Round Type", "Count"]
                    
                    if not round_type_counts.empty:
                        fig = px.pie(
                            round_type_counts, 
                            names="Round Type", 
                            values="Count", 
                            title=f"{selected_team} - Round Types Distribution"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                    # Show credits analysis if available and numeric
                    if credits_col:
                        try:
                            # Try to parse credits values
                            econ_copy = team_econ.copy()
                            econ_copy['Credits_Numeric'] = econ_copy[credits_col].apply(parse_numeric_value)
                            
                            if econ_copy['Credits_Numeric'].sum() > 0:
                                avg_credits = econ_copy.groupby(type_col)['Credits_Numeric'].mean().reset_index()
                                avg_credits.columns = ["Round Type", "Average Credits"]
                                
                                fig2 = px.bar(
                                    avg_credits,
                                    x="Round Type",
                                    y="Average Credits",
                                    title=f"{selected_team} - Average Remaining Credits by Round Type"
                                )
                                st.plotly_chart(fig2, use_container_width=True)
                        except Exception as e:
                            st.info("Could not parse credit values for analysis.")
                            
                    # Show sample data
                    with st.expander("View Economic Data Sample"):
                        display_econ_cols = [col for col in [team_col_econ, type_col, credits_col] if col]
                        st.dataframe(team_econ[display_econ_cols].head(10), use_container_width=True)
                else:
                    st.info(f"No economic data available for {selected_team}.")
            else:
                st.info("Economic data format not recognized. Available columns: " + ", ".join(econ.columns.tolist()))
        else:
            st.info("No economic data available for this year.")
            
    except Exception as e:
        st.error(f"Error processing match data: {str(e)}")
        st.info("This might be due to unexpected data format. Please check the data structure.")
