import sqlite3
import json
import os
import tempfile
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QTextEdit, QComboBox,
    QDialog, QDialogButtonBox, QLineEdit, QSpinBox, QFontComboBox,
    QInputDialog, QMessageBox, QToolBar, QAction, QSizePolicy, QFileDialog,
    QTreeWidgetItem
)
from PyQt5.QtCore import Qt, QSize, QProcess
from PyQt5.QtGui import QIcon, QFont
from PyQt5.Qsci import QsciScintilla, QsciLexerSQL
import pandas as pd

HISTORY_FILE = '../query_history.json'
EDITOR_SETTINGS_FILE = '../editor_settings.json'

class EditorOptionsDialog(QDialog):
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle('SQL Editor Options')
        self.resize(400, 200)
        layout = QVBoxLayout(self)
        
        # Font family
        layout.addWidget(QLabel('Font:'))
        self.font_combo = QFontComboBox()
        layout.addWidget(self.font_combo)
        
        # Font size
        layout.addWidget(QLabel('Font size:'))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 48)
        layout.addWidget(self.font_size_spin)
        
        # Color scheme
        layout.addWidget(QLabel('Color scheme:'))
        self.scheme_combo = QComboBox()
        self.scheme_combo.addItems(['Light', 'Dark'])
        layout.addWidget(self.scheme_combo)
        
        # External editor path
        layout.addWidget(QLabel('External editor path:'))
        self.editor_path_edit = QLineEdit()
        layout.addWidget(self.editor_path_edit)
        
        # Hotkeys info
        layout.addWidget(QLabel('Search/Replace hotkeys:'))
        self.hotkeys_label = QLabel('Search: Ctrl+F   Replace: Ctrl+H   Go to line: Ctrl+G')
        layout.addWidget(self.hotkeys_label)
        
        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # Load current settings
        if current_settings:
            self.font_combo.setCurrentFont(QFont(current_settings.get('font_family', 'Consolas')))
            self.font_size_spin.setValue(current_settings.get('font_size', 12))
            self.scheme_combo.setCurrentIndex(1 if current_settings.get('color_scheme', 'light') == 'dark' else 0)
            self.editor_path_edit.setText(current_settings.get('editor_path', 'code'))
            
    def get_settings(self):
        return {
            'font_family': self.font_combo.currentFont().family(),
            'font_size': self.font_size_spin.value(),
            'color_scheme': 'dark' if self.scheme_combo.currentIndex() == 1 else 'light',
            'editor_path': self.editor_path_edit.text() or 'code'
        }

