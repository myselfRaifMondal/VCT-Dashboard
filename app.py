import streamlit as st
from utils import list_years
from pages import overview, agents, matches, players

# Page configuration
st.set_page_config(
    page_title="VCT Dashboard - VALORANT Champions Tour Analytics",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF4654;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #0F1419 0%, #1E2328 100%);
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FF4654;
    }
</style>
""", unsafe_allow_html=True)

try:
    # Sidebar configuration
    st.sidebar.title("🎯 VCT Explorer")
    st.sidebar.markdown("---")
    
    # Get available years
    available_years = list_years()
    
    if not available_years:
        st.sidebar.error("⚠️ No VCT data found!")
        st.sidebar.info("Please ensure data files are placed in the `data/` directory with the correct structure: `data/vct_YYYY/...`")
        
        # Show main page with error
        st.title("🎯 VCT Dashboard")
        st.error("No data available. Please check the data directory structure.")
        
        with st.expander("Expected Directory Structure"):
            st.code("""
data/
├── vct_2022/
│   ├── agents/
│   │   └── agents_pick_rates.csv
│   ├── matches/
│   │   ├── overview.csv
│   │   └── eco_rounds.csv
│   └── players_stats/
│       └── players_stats.csv
└── vct_2025/
    ├── agents/
    ├── matches/
    └── players_stats/
            """)
        st.stop()
    
    # Year selection
    year = st.sidebar.selectbox(
        "📅 Select Tournament Year", 
        available_years, 
        index=len(available_years)-1,  # Default to most recent year
        help="Choose the VCT year to analyze"
    )
    
    # View selection
    view = st.sidebar.radio(
        "📊 Select Analysis View", 
        ["Overview", "Agents", "Matches", "Players"],
        help="Choose what aspect of VCT data to explore"
    )
    
    # Add some sidebar info
    st.sidebar.markdown("---")
    st.sidebar.info(f"📈 Analyzing VCT {year} data")
    
    # Navigation descriptions
    descriptions = {
        "Overview": "🏆 Tournament statistics and map analysis",
        "Agents": "🎯 Agent pick rates and meta trends", 
        "Matches": "📊 Match results and team performance",
        "Players": "👥 Individual player statistics and comparisons"
    }
    st.sidebar.markdown(f"**Current View:** {descriptions[view]}")
    
    # Load the selected page
    if view == "Overview":
        overview.show(year)
    elif view == "Agents":
        agents.show(year)
    elif view == "Matches":
        matches.show(year)
    else:
        players.show(year)
        
except Exception as e:
    st.error(f"An unexpected error occurred: {str(e)}")
    st.info("Please check the data files and directory structure.")
    
    # Debug information
    with st.expander("Debug Information"):
        st.write(f"Error: {str(e)}")
        st.write(f"Error type: {type(e).__name__}")
        
        try:
            import traceback
            st.code(traceback.format_exc())
        except:
            st.write("Could not display traceback.")
