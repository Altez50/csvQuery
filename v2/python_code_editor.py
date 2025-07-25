import json
import os
import traceback
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QMessageBox, QToolBar, QAction, QTextEdit
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

SNIPPETS_FILE = '../python_snippets.json'

class PythonCodeEditor(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.snippets = []
        self.current_group_idx = -1
        self.current_snippet_idx = -1
        
        self.load_snippets()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(20, 20))
        
        self.execute_btn = QPushButton("Execute (F5)")
        self.execute_btn.setShortcut('F5')
        self.execute_btn.clicked.connect(self.execute_code)
        toolbar.addWidget(self.execute_btn)
        
        toolbar.addSeparator()
        
        self.save_snippet_btn = QPushButton("Save Snippet")
        self.save_snippet_btn.clicked.connect(self.save_snippet)
        toolbar.addWidget(self.save_snippet_btn)
        
        self.load_snippet_btn = QPushButton("Load Snippet")
        self.load_snippet_btn.clicked.connect(self.load_snippet)
        toolbar.addWidget(self.load_snippet_btn)
        
        toolbar.addSeparator()
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_editor)
        toolbar.addWidget(self.clear_btn)
        
        layout.addWidget(toolbar)
        
        # Hint label
        self.hint_label = QLabel(
            '<b>Available variables:</b> results_table, csv_table (QTableWidget), '
            'main_window (MainWindow), sql_editor (SQLQueryEditor), csv_editor (CSVEditor)'
        )
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)
        
        # Code editor
        self.code_edit = QsciScintilla()
        self.code_edit.setUtf8(True)
        self.code_edit.setMarginType(0, QsciScintilla.NumberMargin)
        self.code_edit.setMarginWidth(0, "0000")
        self.code_edit.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.code_edit.setAutoIndent(True)
        self.code_edit.setIndentationGuides(True)
        self.code_edit.setFolding(QsciScintilla.BoxedTreeFoldStyle)
        
        lexer = QsciLexerPython(self.code_edit)
        self.code_edit.setLexer(lexer)
        
        # Set default code template
        default_code = '''# Python code editor\n# Available variables:\n# - main_window: Main application window\n# - sql_editor: SQL query editor\n# - csv_editor: CSV editor\n# - results_table: Query results table\n# - csv_table: CSV data table\n\n# Example: Get data from CSV editor\n# csv_data = csv_editor.csv_data\n# csv_headers = csv_editor.csv_headers\n\n# Example: Execute SQL query\n# sql_editor.sql_edit.setText("SELECT * FROM your_table")\n# sql_editor.execute_query()\n\nprint("Python code executed successfully!")'''
        self.code_edit.setText(default_code)
        
        layout.addWidget(self.code_edit)
        
        # Bottom panel
        bottom_panel = QHBoxLayout()
        bottom_panel.addWidget(QLabel("After execution activate:"))
        
        self.activation_selector = QComboBox()
        self.activation_selector.addItems(["MainWindow", "SQLQueryEditor", "CSVEditor"])
        bottom_panel.addWidget(self.activation_selector)
        
        bottom_panel.addStretch()
        layout.addLayout(bottom_panel)
        
        # Output label
        self.output_label = QLabel('')
        self.output_label.setStyleSheet('color: #005500; background: #f0f0f0; padding: 4px;')
        self.output_label.setWordWrap(True)
        layout.addWidget(self.output_label)
        
    def load_snippets(self):
        """Load code snippets from file"""
        if os.path.exists(SNIPPETS_FILE):
            try:
                with open(SNIPPETS_FILE, 'r', encoding='utf-8') as f:
                    self.snippets = json.load(f)
            except Exception:
                self.snippets = []
        else:
            self.snippets = self.create_default_snippets()
            self.save_snippets()
            
    def create_default_snippets(self):
        """Create default code snippets"""
        return [
            {
                'name': 'Data Analysis',
                'snippets': [
                    {
                        'name': 'Basic Statistics',
                        'code': '''import pandas as pd\nimport numpy as np\n\n# Get CSV data\nif csv_editor.csv_data and csv_editor.csv_headers:\n    df = pd.DataFrame(csv_editor.csv_data, columns=csv_editor.csv_headers)\n    \n    # Basic statistics\n    print("Dataset shape:", df.shape)\n    print("\nData types:")\n    print(df.dtypes)\n    print("\nBasic statistics:")\n    print(df.describe())\n    \n    # Missing values\n    print("\nMissing values:")\n    print(df.isnull().sum())\nelse:\n    print("No CSV data loaded")'''
                    },
                    {
                        'name': 'Data Filtering',
                        'code': '''import pandas as pd\n\n# Get CSV data\nif csv_editor.csv_data and csv_editor.csv_headers:\n    df = pd.DataFrame(csv_editor.csv_data, columns=csv_editor.csv_headers)\n    \n    # Example: Filter data (modify condition as needed)\n    # filtered_df = df[df['column_name'] > 100]\n    \n    print(f"Original data: {len(df)} rows")\n    # print(f"Filtered data: {len(filtered_df)} rows")\n    \n    # Update CSV editor with filtered data\n    # csv_editor.csv_data = filtered_df.values.tolist()\n    # csv_editor.update_table_display()\nelse:\n    print("No CSV data loaded")'''
                    }
                ]
            },
            {
                'name': 'Database Operations',
                'snippets': [
                    {
                        'name': 'List Tables',
                        'code': '''# List all tables in database\nif main_window.sqlite_conn:\n    cursor = main_window.sqlite_conn.cursor()\n    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")\n    tables = cursor.fetchall()\n    \n    print("Tables in database:")\n    for table in tables:\n        print(f"  - {table[0]}")\nelse:\n    print("No database connection")'''
                    },
                    {
                        'name': 'Table Info',
                        'code': '''# Get table information\ntable_name = "your_table_name"  # Change this\n\nif main_window.sqlite_conn:\n    cursor = main_window.sqlite_conn.cursor()\n    \n    try:\n        # Get column info\n        cursor.execute(f"PRAGMA table_info({table_name})")\n        columns = cursor.fetchall()\n        \n        print(f"Table: {table_name}")\n        print("Columns:")\n        for col in columns:\n            print(f"  {col[1]} ({col[2]})")\n            \n        # Get row count\n        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")\n        count = cursor.fetchone()[0]\n        print(f"\nRow count: {count}")\n        \n    except Exception as e:\n        print(f"Error: {e}")\nelse:\n    print("No database connection")'''
                    }
                ]
            }
        ]
        
    def save_snippets(self):
        """Save code snippets to file"""
        try:
            with open(SNIPPETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.snippets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.output_label.setText(f"Failed to save snippets: {e}")
            self.output_label.setStyleSheet('color: #aa0000;')
            
    def execute_code(self):
        """Execute Python code"""
        code = self.code_edit.text()
        
        # Prepare local variables
        local_vars = {
            'main_window': self.main_window,
            'sql_editor': self.main_window.sql_editor,
            'csv_editor': self.main_window.csv_editor,
            'results_table': self.main_window.results_table,
            'csv_table': self.main_window.csv_editor.table
        }
        
        try:
            # Capture print output
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            # Execute code
            exec(code, {}, local_vars)
            
            # Get output
            output = captured_output.getvalue()
            sys.stdout = old_stdout
            
            if output:
                self.output_label.setText(f'Output:\n{output}')
            else:
                self.output_label.setText('Code executed successfully (no output).')
            self.output_label.setStyleSheet('color: #005500; background: #f0fff0; padding: 4px;')
            
            # Log to main window
            self.main_window.log_message("Python code executed successfully")
            
            # Activate target window
            target = self.activation_selector.currentText()
            if target == "MainWindow":
                self.main_window.raise_()
                self.main_window.activateWindow()
            elif target == "SQLQueryEditor":
                self.main_window.editor_tabs.setCurrentWidget(self.main_window.sql_editor)
            elif target == "CSVEditor":
                self.main_window.editor_tabs.setCurrentWidget(self.main_window.csv_editor)
                
        except Exception as e:
            tb = traceback.format_exc()
            self.output_label.setText(f'Error:\n{tb}')
            self.output_label.setStyleSheet('color: #aa0000; background: #fff0f0; padding: 4px;')
            self.main_window.log_message(f"Python code execution failed: {e}")
            
    def save_snippet(self):
        """Save current code as snippet"""
        from PyQt5.QtWidgets import QInputDialog
        
        code = self.code_edit.text().strip()
        if not code:
            QMessageBox.warning(self, "Warning", "No code to save")
            return
            
        # Get snippet name
        name, ok = QInputDialog.getText(self, "Save Snippet", "Enter snippet name:")
        if not ok or not name:
            return
            
        # Get group name
        group_names = [group['name'] for group in self.snippets]
        if group_names:
            group_name, ok = QInputDialog.getItem(
                self, "Select Group", "Choose group:", group_names + ["New Group..."], 0, False
            )
            if not ok:
                return
                
            if group_name == "New Group...":
                group_name, ok = QInputDialog.getText(self, "New Group", "Enter group name:")
                if not ok or not group_name:
                    return
                # Create new group
                self.snippets.append({
                    'name': group_name,
                    'snippets': []
                })
        else:
            group_name = "Default"
            self.snippets.append({
                'name': group_name,
                'snippets': []
            })
            
        # Find group and add snippet
        for group in self.snippets:
            if group['name'] == group_name:
                group['snippets'].append({
                    'name': name,
                    'code': code
                })
                break
                
        self.save_snippets()
        self.output_label.setText(f"Snippet '{name}' saved to group '{group_name}'")
        self.output_label.setStyleSheet('color: #005500; background: #f0fff0; padding: 4px;')
        
        # Refresh snippets tree in main window if available
        if hasattr(self.main_window, 'refresh_snippets_tree'):
            self.main_window.refresh_snippets_tree()
        
    def load_snippet(self):
        """Load snippet from saved snippets"""
        from PyQt5.QtWidgets import QInputDialog
        
        if not self.snippets:
            QMessageBox.information(self, "Info", "No snippets available")
            return
            
        # Get group
        group_names = [group['name'] for group in self.snippets]
        group_name, ok = QInputDialog.getItem(
            self, "Select Group", "Choose group:", group_names, 0, False
        )
        if not ok:
            return
            
        # Find group
        selected_group = None
        for group in self.snippets:
            if group['name'] == group_name:
                selected_group = group
                break
                
        if not selected_group or not selected_group['snippets']:
            QMessageBox.information(self, "Info", "No snippets in selected group")
            return
            
        # Get snippet
        snippet_names = [snippet['name'] for snippet in selected_group['snippets']]
        snippet_name, ok = QInputDialog.getItem(
            self, "Select Snippet", "Choose snippet:", snippet_names, 0, False
        )
        if not ok:
            return
            
        # Find and load snippet
        for snippet in selected_group['snippets']:
            if snippet['name'] == snippet_name:
                self.code_edit.setText(snippet['code'])
                self.output_label.setText(f"Loaded snippet: {snippet_name}")
                self.output_label.setStyleSheet('color: #005500; background: #f0fff0; padding: 4px;')
                break
                
    def clear_editor(self):
        """Clear editor content"""
        self.code_edit.clear()
        self.output_label.clear()
        
    def get_code_text(self):
        """Get current code text"""
        return self.code_edit.text()
        
    def set_code_text(self, code):
        """Set code text"""
        self.code_edit.setText(code)
        
    def add_snippet_to_group(self, group_name, snippet_name, code):
        """Add a snippet to a specific group"""
        # Find or create group
        target_group = None
        for group in self.snippets:
            if group['name'] == group_name:
                target_group = group
                break
                
        if not target_group:
            # Create new group
            target_group = {
                'name': group_name,
                'snippets': []
            }
            self.snippets.append(target_group)
            
        # Check if snippet name already exists in group
        for snippet in target_group['snippets']:
            if snippet['name'] == snippet_name:
                # Update existing snippet
                snippet['code'] = code
                self.save_snippets()
                return
                
        # Add new snippet
        target_group['snippets'].append({
            'name': snippet_name,
            'code': code
        })
        self.save_snippets()
        
    def update_snippet(self, old_name, new_name, new_code):
        """Update an existing snippet"""
        for group in self.snippets:
            for snippet in group['snippets']:
                if snippet['name'] == old_name:
                    snippet['name'] = new_name
                    snippet['code'] = new_code
                    self.save_snippets()
                    return True
        return False
        
    def delete_snippet(self, snippet_name):
        """Delete a snippet by name"""
        for group in self.snippets:
            for i, snippet in enumerate(group['snippets']):
                if snippet['name'] == snippet_name:
                    group['snippets'].pop(i)
                    # Remove group if empty
                    if not group['snippets']:
                        self.snippets.remove(group)
                    self.save_snippets()
                    return True
        return False