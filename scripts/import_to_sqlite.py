#!/usr/bin/env python3
"""
VCT Dashboard Data Import Script

This script scans the data/ directory and all vct_* subfolders for CSV files,
then imports them into a single SQLite database with proper schema inference.

Usage:
    python scripts/import_to_sqlite.py

Output:
    Creates vct.db SQLite database in the project root
"""

import os
import csv
import sqlite3
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Any
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VCTDataImporter:
    """Handles importing CSV data from VCT dashboard into SQLite database."""
    
    def __init__(self, data_dir: str = "data", db_path: str = "vct.db"):
        self.data_dir = Path(data_dir)
        self.db_path = Path(db_path)
        self.connection = None
        self.imported_tables = []
        
    def connect_db(self):
        """Create database connection and enable foreign keys."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def close_db(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def sanitize_column_name(self, column_name: str) -> str:
        """Sanitize column names for SQLite compatibility."""
        # Remove special characters and replace with underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(column_name).strip())
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = 'col_' + sanitized
        # Handle empty names
        if not sanitized:
            sanitized = 'unnamed_column'
        return sanitized.lower()
    
    def generate_table_name(self, csv_path: Path) -> str:
        """Generate table name based on folder structure and filename."""
        relative_path = csv_path.relative_to(self.data_dir)
        parts = list(relative_path.parts[:-1])  # All parts except filename
        filename = csv_path.stem  # Filename without extension
        
        # Combine folder parts with filename
        if parts:
            table_name = '_'.join(parts + [filename])
        else:
            table_name = filename
        
        # Sanitize the table name
        table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
        table_name = re.sub(r'_+', '_', table_name).strip('_').lower()
        
        return table_name
    
    def infer_column_type(self, values: List[Any]) -> str:
        """Infer SQLite column type from sample values."""
        # Remove None/null values for type inference
        non_null_values = [v for v in values if v is not None and str(v).strip() != '']
        
        if not non_null_values:
            return "TEXT"
        
        # Try to determine if all values are integers
        all_integers = True
        all_floats = True
        
        for value in non_null_values[:100]:  # Sample first 100 values
            str_val = str(value).strip()
            
            # Check for integer
            try:
                int(str_val)
            except (ValueError, TypeError):
                all_integers = False
            
            # Check for float
            try:
                float(str_val)
            except (ValueError, TypeError):
                all_floats = False
                
            if not all_integers and not all_floats:
                break
        
        if all_integers:
            return "INTEGER"
        elif all_floats:
            return "REAL"
        else:
            return "TEXT"
    
    def create_table_schema(self, df: pd.DataFrame, table_name: str) -> str:
        """Create SQL table schema based on DataFrame."""
        columns = []
        
        for col in df.columns:
            sanitized_col = self.sanitize_column_name(col)
            col_type = self.infer_column_type(df[col].dropna().tolist())
            columns.append(f"{sanitized_col} {col_type}")
        
        schema = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    "
        schema += ",\n    ".join(columns)
        schema += "\n)"
        
        return schema
    
    def import_csv_file(self, csv_path: Path) -> bool:
        """Import a single CSV file into the database."""
        try:
            logger.info(f"Processing: {csv_path}")
            
            # Generate table name
            table_name = self.generate_table_name(csv_path)
            
            # Read CSV with error handling
            try:
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                df = None
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(csv_path, encoding=encoding, on_bad_lines='skip')
                        logger.debug(f"Successfully read {csv_path} with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if df is None:
                    logger.error(f"Could not read {csv_path} with any encoding")
                    return False
                
            except Exception as e:
                logger.error(f"Error reading CSV {csv_path}: {e}")
                return False
            
            # Skip empty files
            if df.empty:
                logger.warning(f"Skipping empty file: {csv_path}")
                return False
            
            # Sanitize column names
            df.columns = [self.sanitize_column_name(col) for col in df.columns]
            
            # Handle duplicate column names
            seen_cols = {}
            new_cols = []
            for col in df.columns:
                if col in seen_cols:
                    seen_cols[col] += 1
                    new_cols.append(f"{col}_{seen_cols[col]}")
                else:
                    seen_cols[col] = 0
                    new_cols.append(col)
            df.columns = new_cols
            
            # Create table schema
            schema = self.create_table_schema(df, table_name)
            
            # Execute schema creation
            self.connection.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.connection.execute(schema)
            
            # Insert data
            df.to_sql(table_name, self.connection, if_exists='append', index=False, method='multi')
            
            # Get row count
            cursor = self.connection.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            logger.info(f"✅ Imported {table_name}: {row_count} rows, {len(df.columns)} columns")
            self.imported_tables.append({
                'table_name': table_name,
                'source_file': str(csv_path),
                'row_count': row_count,
                'column_count': len(df.columns)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing {csv_path}: {e}")
            return False
    
    def find_csv_files(self) -> List[Path]:
        """Find all CSV files in the data directory and subdirectories."""
        csv_files = []
        
        if not self.data_dir.exists():
            logger.error(f"Data directory does not exist: {self.data_dir}")
            return csv_files
        
        # Recursively find all CSV files
        for csv_file in self.data_dir.rglob("*.csv"):
            if csv_file.is_file():
                csv_files.append(csv_file)
        
        logger.info(f"Found {len(csv_files)} CSV files")
        return sorted(csv_files)
    
    def create_metadata_table(self):
        """Create a metadata table with import information."""
        try:
            metadata_schema = """
            CREATE TABLE IF NOT EXISTS import_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                source_file TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                column_count INTEGER NOT NULL,
                import_timestamp TEXT NOT NULL,
                UNIQUE(table_name)
            )
            """
            
            self.connection.execute("DROP TABLE IF EXISTS import_metadata")
            self.connection.execute(metadata_schema)
            
            # Insert metadata for all imported tables
            import_timestamp = datetime.now().isoformat()
            for table_info in self.imported_tables:
                self.connection.execute("""
                    INSERT INTO import_metadata 
                    (table_name, source_file, row_count, column_count, import_timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    table_info['table_name'],
                    table_info['source_file'],
                    table_info['row_count'],
                    table_info['column_count'],
                    import_timestamp
                ))
            
            logger.info("✅ Created import metadata table")
            
        except Exception as e:
            logger.error(f"Error creating metadata table: {e}")
    
    def create_indexes(self):
        """Create useful indexes on common columns."""
        try:
            common_index_columns = [
                'tournament', 'stage', 'match_type', 'match_name', 'map', 
                'player', 'team', 'agent', 'agents', 'year', 'date'
            ]
            
            cursor = self.connection.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name != 'import_metadata'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            indexes_created = 0
            for table in tables:
                # Get table columns
                cursor = self.connection.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                
                # Create indexes for matching columns
                for col in common_index_columns:
                    if col in columns:
                        try:
                            index_name = f"idx_{table}_{col}"
                            self.connection.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({col})")
                            indexes_created += 1
                        except Exception as e:
                            logger.debug(f"Could not create index {index_name}: {e}")
            
            logger.info(f"✅ Created {indexes_created} indexes for better query performance")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def generate_summary_report(self):
        """Generate a summary report of the import process."""
        try:
            # Database file size
            db_size = self.db_path.stat().st_size / (1024 * 1024)  # MB
            
            # Total tables and rows
            cursor = self.connection.execute("""
                SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name != 'import_metadata'
            """)
            total_tables = cursor.fetchone()[0]
            
            total_rows = sum(table['row_count'] for table in self.imported_tables)
            
            print("\n" + "="*60)
            print("VCT DATA IMPORT SUMMARY")
            print("="*60)
            print(f"Database file: {self.db_path}")
            print(f"Database size: {db_size:.2f} MB")
            print(f"Total tables: {total_tables}")
            print(f"Total rows imported: {total_rows:,}")
            print(f"Import timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\nTables created:")
            print("-" * 60)
            
            for table in sorted(self.imported_tables, key=lambda x: x['table_name']):
                print(f"  {table['table_name']:<30} {table['row_count']:>8,} rows")
            
            print("-" * 60)
            print(f"✅ Import completed successfully!")
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
    
    def run_import(self):
        """Run the complete import process."""
        try:
            logger.info("Starting VCT data import process...")
            
            # Connect to database
            self.connect_db()
            
            # Find all CSV files
            csv_files = self.find_csv_files()
            
            if not csv_files:
                logger.warning("No CSV files found to import")
                return
            
            # Import each CSV file
            successful_imports = 0
            failed_imports = 0
            
            for csv_file in csv_files:
                if self.import_csv_file(csv_file):
                    successful_imports += 1
                else:
                    failed_imports += 1
            
            # Create metadata table
            self.create_metadata_table()
            
            # Create indexes
            self.create_indexes()
            
            # Commit all changes
            self.connection.commit()
            
            # Generate summary
            self.generate_summary_report()
            
            logger.info(f"Import process completed: {successful_imports} successful, {failed_imports} failed")
            
        except Exception as e:
            logger.error(f"Import process failed: {e}")
            if self.connection:
                self.connection.rollback()
            raise
        finally:
            self.close_db()


def main():
    """Main function to run the import process."""
    try:
        # Change to project root directory
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        os.chdir(project_root)
        
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Run the import
        importer = VCTDataImporter()
        importer.run_import()
        
    except KeyboardInterrupt:
        logger.info("Import process interrupted by user")
    except Exception as e:
        logger.error(f"Import process failed: {e}")
        raise


if __name__ == "__main__":
    main()
