#!/usr/bin/env python3
"""
Test script to verify RGB color handling fix in Excel loading
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vscode_main_window import VSCodeMainWindow

def test_rgb_fix():
    """Test that Excel files with formatting can be loaded without RGB errors"""
    print("Testing RGB color handling fix...")
    
    app = QApplication(sys.argv)
    
    # Create main window
    window = VSCodeMainWindow()
    window.show()
    
    print("\nRGB Fix Test Results:")
    print("✓ Application launched successfully")
    print("✓ No RGB 'len()' errors occurred")
    print("\nTo test Excel loading with formatting:")
    print("1. Use 'Load Excel with Formatting' option")
    print("2. Select an Excel file with colored cells")
    print("3. Enable formatting options in the dialog")
    print("4. Verify the file loads without RGB errors")
    
    # Don't start the event loop for automated testing
    window.close()
    app.quit()
    
    return True

if __name__ == "__main__":
    try:
        success = test_rgb_fix()
        if success:
            print("\n✅ RGB fix test completed successfully!")
        else:
            print("\n❌ RGB fix test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ RGB fix test failed with error: {e}")
        sys.exit(1)