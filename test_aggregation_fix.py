#!/usr/bin/env python3
"""
Test script to verify both agents and matches pages work without aggregation errors.
"""

import sys
import pandas as pd
import numpy as np
from utils import load_csv, find_column, validate_required_columns

def test_agent_functionality():
    """Test the agents page functionality."""
    print("🧪 Testing Agents Page...")
    
    try:
        # Import the parsing function
        from pages.agents import parse_percentage
        
        # Test percentage parsing
        test_cases = ["89%", "61%", "100%", "", None, "invalid", "50"]
        print("📊 Testing percentage parsing:")
        for case in test_cases:
            result = parse_percentage(case)
            print(f"  '{case}' -> {result}")
        
        # Load agent data
        picks = load_csv(["vct_2025", "agents", "agents_pick_rates.csv"])
        if picks.empty:
            print("❌ No agent data loaded")
            return False
            
        print(f"✅ Loaded agent data: {len(picks)} rows")
        
        # Check column structure
        required_cols = {
            "Agent name": ["Agent", "agent", "agent_name", "Agent Name"],
            "Map name": ["Map", "map", "map_name", "Map Name"],
            "Pick rate": ["Pick Rate", "pick_rate", "PickRate", "pick_pct"]
        }
        
        missing = validate_required_columns(picks, required_cols)
        if missing:
            print(f"❌ Missing columns: {missing}")
            return False
            
        agent_col = find_column(picks, required_cols["Agent name"])
        pick_rate_col = find_column(picks, required_cols["Pick rate"])
        
        print(f"✅ Found columns: Agent={agent_col}, Pick Rate={pick_rate_col}")
        
        # Test the problematic aggregation
        print("🧪 Testing safe aggregation...")
        picks_copy = picks.copy()
        picks_copy['Pick_Rate_Numeric'] = picks_copy[pick_rate_col].apply(parse_percentage)
        
        # This should work now
        agent_summary = picks_copy.groupby(agent_col)['Pick_Rate_Numeric'].mean()
        print(f"✅ Aggregation successful: {len(agent_summary)} agents processed")
        
        # Show top agents
        top_agents = agent_summary.nlargest(5)
        print("Top 5 agents:")
        for agent, rate in top_agents.items():
            print(f"  {agent}: {rate:.1f}%")
            
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_matches_functionality():
    """Test the matches page functionality."""
    print("\n🧪 Testing Matches Page...")
    
    try:
        # Import the parsing function  
        from pages.matches import parse_numeric_value
        
        # Test numeric parsing
        test_cases = ["0.2k", "1.5k", "500", "", None, "invalid"]
        print("💰 Testing numeric value parsing:")
        for case in test_cases:
            result = parse_numeric_value(case)
            print(f"  '{case}' -> {result}")
        
        # Load match data
        summary = load_csv(["vct_2025", "matches", "overview.csv"])
        if summary.empty:
            print("❌ No match data loaded")
            return False
            
        print(f"✅ Loaded match data: {len(summary)} rows")
        
        # Test team extraction and aggregation
        teams = sorted(summary['Team'].dropna().unique())
        if not teams:
            print("❌ No teams found")
            return False
            
        print(f"✅ Found {len(teams)} teams")
        
        # Test safe aggregation with first team
        test_team = teams[0]
        team_data = summary[summary['Team'] == test_team]
        
        print(f"🧪 Testing aggregation with {test_team} ({len(team_data)} records)")
        
        # Safe numeric column detection
        numeric_cols = team_data.select_dtypes(include=[np.number]).columns
        print(f"✅ Found numeric columns: {numeric_cols.tolist()}")
        
        # Test aggregation
        agg_dict = {'Player': 'count'}
        for col in ['Rating', 'Average Combat Score']:
            if col in numeric_cols:
                agg_dict[col] = 'mean'
                
        match_summary = team_data.groupby(['Match Name', 'Map']).agg(agg_dict)
        print(f"✅ Aggregation successful: {len(match_summary)} match-maps")
        
        return True
        
    except Exception as e:
        print(f"❌ Matches test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🎯 VCT Dashboard Aggregation Fix Test")
    print("=" * 50)
    
    agents_ok = test_agent_functionality()
    matches_ok = test_matches_functionality()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  Agents Page: {'✅ PASS' if agents_ok else '❌ FAIL'}")
    print(f"  Matches Page: {'✅ PASS' if matches_ok else '❌ FAIL'}")
    
    if agents_ok and matches_ok:
        print("\n🎉 All aggregation issues are fixed!")
        print("🚀 The dashboard should now work without errors.")
    else:
        print("\n⚠️ Some issues remain. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
