#!/usr/bin/env python3
"""
Test script for CSV Editor with Formula Engine integration
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from csv_editor import CSVEditor
from excel_format_dialog import ExcelFormatDialog

class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Editor Formula Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create CSV editor
        self.csv_editor = CSVEditor(self)
        layout.addWidget(self.csv_editor)
        
    def log_message(self, message):
        """Log message method required by CSV Editor"""
        print(f"LOG: {message}")
        
    @property
    def row_count_label(self):
        """Mock row count label"""
        class MockLabel:
            def setText(self, text):
                print(f"Row count: {text}")
        return MockLabel()

def test_formula_integration():
    """Test the formula integration with CSV Editor"""
    app = QApplication(sys.argv)
    
    # Create main window
    window = TestMainWindow()
    window.show()
    
    print("CSV Editor with Formula Engine integration test started.")
    print("\nTo test:")
    print("1. Load an Excel file with formulas using 'Load Excel with Formatting'")
    print("2. In the dialog, enable 'Evaluate formulas and show results'")
    print("3. Enable 'Show indicators for cells with formulas'")
    print("4. Enable 'Basic math (SUM, AVG, COUNT, MAX, MIN)'")
    print("5. Enable 'Logical functions (IF, AND, OR, NOT)'")
    print("6. Load the file and observe formula evaluation and indicators")
    print("\nFormula cells should have a light green background tint.")
    print("Evaluated formulas should show their calculated results.")
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_formula_integration()