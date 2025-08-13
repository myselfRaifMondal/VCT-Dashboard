#!/usr/bin/env python3
"""
Simple test script to validate VCT Dashboard functionality.
Run this before deploying to catch common issues.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    try:
        import streamlit
        import pandas
        import plotly
        import altair
        import numpy
        print("✅ All dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_data_structure():
    """Test that data directory structure exists."""
    data_dir = Path("data")
    if not data_dir.exists():
        print("❌ Data directory not found")
        return False
    
    # Check for VCT year directories
    vct_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith("vct_")]
    if not vct_dirs:
        print("❌ No VCT year directories found in data/")
        return False
    
    print(f"✅ Found {len(vct_dirs)} VCT year directories")
    
    # Check for required subdirectories and files
    required_structure = {
        "agents": ["agents_pick_rates.csv"],
        "matches": ["overview.csv"],
        "players_stats": ["players_stats.csv"]
    }
    
    for vct_dir in vct_dirs:
        print(f"  Checking {vct_dir.name}...")
        for subdir, files in required_structure.items():
            subdir_path = vct_dir / subdir
            if subdir_path.exists():
                for file in files:
                    file_path = subdir_path / file
                    if file_path.exists():
                        print(f"    ✅ {subdir}/{file}")
                    else:
                        print(f"    ⚠️  {subdir}/{file} not found")
            else:
                print(f"    ⚠️  {subdir}/ directory not found")
    
    return True

def test_utils():
    """Test utility functions."""
    try:
        from utils import list_years, load_csv
        
        # Test year listing
        years = list_years()
        print(f"✅ Found {len(years)} available years: {years}")
        
        # Test CSV loading (if data exists)
        if years:
            year = years[0]
            try:
                df = load_csv([f"vct_{year}", "matches", "overview.csv"])
                if not df.empty:
                    print(f"✅ Successfully loaded sample data: {len(df)} rows")
                else:
                    print("⚠️  Sample data file exists but is empty")
            except Exception as e:
                print(f"⚠️  Could not load sample data: {e}")
        
        return True
    except ImportError as e:
        print(f"❌ Could not import utils: {e}")
        return False

def test_pages():
    """Test that page modules can be imported."""
    try:
        from pages import overview, agents, matches, players
        print("✅ All page modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Page import error: {e}")
        return False

def main():
    """Run all tests."""
    print("🎯 VCT Dashboard Test Suite")
    print("=" * 40)
    
    tests = [
        ("Dependencies", test_imports),
        ("Data Structure", test_data_structure),
        ("Utils Module", test_utils),
        ("Page Modules", test_pages)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n🧪 Testing {name}...")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {name} failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Dashboard should work correctly.")
        print("\n🚀 To start the dashboard, run: streamlit run app.py")
    else:
        print("⚠️  Some tests failed. Check the issues above before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
