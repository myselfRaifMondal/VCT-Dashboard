#!/usr/bin/env python3
"""
Test script to verify the matches page works correctly.
"""

import sys
import pandas as pd
import numpy as np
from utils import load_csv, find_column, validate_required_columns

def test_matches_functionality():
    """Test the key functionality that was causing issues."""
    try:
        print("🧪 Testing Matches Page Functionality...")
        
        # Load data like the matches page does
        summary = load_csv(["vct_2025", "matches", "overview.csv"])
        econ = load_csv(["vct_2025", "matches", "eco_rounds.csv"])
        
        if summary.empty:
            print("❌ No summary data loaded")
            return False
        
        print(f"✅ Loaded summary data: {len(summary)} rows")
        
        # Test column detection
        required_summary_cols = {
            "Team name": ["Team", "team", "Team A", "Team B"],  
            "Match identifier": ["Match ID", "Match Name", "match_id", "match_name"],
            "Map name": ["Map", "map", "map_name", "Map Name"],
            "Player name": ["Player", "player", "Player Name"]
        }
        
        missing = validate_required_columns(summary, required_summary_cols)
        if missing:
            print(f"❌ Missing columns: {missing}")
            return False
        
        print("✅ All required columns found")
        
        # Get column names
        match_col = find_column(summary, required_summary_cols["Match identifier"])
        map_col = find_column(summary, required_summary_cols["Map name"])
        team_col = find_column(summary, required_summary_cols["Team name"])
        player_col = find_column(summary, required_summary_cols["Player name"])
        
        print(f"✅ Column mapping: Team={team_col}, Match={match_col}, Map={map_col}, Player={player_col}")
        
        # Test team extraction
        teams = sorted(summary[team_col].dropna().unique())
        if not teams:
            print("❌ No teams found")
            return False
            
        print(f"✅ Found {len(teams)} teams")
        
        # Test aggregation with first team
        test_team = teams[0]
        print(f"🧪 Testing aggregation with team: {test_team}")
        
        team_data = summary[summary[team_col] == test_team]
        if team_data.empty:
            print("❌ No data for test team")
            return False
            
        # Test safe aggregation
        agg_dict = {player_col: 'count'}
        numeric_cols = team_data.select_dtypes(include=[np.number]).columns
        
        for col in ['Rating', 'Average Combat Score']:
            if col in numeric_cols:
                agg_dict[col] = 'mean'
        
        print(f"✅ Aggregation dict: {agg_dict}")
        
        # This should not fail now
        match_summary = team_data.groupby([match_col, map_col]).agg(agg_dict).reset_index()
        print(f"✅ Aggregation successful: {len(match_summary)} match-maps")
        
        # Test economic data if available
        if not econ.empty:
            print(f"✅ Economic data available: {len(econ)} rows")
            
            # Test the parsing function
            from pages.matches import parse_numeric_value
            test_values = ["0.2k", "1.5k", "", None, "500", "invalid"]
            
            for val in test_values:
                parsed = parse_numeric_value(val)
                print(f"  Parse '{val}' -> {parsed}")
        
        print("🎉 All matches page tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_matches_functionality()
    if not success:
        sys.exit(1)
    print("\n✅ Matches page is ready for use!")
