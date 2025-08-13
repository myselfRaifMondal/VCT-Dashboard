# VCT Dashboard Database Setup

This guide explains how to import CSV data into SQLite and use the database in your VCT Dashboard.

## Quick Start

1. **Import CSV data to SQLite:**
   ```bash
   python scripts/import_to_sqlite.py
   ```

2. **Import large files (optional):**
   ```bash
   python scripts/import_large_files.py
   ```

3. **Verify the database:**
   ```bash
   python scripts/verify_database.py
   ```

## Database Overview

After running the import script, you'll have:

- **Database file:** `vct.db` (SQLite database)
- **Size:** ~78 MB
- **Tables:** 111 tables with 364,810+ rows
- **Data coverage:** VCT data from 2021-2025

### Table Categories

1. **ID Mappings** - Player, team, and tournament ID mappings
2. **Agent Data** - Agent pick rates, map statistics, team compositions  
3. **Match Data** - Match results, scores, eco rounds, kill statistics
4. **Player Stats** - Individual player performance data

## Using the Database

### Option 1: SQLAlchemy Models (Recommended)

```python
from models import get_session, DatabaseManager, get_matches_overview

# Get database session
session = get_session()

# Or use the database manager
with DatabaseManager() as db:
    results = db.query_table('vct_2024_agents_agents_pick_rates', limit=10)
    
# Helper functions
matches = get_matches_overview(limit=100)
```

### Option 2: Direct SQL Queries

```python
import sqlite3

conn = sqlite3.connect('vct.db')
cursor = conn.cursor()

# Example query
cursor.execute("""
    SELECT agent, COUNT(*) as pick_count 
    FROM vct_2024_agents_agents_pick_rates 
    GROUP BY agent 
    ORDER BY pick_count DESC 
    LIMIT 10
""")

results = cursor.fetchall()
conn.close()
```

### Option 3: Pandas Integration

```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('vct.db')

# Load data into DataFrame
df = pd.read_sql("""
    SELECT * FROM vct_2023_matches_scores 
    WHERE match_result LIKE '%won'
""", conn)

conn.close()
```

## Available Tables

### Key Tables to Start With:

- **Agent Data:**
  - `vct_2024_agents_agents_pick_rates` - Agent popularity
  - `vct_2024_agents_teams_picked_agents` - Team compositions

- **Match Results:**
  - `vct_2023_matches_scores` - Match outcomes
  - `vct_2024_matches_maps_scores` - Map-level results

- **Performance Stats:**
  - `vct_2024_matches_kills_stats` - Kill statistics
  - `vct_2023_matches_eco_stats` - Economy round data

## Example Queries

### Top Agents by Pick Rate (2024)
```sql
SELECT agent, COUNT(*) as picks, 
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM vct_2024_agents_agents_pick_rates), 2) as pick_percentage
FROM vct_2024_agents_agents_pick_rates 
GROUP BY agent 
ORDER BY picks DESC 
LIMIT 10;
```

### Team Win Rates (2023)
```sql
SELECT team, 
       COUNT(*) as matches_played,
       SUM(CASE WHEN match_result LIKE team || ' won' THEN 1 ELSE 0 END) as wins,
       ROUND(SUM(CASE WHEN match_result LIKE team || ' won' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate
FROM (
    SELECT team_a as team, match_result FROM vct_2023_matches_scores
    UNION ALL 
    SELECT team_b as team, match_result FROM vct_2023_matches_scores
)
GROUP BY team 
HAVING matches_played >= 5
ORDER BY win_rate DESC;
```

### Map Performance Analysis
```sql
SELECT map, 
       AVG(team_a_total_rounds + team_b_total_rounds) as avg_total_rounds,
       COUNT(*) as games_played
FROM vct_2024_matches_maps_scores 
GROUP BY map 
ORDER BY avg_total_rounds DESC;
```

## Scripts Documentation

### `scripts/import_to_sqlite.py`
- Main import script for all CSV files
- Handles schema inference and data type detection
- Creates indexes for better query performance
- Generates import metadata and summary report

### `scripts/import_large_files.py`
- Handles large CSV files that exceed SQLite limits
- Processes files in batches to avoid memory issues
- Imports files that failed in the initial import

### `scripts/verify_database.py`
- Verifies database integrity and structure
- Shows table statistics and sample data
- Provides example queries for common use cases

### `models.py`
- SQLAlchemy ORM models for all database tables
- Helper functions for common queries
- Database connection management

## Troubleshooting

### Import Issues
- **"too many SQL variables"** - Run `import_large_files.py` for problematic files
- **Encoding errors** - Script tries multiple encodings automatically
- **Memory issues** - Reduce batch_size in import scripts

### Database Issues  
- **File not found** - Make sure to run the import script first
- **Permission errors** - Check file permissions in project directory
- **Corrupted database** - Delete `vct.db` and re-run import

## Integration with Streamlit

To update your Streamlit app to use the database:

1. **Replace CSV loading:**
   ```python
   # Old CSV approach
   df = pd.read_csv('data/vct_2024/matches/overview.csv')
   
   # New database approach  
   from models import DatabaseManager
   with DatabaseManager() as db:
       df = pd.DataFrame(db.query_table('vct_2024_matches_overview'))
   ```

2. **Update utility functions:**
   ```python
   # In utils.py
   import sqlite3
   
   def load_data_from_db(table_name, limit=None):
       conn = sqlite3.connect('vct.db')
       query = f"SELECT * FROM {table_name}"
       if limit:
           query += f" LIMIT {limit}"
       df = pd.read_sql(query, conn)
       conn.close()
       return df
   ```

## Performance Tips

1. **Use indexes** - The import script creates indexes on common columns
2. **Limit results** - Use `LIMIT` clauses for large tables
3. **Filter early** - Add `WHERE` clauses to reduce data processing
4. **Connection pooling** - Reuse database connections when possible

## Next Steps

1. **Refactor Streamlit app** to use SQLite instead of CSV files
2. **Create Docker setup** with the database included
3. **Add CI/CD pipeline** to rebuild database when data changes
4. **Deploy to cloud** with proper database hosting
