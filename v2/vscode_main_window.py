import sys
import os
import json
import sqlite3
import zipfile
import tempfile
import csv
import pandas as pd
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTextEdit, QListWidget, QToolBar, QStatusBar,
    QDockWidget, QTreeView, QFileSystemModel, QSplitter, QLabel,
    QTableWidget, QTableWidgetItem, QFileDialog, QPushButton,
    QLineEdit, QCheckBox, QComboBox, QMenu, QAction, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QInputDialog, QToolButton, QSizePolicy,
    QDialog
)
from PyQt5.QtCore import Qt, QDir, QSize, QSettings
from PyQt5.QtGui import QIcon, QFont

# Import custom components
from csv_editor import CSVEditor
from sql_query_editor import SQLQueryEditor
from python_code_editor import PythonCodeEditor
from ai_assistant import AIAssistant
from table_manager import TableManager

SETTINGS_FILE = '../settings.json'

class VSCodeMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Query Tool - VSCode Style")
        self.setGeometry(100, 100, 1400, 900)
        
        # Application state
        self.sqlite_conn = None
        self.csv_data = []
        self.csv_headers = []
        self.confirm_on_exit = True
        self.convert_first_row_to_headers = False
        self.last_selected_file = None
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Initialize UI components
        self.init_central_widget()
        self.init_left_dock()
        self.init_right_dock()
        self.init_bottom_dock()
        self.init_toolbar()
        self.init_status_bar()
        self.init_menu_bar()
        
        # Load settings after UI is initialized
        self.load_settings()
        
        # Initialize database
        self.init_database()
        
        # Refresh tables after database initialization
        self.table_manager.refresh_tables()
        
        # Load query history
        self.load_query_history_tree()
        
    def init_central_widget(self):
        """Initialize the central editor area with tabs"""
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Tab Widget for different editors
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.setMovable(True)
        main_layout.addWidget(self.editor_tabs)
        
        # Initialize editor components
        self.csv_editor = CSVEditor(self)
        self.sql_editor = SQLQueryEditor(self)
        self.python_editor = PythonCodeEditor(self)
        self.ai_assistant = AIAssistant(self)
        
        # Add tabs
        self.editor_tabs.addTab(self.csv_editor, "📊 CSV Editor")
        self.editor_tabs.addTab(self.sql_editor, "🗃️ SQL Query")
        self.editor_tabs.addTab(self.python_editor, "🐍 Python")
        self.editor_tabs.addTab(self.ai_assistant, "🤖 AI Assistant")
        
    def init_left_dock(self):
        """Initialize left sidebar with explorer, tables, and snippets"""
        self.left_dock = QDockWidget("Explorer", self)
        self.left_dock_tabs = QTabWidget()
        
        # File Explorer
        self.file_tree = QTreeView()
        self.file_model = QFileSystemModel()
        # Set root to system root instead of current directory
        self.file_model.setRootPath(QDir.rootPath())
        self.file_tree.setModel(self.file_model)
        # Don't set root index to allow browsing entire file system
        self.file_tree.hideColumn(1)  # Hide size
        self.file_tree.hideColumn(2)  # Hide type
        self.file_tree.hideColumn(3)  # Hide date
        
        # Connect double-click to load CSV/Excel files
        self.file_tree.doubleClicked.connect(self.on_file_double_clicked)
        
        self.left_dock_tabs.addTab(self.file_tree, "📁 Files")
        
        # Table Manager
        self.table_manager = TableManager(self)
        self.left_dock_tabs.addTab(self.table_manager, "📋 Tables")
        
        # Query History with command panel
        queries_widget = QWidget()
        queries_layout = QVBoxLayout(queries_widget)
        queries_layout.setContentsMargins(5, 5, 5, 5)
        
        # Header with title and buttons
        queries_header = QHBoxLayout()
        queries_label = QLabel("Query History")
        queries_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        queries_header.addWidget(queries_label)
        queries_header.addStretch()
        
        # Command buttons with font-based icons
        self.add_query_group_btn = QPushButton("➕")
        self.add_query_group_btn.setMaximumSize(25, 25)
        self.add_query_group_btn.setToolTip("Add Query Group")
        self.add_query_group_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.add_query_group_btn.clicked.connect(self.add_query_group)
        queries_header.addWidget(self.add_query_group_btn)
        
        self.edit_query_btn = QPushButton("✏️")
        self.edit_query_btn.setMaximumSize(25, 25)
        self.edit_query_btn.setToolTip("Edit Query")
        self.edit_query_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.edit_query_btn.clicked.connect(self.edit_query_item)
        queries_header.addWidget(self.edit_query_btn)
        
        self.delete_query_btn = QPushButton("🗑️")
        self.delete_query_btn.setMaximumSize(25, 25)
        self.delete_query_btn.setToolTip("Delete Query")
        self.delete_query_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.delete_query_btn.clicked.connect(self.delete_query_item)
        queries_header.addWidget(self.delete_query_btn)
        
        queries_layout.addLayout(queries_header)
        
        # Query history tree
        self.query_history_tree = QTreeWidget()
        self.query_history_tree.setHeaderLabels(["Query History"])
        self.query_history_tree.itemDoubleClicked.connect(self.on_query_double_clicked)
        self.query_history_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.query_history_tree.customContextMenuRequested.connect(self.show_query_context_menu)
        
        # Enable drag and drop
        self.query_history_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.query_history_tree.setDragEnabled(True)
        self.query_history_tree.setAcceptDrops(True)
        self.query_history_tree.setDropIndicatorShown(True)
        
        queries_layout.addWidget(self.query_history_tree)
        self.left_dock_tabs.addTab(queries_widget, "📊 Queries")
        
        # Code Snippets with command panel
        snippets_widget = QWidget()
        snippets_layout = QVBoxLayout(snippets_widget)
        snippets_layout.setContentsMargins(5, 5, 5, 5)
        
        # Header with title and buttons
        snippets_header = QHBoxLayout()
        snippets_label = QLabel("Code Snippets")
        snippets_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        snippets_header.addWidget(snippets_label)
        snippets_header.addStretch()
        
        # Command buttons with font-based icons
        self.add_snippet_btn = QPushButton("➕")
        self.add_snippet_btn.setMaximumSize(25, 25)
        self.add_snippet_btn.setToolTip("Add Snippet")
        self.add_snippet_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.add_snippet_btn.clicked.connect(self.add_snippet)
        snippets_header.addWidget(self.add_snippet_btn)
        
        self.edit_snippet_btn = QPushButton("✏️")
        self.edit_snippet_btn.setMaximumSize(25, 25)
        self.edit_snippet_btn.setToolTip("Edit Snippet")
        self.edit_snippet_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.edit_snippet_btn.clicked.connect(self.edit_snippet)
        snippets_header.addWidget(self.edit_snippet_btn)
        
        self.delete_snippet_btn = QPushButton("🗑️")
        self.delete_snippet_btn.setMaximumSize(25, 25)
        self.delete_snippet_btn.setToolTip("Delete Snippet")
        self.delete_snippet_btn.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.delete_snippet_btn.clicked.connect(self.delete_snippet)
        snippets_header.addWidget(self.delete_snippet_btn)
        
        snippets_layout.addLayout(snippets_header)
        
        # Snippets tree
        self.snippets_tree = QTreeWidget()
        self.snippets_tree.setHeaderLabels(["Code Snippets"])
        self.snippets_tree.itemDoubleClicked.connect(self.on_snippet_double_clicked)
        self.snippets_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.snippets_tree.customContextMenuRequested.connect(self.show_snippet_context_menu)
        
        # Enable drag and drop
        self.snippets_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.snippets_tree.setDragEnabled(True)
        self.snippets_tree.setAcceptDrops(True)
        self.snippets_tree.setDropIndicatorShown(True)
        
        snippets_layout.addWidget(self.snippets_tree)
        self.left_dock_tabs.addTab(snippets_widget, "📝 Snippets")
        
        # Load snippets into tree
        self.load_snippets_tree()
        
        self.left_dock.setWidget(self.left_dock_tabs)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)
        
    def init_right_dock(self):
        """Initialize right sidebar with outline and properties"""
        self.right_dock = QDockWidget("Properties", self)
        self.right_dock_tabs = QTabWidget()
        
        # Table Structure
        self.table_structure = QTreeWidget()
        self.table_structure.setHeaderLabels(["Column", "Type", "Info"])
        self.right_dock_tabs.addTab(self.table_structure, "🏗️ Structure")
        
        # Query Results Info
        self.results_info = QTextEdit()
        self.results_info.setReadOnly(True)
        self.right_dock_tabs.addTab(self.results_info, "ℹ️ Info")
        
        self.right_dock.setWidget(self.right_dock_tabs)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)
        
    def init_bottom_dock(self):
        """Initialize bottom panel with terminal and output"""
        self.bottom_dock = QDockWidget("Output", self)
        self.bottom_dock_tabs = QTabWidget()
        
        # Terminal/Console
        self.terminal = QTextEdit()
        self.terminal.setStyleSheet(
            "background-color: #1e1e1e; color: #ffffff; font-family: 'Consolas', monospace;"
        )
        self.bottom_dock_tabs.addTab(self.terminal, "💻 Terminal")
        
        # Query Results
        self.results_table = QTableWidget()
        self.bottom_dock_tabs.addTab(self.results_table, "📊 Results")
        
        # Problems/Errors
        self.problems_list = QListWidget()
        self.bottom_dock_tabs.addTab(self.problems_list, "⚠️ Problems")
        
        self.bottom_dock.setWidget(self.bottom_dock_tabs)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)
        
    def init_toolbar(self):
        """Initialize main toolbar"""
        self.main_toolbar = QToolBar()
        self.main_toolbar.setMovable(False)
        self.main_toolbar.setFloatable(False)
        self.main_toolbar.setIconSize(QSize(24, 24))
        
        # File operations with font-based icons
        new_action = self.main_toolbar.addAction("📄 New")
        new_action.triggered.connect(self.new_session)
        
        open_action = self.main_toolbar.addAction("📂 Open")
        open_action.triggered.connect(self.open_session)
        
        save_action = self.main_toolbar.addAction("💾 Save")
        save_action.triggered.connect(self.save_session)
        
        self.main_toolbar.addSeparator()
        
        # Quick access buttons
        csv_btn = QPushButton('CSV')
        csv_btn.clicked.connect(lambda: self.editor_tabs.setCurrentIndex(0))
        self.main_toolbar.addWidget(csv_btn)
        
        sql_btn = QPushButton('SQL')
        sql_btn.clicked.connect(lambda: self.editor_tabs.setCurrentIndex(1))
        self.main_toolbar.addWidget(sql_btn)
        
        python_btn = QPushButton('Python')
        python_btn.clicked.connect(lambda: self.editor_tabs.setCurrentIndex(2))
        self.main_toolbar.addWidget(python_btn)
        
        ai_btn = QPushButton('AI')
        ai_btn.clicked.connect(lambda: self.editor_tabs.setCurrentIndex(3))
        self.main_toolbar.addWidget(ai_btn)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.main_toolbar.addWidget(spacer)
        
        # Settings menu
        settings_btn = QToolButton()
        settings_btn.setText('⚙️')
        settings_btn.setPopupMode(QToolButton.InstantPopup)
        settings_menu = QMenu(settings_btn)
        
        settings_action = settings_menu.addAction('Settings')
        settings_action.triggered.connect(self.open_settings)
        
        about_action = settings_menu.addAction('About')
        about_action.triggered.connect(self.show_about)
        
        settings_btn.setMenu(settings_menu)
        self.main_toolbar.addWidget(settings_btn)
        
        self.addToolBar(Qt.TopToolBarArea, self.main_toolbar)
        
        # Initially hide the toolbar
        self.main_toolbar.setVisible(False)
        self.toolbar_hidden = True
        
    def init_status_bar(self):
        """Initialize status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Add status indicators
        self.db_status_label = QLabel("No Database")
        self.status_bar.addPermanentWidget(self.db_status_label)
        
        self.row_count_label = QLabel("0 rows")
        self.status_bar.addPermanentWidget(self.row_count_label)
        
    def init_menu_bar(self):
        """Initialize menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = file_menu.addAction('New Session')
        new_action.triggered.connect(self.new_session)
        
        open_action = file_menu.addAction('Open Session')
        open_action.triggered.connect(self.open_session)
        
        save_action = file_menu.addAction('Save Session')
        save_action.triggered.connect(self.save_session)
        
        file_menu.addSeparator()
        
        import_csv_action = file_menu.addAction('Import CSV')
        import_csv_action.triggered.connect(self.import_csv)
        
        export_csv_action = file_menu.addAction('Export CSV')
        export_csv_action.triggered.connect(self.export_csv)
        
        export_xlsx_action = file_menu.addAction('Export XLSX')
        export_xlsx_action.triggered.connect(self.export_xlsx)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        toggle_left_action = view_menu.addAction('Toggle Left Panel')
        toggle_left_action.triggered.connect(lambda: self.left_dock.setVisible(not self.left_dock.isVisible()))
        
        toggle_right_action = view_menu.addAction('Toggle Right Panel')
        toggle_right_action.triggered.connect(lambda: self.right_dock.setVisible(not self.right_dock.isVisible()))
        
        toggle_bottom_action = view_menu.addAction('Toggle Bottom Panel')
        toggle_bottom_action.triggered.connect(lambda: self.bottom_dock.setVisible(not self.bottom_dock.isVisible()))
        
        #tools_menu.addSeparator()       
               
        toggle_toolbar_action = view_menu.addAction('Toggle Toolbar')
        toggle_toolbar_action.triggered.connect(self.toggle_toolbar)
        

        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        

        
        options_action = tools_menu.addAction('Options...')
        options_action.triggered.connect(self.open_options_dialog)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)
        
    def init_database(self):
        """Initialize SQLite database"""
        try:
            self.sqlite_conn = sqlite3.connect('../session_db.sqlite')
            self.db_status_label.setText("Database Connected")
            self.log_message("Database initialized successfully")
        except Exception as e:
            self.log_message(f"Database initialization failed: {e}")
            
    def load_settings(self):
        """Load application settings"""
        self.settings = {}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                self.confirm_on_exit = self.settings.get('confirm_on_exit', True)
                self.convert_first_row_to_headers = self.settings.get('convert_first_row_to_headers', False)
                
                # Load table double-click mode setting
                table_mode = self.settings.get('table_double_click_mode', 'CSV editor')
                if hasattr(self, 'table_manager'):
                    self.table_manager.double_click_mode = table_mode
                    self.table_manager.mode_switcher.setCurrentText(table_mode)
                    
                # Load and open last selected file
                last_file = self.settings.get('last_selected_file')
                if last_file and os.path.exists(last_file):
                    self.open_last_file(last_file)
                    
                # Load panel states
                self.load_panel_states()
            except Exception:
                pass
                
    def save_settings(self):
        """Save application settings"""
        try:
            # Update settings with current values
            self.settings.update({
                'confirm_on_exit': self.confirm_on_exit,
                'convert_first_row_to_headers': self.convert_first_row_to_headers
            })
            
            # Save table double-click mode if table manager exists
            if hasattr(self, 'table_manager'):
                self.settings['table_double_click_mode'] = self.table_manager.double_click_mode
                
            # Save last selected file if exists
            if hasattr(self, 'last_selected_file') and self.last_selected_file:
                self.settings['last_selected_file'] = self.last_selected_file
                
            # Save panel states
            self.save_panel_states()
                
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
            
    def open_last_file(self, file_path):
        """Open the last selected file on startup"""
        try:
            # Get file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Handle CSV/Excel files
            if ext in ['.csv', '.xlsx', '.xls']:
                if ext == '.csv':
                    # Load CSV file
                    self.csv_editor.load_csv_file(file_path)
                elif ext in ['.xlsx', '.xls']:
                    # Load Excel file
                    self.load_excel_file(file_path)
                    
                # Switch to CSV editor tab
                self.editor_tabs.setCurrentWidget(self.csv_editor)
                
                # Log action
                self.log_message(f"Restored last file: {os.path.basename(file_path)}")
                
                # Set as current last selected file
                self.last_selected_file = file_path
                
        except Exception as e:
            self.log_message(f"Failed to restore last file {file_path}: {e}")
            
    def save_panel_states(self):
        """Save the current state of dock panels"""
        try:
            panel_states = {
                'left_dock_visible': self.left_dock.isVisible(),
                'right_dock_visible': self.right_dock.isVisible(),
                'bottom_dock_visible': self.bottom_dock.isVisible(),
                'left_dock_floating': self.left_dock.isFloating(),
                'right_dock_floating': self.right_dock.isFloating(),
                'bottom_dock_floating': self.bottom_dock.isFloating(),
                'left_dock_tab_index': self.left_dock_tabs.currentIndex(),
                'right_dock_tab_index': self.right_dock_tabs.currentIndex(),
                'bottom_dock_tab_index': self.bottom_dock_tabs.currentIndex(),
                'editor_tab_index': self.editor_tabs.currentIndex(),
                'window_geometry': {
                    'x': self.x(),
                    'y': self.y(),
                    'width': self.width(),
                    'height': self.height()
                },
                'window_maximized': self.isMaximized()
            }
            self.settings['panel_states'] = panel_states
        except Exception as e:
            self.log_message(f"Failed to save panel states: {e}")
            
    def load_panel_states(self):
        """Load and restore the state of dock panels"""
        try:
            panel_states = self.settings.get('panel_states', {})
            
            # Restore dock visibility
            if 'left_dock_visible' in panel_states:
                self.left_dock.setVisible(panel_states['left_dock_visible'])
            if 'right_dock_visible' in panel_states:
                self.right_dock.setVisible(panel_states['right_dock_visible'])
            if 'bottom_dock_visible' in panel_states:
                self.bottom_dock.setVisible(panel_states['bottom_dock_visible'])
                
            # Restore floating state
            if 'left_dock_floating' in panel_states:
                self.left_dock.setFloating(panel_states['left_dock_floating'])
            if 'right_dock_floating' in panel_states:
                self.right_dock.setFloating(panel_states['right_dock_floating'])
            if 'bottom_dock_floating' in panel_states:
                self.bottom_dock.setFloating(panel_states['bottom_dock_floating'])
                
            # Restore tab indices
            if 'left_dock_tab_index' in panel_states:
                self.left_dock_tabs.setCurrentIndex(panel_states['left_dock_tab_index'])
            if 'right_dock_tab_index' in panel_states:
                self.right_dock_tabs.setCurrentIndex(panel_states['right_dock_tab_index'])
            if 'bottom_dock_tab_index' in panel_states:
                self.bottom_dock_tabs.setCurrentIndex(panel_states['bottom_dock_tab_index'])
            if 'editor_tab_index' in panel_states:
                self.editor_tabs.setCurrentIndex(panel_states['editor_tab_index'])
                
            # Restore window geometry
            if 'window_geometry' in panel_states:
                geom = panel_states['window_geometry']
                self.setGeometry(geom['x'], geom['y'], geom['width'], geom['height'])
                
            # Restore maximized state
            if panel_states.get('window_maximized', False):
                self.showMaximized()
                
        except Exception as e:
            self.log_message(f"Failed to load panel states: {e}")
            
    def log_message(self, message):
        """Log message to terminal"""
        self.terminal.append(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] {message}")
        
    def new_session(self):
        """Create new session"""
        self.csv_data = []
        self.csv_headers = []
        self.csv_editor.clear_table()
        self.sql_editor.clear_editor()
        self.python_editor.clear_editor()
        self.log_message("New session created")
        
    def open_session(self):
        """Open session from zip file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Session", "", "Session files (*.zip);;All files (*.*)"
        )
        if file_path:
            try:
                with zipfile.ZipFile(file_path, "r") as zf:
                    # Extract to temporary directory
                    temp_dir = tempfile.mkdtemp()
                    zf.extractall(temp_dir)
                    
                    # Load database if exists
                    db_path = os.path.join(temp_dir, "session_db.sqlite")
                    if os.path.exists(db_path):
                        if self.sqlite_conn:
                            self.sqlite_conn.close()
                        self.sqlite_conn = sqlite3.connect(db_path)
                        self.db_status_label.setText("Database Connected")
                        
                        # Update table manager if exists
                        if hasattr(self, 'table_manager'):
                            self.table_manager.refresh_tables()
                    
                    # Load query history if exists
                    history_path = os.path.join(temp_dir, "history.json")
                    if os.path.exists(history_path):
                        with open(history_path, "r", encoding="utf-8") as f:
                            history_data = json.load(f)
                            if hasattr(self, 'sql_editor') and self.sql_editor:
                                self.sql_editor.history = history_data
                                # Update query history tree if exists
                                if hasattr(self, 'query_history_tree'):
                                    self.load_query_history_tree()
                    
                    # Load session data if exists
                    session_path = os.path.join(temp_dir, "session.json")
                    if os.path.exists(session_path):
                        with open(session_path, "r", encoding="utf-8") as f:
                            session_data = json.load(f)
                            
                            # Load CSV data
                            if 'csv_data' in session_data:
                                self.csv_data = session_data['csv_data']
                            if 'csv_headers' in session_data:
                                self.csv_headers = session_data['csv_headers']
                                
                            # Load editor content
                            if 'sql_query' in session_data and hasattr(self, 'sql_editor'):
                                self.sql_editor.editor.setText(session_data['sql_query'])
                            if 'python_code' in session_data and hasattr(self, 'python_editor'):
                                self.python_editor.set_code_text(session_data['python_code'])
                                
                            # Update CSV editor
                            if self.csv_data and self.csv_headers:
                                self.csv_editor.load_data(self.csv_headers, self.csv_data)
                    
                    # Clean up temporary files (but keep database)
                    import shutil
                    for file in os.listdir(temp_dir):
                        if file != "session_db.sqlite":
                            file_path_temp = os.path.join(temp_dir, file)
                            if os.path.isfile(file_path_temp):
                                os.remove(file_path_temp)
                    
                self.log_message(f"Session loaded from {file_path}")
                QMessageBox.information(self, "Success", "Session loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load session: {e}")
                
    def save_session(self):
        """Save current session to zip file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Session", "", "Session files (*.zip);;All files (*.*)"
        )
        if file_path:
            try:
                # Create temporary files
                temp_dir = tempfile.mkdtemp()
                
                # Save database if exists
                db_temp_path = os.path.join(temp_dir, "session_db.sqlite")
                if self.sqlite_conn:
                    backup_conn = sqlite3.connect(db_temp_path)
                    self.sqlite_conn.backup(backup_conn)
                    backup_conn.close()
                
                # Save query history
                history_temp_path = os.path.join(temp_dir, "history.json")
                history_data = []
                if hasattr(self, 'sql_editor') and self.sql_editor and hasattr(self.sql_editor, 'history'):
                    history_data = self.sql_editor.history
                with open(history_temp_path, "w", encoding="utf-8") as f:
                    json.dump(history_data, f, ensure_ascii=False, indent=2)
                
                # Save session data
                session_temp_path = os.path.join(temp_dir, "session.json")
                session_data = {
                    'csv_data': self.csv_data,
                    'csv_headers': self.csv_headers,
                    'sql_query': self.sql_editor.get_query_text() if hasattr(self, 'sql_editor') else '',
                    'python_code': self.python_editor.get_code_text() if hasattr(self, 'python_editor') else ''
                }
                with open(session_temp_path, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)
                
                # Create zip file
                with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    if os.path.exists(db_temp_path):
                        zf.write(db_temp_path, "session_db.sqlite")
                    zf.write(history_temp_path, "history.json")
                    zf.write(session_temp_path, "session.json")
                
                # Clean up temporary files
                import shutil
                shutil.rmtree(temp_dir)
                
                self.log_message(f"Session saved to {file_path}")
                QMessageBox.information(self, "Success", "Session saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save session: {e}")
                
    def import_csv(self):
        """Import CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", "", "CSV files (*.csv);;All files (*.*)"
        )
        if file_path:
            self.csv_editor.load_csv_file(file_path)
            
    def export_csv(self):
        """Export CSV file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV files (*.csv);;All files (*.*)"
        )
        if file_path:
            self.csv_editor.save_csv_file(file_path)
            
    def export_xlsx(self):
        """Export XLSX file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export XLSX", "", "Excel files (*.xlsx);;All files (*.*)"
        )
        if file_path:
            self.csv_editor.save_xlsx_file(file_path)
            
    def open_settings(self):
        """Open settings dialog"""
        # TODO: Implement settings dialog
        QMessageBox.information(self, "Settings", "Settings dialog not implemented yet")
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", 
            "CSV Query Tool - VSCode Style\n\n"
            "A modern CSV editing and SQLite querying application\n"
            "with VSCode-inspired interface.\n\n"
            "Version: 2.0")
    
    def toggle_toolbar(self):
        """Toggle main toolbar visibility"""
        self.toolbar_hidden = not self.toolbar_hidden
        self.main_toolbar.setVisible(not self.toolbar_hidden)
        self.log_message(f"Toolbar {'hidden' if self.toolbar_hidden else 'shown'}")
    
    def open_options_dialog(self):
        """Open options dialog"""
        from options_dialog import OptionsDialog
        dialog = OptionsDialog(self)
        if dialog.exec_() == dialog.Accepted:
            # Apply settings from dialog
            self.apply_options(dialog.get_options())
    
    def apply_options(self, options):
        """Apply options from the options dialog"""
        # Update settings based on options
        for key, value in options.items():
            self.settings[key] = value
        
        # Apply specific settings
        if 'confirm_on_exit' in options:
            self.confirm_on_exit = options['confirm_on_exit']
        if 'convert_first_row_to_headers' in options:
            self.convert_first_row_to_headers = options['convert_first_row_to_headers']
        
        # Save settings
        self.save_settings()
        self.log_message("Options applied successfully")
            
    def load_snippets_tree(self):
        """Load code snippets into the tree widget"""
        self.snippets_tree.clear()
        
        # Load snippets from python editor
        if hasattr(self.python_editor, 'snippets') and self.python_editor.snippets:
            for group in self.python_editor.snippets:
                group_item = QTreeWidgetItem(self.snippets_tree)
                group_item.setText(0, group['name'])
                group_item.setData(0, Qt.UserRole, {'type': 'group', 'data': group})
                
                for snippet in group['snippets']:
                    snippet_item = QTreeWidgetItem(group_item)
                    snippet_item.setText(0, snippet['name'])
                    snippet_item.setData(0, Qt.UserRole, {'type': 'snippet', 'data': snippet})
                    
            self.snippets_tree.expandAll()
            
    def on_snippet_double_clicked(self, item, column):
        """Handle double-click on snippet item"""
        item_data = item.data(0, Qt.UserRole)
        if item_data and item_data.get('type') == 'snippet':
            snippet = item_data['data']
            
            # Load code into Python editor
            self.python_editor.set_code_text(snippet['code'])
            
            # Switch to Python tab
            self.editor_tabs.setCurrentWidget(self.python_editor)
            
            # Log action
            self.log_message(f"Loaded snippet: {snippet['name']}")
            
            # Focus on the code editor
            self.python_editor.code_edit.setFocus()
            
    def refresh_snippets_tree(self):
        """Refresh the snippets tree (useful after adding/editing snippets)"""
        self.load_snippets_tree()
        
    def show_snippet_context_menu(self, position):
        """Show context menu for snippets tree"""
        item = self.snippets_tree.itemAt(position)
        menu = QMenu(self)
        
        if item:
            item_data = item.data(0, Qt.UserRole)
            if item_data and item_data.get('type') == 'snippet':
                load_action = menu.addAction("Load Snippet")
                load_action.triggered.connect(lambda: self.on_snippet_double_clicked(item, 0))
                
                load_and_run_action = menu.addAction("Load and Execute")
                load_and_run_action.triggered.connect(lambda: self.load_and_execute_snippet(item))
                
        menu.addSeparator()
        refresh_action = menu.addAction("Refresh Snippets")
        refresh_action.triggered.connect(self.refresh_snippets_tree)
        
        open_python_action = menu.addAction("Open Python Editor")
        open_python_action.triggered.connect(lambda: self.editor_tabs.setCurrentWidget(self.python_editor))
        
        if menu.actions():
            menu.exec_(self.snippets_tree.mapToGlobal(position))
            
    def load_and_execute_snippet(self, item):
        """Load snippet and execute it immediately"""
        item_data = item.data(0, Qt.UserRole)
        if item_data and item_data.get('type') == 'snippet':
            snippet = item_data['data']
            
            # Load code into Python editor
            self.python_editor.set_code_text(snippet['code'])
            
            # Switch to Python tab
            self.editor_tabs.setCurrentWidget(self.python_editor)
            
            # Execute the code
            self.python_editor.execute_code()
            
            # Log action
            self.log_message(f"Loaded and executed snippet: {snippet['name']}")
    
    def add_query_group(self):
        """Add a new query group to the history tree"""
        text, ok = QInputDialog.getText(self, 'Add Query Group', 'Enter group name:')
        if ok and text:
            group_item = QTreeWidgetItem([text])
            group_item.setData(0, Qt.UserRole, {'type': 'group', 'name': text})
            self.query_history_tree.addTopLevelItem(group_item)
            group_item.setExpanded(True)
    
    def edit_query_item(self):
         """Edit the selected query item"""
         current_item = self.query_history_tree.currentItem()
         if current_item:
             data = current_item.data(0, Qt.UserRole)
             if data and data.get('type') == 'query':
                 # Load the query into the SQL editor
                 if hasattr(self, 'sql_editor') and self.sql_editor:
                     self.sql_editor.editor.setText(data.get('query', ''))
                     # Switch to SQL tab
                     self.editor_tabs.setCurrentWidget(self.sql_editor)
             elif data and data.get('type') == 'group':
                 # Rename group
                 text, ok = QInputDialog.getText(self, 'Edit Group Name', 'Enter new name:', text=current_item.text(0))
                 if ok and text:
                     current_item.setText(0, text)
                     data['name'] = text
                     current_item.setData(0, Qt.UserRole, data)
    
    def delete_query_item(self):
        """Delete the selected query item"""
        current_item = self.query_history_tree.currentItem()
        if current_item:
            reply = QMessageBox.question(self, 'Delete Item', 
                                       f'Are you sure you want to delete "{current_item.text(0)}"?',
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                parent = current_item.parent()
                if parent:
                    parent.removeChild(current_item)
                else:
                    index = self.query_history_tree.indexOfTopLevelItem(current_item)
                    self.query_history_tree.takeTopLevelItem(index)
    
    def on_query_double_clicked(self, item, column):
         """Handle double-click on query history item"""
         data = item.data(0, Qt.UserRole)
         if data and data.get('type') == 'query':
             # Load the query into the SQL editor
             if hasattr(self, 'sql_editor') and self.sql_editor:
                 query_data = data.get('data', {})
                 self.sql_editor.sql_edit.setText(query_data.get('query', ''))
                 # Load task numbers if available
                 if 'task_numbers' in query_data:
                     self.sql_editor.task_numbers_edit.setPlainText(query_data.get('task_numbers', ''))
                 # Load parameters if available
                 if 'params' in query_data:
                     self.sql_editor.query_params.update(query_data.get('params', {}))
                 # Set the loaded query item so auto-save updates this item
                 self.sql_editor.set_loaded_query_item(item)
                 # Switch to SQL tab
                 self.editor_tabs.setCurrentWidget(self.sql_editor)
         elif data and data.get('type') == 'group':
             # For groups, just expand/collapse
             item.setExpanded(not item.isExpanded())
    
    def show_query_context_menu(self, position):
        """Show context menu for query history tree"""
        item = self.query_history_tree.itemAt(position)
        if item:
            menu = QMenu()
            data = item.data(0, Qt.UserRole)
            
            if data and data.get('type') == 'query':
                load_action = menu.addAction("Load Query")
                edit_action = menu.addAction("Edit Name")
                delete_action = menu.addAction("Delete")
                
                action = menu.exec_(self.query_history_tree.mapToGlobal(position))
                if action == load_action:
                    self.on_query_double_clicked(item, 0)
                elif action == edit_action:
                    self.edit_query_item()
                elif action == delete_action:
                    self.delete_query_item()
            elif data and data.get('type') == 'group':
                add_query_action = menu.addAction("Add Query")
                rename_action = menu.addAction("Rename Group")
                delete_action = menu.addAction("Delete Group")
                
                action = menu.exec_(self.query_history_tree.mapToGlobal(position))
                if action == add_query_action:
                    self.add_query_to_group(item)
                elif action == rename_action:
                    self.edit_query_item()
                elif action == delete_action:
                    self.delete_query_item()
    
    def add_query_to_group(self, group_item):
        """Add a new query to the specified group"""
        name, ok = QInputDialog.getText(self, 'Add Query', 'Enter query name:')
        if ok and name.strip():
            # Get current query from SQL editor if available
            query_text = ''
            task_numbers = ''
            params = {}
            
            if hasattr(self, 'sql_editor') and self.sql_editor:
                query_text = self.sql_editor.sql_edit.text()
                task_numbers = self.sql_editor.task_numbers_edit.toPlainText()
                params = self.sql_editor.query_params.copy()
            
            query_data = {
                'name': name.strip(),
                'query': query_text,
                'task_numbers': task_numbers,
                'params': params,
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            query_item = QTreeWidgetItem([name.strip()])
            query_item.setData(0, Qt.UserRole, {'type': 'query', 'data': query_data})
            group_item.addChild(query_item)
            group_item.setExpanded(True)
            
            # Save to persistent storage
            self.save_query_history_tree()
    
    def save_query_history_tree(self):
        """Save the query history tree to file"""
        history_data = []
        
        for i in range(self.query_history_tree.topLevelItemCount()):
            group_item = self.query_history_tree.topLevelItem(i)
            group_data = group_item.data(0, Qt.UserRole)
            
            if group_data and group_data.get('type') == 'group':
                group_entry = {
                    'name': group_data.get('name', group_item.text(0)),
                    'queries': []
                }
                
                for j in range(group_item.childCount()):
                    query_item = group_item.child(j)
                    query_data = query_item.data(0, Qt.UserRole)
                    
                    if query_data and query_data.get('type') == 'query':
                        group_entry['queries'].append(query_data.get('data', {}))
                
                history_data.append(group_entry)
        
        try:
            with open('query_history.json', 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"Failed to save query history: {e}")
    
    def load_query_history_tree(self):
        """Load the query history tree from file"""
        try:
            if os.path.exists('query_history.json'):
                with open('query_history.json', 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                self.query_history_tree.clear()
                
                for group_entry in history_data:
                    group_item = QTreeWidgetItem([group_entry.get('name', 'Unnamed Group')])
                    group_item.setData(0, Qt.UserRole, {'type': 'group', 'name': group_entry.get('name', 'Unnamed Group')})
                    
                    for query_entry in group_entry.get('queries', []):
                        query_name = query_entry.get('name', 'Unnamed Query')
                        query_item = QTreeWidgetItem([query_name])
                        query_item.setData(0, Qt.UserRole, {'type': 'query', 'data': query_entry})
                        group_item.addChild(query_item)
                    
                    self.query_history_tree.addTopLevelItem(group_item)
                    group_item.setExpanded(True)
        except Exception as e:
            self.log_message(f"Failed to load query history: {e}")
    
    def add_snippet(self):
        """Add a new code snippet"""
        # Get snippet name
        name, ok = QInputDialog.getText(self, "Add Snippet", "Enter snippet name:")
        if not ok or not name.strip():
            return
            
        # Get current code from Python editor
        code = self.python_editor.get_code_text()
        if not code.strip():
            reply = QMessageBox.question(
                self, "Empty Code", 
                "Python editor is empty. Do you want to add an empty snippet?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
        # Get group name
        groups = [group['name'] for group in self.python_editor.snippets] if hasattr(self.python_editor, 'snippets') else []
        if groups:
            group_name, ok = QInputDialog.getItem(
                self, "Select Group", "Choose a group or type a new one:", 
                groups + ["<New Group>"], 0, True
            )
            if not ok:
                return
            if group_name == "<New Group>":
                group_name, ok = QInputDialog.getText(self, "New Group", "Enter group name:")
                if not ok or not group_name.strip():
                    return
        else:
            group_name, ok = QInputDialog.getText(self, "New Group", "Enter group name:")
            if not ok or not group_name.strip():
                return
                
        # Add snippet to python editor
        self.python_editor.add_snippet_to_group(group_name.strip(), name.strip(), code)
        self.refresh_snippets_tree()
        self.log_message(f"Added snippet '{name}' to group '{group_name}'")
        
    def edit_snippet(self):
        """Edit selected snippet"""
        current_item = self.snippets_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Please select a snippet to edit")
            return
            
        item_data = current_item.data(0, Qt.UserRole)
        if not item_data or item_data.get('type') != 'snippet':
            QMessageBox.information(self, "Info", "Please select a snippet (not a group) to edit")
            return
            
        snippet = item_data['data']
        
        # Edit snippet name
        new_name, ok = QInputDialog.getText(
            self, "Edit Snippet", "Enter new name:", text=snippet['name']
        )
        if not ok or not new_name.strip():
            return
            
        # Load current snippet code into editor for editing
        self.python_editor.set_code_text(snippet['code'])
        self.editor_tabs.setCurrentWidget(self.python_editor)
        
        # Ask user to edit code and confirm
        reply = QMessageBox.question(
            self, "Edit Code", 
            "The snippet code has been loaded into the Python editor. "
            "Edit the code as needed, then click Yes to save changes.",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            new_code = self.python_editor.get_code_text()
            # Update snippet in python editor
            self.python_editor.update_snippet(snippet['name'], new_name.strip(), new_code)
            self.refresh_snippets_tree()
            self.log_message(f"Updated snippet '{snippet['name']}' to '{new_name}'")
            
    def delete_snippet(self):
        """Delete selected snippet"""
        current_item = self.snippets_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Please select a snippet to delete")
            return
            
        item_data = current_item.data(0, Qt.UserRole)
        if not item_data or item_data.get('type') != 'snippet':
            QMessageBox.information(self, "Info", "Please select a snippet (not a group) to delete")
            return
            
        snippet = item_data['data']
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Delete Snippet", 
            f"Are you sure you want to delete the snippet '{snippet['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete snippet from python editor
            self.python_editor.delete_snippet(snippet['name'])
            self.refresh_snippets_tree()
            self.log_message(f"Deleted snippet '{snippet['name']}'")
             
    def on_file_double_clicked(self, index):
        """Handle double-click on file in explorer"""
        file_path = self.file_model.filePath(index)
        
        # Check if it's a file (not directory)
        if not os.path.isfile(file_path):
            return
            
        # Save as last selected file
        self.last_selected_file = file_path
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Handle CSV/Excel files
        if ext in ['.csv', '.xlsx', '.xls']:
            try:
                if ext == '.csv':
                    # Load CSV file
                    self.csv_editor.load_csv_file(file_path)
                elif ext in ['.xlsx', '.xls']:
                    # Load Excel file
                    self.load_excel_file(file_path)
                    
                # Switch to CSV editor tab
                self.editor_tabs.setCurrentWidget(self.csv_editor)
                
                # Log action
                self.log_message(f"Loaded file: {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
                self.log_message(f"Failed to load file {file_path}: {e}")
                
    def load_excel_file(self, file_path):
        """Load Excel file with multiple sheets into table manager"""
        try:
            import pandas as pd
            
            # Read all sheets from Excel file
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            if len(sheet_names) == 1:
                # Single sheet - ask user if they want formatting
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self, 'Excel Import Options',
                    'Do you want to import with cell formatting and font options?\n\n'
                    'Yes: Import with formatting (slower but preserves appearance)\n'
                    'No: Import data only (faster)',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # Load with formatting options
                    try:
                        from excel_format_dialog import ExcelFormatDialog
                        dialog = ExcelFormatDialog(self)
                        if dialog.exec_() == QDialog.Accepted:
                            options = dialog.get_options()
                            self.csv_editor.load_excel_file_with_formatting(file_path, options)
                        else:
                            # User cancelled, load without formatting
                            self.csv_editor.load_excel_file_simple(file_path)
                    except ImportError:
                        QMessageBox.warning(self, "Warning", 
                            "openpyxl not available. Loading without formatting.")
                        self.csv_editor.load_excel_file_simple(file_path)
                else:
                    # Load without formatting
                    self.csv_editor.load_excel_file_simple(file_path)
                
                # Update window state
                self.csv_headers = self.csv_editor.csv_headers
                self.csv_data = self.csv_editor.csv_data
            else:
                # Multiple sheets - create tables for each sheet
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                
                for sheet_name in sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Clean and prepare data
                    headers = [str(col) for col in df.columns.tolist()]
                    data = df.fillna('').values.tolist()
                    
                    # Create unique table name
                    table_name = f"{base_name}_{sheet_name}"
                    table_name = self.table_manager.generate_unique_table_name(table_name)
                    
                    # Create table in database
                    self.table_manager.create_table_from_data(table_name, headers, data)
                    
                # Refresh table list
                self.table_manager.refresh_tables()
                
                # Switch to tables tab
                self.left_dock_tabs.setCurrentIndex(1)  # Tables tab
                
                self.log_message(f"Loaded Excel file with {len(sheet_names)} sheets into tables")
            
        except ImportError:
            QMessageBox.critical(self, "Error", 
                "pandas library is required to load Excel files. "
                "Please install it using: pip install pandas openpyxl")
        except Exception as e:
            raise Exception(f"Failed to load Excel file: {e}")
        
    def closeEvent(self, event):
        """Handle application close event"""
        if self.confirm_on_exit:
            reply = QMessageBox.question(
                self, 'Exit Confirmation',
                'Are you sure you want to exit?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.save_settings()
                if self.sqlite_conn:
                    self.sqlite_conn.close()
                event.accept()
            else:
                event.ignore()
        else:
            self.save_settings()
            if self.sqlite_conn:
                self.sqlite_conn.close()
            event.accept()
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            # Check if any of the dragged files are CSV or Excel files
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path and os.path.isfile(file_path):
                    _, ext = os.path.splitext(file_path)
                    if ext.lower() in ['.csv', '.xlsx', '.xls']:
                        event.acceptProposedAction()
                        return
        event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path and os.path.isfile(file_path):
                    _, ext = os.path.splitext(file_path)
                    if ext.lower() in ['.csv', '.xlsx', '.xls']:
                        try:
                            # Save as last selected file
                            self.last_selected_file = file_path
                            
                            if ext.lower() == '.csv':
                                # Load CSV file
                                self.csv_editor.load_csv_file(file_path)
                            elif ext.lower() in ['.xlsx', '.xls']:
                                # Load Excel file
                                self.load_excel_file(file_path)
                            
                            # Switch to CSV editor tab
                            self.editor_tabs.setCurrentWidget(self.csv_editor)
                            
                            # Log action
                            self.log_message(f"Loaded file via drag-and-drop: {os.path.basename(file_path)}")
                            
                            # Save settings to persist last selected file
                            self.save_settings()
                            
                        except Exception as e:
                            QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
                            self.log_message(f"Failed to load file {file_path}: {e}")
                        
                        break  # Only process the first valid file
            
            event.acceptProposedAction()
        else:
            event.ignore()