class ParamsDialog(QDialog):
    def __init__(self, params, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Query Parameters')
        self.resize(400, 300)
        self.params = params.copy() if params else {}
        layout = QVBoxLayout(self)
        self.editors = {}
        
        for key in sorted(self.params.keys()):
            row = QHBoxLayout()
            row.addWidget(QLabel(key+':'))
            editor = QTextEdit()
            editor.setPlainText(self.params[key])
            editor.setMinimumHeight(30)
            row.addWidget(editor)
            self.editors[key] = editor
            layout.addLayout(row)
            
        self.add_btn = QPushButton('Add Parameter')
        self.add_btn.clicked.connect(self.add_param)
        layout.addWidget(self.add_btn)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
    def add_param(self):
        row = QHBoxLayout()
        key_edit = QLineEdit()
        row.addWidget(key_edit)
        value_edit = QTextEdit()
        value_edit.setMinimumHeight(30)
        row.addWidget(value_edit)
        self.editors[key_edit] = value_edit
        self.layout().insertLayout(self.layout().count()-2, row)
        
    def get_params(self):
        result = {}
        for key, editor in self.editors.items():
            if isinstance(key, QLineEdit):
                k = key.text().strip()
            else:
                k = key
            v = editor.toPlainText()
            if k:
                result[k] = v
        return result

class QueryPreviewDialog(QDialog):
    def __init__(self, query_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Query Text with Parameters')
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(query_text)
        layout.addWidget(text)
        
        btn = QPushButton('Close')
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class SQLQueryEditor(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.history = []
        self.current_group_idx = -1
        self.current_query_idx = -1
        self.editor_settings = self.load_editor_settings()
        self.query_params = {'task_numbers': ''}
        self.loaded_query_item = None  # Track which query item was loaded from history
        
        self.load_history()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Main toolbar
        main_toolbar = QToolBar()
        main_toolbar.setIconSize(QSize(20, 20))
        
        self.execute_btn = QPushButton("▶️ Execute (F7)")
        self.execute_btn.setShortcut('F7')
        self.execute_btn.clicked.connect(self.execute_query)
        self.execute_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        main_toolbar.addWidget(self.execute_btn)
        
        self.params_btn = QPushButton("⚙️ Parameters")
        self.params_btn.clicked.connect(self.edit_query_params)
        self.params_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        main_toolbar.addWidget(self.params_btn)
        
        main_toolbar.addSeparator()
        
        self.save_query_btn = QPushButton("💾 Save")
        self.save_query_btn.clicked.connect(self.save_query)
        self.save_query_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        main_toolbar.addWidget(self.save_query_btn)
        
        self.load_query_btn = QPushButton("📂 Load")
        self.load_query_btn.clicked.connect(self.load_query)
        self.load_query_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        main_toolbar.addWidget(self.load_query_btn)
        
        layout.addWidget(main_toolbar)
        
        # SQL editor toolbar
        sql_toolbar = QToolBar()
        sql_toolbar.setIconSize(QSize(16, 16))
        
        self.find_btn = QPushButton("🔍 Find")
        self.find_btn.clicked.connect(self.open_find_dialog)
        self.find_btn.setStyleSheet("font-size: 11px; font-weight: bold;")
        sql_toolbar.addWidget(self.find_btn)
        
        self.replace_btn = QPushButton("🔄 Replace")
        self.replace_btn.clicked.connect(self.open_replace_dialog)
        self.replace_btn.setStyleSheet("font-size: 11px; font-weight: bold;")
        sql_toolbar.addWidget(self.replace_btn)
        
        self.insert_field_btn = QPushButton("📝 Insert Field")
        self.insert_field_btn.clicked.connect(self.insert_field_name)
        self.insert_field_btn.setStyleSheet("font-size: 11px; font-weight: bold;")
        sql_toolbar.addWidget(self.insert_field_btn)
        
        self.format_btn = QPushButton("✨ Format")
        self.format_btn.clicked.connect(self.format_sql)
        self.format_btn.setStyleSheet("font-size: 11px; font-weight: bold;")
        sql_toolbar.addWidget(self.format_btn)
        
        layout.addWidget(sql_toolbar)
        
        # SQL editor and task numbers side by side
        sql_task_layout = QHBoxLayout()
        
        # SQL editor layout
        sql_editor_layout = QVBoxLayout()
        self.label = QLabel("Enter SQL Query:")
        sql_editor_layout.addWidget(self.label)
        
        self.sql_edit = QsciScintilla()
        self.sql_edit.setUtf8(True)
        self.sql_edit.setMarginType(0, QsciScintilla.NumberMargin)
        self.sql_edit.setMarginWidth(0, "0000")
        self.sql_edit.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.sql_edit.setAutoIndent(True)
        self.sql_edit.setIndentationGuides(True)
        self.sql_edit.setFolding(QsciScintilla.BoxedTreeFoldStyle)
        self.sql_edit.setLexer(QsciLexerSQL(self.sql_edit))
        self.sql_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Add focus out event to auto-save query
        self.sql_edit.focusOutEvent = self.on_editor_focus_out
        
        sql_editor_layout.addWidget(self.sql_edit)
        
        self.apply_editor_settings()
        sql_task_layout.addLayout(sql_editor_layout, 7)
        
        # Task numbers
        task_layout = QVBoxLayout()
        task_layout.addWidget(QLabel("Task numbers:"))
        self.task_numbers_edit = QTextEdit()
        self.task_numbers_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        task_layout.addWidget(self.task_numbers_edit)
        sql_task_layout.addLayout(task_layout, 1)
        
        layout.addLayout(sql_task_layout)
        
        # Results area
        self.results_label = QLabel("Query Results:")
        layout.addWidget(self.results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        layout.addWidget(self.results_table)
        
        # Status
        self.status_label = QLabel("Ready to execute queries")
        layout.addWidget(self.status_label)
        
    def load_editor_settings(self):
        """Load editor settings from file"""
        if os.path.exists(EDITOR_SETTINGS_FILE):
            try:
                with open(EDITOR_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'font_family': 'Consolas',
            'font_size': 12,
            'color_scheme': 'light',
            'editor_path': 'code'
        }
        
    def save_editor_settings(self):
        """Save editor settings to file"""
        try:
            with open(EDITOR_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.editor_settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
            
    def apply_editor_settings(self):
        """Apply editor settings to SQL editor"""
        font = QFont(self.editor_settings['font_family'], self.editor_settings['font_size'])
        self.sql_edit.setFont(font)
        
        # Apply color scheme
        if self.editor_settings['color_scheme'] == 'dark':
            self.sql_edit.setStyleSheet(
                "QsciScintilla { background-color: #2b2b2b; color: #ffffff; }"
            )
        else:
            self.sql_edit.setStyleSheet(
                "QsciScintilla { background-color: #ffffff; color: #000000; }"
            )
            
    def load_history(self):
        """Load query history from file"""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []
        else:
            self.history = []
            
    def save_history(self):
        """Save query history to file"""
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
            
    def execute_query(self):
        """Execute SQL query"""
        if not self.main_window.sqlite_conn:
            QMessageBox.warning(self, "Warning", "No database connection")
            return
            
        query_text = self.sql_edit.text().strip()
        if not query_text:
            QMessageBox.warning(self, "Warning", "No query to execute")
            return
            
        try:
            # Replace parameters if any
            final_query = self.replace_parameters(query_text)
            
            cursor = self.main_window.sqlite_conn.cursor()
            cursor.execute(final_query)
            
            if final_query.strip().upper().startswith('SELECT'):
                # Fetch results for SELECT queries
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                # Display results
                self.display_results(results, columns)
                self.status_label.setText(f"Query executed successfully. {len(results)} rows returned.")
                
                # Update main window results table
                self.update_main_results_table(results, columns)
                
            else:
                # For non-SELECT queries
                self.main_window.sqlite_conn.commit()
                affected_rows = cursor.rowcount
                self.status_label.setText(f"Query executed successfully. {affected_rows} rows affected.")
                
                # Clear results table
                self.results_table.clear()
                self.results_table.setRowCount(0)
                self.results_table.setColumnCount(0)
                
            # Save to history
            self.save_query_to_history(query_text)
            
            # Update table manager if tables were modified
            if hasattr(self.main_window, 'table_manager'):
                self.main_window.table_manager.refresh_tables()
                
            self.main_window.log_message(f"Query executed: {query_text[:50]}...")
            
        except Exception as e:
            QMessageBox.critical(self, "Query Error", f"Failed to execute query:\n{e}")
            self.status_label.setText(f"Query failed: {e}")
            
    def replace_parameters(self, query_text):
        """Replace parameters in query text"""
        final_query = query_text
        for key, value in self.query_params.items():
            placeholder = f"{{{key}}}"
            final_query = final_query.replace(placeholder, str(value))
        return final_query
        
    def display_results(self, results, columns):
        """Display query results in table"""
        self.results_table.setRowCount(len(results))
        self.results_table.setColumnCount(len(columns))
        self.results_table.setHorizontalHeaderLabels(columns)
        
        for row_idx, row_data in enumerate(results):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                self.results_table.setItem(row_idx, col_idx, item)
                
        self.results_table.resizeColumnsToContents()
        
    def update_main_results_table(self, results, columns):
        """Update main window results table"""
        main_results = self.main_window.results_table
        main_results.setRowCount(len(results))
        main_results.setColumnCount(len(columns))
        main_results.setHorizontalHeaderLabels(columns)
        
        for row_idx, row_data in enumerate(results):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                main_results.setItem(row_idx, col_idx, item)
                
        main_results.resizeColumnsToContents()
        
        # Update info panel
        info_text = f"Query Results:\n"
        info_text += f"Rows: {len(results)}\n"
        info_text += f"Columns: {len(columns)}\n"
        info_text += f"Columns: {', '.join(columns)}"
        self.main_window.results_info.setPlainText(info_text)
        
    def save_query_to_history(self, query_text):
        """Save query to history"""
        # Simple history implementation
        query_entry = {
            'query': query_text,
            'timestamp': pd.Timestamp.now().isoformat(),
            'task_numbers': self.task_numbers_edit.toPlainText()
        }
        
        # Add to current group or create new group
        if not self.history:
            self.history.append({
                'name': 'Default Group',
                'queries': [query_entry]
            })
        else:
            self.history[0]['queries'].append(query_entry)
            
        self.save_history()
        
    def edit_query_params(self):
        """Edit query parameters"""
        dialog = ParamsDialog(self.query_params, self)
        if dialog.exec_() == QDialog.Accepted:
            self.query_params = dialog.get_params()
            
    def save_query(self):
        """Save current query to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Query", "", "SQL files (*.sql);;All files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.sql_edit.text())
                self.main_window.log_message(f"Query saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save query: {e}")
                
    def load_query(self):
        """Load query from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Query", "", "SQL files (*.sql);;All files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    query_text = f.read()
                self.sql_edit.setText(query_text)
                # Clear loaded query item since this is a new query from file
                self.clear_loaded_query_item()
                self.main_window.log_message(f"Query loaded from {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load query: {e}")
                
    def open_find_dialog(self):
        """Open find dialog"""
        # Use built-in find functionality
        self.sql_edit.SendScintilla(QsciScintilla.SCI_SEARCHANCHOR)
        
    def open_replace_dialog(self):
        """Open replace dialog"""
        # TODO: Implement replace dialog
        QMessageBox.information(self, "Replace", "Replace dialog not implemented yet")
        
    def insert_field_name(self):
        """Insert field name from available tables"""
        if not self.main_window.sqlite_conn:
            QMessageBox.warning(self, "Warning", "No database connection")
            return
            
        try:
            cursor = self.main_window.sqlite_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                QMessageBox.information(self, "Info", "No tables found in database")
                return
                
            # Simple implementation - just show table names
            table_name, ok = QInputDialog.getItem(
                self, "Select Table", "Choose table:", tables, 0, False
            )
            if ok and table_name:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                
                column_name, ok = QInputDialog.getItem(
                    self, "Select Column", "Choose column:", columns, 0, False
                )
                if ok and column_name:
                    self.sql_edit.insert(f'"{column_name}"')
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get field names: {e}")
            
    def format_sql(self):
        """Format SQL query"""
        # Simple SQL formatting
        query_text = self.sql_edit.text()
        # TODO: Implement proper SQL formatting
        QMessageBox.information(self, "Format SQL", "SQL formatting not implemented yet")
        
    def open_editor_options(self):
        """Open editor options dialog"""
        dialog = EditorOptionsDialog(self, self.editor_settings)
        if dialog.exec_() == QDialog.Accepted:
            self.editor_settings = dialog.get_settings()
            self.save_editor_settings()
            self.apply_editor_settings()
            
    def get_query_text(self):
        """Get current query text"""
        return self.sql_edit.text()
    
    def set_loaded_query_item(self, query_item):
        """Set the query item that was loaded from history"""
        self.loaded_query_item = query_item
    
    def clear_loaded_query_item(self):
        """Clear the loaded query item reference"""
        self.loaded_query_item = None
        
    def clear_editor(self):
        """Clear editor content"""
        self.sql_edit.clear()
        self.task_numbers_edit.clear()
        self.results_table.clear()
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        self.status_label.setText("Ready to execute queries")
        # Clear the loaded query item reference
        self.clear_loaded_query_item()
    
    def on_editor_focus_out(self, event):
        """Handle focus out event to auto-save query"""
        # Call the original focus out event first
        super(QsciScintilla, self.sql_edit).focusOutEvent(event)
        
        # Auto-save current query if it has content
        query_text = self.sql_edit.text().strip()
        if query_text:
            self.auto_save_query_to_history(query_text)
    
    def auto_save_query_to_history(self, query_text):
        """Auto-save query to history tree in main window"""
        if hasattr(self.main_window, 'query_history_tree'):
            # If we have a loaded query item, update it instead of creating new
            if self.loaded_query_item:
                query_data = self.loaded_query_item.data(0, Qt.UserRole)
                if query_data and query_data.get('type') == 'query':
                    # Update the existing query data
                    stored_data = query_data.get('data', {})
                    stored_data['query'] = query_text
                    stored_data['task_numbers'] = self.task_numbers_edit.toPlainText()
                    stored_data['params'] = self.query_params.copy()
                    stored_data['timestamp'] = pd.Timestamp.now().isoformat()
                    
                    # Update the tree item data
                    self.loaded_query_item.setData(0, Qt.UserRole, {'type': 'query', 'data': stored_data})
                    
                    # Save to persistent storage
                    self.main_window.save_query_history_tree()
                    return
            
            # Check if this exact query already exists to avoid duplicates
            existing_query = self.find_existing_query(query_text)
            if existing_query:
                # Update existing query with current parameters
                existing_query['task_numbers'] = self.task_numbers_edit.toPlainText()
                existing_query['params'] = self.query_params.copy()
                existing_query['timestamp'] = pd.Timestamp.now().isoformat()
                self.main_window.save_query_history_tree()
                return
            
            # Create new query entry
            query_data = {
                'name': f"Auto-saved Query {pd.Timestamp.now().strftime('%H:%M:%S')}",
                'query': query_text,
                'task_numbers': self.task_numbers_edit.toPlainText(),
                'params': self.query_params.copy(),
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            # Find or create "Auto-saved" group
            auto_group = None
            for i in range(self.main_window.query_history_tree.topLevelItemCount()):
                group_item = self.main_window.query_history_tree.topLevelItem(i)
                group_data = group_item.data(0, Qt.UserRole)
                if group_data and group_data.get('name') == 'Auto-saved':
                    auto_group = group_item
                    break
            
            if not auto_group:
                auto_group = QTreeWidgetItem(['Auto-saved'])
                auto_group.setData(0, Qt.UserRole, {'type': 'group', 'name': 'Auto-saved'})
                self.main_window.query_history_tree.addTopLevelItem(auto_group)
            
            # Add query to auto-saved group
            query_item = QTreeWidgetItem([query_data['name']])
            query_item.setData(0, Qt.UserRole, {'type': 'query', 'data': query_data})
            auto_group.addChild(query_item)
            auto_group.setExpanded(True)
            
            # Save to persistent storage
            self.main_window.save_query_history_tree()
    
    def find_existing_query(self, query_text):
        """Find if the exact query already exists in history"""
        if not hasattr(self.main_window, 'query_history_tree'):
            return None
            
        for i in range(self.main_window.query_history_tree.topLevelItemCount()):
            group_item = self.main_window.query_history_tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                query_item = group_item.child(j)
                query_data = query_item.data(0, Qt.UserRole)
                if query_data and query_data.get('type') == 'query':
                    stored_query = query_data.get('data', {}).get('query', '')
                    if stored_query.strip() == query_text.strip():
                        return query_data.get('data', {})
        return None