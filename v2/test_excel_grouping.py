#!/usr/bin/env python3
"""
Test script for Excel grouping functionality in CSV Query Tool.
This script creates a sample Excel file with multiple sheets and demonstrates
the new grouping feature in the tables tree.
"""

import pandas as pd
import os
import sqlite3
from table_manager import TableManager

def create_sample_excel_file():
    """Create a sample Excel file with multiple sheets for testing"""
    # Sample data for different sheets
    sales_data = {
        'Product': ['Laptop', 'Mouse', 'Keyboard', 'Monitor'],
        'Price': [999.99, 25.50, 75.00, 299.99],
        'Quantity': [10, 50, 30, 15],
        'Total': [9999.90, 1275.00, 2250.00, 4499.85]
    }
    
    employees_data = {
        'Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
        'Department': ['IT', 'Sales', 'HR', 'Marketing'],
        'Salary': [75000, 65000, 55000, 60000],
        'Years': [5, 3, 8, 2]
    }
    
    inventory_data = {
        'Item': ['Widget A', 'Widget B', 'Widget C', 'Widget D'],
        'Stock': [100, 250, 75, 180],
        'Location': ['Warehouse A', 'Warehouse B', 'Warehouse A', 'Warehouse C'],
        'Status': ['In Stock', 'Low Stock', 'In Stock', 'In Stock']
    }
    
    # Create DataFrames
    sales_df = pd.DataFrame(sales_data)
    employees_df = pd.DataFrame(employees_data)
    inventory_df = pd.DataFrame(inventory_data)
    
    # Write to Excel file with multiple sheets
    excel_file = 'sample_company_data.xlsx'
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        sales_df.to_excel(writer, sheet_name='Sales', index=False)
        employees_df.to_excel(writer, sheet_name='Employees', index=False)
        inventory_df.to_excel(writer, sheet_name='Inventory', index=False)
    
    print(f"✅ Created sample Excel file: {excel_file}")
    print(f"   📊 Contains 3 sheets: Sales, Employees, Inventory")
    return excel_file

def simulate_excel_loading(excel_file):
    """Simulate loading Excel file into database (like the main application does)"""
    print(f"\n🔄 Simulating Excel file loading...")
    
    # Create in-memory database
    conn = sqlite3.connect(':memory:')
    
    try:
        # Read all sheets from Excel file
        excel_data = pd.ExcelFile(excel_file)
        sheet_names = excel_data.sheet_names
        base_name = os.path.splitext(os.path.basename(excel_file))[0]
        
        print(f"   📁 Base name: {base_name}")
        print(f"   📋 Found {len(sheet_names)} sheets: {', '.join(sheet_names)}")
        
        # Create tables for each sheet (simulating the main app logic)
        created_tables = []
        for sheet_name in sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Create table name like the main app does
            table_name = f"{base_name}_{sheet_name}"
            
            # Create table in database
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            created_tables.append(table_name)
            
            print(f"   ✅ Created table: {table_name} ({len(df)} rows, {len(df.columns)} columns)")
        
        # Test the grouping logic
        print(f"\n🔍 Testing grouping logic...")
        test_grouping_logic(conn, created_tables)
        
    except Exception as e:
        print(f"❌ Error during simulation: {e}")
    finally:
        conn.close()

def test_grouping_logic(conn, table_names):
    """Test the grouping logic that would be used in refresh_tables"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    # Group tables by Excel file origin (same logic as in table_manager.py)
    excel_groups = {}
    standalone_tables = []
    
    for table in tables:
        table_name = table[0]
        if not table_name.startswith('sqlite_'):  # Skip system tables
            # Check if table name follows Excel pattern: filename_sheetname
            if '_' in table_name:
                # Try to identify Excel file groups
                parts = table_name.split('_')
                if len(parts) >= 2:
                    # Assume last part is sheet name, rest is file name
                    potential_file = '_'.join(parts[:-1])
                    sheet_name = parts[-1]
                    
                    # Check if there are other tables with same file prefix
                    similar_tables = [t[0] for t in tables if t[0].startswith(potential_file + '_') and not t[0].startswith('sqlite_')]
                    
                    if len(similar_tables) > 1:
                        # This is part of an Excel group
                        if potential_file not in excel_groups:
                            excel_groups[potential_file] = []
                        excel_groups[potential_file].append(table_name)
                    else:
                        standalone_tables.append(table_name)
                else:
                    standalone_tables.append(table_name)
            else:
                standalone_tables.append(table_name)
    
    # Display results
    print(f"   📊 Excel Groups Found: {len(excel_groups)}")
    for file_name, table_list in excel_groups.items():
        print(f"      🗂️  Group: {file_name} ({len(table_list)} sheets)")
        for table_name in sorted(table_list):
            sheet_name = table_name.replace(file_name + '_', '', 1)
            print(f"         📋 {sheet_name} -> {table_name}")
    
    print(f"   📋 Standalone Tables: {len(standalone_tables)}")
    for table_name in standalone_tables:
        print(f"      📄 {table_name}")
    
    return excel_groups, standalone_tables

def main():
    """Main test function"""
    print("🧪 Testing Excel Grouping Functionality")
    print("=" * 50)
    
    # Create sample Excel file
    excel_file = create_sample_excel_file()
    
    # Simulate loading it into the application
    simulate_excel_loading(excel_file)
    
    print("\n✅ Test completed!")
    print("\n📝 Instructions for manual testing:")
    print("   1. Open the CSV Query Tool application")
    print(f"   2. Load the Excel file: {excel_file}")
    print("   3. Check the Tables tab - you should see:")
    print("      📊 sample_company_data (3 sheets) - expandable group")
    print("         📋 Sales")
    print("         📋 Employees")
    print("         📋 Inventory")
    print("   4. Right-click on the group to see 'Delete Entire Group' option")
    print("   5. Double-click individual sheets to load them into CSV editor")
    print("   6. Double-click the group to expand/collapse it")

if __name__ == "__main__":
    main()