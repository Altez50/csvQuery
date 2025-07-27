from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                             QTreeWidgetItem, QStackedWidget, QWidget, QLabel, 
                             QCheckBox, QComboBox, QSpinBox, QLineEdit, QPushButton,
                             QGroupBox, QGridLayout, QScrollArea, QSplitter,
                             QDialogButtonBox, QFrame, QTextEdit, QSlider,
                             QColorDialog, QFontDialog, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
import json
import os

class OptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.options = {}
        self.option_widgets = {}
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.init_ui()
        self.load_current_settings()
        
    def init_ui(self):
        """Initialize the options dialog UI"""
        self.setWindowTitle("Options")
        self.setModal(True)
        self.resize(800, 600)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search options...")
        self.search_edit.textChanged.connect(self.on_search_changed)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        main_layout.addLayout(search_layout)
        
        # Splitter for tree and content
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Options tree
        self.options_tree = QTreeWidget()
        self.options_tree.setHeaderLabel("Options")
        self.options_tree.setMaximumWidth(250)
        self.options_tree.currentItemChanged.connect(self.on_tree_selection_changed)
        
        # Right side - Options content
        self.content_stack = QStackedWidget()
        
        splitter.addWidget(self.options_tree)
        splitter.addWidget(self.content_stack)
        splitter.setSizes([250, 550])
        
        main_layout.addWidget(splitter)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_options)
        
        main_layout.addLayout(QHBoxLayout())
        main_layout.addWidget(button_box)
        
        self.create_option_pages()
        
    def create_option_pages(self):
        """Create all option pages and populate the tree"""
        # General options
        general_item = QTreeWidgetItem(["General"])
        self.options_tree.addTopLevelItem(general_item)
        general_page = self.create_general_page()
        self.content_stack.addWidget(general_page)
        general_item.setData(0, Qt.UserRole, self.content_stack.count() - 1)
        
        # Appearance options
        appearance_item = QTreeWidgetItem(["Appearance"])
        self.options_tree.addTopLevelItem(appearance_item)
        
        # Theme sub-item
        theme_item = QTreeWidgetItem(["Theme"])
        appearance_item.addChild(theme_item)
        theme_page = self.create_theme_page()
        self.content_stack.addWidget(theme_page)
        theme_item.setData(0, Qt.UserRole, self.content_stack.count() - 1)
        
        # Font sub-item
        font_item = QTreeWidgetItem(["Font"])
        appearance_item.addChild(font_item)
        font_page = self.create_font_page()
        self.content_stack.addWidget(font_page)
        font_item.setData(0, Qt.UserRole, self.content_stack.count() - 1)
        
        # Editor options
        editor_item = QTreeWidgetItem(["Editor"])
        self.options_tree.addTopLevelItem(editor_item)
        
        # CSV Editor sub-item
        csv_editor_item = QTreeWidgetItem(["CSV Editor"])
        editor_item.addChild(csv_editor_item)
        csv_page = self.create_csv_editor_page()
        self.content_stack.addWidget(csv_page)
        csv_editor_item.setData(0, Qt.UserRole, self.content_stack.count() - 1)
        
        # SQL Editor sub-item
        sql_editor_item = QTreeWidgetItem(["SQL Editor"])
        editor_item.addChild(sql_editor_item)
        sql_page = self.create_sql_editor_page()
        self.content_stack.addWidget(sql_page)
        sql_editor_item.setData(0, Qt.UserRole, self.content_stack.count() - 1)
        
        # Python Editor sub-item
        python_editor_item = QTreeWidgetItem(["Python Editor"])
        editor_item.addChild(python_editor_item)
        python_page = self.create_python_editor_page()
        self.content_stack.addWidget(python_page)
        python_editor_item.setData(0, Qt.UserRole, self.content_stack.count() - 1)
        
        # Excel Import sub-item
        excel_import_item = QTreeWidgetItem(["Excel Import"])
        editor_item.addChild(excel_import_item)
        excel_page = self.create_excel_import_page()
        self.content_stack.addWidget(excel_page)
        excel_import_item.setData(0, Qt.UserRole, self.content_stack.count() - 1)
        
        # Advanced options
        advanced_item = QTreeWidgetItem(["Advanced"])
        self.options_tree.addTopLevelItem(advanced_item)
        
        # Performance sub-item
        performance_item = QTreeWidgetItem(["Performance"])
        advanced_item.addChild(performance_item)
        performance_page = self.create_performance_page()
        self.content_stack.addWidget(performance_page)
        performance_item.setData(0, Qt.UserRole, self.content_stack.count() - 1)
        
        # Debugging sub-item
        debug_item = QTreeWidgetItem(["Debugging"])
        advanced_item.addChild(debug_item)
        debug_page = self.create_debug_page()
        self.content_stack.addWidget(debug_page)
        debug_item.setData(0, Qt.UserRole, self.content_stack.count() - 1)
        
        # Expand all items
        self.options_tree.expandAll()
        
        # Select first item
        self.options_tree.setCurrentItem(general_item)
        
    def create_general_page(self):
        """Create general options page"""
        page = QScrollArea()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Startup group
        startup_group = QGroupBox("Startup")
        startup_layout = QGridLayout(startup_group)
        
        # Confirm on exit
        confirm_exit_cb = QCheckBox("Confirm before exiting")
        self.option_widgets['confirm_on_exit'] = confirm_exit_cb
        startup_layout.addWidget(confirm_exit_cb, 0, 0, 1, 2)
        
        # Restore last session
        restore_session_cb = QCheckBox("Restore last session on startup")
        self.option_widgets['restore_last_session'] = restore_session_cb
        startup_layout.addWidget(restore_session_cb, 1, 0, 1, 2)
        
        # Open last opened file
        open_last_file_cb = QCheckBox("Open last opened file on startup")
        self.option_widgets['open_last_opened_file'] = open_last_file_cb
        startup_layout.addWidget(open_last_file_cb, 2, 0, 1, 2)
        
        # Last opened file display
        startup_layout.addWidget(QLabel("Last opened file:"), 3, 0)
        self.last_file_label = QLabel("None")
        self.last_file_label.setWordWrap(True)
        self.last_file_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        startup_layout.addWidget(self.last_file_label, 3, 1)
        
        # Auto-save interval
        startup_layout.addWidget(QLabel("Auto-save interval (minutes):"), 4, 0)
        autosave_spin = QSpinBox()
        autosave_spin.setRange(0, 60)
        autosave_spin.setValue(5)
        autosave_spin.setSpecialValueText("Disabled")
        self.option_widgets['autosave_interval'] = autosave_spin
        startup_layout.addWidget(autosave_spin, 4, 1)
        
        layout.addWidget(startup_group)
        
        # File handling group
        file_group = QGroupBox("File Handling")
        file_layout = QGridLayout(file_group)
        
        # Convert first row to headers
        headers_cb = QCheckBox("Convert first row to headers when loading CSV")
        self.option_widgets['convert_first_row_to_headers'] = headers_cb
        file_layout.addWidget(headers_cb, 0, 0, 1, 2)
        
        # Default encoding
        file_layout.addWidget(QLabel("Default file encoding:"), 1, 0)
        encoding_combo = QComboBox()
        encoding_combo.addItems(['utf-8', 'utf-16', 'ascii', 'latin-1', 'cp1252'])
        self.option_widgets['default_encoding'] = encoding_combo
        file_layout.addWidget(encoding_combo, 1, 1)
        
        # Max recent files
        file_layout.addWidget(QLabel("Maximum recent files:"), 2, 0)
        recent_spin = QSpinBox()
        recent_spin.setRange(5, 50)
        recent_spin.setValue(10)
        self.option_widgets['max_recent_files'] = recent_spin
        file_layout.addWidget(recent_spin, 2, 1)
        
        layout.addWidget(file_group)
        
        layout.addStretch()
        page.setWidget(widget)
        return page
        
    def create_theme_page(self):
        """Create theme options page"""
        page = QScrollArea()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Theme group
        theme_group = QGroupBox("Color Theme")
        theme_layout = QGridLayout(theme_group)
        
        # Theme selection
        theme_layout.addWidget(QLabel("Theme:"), 0, 0)
        theme_combo = QComboBox()
        theme_combo.addItems(['Light', 'Dark', 'Auto (System)', 'High Contrast'])
        self.option_widgets['theme'] = theme_combo
        theme_layout.addWidget(theme_combo, 0, 1)
        
        # Custom colors
        theme_layout.addWidget(QLabel("Background color:"), 1, 0)
        bg_color_btn = QPushButton("Choose Color")
        bg_color_btn.clicked.connect(lambda: self.choose_color('background_color'))
        self.option_widgets['background_color'] = bg_color_btn
        theme_layout.addWidget(bg_color_btn, 1, 1)
        
        theme_layout.addWidget(QLabel("Text color:"), 2, 0)
        text_color_btn = QPushButton("Choose Color")
        text_color_btn.clicked.connect(lambda: self.choose_color('text_color'))
        self.option_widgets['text_color'] = text_color_btn
        theme_layout.addWidget(text_color_btn, 2, 1)
        
        layout.addWidget(theme_group)
        layout.addStretch()
        page.setWidget(widget)
        return page
        
    def create_font_page(self):
        """Create font options page"""
        page = QScrollArea()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Font group
        font_group = QGroupBox("Font Settings")
        font_layout = QGridLayout(font_group)
        
        # Font family
        font_layout.addWidget(QLabel("Font family:"), 0, 0)
        font_btn = QPushButton("Choose Font")
        font_btn.clicked.connect(self.choose_font)
        self.option_widgets['font_family'] = font_btn
        font_layout.addWidget(font_btn, 0, 1)
        
        # Font size
        font_layout.addWidget(QLabel("Font size:"), 1, 0)
        font_size_spin = QSpinBox()
        font_size_spin.setRange(8, 72)
        font_size_spin.setValue(10)
        self.option_widgets['font_size'] = font_size_spin
        font_layout.addWidget(font_size_spin, 1, 1)
        
        layout.addWidget(font_group)
        layout.addStretch()
        page.setWidget(widget)
        return page
        
    def create_csv_editor_page(self):
        """Create CSV editor options page"""
        page = QScrollArea()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Display group
        display_group = QGroupBox("Display Options")
        display_layout = QGridLayout(display_group)
        
        # Show grid lines
        grid_cb = QCheckBox("Show grid lines")
        self.option_widgets['csv_show_grid'] = grid_cb
        display_layout.addWidget(grid_cb, 0, 0, 1, 2)
        
        # Alternate row colors
        alt_colors_cb = QCheckBox("Alternate row colors")
        self.option_widgets['csv_alternate_colors'] = alt_colors_cb
        display_layout.addWidget(alt_colors_cb, 1, 0, 1, 2)
        
        # Max rows to display
        display_layout.addWidget(QLabel("Max rows to display:"), 2, 0)
        max_rows_spin = QSpinBox()
        max_rows_spin.setRange(100, 100000)
        max_rows_spin.setValue(10000)
        self.option_widgets['csv_max_rows'] = max_rows_spin
        display_layout.addWidget(max_rows_spin, 2, 1)
        
        layout.addWidget(display_group)
        
        # Editing group
        editing_group = QGroupBox("Editing Options")
        editing_layout = QGridLayout(editing_group)
        
        # Auto-resize columns
        auto_resize_cb = QCheckBox("Auto-resize columns to content")
        self.option_widgets['csv_auto_resize'] = auto_resize_cb
        editing_layout.addWidget(auto_resize_cb, 0, 0, 1, 2)
        
        # Undo levels
        editing_layout.addWidget(QLabel("Undo levels:"), 1, 0)
        undo_spin = QSpinBox()
        undo_spin.setRange(10, 1000)
        undo_spin.setValue(100)
        self.option_widgets['csv_undo_levels'] = undo_spin
        editing_layout.addWidget(undo_spin, 1, 1)
        
        layout.addWidget(editing_group)
        layout.addStretch()
        page.setWidget(widget)
        return page
        
    def create_sql_editor_page(self):
        """Create SQL editor options page"""
        page = QScrollArea()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Editor group
        editor_group = QGroupBox("SQL Editor")
        editor_layout = QGridLayout(editor_group)
        
        # Syntax highlighting
        syntax_cb = QCheckBox("Enable syntax highlighting")
        self.option_widgets['sql_syntax_highlighting'] = syntax_cb
        editor_layout.addWidget(syntax_cb, 0, 0, 1, 2)
        
        # Auto-completion
        autocomplete_cb = QCheckBox("Enable auto-completion")
        self.option_widgets['sql_auto_completion'] = autocomplete_cb
        editor_layout.addWidget(autocomplete_cb, 1, 0, 1, 2)
        
        # Line numbers
        line_numbers_cb = QCheckBox("Show line numbers")
        self.option_widgets['sql_line_numbers'] = line_numbers_cb
        editor_layout.addWidget(line_numbers_cb, 2, 0, 1, 2)
        
        # Tab size
        editor_layout.addWidget(QLabel("Tab size:"), 3, 0)
        tab_size_spin = QSpinBox()
        tab_size_spin.setRange(2, 8)
        tab_size_spin.setValue(4)
        self.option_widgets['sql_tab_size'] = tab_size_spin
        editor_layout.addWidget(tab_size_spin, 3, 1)
        
        layout.addWidget(editor_group)
        
        # Query execution group
        exec_group = QGroupBox("Query Execution")
        exec_layout = QGridLayout(exec_group)
        
        # Query timeout
        exec_layout.addWidget(QLabel("Query timeout (seconds):"), 0, 0)
        timeout_spin = QSpinBox()
        timeout_spin.setRange(5, 300)
        timeout_spin.setValue(30)
        self.option_widgets['sql_query_timeout'] = timeout_spin
        exec_layout.addWidget(timeout_spin, 0, 1)
        
        # Max result rows
        exec_layout.addWidget(QLabel("Max result rows:"), 1, 0)
        max_result_spin = QSpinBox()
        max_result_spin.setRange(100, 50000)
        max_result_spin.setValue(5000)
        self.option_widgets['sql_max_results'] = max_result_spin
        exec_layout.addWidget(max_result_spin, 1, 1)
        
        layout.addWidget(exec_group)
        layout.addStretch()
        page.setWidget(widget)
        return page
        
    def create_python_editor_page(self):
        """Create Python editor options page"""
        page = QScrollArea()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Editor group
        editor_group = QGroupBox("Python Editor")
        editor_layout = QGridLayout(editor_group)
        
        # Syntax highlighting
        syntax_cb = QCheckBox("Enable syntax highlighting")
        self.option_widgets['python_syntax_highlighting'] = syntax_cb
        editor_layout.addWidget(syntax_cb, 0, 0, 1, 2)
        
        # Auto-indentation
        auto_indent_cb = QCheckBox("Enable auto-indentation")
        self.option_widgets['python_auto_indent'] = auto_indent_cb
        editor_layout.addWidget(auto_indent_cb, 1, 0, 1, 2)
        
        # Show whitespace
        whitespace_cb = QCheckBox("Show whitespace characters")
        self.option_widgets['python_show_whitespace'] = whitespace_cb
        editor_layout.addWidget(whitespace_cb, 2, 0, 1, 2)
        
        # Indent size
        editor_layout.addWidget(QLabel("Indent size:"), 3, 0)
        indent_spin = QSpinBox()
        indent_spin.setRange(2, 8)
        indent_spin.setValue(4)
        self.option_widgets['python_indent_size'] = indent_spin
        editor_layout.addWidget(indent_spin, 3, 1)
        
        layout.addWidget(editor_group)
        
        # Execution group
        exec_group = QGroupBox("Code Execution")
        exec_layout = QGridLayout(exec_group)
        
        # Python interpreter
        exec_layout.addWidget(QLabel("Python interpreter:"), 0, 0)
        interpreter_edit = QLineEdit()
        interpreter_edit.setPlaceholderText("Path to Python interpreter")
        self.option_widgets['python_interpreter'] = interpreter_edit
        exec_layout.addWidget(interpreter_edit, 0, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_python_interpreter)
        exec_layout.addWidget(browse_btn, 0, 2)
        
        layout.addWidget(exec_group)
        layout.addStretch()
        page.setWidget(widget)
        return page
        
    def create_performance_page(self):
        """Create performance options page"""
        page = QScrollArea()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Memory group
        memory_group = QGroupBox("Memory Management")
        memory_layout = QGridLayout(memory_group)
        
        # Memory limit
        memory_layout.addWidget(QLabel("Memory limit (MB):"), 0, 0)
        memory_spin = QSpinBox()
        memory_spin.setRange(256, 8192)
        memory_spin.setValue(1024)
        self.option_widgets['memory_limit'] = memory_spin
        memory_layout.addWidget(memory_spin, 0, 1)
        
        # Cache size
        memory_layout.addWidget(QLabel("Cache size (MB):"), 1, 0)
        cache_spin = QSpinBox()
        cache_spin.setRange(50, 1024)
        cache_spin.setValue(256)
        self.option_widgets['cache_size'] = cache_spin
        memory_layout.addWidget(cache_spin, 1, 1)
        
        layout.addWidget(memory_group)
        
        # Processing group
        processing_group = QGroupBox("Processing")
        processing_layout = QGridLayout(processing_group)
        
        # Thread count
        processing_layout.addWidget(QLabel("Worker threads:"), 0, 0)
        thread_spin = QSpinBox()
        thread_spin.setRange(1, 16)
        thread_spin.setValue(4)
        self.option_widgets['worker_threads'] = thread_spin
        processing_layout.addWidget(thread_spin, 0, 1)
        
        # Chunk size
        processing_layout.addWidget(QLabel("Processing chunk size:"), 1, 0)
        chunk_spin = QSpinBox()
        chunk_spin.setRange(1000, 100000)
        chunk_spin.setValue(10000)
        self.option_widgets['chunk_size'] = chunk_spin
        processing_layout.addWidget(chunk_spin, 1, 1)
        
        layout.addWidget(processing_group)
        layout.addStretch()
        page.setWidget(widget)
        return page
        
    def create_debug_page(self):
        """Create debugging options page"""
        page = QScrollArea()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Logging group
        logging_group = QGroupBox("Logging")
        logging_layout = QGridLayout(logging_group)
        
        # Enable logging
        logging_cb = QCheckBox("Enable debug logging")
        self.option_widgets['debug_logging'] = logging_cb
        logging_layout.addWidget(logging_cb, 0, 0, 1, 2)
        
        # Log level
        logging_layout.addWidget(QLabel("Log level:"), 1, 0)
        log_level_combo = QComboBox()
        log_level_combo.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
        log_level_combo.setCurrentText('INFO')
        self.option_widgets['log_level'] = log_level_combo
        logging_layout.addWidget(log_level_combo, 1, 1)
        
        # Log file
        logging_layout.addWidget(QLabel("Log file:"), 2, 0)
        log_file_edit = QLineEdit()
        log_file_edit.setPlaceholderText("Path to log file")
        self.option_widgets['log_file'] = log_file_edit
        logging_layout.addWidget(log_file_edit, 2, 1)
        
        layout.addWidget(logging_group)
        
        # Development group
        dev_group = QGroupBox("Development")
        dev_layout = QGridLayout(dev_group)
        
        # Show debug info
        debug_info_cb = QCheckBox("Show debug information in status bar")
        self.option_widgets['show_debug_info'] = debug_info_cb
        dev_layout.addWidget(debug_info_cb, 0, 0, 1, 2)
        
        # Enable profiling
        profiling_cb = QCheckBox("Enable performance profiling")
        self.option_widgets['enable_profiling'] = profiling_cb
        dev_layout.addWidget(profiling_cb, 1, 0, 1, 2)
        
        layout.addWidget(dev_group)
        layout.addStretch()
        page.setWidget(widget)
        return page
        
    def create_excel_import_page(self):
        """Create Excel import options page"""
        page = QScrollArea()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Excel Import Settings group
        excel_group = QGroupBox("Excel Import Settings")
        excel_layout = QGridLayout(excel_group)
        
        # Prompt for options
        prompt_cb = QCheckBox("Prompt for options when opening Excel files")
        prompt_cb.setChecked(True)
        self.option_widgets['excel_prompt_for_options'] = prompt_cb
        excel_layout.addWidget(prompt_cb, 0, 0, 1, 2)
        
        # Import with formatting by default
        import_with_formatting_cb = QCheckBox("Import Excel data with formatting by default")
        import_with_formatting_cb.setChecked(False)
        self.option_widgets['excel_import_with_formatting'] = import_with_formatting_cb
        excel_layout.addWidget(import_with_formatting_cb, 1, 0, 1, 2)
        
        layout.addWidget(excel_group)
        
        # Default Excel Import Options group
        defaults_group = QGroupBox("Default Excel Import Options")
        defaults_layout = QGridLayout(defaults_group)
        
        # Cell formatting options
        defaults_layout.addWidget(QLabel("Cell Formatting:"), 0, 0, 1, 2)
        
        apply_bg_colors_cb = QCheckBox("Apply background colors")
        apply_bg_colors_cb.setChecked(True)
        self.option_widgets['excel_default_apply_background_colors'] = apply_bg_colors_cb
        defaults_layout.addWidget(apply_bg_colors_cb, 1, 0)
        
        apply_text_colors_cb = QCheckBox("Apply text colors")
        apply_text_colors_cb.setChecked(True)
        self.option_widgets['excel_default_apply_text_colors'] = apply_text_colors_cb
        defaults_layout.addWidget(apply_text_colors_cb, 1, 1)
        
        apply_borders_cb = QCheckBox("Apply cell borders")
        apply_borders_cb.setChecked(False)
        self.option_widgets['excel_default_apply_borders'] = apply_borders_cb
        defaults_layout.addWidget(apply_borders_cb, 2, 0)
        
        # Font formatting options
        defaults_layout.addWidget(QLabel("Font Formatting:"), 3, 0, 1, 2)
        
        apply_font_family_cb = QCheckBox("Apply font family")
        apply_font_family_cb.setChecked(True)
        self.option_widgets['excel_default_apply_font_family'] = apply_font_family_cb
        defaults_layout.addWidget(apply_font_family_cb, 4, 0)
        
        apply_font_size_cb = QCheckBox("Apply font size")
        apply_font_size_cb.setChecked(True)
        self.option_widgets['excel_default_apply_font_size'] = apply_font_size_cb
        defaults_layout.addWidget(apply_font_size_cb, 4, 1)
        
        apply_font_style_cb = QCheckBox("Apply font style (bold, italic)")
        apply_font_style_cb.setChecked(True)
        self.option_widgets['excel_default_apply_font_style'] = apply_font_style_cb
        defaults_layout.addWidget(apply_font_style_cb, 5, 0)
        
        # Data options
        defaults_layout.addWidget(QLabel("Data Options:"), 6, 0, 1, 2)
        
        preserve_formulas_cb = QCheckBox("Preserve formulas (show as text)")
        preserve_formulas_cb.setChecked(False)
        self.option_widgets['excel_default_preserve_formulas'] = preserve_formulas_cb
        defaults_layout.addWidget(preserve_formulas_cb, 7, 0)
        
        convert_dates_cb = QCheckBox("Convert date formats to text")
        convert_dates_cb.setChecked(True)
        self.option_widgets['excel_default_convert_dates'] = convert_dates_cb
        defaults_layout.addWidget(convert_dates_cb, 7, 1)
        
        layout.addWidget(defaults_group)
        layout.addStretch()
        page.setWidget(widget)
        return page
        
    def on_search_changed(self):
        """Handle search text change with debouncing"""
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms delay
        
    def perform_search(self):
        """Perform search in options tree"""
        search_text = self.search_edit.text().lower()
        
        if not search_text:
            # Show all items
            self.show_all_items()
            return
            
        # Hide all items first
        self.hide_all_items()
        
        # Search and show matching items
        self.search_items(self.options_tree.invisibleRootItem(), search_text)
        
    def show_all_items(self):
        """Show all items in the tree"""
        self.set_items_visibility(self.options_tree.invisibleRootItem(), True)
        
    def hide_all_items(self):
        """Hide all items in the tree"""
        self.set_items_visibility(self.options_tree.invisibleRootItem(), False)
        
    def set_items_visibility(self, parent_item, visible):
        """Recursively set visibility of items"""
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            item.setHidden(not visible)
            self.set_items_visibility(item, visible)
            
    def search_items(self, parent_item, search_text):
        """Recursively search items and show matches"""
        found_match = False
        
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            item_text = item.text(0).lower()
            
            # Check if this item matches
            item_matches = search_text in item_text
            
            # Check children
            child_matches = self.search_items(item, search_text)
            
            # Show item if it or any child matches
            if item_matches or child_matches:
                item.setHidden(False)
                found_match = True
                
                # Expand parent to show matching children
                if child_matches:
                    item.setExpanded(True)
            else:
                item.setHidden(True)
                
        return found_match
        
    def on_tree_selection_changed(self, current, previous):
        """Handle tree selection change"""
        if current:
            page_index = current.data(0, Qt.UserRole)
            if page_index is not None:
                self.content_stack.setCurrentIndex(page_index)
                
    def choose_color(self, option_key):
        """Open color chooser dialog"""
        color = QColorDialog.getColor(Qt.white, self)
        if color.isValid():
            button = self.option_widgets[option_key]
            button.setStyleSheet(f"background-color: {color.name()}")
            button.setText(color.name())
            
    def choose_font(self):
        """Open font chooser dialog"""
        font, ok = QFontDialog.getFont(QFont(), self)
        if ok:
            button = self.option_widgets['font_family']
            button.setText(f"{font.family()} {font.pointSize()}pt")
            button.setFont(font)
            
    def browse_python_interpreter(self):
        """Browse for Python interpreter"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Python Interpreter", "", 
            "Executable files (*.exe);;All files (*.*)"
        )
        if file_path:
            self.option_widgets['python_interpreter'].setText(file_path)
            
    def load_current_settings(self):
        """Load current settings into the dialog"""
        if self.parent_window and hasattr(self.parent_window, 'settings'):
            settings = self.parent_window.settings
            
            # Update last opened file display
            last_file = settings.get('last_selected_file', 'None')
            if last_file and last_file != 'None':
                # Show just the filename for better readability
                filename = os.path.basename(last_file)
                self.last_file_label.setText(filename)
                self.last_file_label.setToolTip(last_file)  # Full path in tooltip
            else:
                self.last_file_label.setText('None')
                self.last_file_label.setToolTip('')
            
            # Define default values for new settings
            defaults = {
                'open_last_file_on_startup': True,
                'excel_prompt_for_options': True,
                'excel_import_with_formatting': False,
                'excel_default_apply_background_colors': True,
                'excel_default_apply_text_colors': True,
                'excel_default_apply_borders': False,
                'excel_default_apply_font_family': True,
                'excel_default_apply_font_size': True,
                'excel_default_apply_font_style': True,
                'excel_default_preserve_formulas': False,
                'excel_default_convert_dates': True
            }
            
            # Load settings into widgets
            for key, widget in self.option_widgets.items():
                # Use setting value if exists, otherwise use default
                value = settings.get(key, defaults.get(key))
                
                if isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, QComboBox):
                    index = widget.findText(str(value))
                    if index >= 0:
                        widget.setCurrentIndex(index)
                elif isinstance(widget, (QSpinBox, QSlider)):
                    if value is not None:
                        widget.setValue(int(value))
                    else:
                        widget.setValue(0)  # Default value
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                        
    def get_options(self):
        """Get all options from the dialog"""
        options = {}
        
        for key, widget in self.option_widgets.items():
            if isinstance(widget, QCheckBox):
                options[key] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                options[key] = widget.currentText()
            elif isinstance(widget, (QSpinBox, QSlider)):
                options[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                options[key] = widget.text()
            elif isinstance(widget, QPushButton):
                # For color/font buttons, get the text
                options[key] = widget.text()
                
        return options
        
    def apply_options(self):
        """Apply options without closing dialog"""
        if self.parent_window:
            self.parent_window.apply_options(self.get_options())