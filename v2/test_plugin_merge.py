#!/usr/bin/env python3
"""
Test script to verify plugin functionality has been successfully merged to main project.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_plugin_imports():
    """Test that plugin-related imports work correctly."""
    try:
        from utils.plugin_loader import PluginLoader
        from plugin_compare_dialog import PluginCompareDialog
        print("✅ Plugin imports successful")
        return True
    except ImportError as e:
        print(f"❌ Plugin import failed: {e}")
        return False

def test_plugin_loader():
    """Test that plugin loader can load plugins."""
    try:
        from utils.plugin_loader import PluginLoader
        loader = PluginLoader()
        plugins = loader.load_plugins()
        print(f"✅ Plugin loader works - found {len(plugins)} plugins")
        
        # List available plugins
        for plugin_class in plugins:
            try:
                plugin_instance = plugin_class()
                print(f"  - {plugin_instance.get_name()}: {plugin_instance.get_description()}")
            except Exception as e:
                print(f"  - {plugin_class.__name__}: Error creating instance - {e}")
        
        return True
    except Exception as e:
        print(f"❌ Plugin loader failed: {e}")
        return False

def test_vscode_main_window():
    """Test that VSCodeMainWindow can be imported with plugin functionality."""
    try:
        from vscode_main_window import VSCodeMainWindow
        print("✅ VSCodeMainWindow import successful")
        
        # Check if plugin-related attributes exist
        import inspect
        methods = [method for method in dir(VSCodeMainWindow) if 'plugin' in method.lower() or 'comparison' in method.lower()]
        if methods:
            print(f"✅ Plugin-related methods found: {', '.join(methods)}")
        else:
            print("⚠️  No plugin-related methods found")
        
        return True
    except ImportError as e:
        print(f"❌ VSCodeMainWindow import failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Plugin Functionality Merge")
    print("=" * 40)
    
    tests = [
        ("Plugin Imports", test_plugin_imports),
        ("Plugin Loader", test_plugin_loader),
        ("VSCode Main Window", test_vscode_main_window)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append(result)
    
    print("\n" + "=" * 40)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Plugin functionality successfully merged.")
    else:
        print("⚠️  Some tests failed. Plugin merge may be incomplete.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)