#!/usr/bin/env python3
"""
SQLite Database Conversion Script
Converts SQLite 3.49 database to SQLite3 format (3.7+)
"""

import sqlite3
import shutil
import os
from datetime import datetime

def check_database_info(db_path):
    """Check database version and compatibility info"""
    print(f"Checking database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get database info
        cursor.execute("PRAGMA user_version")
        user_version = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA schema_version")
        schema_version = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA database_list")
        databases = cursor.fetchall()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"User version: {user_version}")
        print(f"Schema version: {schema_version}")
        print(f"Tables found: {[table[0] for table in tables]}")
        
        # Check if we can read the data
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} rows")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return False

def backup_database(db_path):
    """Create a backup of the original database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

def convert_database(old_db_path, new_db_path=None):
    """Convert database to newer SQLite format"""
    if new_db_path is None:
        new_db_path = old_db_path.replace('.db', '_converted.db')
    
    print(f"Converting database from {old_db_path} to {new_db_path}")
    
    try:
        # Create backup first
        backup_path = backup_database(old_db_path)
        if not backup_path:
            print("Failed to create backup. Aborting conversion.")
            return None
        
        # Connect to old database
        old_conn = sqlite3.connect(old_db_path)
        old_cursor = old_conn.cursor()
        
        # Create new database
        new_conn = sqlite3.connect(new_db_path)
        new_cursor = new_conn.cursor()
        
        # Get all tables and their schemas
        old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = old_cursor.fetchall()
        
        total_rows_copied = 0
        
        for table in tables:
            table_name = table[0]
            print(f"Converting table: {table_name}")
            
            # Get table schema
            old_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            schema = old_cursor.fetchone()[0]
            
            # Create table in new database
            new_cursor.execute(schema)
            
            # Copy data with improved error handling
            try:
                old_cursor.execute(f"SELECT * FROM {table_name}")
                rows = old_cursor.fetchall()
                
                if rows:
                    # Get column names and types
                    old_cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = old_cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    
                    # Insert data in batches for better performance
                    batch_size = 1000
                    placeholders = ','.join(['?' for _ in column_names])
                    insert_sql = f"INSERT INTO {table_name} ({','.join(column_names)}) VALUES ({placeholders})"
                    
                    # Process in batches
                    for i in range(0, len(rows), batch_size):
                        batch = rows[i:i + batch_size]
                        new_cursor.executemany(insert_sql, batch)
                    
                    print(f"  Copied {len(rows)} rows")
                    total_rows_copied += len(rows)
                else:
                    print(f"  Table {table_name} is empty")
                    
            except Exception as e:
                print(f"  Error copying data from {table_name}: {e}")
                continue
        
        # Copy indexes with improved handling
        try:
            old_cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
            indexes = old_cursor.fetchall()
            
            for index in indexes:
                index_sql = index[0]
                try:
                    new_cursor.execute(index_sql)
                    print(f"  Created index: {index_sql[:50]}...")
                except Exception as e:
                    print(f"  Warning: Could not create index: {e}")
        except Exception as e:
            print(f"  Warning: Could not copy indexes: {e}")
        
        # Copy triggers
        try:
            old_cursor.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND sql IS NOT NULL")
            triggers = old_cursor.fetchall()
            
            for trigger in triggers:
                trigger_sql = trigger[0]
                try:
                    new_cursor.execute(trigger_sql)
                    print(f"  Created trigger: {trigger_sql[:50]}...")
                except Exception as e:
                    print(f"  Warning: Could not create trigger: {e}")
        except Exception as e:
            print(f"  Warning: Could not copy triggers: {e}")
        
        # Set pragmas for newer SQLite
        try:
            new_cursor.execute("PRAGMA journal_mode=WAL")
            new_cursor.execute("PRAGMA synchronous=NORMAL")
            new_cursor.execute("PRAGMA cache_size=1000")
            new_cursor.execute("PRAGMA foreign_keys=ON")
            print("  Applied modern SQLite pragmas")
        except Exception as e:
            print(f"  Warning: Could not set some pragmas: {e}")
        
        # Commit and close
        new_conn.commit()
        old_conn.close()
        new_conn.close()
        
        print(f"Conversion completed successfully!")
        print(f"New database: {new_db_path}")
        print(f"Backup: {backup_path}")
        print(f"Total rows copied: {total_rows_copied}")
        
        return new_db_path
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        return None

def convert_database_backup_api(old_db_path, new_db_path=None):
    """Convert database using SQLite's backup API (more reliable)"""
    if new_db_path is None:
        new_db_path = old_db_path.replace('.db', '_converted.db')
    
    print(f"Converting database using backup API from {old_db_path} to {new_db_path}")
    
    try:
        # Create backup first
        backup_path = backup_database(old_db_path)
        if not backup_path:
            print("Failed to create backup. Aborting conversion.")
            return None
        
        # Connect to old database
        old_conn = sqlite3.connect(old_db_path)
        
        # Create new database
        new_conn = sqlite3.connect(new_db_path)
        
        # Use SQLite's backup API for reliable conversion
        print("Using SQLite backup API for conversion...")
        old_conn.backup(new_conn)
        
        # Set modern pragmas on the new database
        new_cursor = new_conn.cursor()
        try:
            new_cursor.execute("PRAGMA journal_mode=WAL")
            new_cursor.execute("PRAGMA synchronous=NORMAL")
            new_cursor.execute("PRAGMA cache_size=1000")
            new_cursor.execute("PRAGMA foreign_keys=ON")
            print("Applied modern SQLite pragmas")
        except Exception as e:
            print(f"Warning: Could not set some pragmas: {e}")
        
        # Close connections
        old_conn.close()
        new_conn.close()
        
        print(f"Backup API conversion completed successfully!")
        print(f"New database: {new_db_path}")
        print(f"Backup: {backup_path}")
        
        return new_db_path
        
    except Exception as e:
        print(f"Error during backup API conversion: {e}")
        return None

