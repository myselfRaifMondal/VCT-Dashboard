import streamlit as st
import plotly.express as px
from utils import load_csv, find_column, validate_required_columns, safe_get_column_data

def show(year: int):
    st.title(f"🏆 VCT {year} Overview")
    st.markdown("""Welcome to the VCT Dashboard! This overview shows key statistics 
                   and trends from the VALORANT Champions Tour.""")

    # Load match overview
    df = load_csv([f"vct_{year}", "matches", "overview.csv"])
    
    if df.empty:
        st.warning(f"No overview data available for {year}. Please check if the data files exist.")
        return

    # Validate required columns
    required_cols = {
        "Match identifier": ["Match ID", "Match Name", "match_id", "match_name"],
        "Map name": ["Map", "map", "map_name", "Map Name"]
    }
    
    missing = validate_required_columns(df, required_cols)
    if missing:
        st.error(f"⚠️ Missing required columns: {'; '.join(missing)}")
        st.info("Available columns: " + ", ".join(df.columns.tolist()))
        return

    # Get column names
    match_col = find_column(df, required_cols["Match identifier"])
    map_col = find_column(df, required_cols["Map name"])
    
    # Calculate metrics
    try:
        if match_col:
            total_matches = df[match_col].nunique()
        else:
            total_matches = "N/A"
            
        total_maps = len(df)
        unique_maps = df[map_col].nunique() if map_col else 0

        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Matches", total_matches)
        with col2:
            st.metric("🗺️ Total Maps Played", total_maps)
        with col3:
            st.metric("🎯 Unique Maps", unique_maps)

        # Map frequency chart
        if map_col and not df[map_col].isna().all():
            st.subheader("Map Frequency Analysis")
            freq = df[map_col].value_counts().reset_index()
            freq.columns = ["Map", "Count"]
            
            if len(freq) > 0:
                fig = px.bar(
                    freq.head(10), 
                    x="Map", 
                    y="Count", 
                    title="Most Played Maps",
                    color="Count",
                    color_continuous_scale="Viridis"
                )
                fig.update_layout(xaxis_tickangle=-45, height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                # Show data table
                with st.expander("📋 View Raw Map Data"):
                    st.dataframe(freq, use_container_width=True)
            else:
                st.info("No map data available for visualization.")
        else:
            st.warning("Map column not found or contains no data.")
            
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        st.info("This might be due to unexpected data format. Please check the data structure.")
