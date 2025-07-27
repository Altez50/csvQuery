#!/usr/bin/env python3
"""
Test script for the plugin comparison system
"""

import sys
import os
import pandas as pd
from PyQt5.QtWidgets import QApplication

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from utils.plugin_loader import PluginLoader
from plugins.row_compare import RowComparePlugin
from plugins.column_compare import ColumnComparePlugin
from plugins.hash_compare import HashComparePlugin
from plugins.schema_compare import SchemaComparePlugin

def create_test_data():
    """Create test CSV files for comparison"""
    # Create test data directory
    test_dir = "test_data"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    # Test data 1
    df1 = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 28, 32],
        'city': ['New York', 'London', 'Paris', 'Tokyo', 'Berlin']
    })
    df1.to_csv(os.path.join(test_dir, 'data1.csv'), index=False)
    
    # Test data 2 (with some differences)
    df2 = pd.DataFrame({
        'id': [1, 2, 3, 4, 6],  # Changed: 5 -> 6
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Frank'],  # Changed: Eve -> Frank
        'age': [25, 31, 35, 28, 29],  # Changed: 30 -> 31, 32 -> 29
        'city': ['New York', 'London', 'Paris', 'Tokyo', 'Madrid'],  # Changed: Berlin -> Madrid
        'country': ['USA', 'UK', 'France', 'Japan', 'Spain']  # New column
    })
    df2.to_csv(os.path.join(test_dir, 'data2.csv'), index=False)
    
    # Test data 3 (completely different structure)
    df3 = pd.DataFrame({
        'product_id': [101, 102, 103],
        'product_name': ['Laptop', 'Mouse', 'Keyboard'],
        'price': [999.99, 29.99, 79.99]
    })
    df3.to_csv(os.path.join(test_dir, 'data3.csv'), index=False)
    
    print(f"Created test data in {test_dir}/")
    return [
        os.path.abspath(os.path.join(test_dir, 'data1.csv')),
        os.path.abspath(os.path.join(test_dir, 'data2.csv')),
        os.path.abspath(os.path.join(test_dir, 'data3.csv'))
    ]

def test_plugin_loader():
    """Test the plugin loader functionality"""
    print("\n=== Testing Plugin Loader ===")
    
    loader = PluginLoader()
    plugins = loader.get_available_plugins()
    
    print(f"Found {len(plugins)} plugins:")
    for name, plugin_class in plugins.items():
        try:
            plugin = plugin_class()
            print(f"  - {plugin.get_name()} (v{plugin.get_version()})")
            print(f"    Description: {plugin.get_description()}")
        except Exception as e:
            print(f"  - {name}: Error loading - {e}")
    
    return plugins

def test_plugins_with_data(plugins, test_files):
    """Test each plugin with the test data"""
    print("\n=== Testing Plugins with Data ===")
    
    # Load test data
    df1 = pd.read_csv(test_files[0])
    df2 = pd.read_csv(test_files[1])
    df3 = pd.read_csv(test_files[2])
    
    print(f"\nData 1 shape: {df1.shape}")
    print(f"Data 2 shape: {df2.shape}")
    print(f"Data 3 shape: {df3.shape}")
    
    for name, plugin_class in plugins.items():
        print(f"\n--- Testing {name} ---")
        try:
            plugin = plugin_class()
            
            # Test with similar data (df1 vs df2)
            print("Comparing similar data (data1 vs data2):")
            result = plugin.compare(df1, df2)
            print(f"  Result keys: {list(result.keys())}")
            if 'summary' in result:
                print(f"  Summary: {result['summary']}")
            
            # Test with different data (df1 vs df3)
            print("Comparing different data (data1 vs data3):")
            result = plugin.compare(df1, df3)
            print(f"  Result keys: {list(result.keys())}")
            if 'summary' in result:
                print(f"  Summary: {result['summary']}")
                
        except Exception as e:
            print(f"  Error: {e}")

def test_plugin_parameters():
    """Test plugin parameter functionality"""
    print("\n=== Testing Plugin Parameters ===")
    
    plugins = [
        RowComparePlugin(),
        ColumnComparePlugin(),
        HashComparePlugin(),
        SchemaComparePlugin()
    ]
    
    for plugin in plugins:
        print(f"\n--- {plugin.get_name()} Parameters ---")
        try:
            params = plugin.get_parameters()
            if params:
                for param_name, param_info in params.items():
                    print(f"  {param_name}: {param_info}")
            else:
                print("  No configurable parameters")
        except Exception as e:
            print(f"  Error getting parameters: {e}")

def main():
    """Main test function"""
    print("Plugin System Test")
    print("==================")
    
    # Create test data
    test_files = create_test_data()
    
    # Test plugin loader
    plugins = test_plugin_loader()
    
    if not plugins:
        print("No plugins found! Check plugin directory and imports.")
        return
    
    # Test plugin parameters
    test_plugin_parameters()
    
    # Test plugins with data
    test_plugins_with_data(plugins, test_files)
    
    print("\n=== Test Complete ===")
    print("\nTo test the GUI:")
    print("1. Run the main application")
    print("2. Right-click on CSV files in the file tree")
    print("3. Use 'Add to Comparison' and 'Compare With...' options")

if __name__ == "__main__":
    # Create QApplication for testing (required for some Qt components)
    app = QApplication(sys.argv)
    
    try:
        main()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Don't start the event loop, just exit
    sys.exit(0)