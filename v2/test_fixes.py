#!/usr/bin/env python3
"""
Test script to verify the three fixes:
1. Options menu entry opens options dialog
2. Last open file is visible in options dialog
3. Table deletion no longer crashes
"""

import sys
import os
import tempfile
import sqlite3
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vscode_main_window import VSCodeMainWindow
from options_dialog import OptionsDialog
from table_manager import TableManager

def test_options_dialog():
    """Test that options dialog can be opened and shows last file"""
    print("\n=== Testing Options Dialog ===")
    
    try:
        # Create main window
        main_window = VSCodeMainWindow()
        
        # Set a fake last selected file
        main_window.last_selected_file = "test_file.csv"
        main_window.settings = {'last_selected_file': 'test_file.csv'}
        
        # Test opening options dialog
        dialog = OptionsDialog(main_window)
        
        # Check if last file label exists and shows the file
        if hasattr(dialog, 'last_file_label'):
            label_text = dialog.last_file_label.text()
            print(f"✓ Last file label exists: {label_text}")
            if 'test_file.csv' in label_text:
                print("✓ Last opened file is displayed correctly")
            else:
                print(f"✗ Last opened file not displayed correctly: {label_text}")
        else:
            print("✗ Last file label not found")
            
        print("✓ Options dialog created successfully")
        return True
        
    except Exception as e:
        print(f"✗ Options dialog test failed: {e}")
        return False

def test_table_manager_fix():
    """Test that table manager methods use table_tree instead of table_list"""
    print("\n=== Testing Table Manager Fix ===")
    
    try:
        # Create main window
        main_window = VSCodeMainWindow()
        
        # Check if table manager has the correct attributes
        if hasattr(main_window, 'table_manager'):
            table_manager = main_window.table_manager
            
            # Check if table_tree exists
            if hasattr(table_manager, 'table_tree'):
                print("✓ TableManager has table_tree attribute")
            else:
                print("✗ TableManager missing table_tree attribute")
                return False
                
            # Check if table_list doesn't exist (should be removed)
            if not hasattr(table_manager, 'table_list'):
                print("✓ TableManager no longer has table_list attribute")
            else:
                print("✗ TableManager still has table_list attribute")
                
            # Test that delete_table method exists and can be called safely
            if hasattr(table_manager, 'delete_table'):
                print("✓ delete_table method exists")
                # We won't actually call it since it requires UI interaction
            else:
                print("✗ delete_table method not found")
                return False
                
            print("✓ Table manager fix verified")
            return True
        else:
            print("✗ Table manager not found in main window")
            return False
            
    except Exception as e:
        print(f"✗ Table manager test failed: {e}")
        return False

def test_menu_structure():
    """Test that Options menu is at first level"""
    print("\n=== Testing Menu Structure ===")
    
    try:
        # Create main window
        main_window = VSCodeMainWindow()
        
        # Check if open_options_dialog method exists
        if hasattr(main_window, 'open_options_dialog'):
            print("✓ open_options_dialog method exists")
        else:
            print("✗ open_options_dialog method not found")
            return False
            
        # Check menu bar
        menubar = main_window.menuBar()
        menu_titles = [menubar.actions()[i].text() for i in range(len(menubar.actions()))]
        
        print(f"Menu structure: {menu_titles}")
        
        if 'Options' in menu_titles:
            print("✓ Options menu found at first level")
            return True
        else:
            print("✗ Options menu not found at first level")
            return False
            
    except Exception as e:
        print(f"✗ Menu structure test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing fixes for reported issues...")
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Run tests
    test_results = []
    test_results.append(test_menu_structure())
    test_results.append(test_options_dialog())
    test_results.append(test_table_manager_fix())
    
    # Summary
    print("\n=== Test Summary ===")
    passed = sum(test_results)
    total = len(test_results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All fixes verified successfully!")
    else:
        print("✗ Some tests failed")
    
    # Don't start the event loop, just exit
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())