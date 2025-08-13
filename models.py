"""
VCT Dashboard Database Models

SQLAlchemy ORM models for the VCT database tables.
These models are automatically generated based on the imported CSV data structure.

Usage:
    from models import get_session, VCTMatch, VCTPlayer, etc.
    
    session = get_session()
    matches = session.query(VCTMatch).all()
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Dict, Any, Optional, List
import sqlite3
import os
from pathlib import Path

# Database configuration
DATABASE_URL = "sqlite:///vct.db"
Base = declarative_base()

# Global engine and session factory
engine = None
SessionLocal = None

def init_database(db_path: str = "vct.db"):
    """Initialize database connection and session factory."""
    global engine, SessionLocal
    
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(
        db_url,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
            "timeout": 30
        },
        echo=False  # Set to True for SQL debugging
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

def get_session() -> Session:
    """Get a new database session."""
    if SessionLocal is None:
        init_database()
    return SessionLocal()

def get_engine():
    """Get the database engine."""
    if engine is None:
        init_database()
    return engine

def get_table_info() -> Dict[str, Dict]:
    """Get information about all tables in the database."""
    if not os.path.exists("vct.db"):
        return {}
    
    conn = sqlite3.connect("vct.db")
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'import_metadata'")
    tables = [row[0] for row in cursor.fetchall()]
    
    table_info = {}
    for table in tables:
        # Get column information
        cursor.execute(f"PRAGMA table_info({table})")
        columns = []
        for col_info in cursor.fetchall():
            columns.append({
                'name': col_info[1],
                'type': col_info[2],
                'nullable': not bool(col_info[3]),
                'primary_key': bool(col_info[5])
            })
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        
        table_info[table] = {
            'columns': columns,
            'row_count': row_count
        }
    
    conn.close()
    return table_info

class ImportMetadata(Base):
    """Model for tracking import metadata."""
    __tablename__ = 'import_metadata'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String, nullable=False, unique=True)
    source_file = Column(String, nullable=False)
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    import_timestamp = Column(String, nullable=False)

# Dynamic model creation based on actual database structure
def create_dynamic_models():
    """Create SQLAlchemy models dynamically based on database tables."""
    table_info = get_table_info()
    models = {}
    
    for table_name, info in table_info.items():
        # Create class name (PascalCase)
        class_name = ''.join(word.capitalize() for word in table_name.split('_'))
        
        # Create column definitions
        columns = {'__tablename__': table_name}
        
        for col in info['columns']:
            col_name = col['name']
            col_type = col['type'].upper()
            
            if col_type in ('INTEGER', 'INT'):
                if col['primary_key']:
                    columns[col_name] = Column(Integer, primary_key=True)
                else:
                    columns[col_name] = Column(Integer, nullable=col['nullable'])
            elif col_type in ('REAL', 'FLOAT', 'DOUBLE'):
                columns[col_name] = Column(Float, nullable=col['nullable'])
            else:  # TEXT, VARCHAR, etc.
                columns[col_name] = Column(Text, nullable=col['nullable'])
        
        # Create the model class dynamically
        model_class = type(class_name, (Base,), columns)
        models[table_name] = model_class
        
        # Add to global namespace for easy access
        globals()[class_name] = model_class
    
    return models

class DatabaseManager:
    """Helper class for common database operations."""
    
    def __init__(self, db_path: str = "vct.db"):
        self.db_path = db_path
        self.session = None
        
    def __enter__(self):
        self.session = get_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute raw SQL query and return results."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_table_names(self) -> List[str]:
        """Get all table names in the database."""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name != 'import_metadata'"
        results = self.execute_query(query)
        return [row[0] for row in results]
    
    def get_column_names(self, table_name: str) -> List[str]:
        """Get column names for a specific table."""
        query = f"PRAGMA table_info({table_name})"
        results = self.execute_query(query)
        return [row[1] for row in results]
    
    def query_table(self, table_name: str, limit: int = None, where: str = None) -> List[tuple]:
        """Query a table with optional limit and where clause."""
        query = f"SELECT * FROM {table_name}"
        
        if where:
            query += f" WHERE {where}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query)

# Convenience functions for common queries
def get_matches_overview(limit: int = 100) -> List[tuple]:
    """Get matches overview data."""
    with DatabaseManager() as db:
        tables = db.get_table_names()
        
        # Look for overview table
        overview_tables = [t for t in tables if 'overview' in t.lower()]
        if overview_tables:
            return db.query_table(overview_tables[0], limit=limit)
        
        # Look for matches table
        match_tables = [t for t in tables if 'match' in t.lower()]
        if match_tables:
            return db.query_table(match_tables[0], limit=limit)
        
        return []

def get_player_stats(player_name: str = None, limit: int = 100) -> List[tuple]:
    """Get player statistics."""
    with DatabaseManager() as db:
        tables = db.get_table_names()
        
        # Look for player stats table
        player_tables = [t for t in tables if 'player' in t.lower() and 'stat' in t.lower()]
        if player_tables:
            table = player_tables[0]
            where = f"player = '{player_name}'" if player_name else None
            return db.query_table(table, limit=limit, where=where)
        
        return []

def get_agent_stats(agent_name: str = None, limit: int = 100) -> List[tuple]:
    """Get agent statistics."""
    with DatabaseManager() as db:
        tables = db.get_table_names()
        
        # Look for agent tables
        agent_tables = [t for t in tables if 'agent' in t.lower()]
        if agent_tables:
            table = agent_tables[0]
            where = f"agent = '{agent_name}'" if agent_name else None
            return db.query_table(table, limit=limit, where=where)
        
        return []

def get_team_stats(team_name: str = None, limit: int = 100) -> List[tuple]:
    """Get team statistics."""
    with DatabaseManager() as db:
        tables = db.get_table_names()
        
        # Look for team tables
        team_tables = [t for t in tables if 'team' in t.lower()]
        if team_tables:
            table = team_tables[0]
            columns = db.get_column_names(table)
            
            # Find team column
            team_col = None
            for col in columns:
                if 'team' in col.lower():
                    team_col = col
                    break
            
            if team_col and team_name:
                where = f"{team_col} = '{team_name}'"
                return db.query_table(table, limit=limit, where=where)
            else:
                return db.query_table(table, limit=limit)
        
        return []

# Initialize models when module is imported
if os.path.exists("vct.db"):
    try:
        init_database()
        dynamic_models = create_dynamic_models()
        print(f"Loaded {len(dynamic_models)} database models")
    except Exception as e:
        print(f"Warning: Could not initialize database models: {e}")
else:
    print("Database not found. Run the import script first: python scripts/import_to_sqlite.py")

# Export commonly used items
__all__ = [
    'Base', 'get_session', 'get_engine', 'init_database',
    'DatabaseManager', 'ImportMetadata', 'get_table_info',
    'get_matches_overview', 'get_player_stats', 'get_agent_stats', 'get_team_stats'
]
