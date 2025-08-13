import streamlit as st
import altair as alt
import plotly.express as px
import pandas as pd
import numpy as np
from utils import load_csv, find_column, validate_required_columns

def parse_percentage(value):
    """Parse percentage strings like '89%', '61%' to numeric."""
    if pd.isna(value) or value == '':
        return 0.0
    
    try:
        if isinstance(value, str):
            value = value.strip()
            if '%' in value:
                return float(value.replace('%', ''))
            else:
                return float(value)
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def show(year: int):
    st.title(f"🎯 VCT {year} Agent Analytics")
    st.markdown("""Explore agent pick rates, performance metrics, and meta trends across different maps and tournaments.""")

    # Load agent data
    picks = load_csv([f"vct_{year}", "agents", "agents_pick_rates.csv"])
    
    if picks.empty:
        st.warning(f"No agent data available for {year}. Please check if the data files exist.")
        return

    # Validate required columns for pick rates
    required_cols = {
        "Agent name": ["Agent", "agent", "agent_name", "Agent Name"],
        "Map name": ["Map", "map", "map_name", "Map Name"],
        "Pick rate": ["Pick Rate", "pick_rate", "PickRate", "pick_pct"]
    }
    
    missing = validate_required_columns(picks, required_cols)
    if missing:
        st.error(f"⚠️ Missing required columns in pick rates data: {'; '.join(missing)}")
        st.info("Available columns: " + ", ".join(picks.columns.tolist()))
        return

    # Get column names
    agent_col = find_column(picks, required_cols["Agent name"])
    map_col = find_column(picks, required_cols["Map name"])
    pick_rate_col = find_column(picks, required_cols["Pick rate"])

    try:
        # Parse pick rates to numeric first to avoid aggregation errors
        picks_copy = picks.copy()
        picks_copy['Pick_Rate_Numeric'] = picks_copy[pick_rate_col].apply(parse_percentage)
        
        # Agent selection
        available_agents = sorted(picks[agent_col].dropna().unique())
        if not available_agents:
            st.error("No agents found in the data.")
            return
            
        col1, col2 = st.columns([2, 1])
        with col1:
            agent = st.selectbox("Select Agent", available_agents, key="agent_select")
        with col2:
            show_all = st.checkbox("Show all agents comparison", key="show_all_agents")

        if show_all:
            # Overall agent pick rate comparison - use numeric values
            st.subheader("📊 Agent Pick Rate Comparison")
            
            # Safely aggregate using numeric column
            agent_summary = picks_copy.groupby(agent_col)['Pick_Rate_Numeric'].mean().sort_values(ascending=False).reset_index()
            agent_summary.columns = ["Agent", "Average Pick Rate"]
            
            # Only show agents with data
            agent_summary = agent_summary[agent_summary["Average Pick Rate"] > 0]
            
            if not agent_summary.empty:
                fig = px.bar(
                    agent_summary.head(15), 
                    x="Agent", 
                    y="Average Pick Rate", 
                    title="Top 15 Agents by Average Pick Rate (%)",
                    color="Average Pick Rate",
                    color_continuous_scale="Plasma"
                )
                fig.update_layout(xaxis_tickangle=-45, height=500)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No valid pick rate data for visualization.")
            
        # Individual agent analysis
        st.subheader(f"🔍 {agent} Analysis")
        agent_data = picks[picks[agent_col] == agent].copy()
        
        if agent_data.empty:
            st.warning(f"No data available for {agent}.")
        else:
            # Add numeric pick rate for this agent's data
            agent_data['Pick_Rate_Numeric'] = agent_data[pick_rate_col].apply(parse_percentage)
            
            # Pick rate by map - use original data for display but numeric for sorting
            if map_col and not agent_data[map_col].isna().all():
                # Filter out "All Maps" if present, or handle it specially
                map_specific_data = agent_data[agent_data[map_col] != "All Maps"] if "All Maps" in agent_data[map_col].values else agent_data
                
                if not map_specific_data.empty:
                    # Create chart using numeric values
                    chart = (
                        alt.Chart(map_specific_data)
                        .mark_circle(size=100)
                        .encode(
                            x=alt.X(f"{map_col}:N", title="Map"),
                            y=alt.Y('Pick_Rate_Numeric:Q', title="Pick Rate (%)"),
                            color=alt.Color('Pick_Rate_Numeric:Q', scale=alt.Scale(scheme="viridis")),
                            tooltip=[map_col, pick_rate_col, 'Pick_Rate_Numeric']
                        )
                        .properties(
                            title=f"{agent} Pick Rate by Map",
                            width=600,
                            height=400
                        )
                    )
                    st.altair_chart(chart, use_container_width=True)
                    
                    # Show key metrics
                    col1, col2 = st.columns(2)
                    with col1:
                        avg_pick_rate = map_specific_data['Pick_Rate_Numeric'].mean()
                        st.metric("Average Pick Rate", f"{avg_pick_rate:.1f}%")
                    with col2:
                        max_pick_rate = map_specific_data['Pick_Rate_Numeric'].max()
                        best_map = map_specific_data.loc[map_specific_data['Pick_Rate_Numeric'].idxmax(), map_col]
                        st.metric("Best Map", f"{best_map}", f"{max_pick_rate:.1f}%")
                
                # Data table
                with st.expander(f"📋 {agent} Detailed Stats"):
                    display_data = agent_data.copy()
                    display_data = display_data.sort_values('Pick_Rate_Numeric', ascending=False)
                    display_cols = [col for col in [agent_col, map_col, pick_rate_col] if col]
                    st.dataframe(display_data[display_cols], use_container_width=True)
            else:
                st.warning("Map data not available for detailed analysis.")

        # Additional insights - using numeric data
        if len(available_agents) > 1:
            st.subheader("📈 Meta Insights")
            
            try:
                # Calculate insights using numeric values
                agent_stats = picks_copy.groupby(agent_col)['Pick_Rate_Numeric'].agg(['mean', 'count']).reset_index()
                agent_stats.columns = [agent_col, 'avg_pick_rate', 'appearances']
                agent_stats = agent_stats[agent_stats['avg_pick_rate'] > 0]  # Filter out zero rates
                
                if not agent_stats.empty:
                    top_agent = agent_stats.loc[agent_stats['avg_pick_rate'].idxmax()]
                    meta_agents = len(agent_stats[agent_stats['avg_pick_rate'] > 10])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Most Picked Agent", top_agent[agent_col], f"{top_agent['avg_pick_rate']:.1f}%")
                    with col2:
                        st.metric("Meta Agents", meta_agents, ">10% pick rate")
                else:
                    st.info("No statistical insights available with current data.")
            except Exception as insight_error:
                st.info(f"Could not calculate meta insights: {str(insight_error)}")
                
    except Exception as e:
        st.error(f"Error processing agent data: {str(e)}")
        st.info("This might be due to unexpected data format. Please check the data structure.")
