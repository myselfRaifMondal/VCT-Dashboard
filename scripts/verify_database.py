#!/usr/bin/env python3
"""
VCT Database Verification Utility

This script verifies the SQLite database structure and provides
useful information about the imported data.

Usage:
    python scripts/verify_database.py
"""

import sqlite3
import os
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

def connect_database(db_path: str = "vct.db") -> sqlite3.Connection:
    """Connect to the VCT database."""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Run the import script first: python scripts/import_to_sqlite.py")
        return None
    
    return sqlite3.connect(db_path)

def get_database_info(conn: sqlite3.Connection) -> Dict:
    """Get basic information about the database."""
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    # Exclude metadata table for counts
    data_tables = [t for t in all_tables if t != 'import_metadata']
    
    # Get total row count across all tables
    total_rows = 0
    table_info = {}
    
    for table in data_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        total_rows += row_count
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        table_info[table] = {
            'row_count': row_count,
            'column_count': len(columns),
            'columns': [(col[1], col[2]) for col in columns]  # (name, type)
        }
    
    # Get database file size
    db_size = Path("vct.db").stat().st_size / (1024 * 1024)  # MB
    
    return {
        'total_tables': len(data_tables),
        'total_rows': total_rows,
        'db_size_mb': db_size,
        'table_info': table_info
    }

def display_summary(info: Dict):
    """Display a summary of the database."""
    print("=" * 70)
    print("VCT DATABASE VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"Database file: vct.db")
    print(f"File size: {info['db_size_mb']:.2f} MB")
    print(f"Total tables: {info['total_tables']}")
    print(f"Total rows: {info['total_rows']:,}")
    print()

def display_tables_by_category(info: Dict):
    """Display tables organized by category."""
    table_info = info['table_info']
    
    # Categorize tables
    categories = {
        'ID Mappings': [],
        'Agent Data': [],
        'Match Data': [],
        'Player Stats': [],
        'Other': []
    }
    
    for table_name, details in table_info.items():
        if 'ids' in table_name:
            categories['ID Mappings'].append((table_name, details))
        elif 'agent' in table_name:
            categories['Agent Data'].append((table_name, details))
        elif 'match' in table_name or 'eco' in table_name or 'kill' in table_name:
            categories['Match Data'].append((table_name, details))
        elif 'player' in table_name:
            categories['Player Stats'].append((table_name, details))
        else:
            categories['Other'].append((table_name, details))
    
    for category, tables in categories.items():
        if tables:
            print(f"\n{category.upper()}")
            print("-" * 50)
            for table_name, details in sorted(tables, key=lambda x: x[0]):
                print(f"  {table_name:<35} {details['row_count']:>8,} rows  {details['column_count']:>2} cols")

def show_sample_data(conn: sqlite3.Connection, table_name: str, limit: int = 3):
    """Show sample data from a table."""
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name} LIMIT {limit}", conn)
        print(f"\nSample data from {table_name}:")
        print("-" * 50)
        print(df.to_string(index=False))
        print()
    except Exception as e:
        print(f"Error reading sample data from {table_name}: {e}")

def verify_data_integrity(conn: sqlite3.Connection, info: Dict):
    """Perform basic data integrity checks."""
    print("\nDATA INTEGRITY CHECKS")
    print("-" * 50)
    
    issues = []
    
    # Check for empty tables
    for table_name, details in info['table_info'].items():
        if details['row_count'] == 0:
            issues.append(f"Empty table: {table_name}")
    
    # Check for tables with suspicious column counts
    for table_name, details in info['table_info'].items():
        if details['column_count'] > 50:
            issues.append(f"Many columns ({details['column_count']}): {table_name}")
        elif details['column_count'] == 1:
            issues.append(f"Only one column: {table_name}")
    
    if issues:
        print("⚠️  Potential issues found:")
        for issue in issues[:10]:  # Show first 10 issues
            print(f"   - {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more")
    else:
        print("✅ No obvious data integrity issues found")

def show_popular_queries(conn: sqlite3.Connection):
    """Show some example queries that can be run on the database."""
    print("\nEXAMPLE QUERIES YOU CAN RUN")
    print("-" * 50)
    
    queries = [
        ("Top 10 players by kills (2025)", """
            SELECT player, SUM(kills) as total_kills, team
            FROM vct_2025_matches_overview 
            WHERE player IS NOT NULL 
            GROUP BY player, team
            ORDER BY total_kills DESC 
            LIMIT 10
        """),
        ("Most picked agents (2024)", """
            SELECT agent, COUNT(*) as pick_count 
            FROM vct_2024_agents_agents_pick_rates 
            GROUP BY agent 
            ORDER BY pick_count DESC 
            LIMIT 10
        """),
        ("Team win rates", """
            SELECT team, 
                   COUNT(*) as matches_played,
                   AVG(CASE WHEN score_1 > score_2 THEN 1.0 ELSE 0.0 END) as win_rate
            FROM vct_2023_matches_scores 
            GROUP BY team 
            HAVING matches_played >= 5
            ORDER BY win_rate DESC
        """)
    ]
    
    for title, query in queries:
        print(f"\n{title}:")
        print(f"  {query.strip()}")

def main():
    """Main verification function."""
    print("Verifying VCT database...")
    
    # Connect to database
    conn = connect_database()
    if not conn:
        return
    
    try:
        # Get database info
        info = get_database_info(conn)
        
        # Display summary
        display_summary(info)
        
        # Display tables by category
        display_tables_by_category(info)
        
        # Show sample data from a few interesting tables
        interesting_tables = [
            'vct_2025_matches_overview',
            'vct_2024_agents_agents_pick_rates',
            'vct_2023_matches_scores'
        ]
        
        print("\nSAMPLE DATA")
        print("-" * 50)
        for table in interesting_tables:
            if table in info['table_info']:
                show_sample_data(conn, table)
        
        # Verify data integrity
        verify_data_integrity(conn, info)
        
        # Show example queries
        show_popular_queries(conn)
        
        print("\n" + "=" * 70)
        print("✅ Database verification completed!")
        print("\nYou can now:")
        print("1. Use the models.py file to query data with SQLAlchemy")
        print("2. Update your Streamlit app to use SQLite instead of CSV")
        print("3. Run custom SQL queries on the database")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
