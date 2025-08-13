import pandas as pd
from pathlib import Path
import streamlit as st
from typing import Optional, List

BASE_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_csv(path_parts: list[str]) -> pd.DataFrame:
    """
    Load a CSV given a list of subpaths relative to data/
    Example: ["vct_2021", "matches", "overview.csv"]
    """
    path = BASE_DIR.joinpath(*path_parts)
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        st.error(f"⚠️ Data file not found: {'/'.join(path_parts)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Error loading {'/'.join(path_parts)}: {str(e)}")
        return pd.DataFrame()

def find_column(df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
    """
    Find the first matching column name from a list of possibilities.
    Returns None if no match is found.
    """
    if df.empty:
        return None
    
    available_cols = df.columns.tolist()
    for name in possible_names:
        if name in available_cols:
            return name
    return None

def safe_get_column_data(df: pd.DataFrame, possible_names: List[str], fallback_value=None):
    """
    Safely get data from a column, trying multiple possible column names.
    Returns fallback_value if column not found.
    """
    column_name = find_column(df, possible_names)
    if column_name:
        return df[column_name]
    return fallback_value

def validate_required_columns(df: pd.DataFrame, required_columns: dict) -> List[str]:
    """
    Validate that required columns exist in the dataframe.
    
    Args:
        df: The dataframe to validate
        required_columns: Dict of {description: [possible_column_names]}
    
    Returns:
        List of missing column descriptions
    """
    missing = []
    for description, possible_names in required_columns.items():
        if not find_column(df, possible_names):
            missing.append(f"{description} (tried: {', '.join(possible_names)})")
    return missing

def list_years() -> list[int]:
    """Detect available VCT year folders under data/"""
    years = []
    for p in BASE_DIR.iterdir():
        if p.is_dir() and p.name.startswith("vct_"):
            try:
                year = int(p.name.split("_")[1])
                years.append(year)
            except ValueError:
                continue
    return sorted(years)
