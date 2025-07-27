#!/usr/bin/env python3
"""
Test script to verify the plugin loading fix in vscode_main_window.py
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QPoint

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vscode_main_window import VSCodeMainWindow
from utils.plugin_loader import PluginLoader

def test_plugin_loading():
    """Test that plugins load correctly without errors"""
    print("Testing plugin loading...")
    
    try:
        # Test plugin loader directly
        plugin_loader = PluginLoader()
        plugins = plugin_loader.load_plugins()
        
        print(f"Found {len(plugins)} plugins:")
        for plugin in plugins:
            try:
                plugin_name = plugin.get_name()
                print(f"  - {plugin_name} (type: {type(plugin).__name__})")
            except Exception as e:
                print(f"  - Error getting plugin name: {e}")
        
        print("✅ Plugin loading test passed")
        return True
        
    except Exception as e:
        print(f"❌ Plugin loading test failed: {e}")
        return False

def test_main_window_plugin_integration():
    """Test that main window integrates with plugins correctly"""
    print("\nTesting main window plugin integration...")
    
    try:
        app = QApplication([])
        
        # Create main window
        window = VSCodeMainWindow()
        
        # Test that plugin loader is initialized
        if hasattr(window, 'plugin_loader'):
            print("✅ Plugin loader initialized in main window")
            
            # Test that selected_files_for_comparison is initialized
            if hasattr(window, 'selected_files_for_comparison'):
                print("✅ File comparison selection initialized")
                
                # Test plugin loading in context menu (simulate)
                try:
                    plugins = window.plugin_loader.load_plugins()
                    print(f"✅ Main window can load {len(plugins)} plugins")
                    
                    # Test that we can access plugin names without errors
                    for plugin in plugins:
                        plugin_name = plugin.get_name()
                        print(f"  - Plugin accessible: {plugin_name}")
                    
                    print("✅ Main window plugin integration test passed")
                    return True
                    
                except Exception as e:
                    print(f"❌ Error in plugin integration: {e}")
                    return False
            else:
                print("❌ File comparison selection not initialized")
                return False
        else:
            print("❌ Plugin loader not initialized in main window")
            return False
            
    except Exception as e:
        print(f"❌ Main window plugin integration test failed: {e}")
        return False
    finally:
        app.quit()

if __name__ == "__main__":
    print("=== Plugin Fix Verification Test ===")
    
    test1_passed = test_plugin_loading()
    test2_passed = test_main_window_plugin_integration()
    
    print("\n=== Test Results ===")
    print(f"Plugin Loading: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Main Window Integration: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Plugin fix is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")