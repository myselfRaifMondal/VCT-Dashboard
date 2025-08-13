import pandas as pd
from pathlib import Path
import streamlit as st
from typing import Optional, List
import sqlite3
import os
from sqlalchemy.orm import Session
from contextlib import contextmanager

# Database configuration
DB_PATH = Path(__file__).parent / "vct.db"
BASE_DIR = Path(__file__).parent / "data"  # Keep for fallback

def get_sqlite_connection():
    """Get a raw SQLite connection"""
    if not DB_PATH.exists():
        st.error("⚠️ Database not found! Please run the import script first: `python scripts/import_to_sqlite.py`")
        return None
    return sqlite3.connect(str(DB_PATH))

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = get_sqlite_connection()
    if conn:
        try:
            yield conn
        finally:
            conn.close()
    else:
        yield None

def get_session() -> Optional[Session]:
    """Get SQLAlchemy session - imports here to avoid circular imports"""
    try:
        from models import get_session as get_sqlalchemy_session
        return get_sqlalchemy_session()
    except ImportError:
        st.error("SQLAlchemy models not available. Using direct SQL queries.")
        return None
    except Exception as e:
        st.error(f"Error creating database session: {e}")
        return None

@st.cache_data
def load_table_from_db(table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
    """
    Load data from SQLite database table.
    
    Args:
        table_name: Name of the database table
        limit: Optional limit on number of rows to return
    
    Returns:
        pandas DataFrame with the table data
    """
    try:
        with get_db_connection() as conn:
            if conn is None:
                return pd.DataFrame()
            
            query = f"SELECT * FROM {table_name}"
            if limit:
                query += f" LIMIT {limit}"
                
            return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"⚠️ Error loading table {table_name}: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def load_csv(path_parts: list[str]) -> pd.DataFrame:
    """
    Load data using new database-first approach with CSV fallback.
    Maps CSV path parts to database table names.
    
    Example: ["vct_2021", "matches", "overview.csv"] -> table "vct_2021_matches_overview"
    """
    # Convert path parts to table name
    table_name = "_".join(path_parts).replace(".csv", "").lower()
    
    # Try database first
    if DB_PATH.exists():
        try:
            return load_table_from_db(table_name)
        except Exception as e:
            st.warning(f"Database lookup failed for {table_name}, trying CSV fallback: {e}")
    
    # Fallback to CSV if database fails or doesn't exist
    path = BASE_DIR.joinpath(*path_parts)
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        st.error(f"⚠️ Data not found in database or CSV: {'/'.join(path_parts)}")
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

@st.cache_data
def get_available_tables() -> List[str]:
    """Get list of all available database tables"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []
            
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name != 'import_metadata'"
            result = conn.execute(query).fetchall()
            return sorted([row[0] for row in result])
    except Exception as e:
        st.error(f"Error getting table list: {e}")
        return []

def list_years() -> list[int]:
    """Detect available VCT years from database or data directory"""
    # Try database first
    if DB_PATH.exists():
        try:
            tables = get_available_tables()
            years = set()
            for table in tables:
                if table.startswith("vct_"):
                    try:
                        year_str = table.split("_")[1]
                        if year_str.isdigit():
                            years.add(int(year_str))
                    except (IndexError, ValueError):
                        continue
            if years:
                return sorted(list(years))
        except Exception:
            pass
    
    # Fallback to directory scanning
    years = []
    for p in BASE_DIR.iterdir():
        if p.is_dir() and p.name.startswith("vct_"):
            try:
                year = int(p.name.split("_")[1])
                years.append(year)
            except ValueError:
                continue
    return sorted(years)

@st.cache_data
def execute_query(query: str, params: Optional[tuple] = None) -> pd.DataFrame:
    """Execute a custom SQL query and return results as DataFrame"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return pd.DataFrame()
            
            if params:
                return pd.read_sql_query(query, conn, params=params)
            else:
                return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()

def get_table_info(table_name: str) -> dict:
    """Get information about a specific table"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                return {}
            
            # Get column info
            pragma_query = f"PRAGMA table_info({table_name})"
            columns = pd.read_sql_query(pragma_query, conn)
            
            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_result = pd.read_sql_query(count_query, conn)
            row_count = count_result.iloc[0]['count']
            
            return {
                'table_name': table_name,
                'columns': columns.to_dict('records'),
                'row_count': row_count
            }
    except Exception as e:
        st.error(f"Error getting table info for {table_name}: {e}")
        return {}
