#!/usr/bin/env python3
"""
Test script to verify that the main window title bar displays the currently edited CSV file name.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from vscode_main_window import VSCodeMainWindow

def test_title_bar_functionality():
    """Test that the title bar updates when CSV files are loaded"""
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = VSCodeMainWindow()
    
    # Test 1: Initial title should be the base title
    initial_title = main_window.windowTitle()
    print(f"Initial title: {initial_title}")
    assert "CSV Query Tool - VSCode Style" in initial_title
    
    # Test 2: Simulate loading a CSV file
    csv_editor = main_window.csv_editor
    
    # Set up some test data
    test_headers = ['Name', 'Age', 'City']
    test_data = [['John', '25', 'New York'], ['Jane', '30', 'London']]
    
    # Simulate loading a file by setting current_file and calling update_main_window_title
    csv_editor.current_file = "C:\\test\\sample.csv"
    csv_editor.csv_headers = test_headers
    csv_editor.csv_data = test_data
    csv_editor.update_main_window_title()
    
    # Check that title now includes the filename
    updated_title = main_window.windowTitle()
    print(f"Updated title: {updated_title}")
    assert "sample.csv" in updated_title
    assert "CSV Query Tool - VSCode Style - sample.csv" == updated_title
    
    # Test 3: Clear the table and check title resets
    csv_editor.clear_table()
    cleared_title = main_window.windowTitle()
    print(f"Cleared title: {cleared_title}")
    assert cleared_title == "CSV Query Tool - VSCode Style"
    
    print("All title bar tests passed!")
    
    # Don't show the GUI, just test the functionality
    app.quit()
    return True

if __name__ == "__main__":
    try:
        test_title_bar_functionality()
        print("\n✅ Title bar functionality is working correctly!")
        print("The main window title will now display the name of the currently edited CSV file.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)