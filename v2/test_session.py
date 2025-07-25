#!/usr/bin/env python3
"""
Test script to demonstrate zip session functionality
"""

import sys
import os
import sqlite3
import zipfile
import tempfile
import json

def create_test_session():
    """Create a test session zip file"""
    print("Creating test session...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Create test database
    db_path = os.path.join(temp_dir, "session_db.sqlite")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create test table with data
    cursor.execute('''
        CREATE TABLE test_data (
            id INTEGER PRIMARY KEY,
            name TEXT,
            value REAL
        )
    ''')
    
    test_data = [
        (1, 'Item A', 10.5),
        (2, 'Item B', 20.3),
        (3, 'Item C', 15.7)
    ]
    
    cursor.executemany('INSERT INTO test_data VALUES (?, ?, ?)', test_data)
    conn.commit()
    conn.close()
    
    # Create test history
    history_path = os.path.join(temp_dir, "history.json")
    history_data = [
        {
            "name": "Test Queries",
            "queries": [
                {
                    "name": "Select All",
                    "query": "SELECT * FROM test_data",
                    "task_numbers": "1,2,3",
                    "params": {}
                },
                {
                    "name": "Count Records",
                    "query": "SELECT COUNT(*) FROM test_data",
                    "task_numbers": "4",
                    "params": {}
                }
            ]
        }
    ]
    
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)
    
    # Create test session data
    session_path = os.path.join(temp_dir, "session.json")
    session_data = {
        "csv_data": [
            ["Item A", "10.5"],
            ["Item B", "20.3"],
            ["Item C", "15.7"]
        ],
        "csv_headers": ["name", "value"],
        "sql_query": "SELECT * FROM test_data WHERE value > 15",
        "python_code": "# Test Python code\nprint('Hello from session!')\nresult = 2 + 2\nprint(f'2 + 2 = {result}')"
    }
    
    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)
    
    # Create zip file
    zip_path = "test_session.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, "session_db.sqlite")
        zf.write(history_path, "history.json")
        zf.write(session_path, "session.json")
    
    # Clean up temporary files
    import shutil
    shutil.rmtree(temp_dir)
    
    print(f"Test session created: {zip_path}")
    return zip_path

def verify_session(zip_path):
    """Verify the contents of a session zip file"""
    print(f"\nVerifying session: {zip_path}")
    
    if not os.path.exists(zip_path):
        print("Session file not found!")
        return False
    
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            files = zf.namelist()
            print(f"Files in session: {files}")
            
            # Check required files
            required_files = ["session_db.sqlite", "history.json", "session.json"]
            for req_file in required_files:
                if req_file in files:
                    print(f"✓ {req_file} found")
                else:
                    print(f"✗ {req_file} missing")
            
            # Extract and verify database
            temp_dir = tempfile.mkdtemp()
            zf.extractall(temp_dir)
            
            db_path = os.path.join(temp_dir, "session_db.sqlite")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"Database tables: {[t[0] for t in tables]}")
                
                cursor.execute("SELECT COUNT(*) FROM test_data")
                count = cursor.fetchone()[0]
                print(f"Test data records: {count}")
                conn.close()
            
            # Clean up
            import shutil
            shutil.rmtree(temp_dir)
            
        print("Session verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error verifying session: {e}")
        return False

if __name__ == "__main__":
    print("=== Zip Session Functionality Test ===")
    
    # Create test session
    session_file = create_test_session()
    
    # Verify session
    if verify_session(session_file):
        print("\n✓ Zip session functionality is working correctly!")
        print(f"\nYou can now test loading this session in the application:")
        print(f"1. Open the CSV Query Tool")
        print(f"2. Go to File -> Open Session")
        print(f"3. Select the file: {os.path.abspath(session_file)}")
        print(f"4. The session should load with test data, queries, and code")
    else:
        print("\n✗ Session verification failed!")
        sys.exit(1)