def convert_database_vacuum(old_db_path, new_db_path=None):
    """Convert database using VACUUM INTO (SQLite 3.27+)"""
    if new_db_path is None:
        new_db_path = old_db_path.replace('.db', '_converted.db')
    
    print(f"Converting database using VACUUM INTO from {old_db_path} to {new_db_path}")
    
    try:
        # Create backup first
        backup_path = backup_database(old_db_path)
        if not backup_path:
            print("Failed to create backup. Aborting conversion.")
            return None
        
        # Connect to old database and use VACUUM INTO
        conn = sqlite3.connect(old_db_path)
        conn.execute(f"VACUUM INTO '{new_db_path}'")
        conn.close()
        
        # Apply modern pragmas to the new database
        new_conn = sqlite3.connect(new_db_path)
        new_cursor = new_conn.cursor()
        try:
            new_cursor.execute("PRAGMA journal_mode=WAL")
            new_cursor.execute("PRAGMA synchronous=NORMAL")
            new_cursor.execute("PRAGMA cache_size=1000")
            new_cursor.execute("PRAGMA foreign_keys=ON")
            print("Applied modern SQLite pragmas")
        except Exception as e:
            print(f"Warning: Could not set some pragmas: {e}")
        new_conn.close()
        
        print(f"VACUUM INTO conversion completed successfully!")
        print(f"New database: {new_db_path}")
        print(f"Backup: {backup_path}")
        
        return new_db_path
        
    except sqlite3.OperationalError as e:
        if "VACUUM INTO" in str(e):
            print("VACUUM INTO not supported in this SQLite version")
            return None
        else:
            print(f"Error during VACUUM conversion: {e}")
            return None
    except Exception as e:
        print(f"Error during VACUUM conversion: {e}")
        return None

def test_converted_database(db_path):
    """Test the converted database"""
    print(f"\nTesting converted database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables in converted DB: {[table[0] for table in tables]}")
        
        # Test data access
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} rows")
            
            # Test a sample query
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                print(f"    Sample data: {sample}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error testing converted database: {e}")
        return False

def main():
    """Main conversion process with multiple conversion methods"""
    db_path = "intro/ind.db"
    
    print("SQLite Database Conversion Tool")
    print("=" * 40)
    
    # Check original database
    if not check_database_info(db_path):
        print("Cannot proceed with conversion.")
        return
    
    # Try multiple conversion methods in order of preference
    conversion_methods = [
        ("VACUUM INTO", convert_database_vacuum),
        ("Backup API", convert_database_backup_api),
        ("Manual Table-by-Table", convert_database)
    ]
    
    converted_path = None
    successful_method = None
    
    for method_name, method_func in conversion_methods:
        print(f"\nTrying {method_name} conversion method...")
        converted_path = method_func(db_path)
        
        if converted_path:
            successful_method = method_name
            print(f"✓ {method_name} conversion successful!")
            break
        else:
            print(f"✗ {method_name} conversion failed, trying next method...")
    
    if converted_path:
        # Test converted database
        test_converted_database(converted_path)
        
        print(f"\n" + "="*50)
        print(f"CONVERSION SUMMARY:")
        print(f"Original: {db_path}")
        print(f"Converted: {converted_path}")
        print(f"Method used: {successful_method}")
        print(f"Backup: {db_path}.backup_*")
        print("="*50)
        
        # Option to replace original
        response = input(f"\nReplace original database with converted version? (y/N): ")
        if response.lower() == 'y':
            try:
                shutil.move(converted_path, db_path)
                print(f"✓ Original database replaced with converted version.")
            except Exception as e:
                print(f"✗ Error replacing original database: {e}")
        else:
            print(f"Converted database saved as: {converted_path}")
    else:
        print("\n✗ All conversion methods failed!")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main()
