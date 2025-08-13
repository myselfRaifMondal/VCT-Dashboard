#!/usr/bin/env python3
"""
VCT Dashboard Enhanced Data Import Script

This script handles the import of large CSV files that failed in the initial import
by processing them in smaller batches to avoid SQLite's column/variable limits.

Usage:
    python scripts/import_large_files.py
"""

import os
import sqlite3
import pandas as pd
from pathlib import Path
import logging
from typing import List
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_large_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LargeFileImporter:
    """Handles importing large CSV files in batches."""
    
    def __init__(self, data_dir: str = "data", db_path: str = "vct.db", batch_size: int = 1000):
        self.data_dir = Path(data_dir)
        self.db_path = Path(db_path)
        self.batch_size = batch_size
        self.connection = None
        self.imported_files = []
        
        # Files that failed in the previous import due to size
        self.large_files = [
            "data/all_ids/all_matches_games_ids.csv",
            "data/vct_2021/agents/agents_pick_rates.csv",
            "data/vct_2021/agents/teams_picked_agents.csv",
            "data/vct_2021/matches/eco_rounds.csv",
            "data/vct_2021/matches/eco_stats.csv",
            "data/vct_2021/matches/kills.csv",
            "data/vct_2021/matches/kills_stats.csv",
            "data/vct_2021/matches/overview.csv",
            "data/vct_2021/matches/rounds_kills.csv",
            "data/vct_2021/matches/win_loss_methods_count.csv",
            "data/vct_2021/matches/win_loss_methods_round_number.csv",
            "data/vct_2021/players_stats/players_stats.csv",
            "data/vct_2022/agents/agents_pick_rates.csv",
            "data/vct_2022/agents/teams_picked_agents.csv",
            "data/vct_2022/matches/eco_rounds.csv",
            "data/vct_2022/matches/eco_stats.csv",
            "data/vct_2022/matches/kills.csv",
            "data/vct_2022/matches/kills_stats.csv",
            "data/vct_2022/matches/overview.csv",
            "data/vct_2022/matches/rounds_kills.csv",
            "data/vct_2022/matches/win_loss_methods_round_number.csv",
            "data/vct_2022/players_stats/players_stats.csv",
            "data/vct_2023/matches/eco_rounds.csv",
            "data/vct_2023/matches/kills.csv",
            "data/vct_2023/matches/overview.csv",
            "data/vct_2023/matches/rounds_kills.csv",
            "data/vct_2023/matches/win_loss_methods_round_number.csv",
            "data/vct_2023/players_stats/players_stats.csv",
            "data/vct_2024/matches/eco_rounds.csv",
            "data/vct_2024/matches/kills.csv",
            "data/vct_2024/matches/overview.csv",
            "data/vct_2024/matches/rounds_kills.csv",
            "data/vct_2024/matches/win_loss_methods_round_number.csv",
            "data/vct_2024/players_stats/players_stats.csv",
            "data/vct_2025/matches/eco_rounds.csv",
            "data/vct_2025/matches/kills.csv",
            "data/vct_2025/matches/overview.csv",
            "data/vct_2025/matches/rounds_kills.csv",
            "data/vct_2025/matches/win_loss_methods_round_number.csv",
            "data/vct_2025/players_stats/players_stats.csv"
        ]
    
    def connect_db(self):
        """Create database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.execute("PRAGMA journal_mode = WAL")
            self.connection.execute("PRAGMA synchronous = NORMAL")
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
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(column_name).strip())
        sanitized = re.sub(r'_+', '_', sanitized)
        sanitized = sanitized.strip('_')
        if sanitized and sanitized[0].isdigit():
            sanitized = 'col_' + sanitized
        if not sanitized:
            sanitized = 'unnamed_column'
        return sanitized.lower()
    
    def generate_table_name(self, csv_path: Path) -> str:
        """Generate table name based on folder structure and filename."""
        import re
        relative_path = csv_path.relative_to(self.data_dir)
        parts = list(relative_path.parts[:-1])
        filename = csv_path.stem
        
        if parts:
            table_name = '_'.join(parts + [filename])
        else:
            table_name = filename
        
        table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
        table_name = re.sub(r'_+', '_', table_name).strip('_').lower()
        
        return table_name
    
    def infer_column_type(self, series: pd.Series) -> str:
        """Infer SQLite column type from pandas series."""
        # Remove null values for type inference
        non_null_series = series.dropna()
        
        if len(non_null_series) == 0:
            return "TEXT"
        
        # Check if all values can be converted to integers
        try:
            pd.to_numeric(non_null_series, downcast='integer')
            # Check if they're actually integers (no decimal part)
            if all(float(x).is_integer() for x in non_null_series.head(100) if pd.notna(x)):
                return "INTEGER"
        except (ValueError, TypeError):
            pass
        
        # Check if all values can be converted to floats
        try:
            pd.to_numeric(non_null_series)
            return "REAL"
        except (ValueError, TypeError):
            pass
        
        return "TEXT"
    
    def create_table_schema(self, df: pd.DataFrame, table_name: str) -> str:
        """Create SQL table schema based on DataFrame."""
        columns = []
        
        for col in df.columns:
            sanitized_col = self.sanitize_column_name(col)
            col_type = self.infer_column_type(df[col])
            columns.append(f"{sanitized_col} {col_type}")
        
        schema = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    "
        schema += ",\n    ".join(columns)
        schema += "\n)"
        
        return schema
    
    def import_csv_in_batches(self, csv_path: Path) -> bool:
        """Import a large CSV file in batches."""
        try:
            logger.info(f"Processing large file in batches: {csv_path}")
            
            # Generate table name
            table_name = self.generate_table_name(csv_path)
            
            # Check if the file exists
            if not csv_path.exists():
                logger.warning(f"File not found: {csv_path}")
                return False
            
            # Read CSV headers first
            try:
                sample_df = pd.read_csv(csv_path, nrows=1000, encoding='utf-8', on_bad_lines='skip')
            except UnicodeDecodeError:
                try:
                    sample_df = pd.read_csv(csv_path, nrows=1000, encoding='latin-1', on_bad_lines='skip')
                except:
                    logger.error(f"Could not read {csv_path} with any encoding")
                    return False
            except Exception as e:
                logger.error(f"Error reading CSV headers {csv_path}: {e}")
                return False
            
            if sample_df.empty:
                logger.warning(f"Skipping empty file: {csv_path}")
                return False
            
            # Sanitize column names
            original_columns = sample_df.columns.tolist()
            sample_df.columns = [self.sanitize_column_name(col) for col in sample_df.columns]
            
            # Handle duplicate column names
            seen_cols = {}
            new_cols = []
            for col in sample_df.columns:
                if col in seen_cols:
                    seen_cols[col] += 1
                    new_cols.append(f"{col}_{seen_cols[col]}")
                else:
                    seen_cols[col] = 0
                    new_cols.append(col)
            sample_df.columns = new_cols
            column_mapping = new_cols
            
            # Create table schema
            schema = self.create_table_schema(sample_df, table_name)
            
            # Drop existing table and create new one
            self.connection.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.connection.execute(schema)
            
            # Read and insert file in chunks
            total_rows = 0
            chunk_num = 0
            
            # Use chunksize to read file in batches
            try:
                encoding = 'utf-8'
                for chunk_df in pd.read_csv(csv_path, chunksize=self.batch_size, encoding=encoding, on_bad_lines='skip'):
                    chunk_num += 1
                    
                    # Sanitize column names for this chunk
                    chunk_df.columns = column_mapping
                    
                    # Insert chunk into database
                    chunk_df.to_sql(table_name, self.connection, if_exists='append', index=False, method='multi')
                    total_rows += len(chunk_df)
                    
                    if chunk_num % 10 == 0:
                        logger.info(f"  Processed {chunk_num} batches, {total_rows:,} rows so far...")
                        self.connection.commit()  # Commit periodically
                        
            except UnicodeDecodeError:
                # Try with latin-1 encoding
                logger.info(f"Retrying with latin-1 encoding for {csv_path}")
                encoding = 'latin-1'
                total_rows = 0
                chunk_num = 0
                
                for chunk_df in pd.read_csv(csv_path, chunksize=self.batch_size, encoding=encoding, on_bad_lines='skip'):
                    chunk_num += 1
                    chunk_df.columns = column_mapping
                    chunk_df.to_sql(table_name, self.connection, if_exists='append', index=False, method='multi')
                    total_rows += len(chunk_df)
                    
                    if chunk_num % 10 == 0:
                        logger.info(f"  Processed {chunk_num} batches, {total_rows:,} rows so far...")
                        self.connection.commit()
            
            # Final commit
            self.connection.commit()
            
            # Verify row count
            cursor = self.connection.execute(f"SELECT COUNT(*) FROM {table_name}")
            final_count = cursor.fetchone()[0]
            
            logger.info(f"✅ Imported {table_name}: {final_count:,} rows, {len(column_mapping)} columns")
            self.imported_files.append({
                'table_name': table_name,
                'source_file': str(csv_path),
                'row_count': final_count,
                'column_count': len(column_mapping)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing {csv_path}: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def update_metadata_table(self):
        """Update the import metadata table with new imports."""
        try:
            from datetime import datetime
            import_timestamp = datetime.now().isoformat()
            
            for file_info in self.imported_files:
                # Insert or update metadata
                self.connection.execute("""
                    INSERT OR REPLACE INTO import_metadata 
                    (table_name, source_file, row_count, column_count, import_timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    file_info['table_name'],
                    file_info['source_file'],
                    file_info['row_count'],
                    file_info['column_count'],
                    import_timestamp
                ))
            
            self.connection.commit()
            logger.info("✅ Updated import metadata table")
            
        except Exception as e:
            logger.error(f"Error updating metadata table: {e}")
    
    def generate_summary(self):
        """Generate a summary of the import process."""
        try:
            db_size = self.db_path.stat().st_size / (1024 * 1024)  # MB
            total_rows = sum(file['row_count'] for file in self.imported_files)
            
            print("\n" + "="*60)
            print("LARGE FILES IMPORT SUMMARY")
            print("="*60)
            print(f"Database file: {self.db_path}")
            print(f"Database size: {db_size:.2f} MB")
            print(f"Files imported: {len(self.imported_files)}")
            print(f"Total rows imported: {total_rows:,}")
            print("\nLarge files imported:")
            print("-" * 60)
            
            for file_info in sorted(self.imported_files, key=lambda x: x['table_name']):
                print(f"  {file_info['table_name']:<40} {file_info['row_count']:>10,} rows")
            
            print("-" * 60)
            print(f"✅ Large file import completed!")
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
    
    def run_import(self):
        """Run the large file import process."""
        try:
            logger.info("Starting large file import process...")
            
            # Connect to database
            self.connect_db()
            
            # Process each large file
            successful_imports = 0
            failed_imports = 0
            
            for file_path in self.large_files:
                csv_path = Path(file_path)
                if self.import_csv_in_batches(csv_path):
                    successful_imports += 1
                else:
                    failed_imports += 1
            
            # Update metadata
            if self.imported_files:
                self.update_metadata_table()
            
            # Generate summary
            self.generate_summary()
            
            logger.info(f"Large file import completed: {successful_imports} successful, {failed_imports} failed")
            
        except Exception as e:
            logger.error(f"Large file import failed: {e}")
            raise
        finally:
            self.close_db()


def main():
    """Main function to run the large file import."""
    try:
        # Change to project root directory
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        os.chdir(project_root)
        
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Run the import with smaller batch size for very large files
        importer = LargeFileImporter(batch_size=500)  # Smaller batches for safety
        importer.run_import()
        
    except KeyboardInterrupt:
        logger.info("Large file import process interrupted by user")
    except Exception as e:
        logger.error(f"Large file import process failed: {e}")
        raise


if __name__ == "__main__":
    main()
