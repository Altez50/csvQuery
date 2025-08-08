from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
                             QListWidgetItem, QPushButton, QTextEdit, QComboBox, 
                             QSplitter, QGroupBox, QCheckBox, QLineEdit, QSpinBox,
                             QDialogButtonBox, QMessageBox, QTabWidget, QWidget,
                             QTreeWidget, QTreeWidgetItem, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import sqlite3

class SQLQueryConstructorDialog(QDialog):
    query_generated = pyqtSignal(str)
    
    def __init__(self, connection, parent=None):
        super().__init__(parent)
        self.conn = connection
        self.parent_widget = parent
        self.current_language = 'en'  # Default to Russian
        self.setWindowTitle('Конструктор SQL запросов')
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Initialize data structures
        self.available_tables = []
        self.available_fields = {}
        self.selected_fields = []
        self.where_conditions = []
        self.join_conditions = []
        self.group_by_fields = []
        self.having_conditions = []
        self.order_by_fields = []
        
        # Language dictionaries
        self.translations = {
            'ru': {
                'title': 'Конструктор SQL запросов',
                'tables': 'Таблицы',
                'fields': 'Поля',
                'search_fields': 'Поиск полей...',
                'add_field_select': 'Добавить поле в SELECT',
                'sql_keywords': 'SQL Ключевые слова',
                'selected_fields': 'Выбранные поля:',
                'remove_field': 'Удалить поле',
                'clear_all': 'Очистить все',
                'main_table': 'Основная таблица:',
                'join_conditions': 'JOIN условия:',
                'add_join': 'Добавить JOIN',
                'where_conditions': 'WHERE условия:',
                'add_condition': 'Добавить условие',
                'remove_condition': 'Удалить условие',
                'group_by_fields': 'GROUP BY поля:',
                'add_field': 'Добавить поле',
                'remove_field_btn': 'Удалить поле',
                'having_conditions': 'HAVING условия:',
                'order_by_fields': 'ORDER BY поля:',
                'generated_query': 'Сгенерированный запрос:',
                'copy_query': 'Копировать запрос',
                'use_query': 'Использовать запрос',
                'language': 'Язык'
            },
            'en': {
                'title': 'SQL Query Constructor',
                'tables': 'Tables',
                'fields': 'Fields',
                'search_fields': 'Search fields...',
                'add_field_select': 'Add field to SELECT',
                'sql_keywords': 'SQL Keywords',
                'selected_fields': 'Selected fields:',
                'remove_field': 'Remove field',
                'clear_all': 'Clear all',
                'main_table': 'Main table:',
                'join_conditions': 'JOIN conditions:',
                'add_join': 'Add JOIN',
                'where_conditions': 'WHERE conditions:',
                'add_condition': 'Add condition',
                'remove_condition': 'Remove condition',
                'group_by_fields': 'GROUP BY fields:',
                'add_field': 'Add field',
                'remove_field_btn': 'Remove field',
                'having_conditions': 'HAVING conditions:',
                'order_by_fields': 'ORDER BY fields:',
                'generated_query': 'Generated query:',
                'copy_query': 'Copy query',
                'use_query': 'Use query',
                'language': 'Language'
            }
        }
        
        self.setup_ui()
        self.load_database_schema()
        self.load_existing_query()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Top panel - Language switcher
        top_panel = self.create_top_panel()
        layout.addWidget(top_panel)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Available fields and keywords
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Query builder
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([300, 700])
        layout.addWidget(main_splitter)
        
        # Bottom panel - Generated query and buttons
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)
        
    def create_top_panel(self):
        """Create top panel with language switcher"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Language switcher
        layout.addWidget(QLabel(self.get_text('language') + ':'))
        
        self.language_combo = QComboBox()
        self.language_combo.addItem('Русский', 'ru')
        self.language_combo.addItem('English', 'en')
        self.language_combo.setCurrentIndex(0 if self.current_language == 'ru' else 1)
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        layout.addWidget(self.language_combo)
        
        layout.addStretch()
        
        return widget
        
    def get_text(self, key):
        """Get translated text for the current language"""
        return self.translations[self.current_language].get(key, key)
        
    def on_language_changed(self):
        """Handle language change"""
        self.current_language = self.language_combo.currentData()
        self.update_ui_language()
        
    def get_keywords_for_language(self, language):
        """Get keywords for the specified language"""
        if language == 'ru':
            return list(self.keyword_mappings['ru'].keys())
        else:  # English
            return list(self.keyword_mappings['en'].keys())
    
    def translate_keyword(self, keyword, from_lang, to_lang):
        """Translate a keyword from one language to another"""
        if from_lang == to_lang:
            return keyword
        
        if from_lang in self.keyword_mappings and keyword in self.keyword_mappings[from_lang]:
            return self.keyword_mappings[from_lang][keyword]
        
        return keyword
    
    def update_ui_language(self):
        """Update UI elements with new language"""
        self.setWindowTitle(self.get_text('title'))
        
        # Update keywords list for the new language
        self.keywords_list.clear()
        keywords = self.get_keywords_for_language(self.current_language)
        for keyword in keywords:
            self.keywords_list.addItem(keyword)
        
        # Translate existing query if it contains keywords
        self.translate_existing_query()
        
    def translate_existing_query(self):
        """Translate keywords in the existing query to the current language"""
        if not hasattr(self, 'query_display') or not self.query_display:
            return
            
        current_query = self.query_display.toPlainText()
        if not current_query.strip():
            return
            
        # Determine the source language by checking which keywords are present
        source_lang = self.detect_query_language(current_query)
        if source_lang == self.current_language:
            return  # No translation needed
            
        # Translate the query
        translated_query = self.translate_query_text(current_query, source_lang, self.current_language)
        self.query_display.setPlainText(translated_query)
        
    def detect_query_language(self, query_text):
        """Detect the language of the query based on keywords present"""
        query_upper = query_text.upper()
        
        ru_keywords_found = 0
        en_keywords_found = 0
        
        # Check for Russian keywords
        for keyword in self.keyword_mappings['ru'].keys():
            if keyword in query_upper:
                ru_keywords_found += 1
                
        # Check for English keywords
        for keyword in self.keyword_mappings['en'].keys():
            if keyword in query_upper:
                en_keywords_found += 1
                
        # Return the language with more keywords found
        return 'ru' if ru_keywords_found > en_keywords_found else 'en'
        
    def translate_query_text(self, query_text, from_lang, to_lang):
        """Translate query text from one language to another"""
        if from_lang == to_lang:
            return query_text
            
        translated_query = query_text
        
        # Get the appropriate mapping
        if from_lang in self.keyword_mappings:
            for source_keyword, target_keyword in self.keyword_mappings[from_lang].items():
                # Use word boundaries to avoid partial matches
                import re
                pattern = r'\b' + re.escape(source_keyword) + r'\b'
                translated_query = re.sub(pattern, target_keyword, translated_query, flags=re.IGNORECASE)
                
        return translated_query
        
    def create_left_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tables section
        tables_group = QGroupBox('Таблицы')
        tables_layout = QVBoxLayout(tables_group)
        
        self.tables_list = QListWidget()
        self.tables_list.itemSelectionChanged.connect(self.on_table_selected)
        tables_layout.addWidget(self.tables_list)
        
        layout.addWidget(tables_group)
        
        # Fields section
        fields_group = QGroupBox('Поля')
        fields_layout = QVBoxLayout(fields_group)
        
        # Search field
        self.field_search = QLineEdit()
        self.field_search.setPlaceholderText('Поиск полей...')
        self.field_search.textChanged.connect(self.filter_fields)
        fields_layout.addWidget(self.field_search)
        
        self.fields_tree = QTreeWidget()
        self.fields_tree.setHeaderLabels(['Поле', 'Тип'])
        self.fields_tree.itemDoubleClicked.connect(self.add_field_to_select)
        fields_layout.addWidget(self.fields_tree)
        
        # Add field button
        add_field_btn = QPushButton('Добавить поле в SELECT')
        add_field_btn.clicked.connect(self.add_field_to_select)
        fields_layout.addWidget(add_field_btn)
        
        layout.addWidget(fields_group)
        
        # SQL Keywords section
        keywords_group = QGroupBox('SQL Ключевые слова')
        keywords_layout = QVBoxLayout(keywords_group)
        
        self.keywords_list = QListWidget()
        # Define keyword mappings for translation
        self.keyword_mappings = {
            'ru': {
                # Basic SQL
                'ВЫБРАТЬ': 'SELECT', 'ИЗ': 'FROM', 'ГДЕ': 'WHERE', 
                'СОЕДИНЕНИЕ': 'JOIN', 'ЛЕВОЕ СОЕДИНЕНИЕ': 'LEFT JOIN', 'ПРАВОЕ СОЕДИНЕНИЕ': 'RIGHT JOIN',
                'ВНУТРЕННЕЕ СОЕДИНЕНИЕ': 'INNER JOIN', 'ПОЛНОЕ СОЕДИНЕНИЕ': 'FULL JOIN',
                'СГРУППИРОВАТЬ ПО': 'GROUP BY', 'ИМЕЮЩИЕ': 'HAVING', 'УПОРЯДОЧИТЬ ПО': 'ORDER BY',
                'ПЕРВЫЕ': 'LIMIT', 'РАЗЛИЧНЫЕ': 'DISTINCT',
                # Aggregate functions
                'КОЛИЧЕСТВО': 'COUNT', 'СУММА': 'SUM', 'СРЕДНЕЕ': 'AVG', 'МАКСИМУМ': 'MAX', 'МИНИМУМ': 'MIN',
                'ПЕРВЫЙ': 'FIRST', 'ПОСЛЕДНИЙ': 'LAST',
                # Logical operators
                'И': 'AND', 'ИЛИ': 'OR', 'НЕ': 'NOT', 'ПОДОБНО': 'LIKE', 'В': 'IN', 'МЕЖДУ': 'BETWEEN',
                'ЕСТЬ NULL': 'IS NULL', 'НЕ ЕСТЬ NULL': 'IS NOT NULL',
                # Set operations
                'ОБЪЕДИНИТЬ': 'UNION', 'ОБЪЕДИНИТЬ ВСЕ': 'UNION ALL', 'ПЕРЕСЕЧЕНИЕ': 'INTERSECT', 'ИСКЛЮЧИТЬ': 'EXCEPT',
                # Subqueries and CTEs
                'С': 'WITH', 'КАК': 'AS', 'СУЩЕСТВУЕТ': 'EXISTS', 'ЛЮБОЙ': 'ANY', 'ВСЕ': 'ALL',
                # Date/Time functions
                'ДАТАВРЕМЯ': 'DATETIME', 'ДАТА': 'DATE', 'ВРЕМЯ': 'TIME', 'ГОД': 'YEAR', 'МЕСЯЦ': 'MONTH', 'ДЕНЬ': 'DAY',
                # String functions
                'ПОДСТРОКА': 'SUBSTRING', 'ДЛИНА': 'LENGTH', 'ВЕРХНИЙ': 'UPPER', 'НИЖНИЙ': 'LOWER',
                # Type conversion
                'ВЫРАЗИТЬ': 'CAST'
            },
            'en': {
                # Basic SQL
                'SELECT': 'ВЫБРАТЬ', 'FROM': 'ИЗ', 'WHERE': 'ГДЕ',
                'JOIN': 'СОЕДИНЕНИЕ', 'LEFT JOIN': 'ЛЕВОЕ СОЕДИНЕНИЕ', 'RIGHT JOIN': 'ПРАВОЕ СОЕДИНЕНИЕ',
                'INNER JOIN': 'ВНУТРЕННЕЕ СОЕДИНЕНИЕ', 'FULL JOIN': 'ПОЛНОЕ СОЕДИНЕНИЕ',
                'GROUP BY': 'СГРУППИРОВАТЬ ПО', 'HAVING': 'ИМЕЮЩИЕ', 'ORDER BY': 'УПОРЯДОЧИТЬ ПО',
                'LIMIT': 'ПЕРВЫЕ', 'DISTINCT': 'РАЗЛИЧНЫЕ',
                # Aggregate functions
                'COUNT': 'КОЛИЧЕСТВО', 'SUM': 'СУММА', 'AVG': 'СРЕДНЕЕ', 'MAX': 'МАКСИМУМ', 'MIN': 'МИНИМУМ',
                'FIRST': 'ПЕРВЫЙ', 'LAST': 'ПОСЛЕДНИЙ',
                # Logical operators
                'AND': 'И', 'OR': 'ИЛИ', 'NOT': 'НЕ', 'LIKE': 'ПОДОБНО', 'IN': 'В', 'BETWEEN': 'МЕЖДУ',
                'IS NULL': 'ЕСТЬ NULL', 'IS NOT NULL': 'НЕ ЕСТЬ NULL',
                # Set operations
                'UNION': 'ОБЪЕДИНИТЬ', 'UNION ALL': 'ОБЪЕДИНИТЬ ВСЕ', 'INTERSECT': 'ПЕРЕСЕЧЕНИЕ', 'EXCEPT': 'ИСКЛЮЧИТЬ',
                # Subqueries and CTEs
                'WITH': 'С', 'AS': 'КАК', 'EXISTS': 'СУЩЕСТВУЕТ', 'ANY': 'ЛЮБОЙ', 'ALL': 'ВСЕ',
                # Date/Time functions
                'DATETIME': 'ДАТАВРЕМЯ', 'DATE': 'ДАТА', 'TIME': 'ВРЕМЯ', 'YEAR': 'ГОД', 'MONTH': 'МЕСЯЦ', 'DAY': 'ДЕНЬ',
                # String functions
                'SUBSTRING': 'ПОДСТРОКА', 'LENGTH': 'ДЛИНА', 'UPPER': 'ВЕРХНИЙ', 'LOWER': 'НИЖНИЙ',
                # Type conversion
                'CAST': 'ВЫРАЗИТЬ', 'CONVERT': 'ПРЕОБРАЗОВАТЬ'
            }
        }
        
        # Get keywords for current language
        keywords = self.get_keywords_for_language(self.current_language)
        
        for keyword in keywords:
            item = QListWidgetItem(keyword)
            self.keywords_list.addItem(item)
            
        self.keywords_list.itemDoubleClicked.connect(self.add_keyword_to_query)
        keywords_layout.addWidget(self.keywords_list)
        
        layout.addWidget(keywords_group)
        
        return widget
        
    def create_right_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Query builder tabs
        self.query_tabs = QTabWidget()
        
        # SELECT tab
        select_tab = self.create_select_tab()
        self.query_tabs.addTab(select_tab, 'SELECT')
        
        # FROM/JOIN tab
        from_tab = self.create_from_tab()
        self.query_tabs.addTab(from_tab, 'FROM/JOIN')
        
        # WHERE tab
        where_tab = self.create_where_tab()
        self.query_tabs.addTab(where_tab, 'WHERE')
        
        # GROUP BY/HAVING tab
        group_tab = self.create_group_tab()
        self.query_tabs.addTab(group_tab, 'GROUP BY')
        
        # ORDER BY tab
        order_tab = self.create_order_tab()
        self.query_tabs.addTab(order_tab, 'ORDER BY')
        
        layout.addWidget(self.query_tabs)
        
        return widget
        
    def create_select_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # DISTINCT option
        self.distinct_checkbox = QCheckBox('DISTINCT')
        self.distinct_checkbox.stateChanged.connect(self.update_query)
        layout.addWidget(self.distinct_checkbox)
        
        # Selected fields
        layout.addWidget(QLabel('Выбранные поля:'))
        
        self.selected_fields_list = QListWidget()
        self.selected_fields_list.setDragDropMode(QListWidget.InternalMove)
        layout.addWidget(self.selected_fields_list)
        
        # Buttons for field management
        buttons_layout = QHBoxLayout()
        
        remove_field_btn = QPushButton('Удалить поле')
        remove_field_btn.clicked.connect(self.remove_selected_field)
        buttons_layout.addWidget(remove_field_btn)
        
        clear_fields_btn = QPushButton('Очистить все')
        clear_fields_btn.clicked.connect(self.clear_selected_fields)
        buttons_layout.addWidget(clear_fields_btn)
        
        layout.addLayout(buttons_layout)
        
        return widget
        
    def create_from_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Main table selection
        layout.addWidget(QLabel('Основная таблица:'))
        self.main_table_combo = QComboBox()
        self.main_table_combo.currentTextChanged.connect(self.update_query)
        layout.addWidget(self.main_table_combo)
        
        # JOIN conditions
        layout.addWidget(QLabel('JOIN условия:'))
        
        self.joins_list = QListWidget()
        layout.addWidget(self.joins_list)
        
        # Add JOIN button
        add_join_btn = QPushButton('Добавить JOIN')
        add_join_btn.clicked.connect(self.add_join_condition)
        layout.addWidget(add_join_btn)
        
        return widget
        
    def create_where_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel('WHERE условия:'))
        
        self.where_list = QListWidget()
        layout.addWidget(self.where_list)
        
        # Buttons for WHERE management
        buttons_layout = QHBoxLayout()
        
        add_where_btn = QPushButton('Добавить условие')
        add_where_btn.clicked.connect(self.add_where_condition)
        buttons_layout.addWidget(add_where_btn)
        
        remove_where_btn = QPushButton('Удалить условие')
        remove_where_btn.clicked.connect(self.remove_where_condition)
        buttons_layout.addWidget(remove_where_btn)
        
        layout.addLayout(buttons_layout)
        
        return widget
        
    def create_group_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # GROUP BY
        layout.addWidget(QLabel('GROUP BY поля:'))
        
        self.group_by_list = QListWidget()
        layout.addWidget(self.group_by_list)
        
        group_buttons_layout = QHBoxLayout()
        add_group_btn = QPushButton('Добавить поле')
        add_group_btn.clicked.connect(self.add_group_by_field)
        group_buttons_layout.addWidget(add_group_btn)
        
        remove_group_btn = QPushButton('Удалить поле')
        remove_group_btn.clicked.connect(self.remove_group_by_field)
        group_buttons_layout.addWidget(remove_group_btn)
        
        layout.addLayout(group_buttons_layout)
        
        # HAVING
        layout.addWidget(QLabel('HAVING условия:'))
        
        self.having_list = QListWidget()
        layout.addWidget(self.having_list)
        
        having_buttons_layout = QHBoxLayout()
        add_having_btn = QPushButton('Добавить условие')
        add_having_btn.clicked.connect(self.add_having_condition)
        having_buttons_layout.addWidget(add_having_btn)
        
        remove_having_btn = QPushButton('Удалить условие')
        remove_having_btn.clicked.connect(self.remove_having_condition)
        having_buttons_layout.addWidget(remove_having_btn)
        
        layout.addLayout(having_buttons_layout)
        
        return widget
        
    def create_order_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel('ORDER BY поля:'))
        
        self.order_by_list = QListWidget()
        self.order_by_list.setDragDropMode(QListWidget.InternalMove)
        layout.addWidget(self.order_by_list)
        
        # Buttons for ORDER BY management
        buttons_layout = QHBoxLayout()
        
        add_order_btn = QPushButton('Добавить поле')
        add_order_btn.clicked.connect(self.add_order_by_field)
        buttons_layout.addWidget(add_order_btn)
        
        remove_order_btn = QPushButton('Удалить поле')
        remove_order_btn.clicked.connect(self.remove_order_by_field)
        buttons_layout.addWidget(remove_order_btn)
        
        layout.addLayout(buttons_layout)
        
        # LIMIT
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel('LIMIT:'))
        
        self.limit_checkbox = QCheckBox('Использовать LIMIT')
        self.limit_checkbox.stateChanged.connect(self.update_query)
        limit_layout.addWidget(self.limit_checkbox)
        
        self.limit_spinbox = QSpinBox()
        self.limit_spinbox.setMinimum(1)
        self.limit_spinbox.setMaximum(999999)
        self.limit_spinbox.setValue(100)
        self.limit_spinbox.valueChanged.connect(self.update_query)
        limit_layout.addWidget(self.limit_spinbox)
        
        layout.addLayout(limit_layout)
        
        return widget
        
    def create_bottom_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Generated query display
        layout.addWidget(QLabel('Сгенерированный запрос:'))
        
        self.query_display = QTextEdit()
        self.query_display.setMaximumHeight(150)
        self.query_display.setFont(QFont('Courier New', 10))
        layout.addWidget(self.query_display)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        update_btn = QPushButton('Обновить запрос')
        update_btn.clicked.connect(self.update_query)
        buttons_layout.addWidget(update_btn)
        
        copy_btn = QPushButton('Копировать запрос')
        copy_btn.clicked.connect(self.copy_query)
        buttons_layout.addWidget(copy_btn)
        
        use_btn = QPushButton('Использовать запрос')
        use_btn.clicked.connect(self.use_query)
        buttons_layout.addWidget(use_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton('Закрыть')
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        return widget
        
    def load_database_schema(self):
        """Load tables and their fields from the database"""
        if not self.conn:
            return
            
        try:
            cursor = self.conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            
            self.available_tables = [table[0] for table in tables]
            
            # Populate tables list
            self.tables_list.clear()
            self.main_table_combo.clear()
            
            for table_name in self.available_tables:
                self.tables_list.addItem(table_name)
                self.main_table_combo.addItem(table_name)
                
            # Get fields for each table
            self.available_fields = {}
            for table_name in self.available_tables:
                cursor.execute(f'PRAGMA table_info("{table_name}")')
                columns = cursor.fetchall()
                self.available_fields[table_name] = [(col[1], col[2]) for col in columns]  # (name, type)
                
        except Exception as e:
            QMessageBox.warning(self, 'Ошибка', f'Не удалось загрузить схему базы данных: {e}')
            
    def on_table_selected(self):
        """Handle table selection to show its fields"""
        current_item = self.tables_list.currentItem()
        if not current_item:
            return
            
        table_name = current_item.text()
        self.populate_fields_tree(table_name)
        
    def populate_fields_tree(self, table_name=None):
        """Populate the fields tree with fields from selected table or all tables"""
        self.fields_tree.clear()
        
        if table_name:
            # Show fields for specific table
            if table_name in self.available_fields:
                table_item = QTreeWidgetItem([table_name, ''])
                self.fields_tree.addTopLevelItem(table_item)
                
                for field_name, field_type in self.available_fields[table_name]:
                    field_item = QTreeWidgetItem([field_name, field_type])
                    field_item.setData(0, Qt.UserRole, table_name)  # Store table name
                    table_item.addChild(field_item)
                    
                table_item.setExpanded(True)
        else:
            # Show all fields from all tables
            for table_name, fields in self.available_fields.items():
                table_item = QTreeWidgetItem([table_name, ''])
                self.fields_tree.addTopLevelItem(table_item)
                
                for field_name, field_type in fields:
                    field_item = QTreeWidgetItem([field_name, field_type])
                    field_item.setData(0, Qt.UserRole, table_name)  # Store table name
                    table_item.addChild(field_item)
                    
    def filter_fields(self):
        """Filter fields based on search text"""
        search_text = self.field_search.text().lower()
        
        for i in range(self.fields_tree.topLevelItemCount()):
            table_item = self.fields_tree.topLevelItem(i)
            table_visible = False
            
            for j in range(table_item.childCount()):
                field_item = table_item.child(j)
                field_name = field_item.text(0).lower()
                field_visible = search_text in field_name
                field_item.setHidden(not field_visible)
                
                if field_visible:
                    table_visible = True
                    
            table_item.setHidden(not table_visible)
            
    def add_field_to_select(self):
        """Add selected field to SELECT clause"""
        current_item = self.fields_tree.currentItem()
        if not current_item or not current_item.parent():
            return
            
        field_name = current_item.text(0)
        table_name = current_item.data(0, Qt.UserRole)
        
        # Create qualified field name
        qualified_name = self.format_qualified_field_name(table_name, field_name)
        
        # Check if already added
        for i in range(self.selected_fields_list.count()):
            if self.selected_fields_list.item(i).text() == qualified_name:
                return
                
        self.selected_fields_list.addItem(qualified_name)
        self.update_query()
        
    def add_keyword_to_query(self):
        """Add selected keyword to current query position"""
        current_item = self.keywords_list.currentItem()
        if not current_item:
            return
            
        keyword = current_item.text()
        current_text = self.query_display.toPlainText()
        
        # Insert keyword at cursor position
        cursor = self.query_display.textCursor()
        cursor.insertText(keyword + ' ')
        
    def remove_selected_field(self):
        """Remove selected field from SELECT clause"""
        current_row = self.selected_fields_list.currentRow()
        if current_row >= 0:
            self.selected_fields_list.takeItem(current_row)
            self.update_query()
            
    def clear_selected_fields(self):
        """Clear all selected fields"""
        self.selected_fields_list.clear()
        self.update_query()
        
    def add_where_condition(self):
        """Add WHERE condition"""
        from sql_condition_dialog import SQLConditionDialog
        
        dialog = SQLConditionDialog(self.available_fields, 'WHERE', self)
        if dialog.exec_() == QDialog.Accepted:
            condition = dialog.get_condition()
            if condition:
                self.where_list.addItem(condition)
                self.update_query()
                
    def remove_where_condition(self):
        """Remove selected WHERE condition"""
        current_row = self.where_list.currentRow()
        if current_row >= 0:
            self.where_list.takeItem(current_row)
            self.update_query()
            
    def add_join_condition(self):
        """Add JOIN condition"""
        from sql_join_dialog import SQLJoinDialog
        
        dialog = SQLJoinDialog(self.available_tables, self.available_fields, self)
        if dialog.exec_() == QDialog.Accepted:
            join_clause = dialog.get_join_clause()
            if join_clause:
                self.joins_list.addItem(join_clause)
                self.update_query()
                
    def add_group_by_field(self):
        """Add field to GROUP BY"""
        current_item = self.fields_tree.currentItem()
        if not current_item or not current_item.parent():
            return
            
        field_name = current_item.text(0)
        table_name = current_item.data(0, Qt.UserRole)
        qualified_name = self.format_qualified_field_name(table_name, field_name)
        
        # Check if already added
        for i in range(self.group_by_list.count()):
            if self.group_by_list.item(i).text() == qualified_name:
                return
                
        self.group_by_list.addItem(qualified_name)
        self.update_query()
        
    def remove_group_by_field(self):
        """Remove selected GROUP BY field"""
        current_row = self.group_by_list.currentRow()
        if current_row >= 0:
            self.group_by_list.takeItem(current_row)
            self.update_query()
            
    def add_having_condition(self):
        """Add HAVING condition"""
        from sql_condition_dialog import SQLConditionDialog
        
        dialog = SQLConditionDialog(self.available_fields, 'HAVING', self)
        if dialog.exec_() == QDialog.Accepted:
            condition = dialog.get_condition()
            if condition:
                self.having_list.addItem(condition)
                self.update_query()
                
    def remove_having_condition(self):
        """Remove selected HAVING condition"""
        current_row = self.having_list.currentRow()
        if current_row >= 0:
            self.having_list.takeItem(current_row)
            self.update_query()
            
    def add_order_by_field(self):
        """Add field to ORDER BY"""
        current_item = self.fields_tree.currentItem()
        if not current_item or not current_item.parent():
            return
            
        field_name = current_item.text(0)
        table_name = current_item.data(0, Qt.UserRole)
        qualified_name = self.format_qualified_field_name(table_name, field_name)
        
        # Ask for sort direction
        from PyQt5.QtWidgets import QInputDialog
        direction, ok = QInputDialog.getItem(self, 'Направление сортировки', 
                                           'Выберите направление:', 
                                           ['ASC', 'DESC'], 0, False)
        if ok:
            order_clause = f'{qualified_name} {direction}'
            
            # Check if already added
            for i in range(self.order_by_list.count()):
                if self.order_by_list.item(i).text().startswith(qualified_name):
                    return
                    
            self.order_by_list.addItem(order_clause)
            self.update_query()
            
    def remove_order_by_field(self):
        """Remove selected ORDER BY field"""
        current_row = self.order_by_list.currentRow()
        if current_row >= 0:
            self.order_by_list.takeItem(current_row)
            self.update_query()
            
    def update_query(self):
        """Generate and update the SQL query based on current selections"""
        query_parts = []
        
        # SELECT clause
        select_fields = []
        for i in range(self.selected_fields_list.count()):
            select_fields.append(self.selected_fields_list.item(i).text())
            
        if not select_fields:
            select_fields = ['*']
            
        distinct = 'DISTINCT ' if self.distinct_checkbox.isChecked() else ''
        query_parts.append(f"SELECT {distinct}{', '.join(select_fields)}")
        
        # FROM clause
        main_table = self.main_table_combo.currentText()
        if main_table:
            formatted_table = self.format_field_name(main_table)
            query_parts.append(f"FROM {formatted_table}")
            
        # JOIN clauses
        for i in range(self.joins_list.count()):
            query_parts.append(self.joins_list.item(i).text())
            
        # WHERE clause
        where_conditions = []
        for i in range(self.where_list.count()):
            where_conditions.append(self.where_list.item(i).text())
            
        if where_conditions:
            query_parts.append(f"WHERE {' AND '.join(where_conditions)}")
            
        # GROUP BY clause
        group_by_fields = []
        for i in range(self.group_by_list.count()):
            group_by_fields.append(self.group_by_list.item(i).text())
            
        if group_by_fields:
            query_parts.append(f"GROUP BY {', '.join(group_by_fields)}")
            
        # HAVING clause
        having_conditions = []
        for i in range(self.having_list.count()):
            having_conditions.append(self.having_list.item(i).text())
            
        if having_conditions:
            query_parts.append(f"HAVING {' AND '.join(having_conditions)}")
            
        # ORDER BY clause
        order_by_fields = []
        for i in range(self.order_by_list.count()):
            order_by_fields.append(self.order_by_list.item(i).text())
            
        if order_by_fields:
            query_parts.append(f"ORDER BY {', '.join(order_by_fields)}")
            
        # LIMIT clause
        if self.limit_checkbox.isChecked():
            query_parts.append(f"LIMIT {self.limit_spinbox.value()}")
            
        # Join all parts
        query = '\n'.join(query_parts) + ';'
        
        self.query_display.setPlainText(query)
        
    def copy_query(self):
        """Copy generated query to clipboard"""
        from PyQt5.QtWidgets import QApplication
        
        query = self.query_display.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(query)
        
        QMessageBox.information(self, 'Успех', 'Запрос скопирован в буфер обмена!')
        
    def use_query(self):
        """Emit signal with generated query and close dialog"""
        query = self.query_display.toPlainText()
        self.query_generated.emit(query)
        self.accept()
        
    def load_existing_query(self):
        """Load existing query text from parent SQL editor and parse it"""
        if hasattr(self.parent_widget, 'sql_edit'):
            existing_query = self.parent_widget.sql_edit.text().strip()
            if existing_query:
                self.query_display.setPlainText(existing_query)
                self.parse_existing_query(existing_query)
                
    def parse_existing_query(self, query):
        """Parse existing SQL query and populate data structures"""
        import re
        
        # Clean up the query - remove extra whitespace and normalize
        query = re.sub(r'\s+', ' ', query.strip())
        query_upper = query.upper()
        
        try:
            # Parse SELECT clause
            self.parse_select_clause(query, query_upper)
            
            # Parse FROM clause
            self.parse_from_clause(query, query_upper)
            
            # Parse WHERE clause
            self.parse_where_clause(query, query_upper)
            
            # Parse JOIN clauses
            self.parse_join_clauses(query, query_upper)
            
            # Parse GROUP BY clause
            self.parse_group_by_clause(query, query_upper)
            
            # Parse HAVING clause
            self.parse_having_clause(query, query_upper)
            
            # Parse ORDER BY clause
            self.parse_order_by_clause(query, query_upper)
            
        except Exception as e:
            print(f"Error parsing query: {e}")
            
    def parse_select_clause(self, query, query_upper):
        """Parse SELECT clause and populate selected fields"""
        import re
        
        # Find SELECT clause
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query_upper)
        if not select_match:
            return
            
        select_part = select_match.group(1)
        
        # Check for DISTINCT
        if 'DISTINCT' in select_part:
            self.distinct_checkbox.setChecked(True)
            select_part = select_part.replace('DISTINCT', '').strip()
            
        # Get the original case version
        original_select = query[select_match.start(1):select_match.end(1)]
        
        # Split fields by comma (but not inside parentheses)
        fields = self.split_sql_list(original_select)
        
        # Clear existing fields and add parsed ones
        self.selected_fields_list.clear()
        for field in fields:
            field = field.strip()
            if field and field != '*':
                self.selected_fields_list.addItem(field)
                
    def parse_from_clause(self, query, query_upper):
        """Parse FROM clause and set main table"""
        import re
        
        # Find FROM clause (before any JOIN)
        from_match = re.search(r'FROM\s+([^\s]+)', query_upper)
        if from_match:
            table_name = from_match.group(1)
            # Remove brackets if present
            table_name = table_name.strip('[]')
            
            # Set main table if it exists in available tables
            index = self.main_table_combo.findText(table_name)
            if index >= 0:
                self.main_table_combo.setCurrentIndex(index)
                
    def parse_where_clause(self, query, query_upper):
        """Parse WHERE clause and populate conditions"""
        import re
        
        # Find WHERE clause (before GROUP BY, HAVING, ORDER BY)
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+(?:GROUP\s+BY|HAVING|ORDER\s+BY|LIMIT)|$)', query_upper)
        if where_match:
            where_part = query[where_match.start(1):where_match.end(1)].strip()
            
            # Split by AND/OR (simple parsing)
            conditions = re.split(r'\s+(?:AND|OR)\s+', where_part, flags=re.IGNORECASE)
            
            self.where_list.clear()
            for condition in conditions:
                condition = condition.strip()
                if condition:
                    self.where_list.addItem(condition)
                    
    def parse_join_clauses(self, query, query_upper):
        """Parse JOIN clauses and populate join conditions"""
        import re
        
        # Find all JOIN clauses
        join_pattern = r'((?:INNER|LEFT|RIGHT|FULL\s+OUTER)?\s*JOIN\s+[^\s]+(?:\s+[^\s]+)?\s+ON\s+[^\s]+(?:\s*[=<>!]+\s*[^\s]+)?(?:\s+AND\s+[^\s]+(?:\s*[=<>!]+\s*[^\s]+)?)*?)'
        joins = re.findall(join_pattern, query, flags=re.IGNORECASE)
        
        self.joins_list.clear()
        for join in joins:
            join = join.strip()
            if join:
                self.joins_list.addItem(join)
                
    def parse_group_by_clause(self, query, query_upper):
        """Parse GROUP BY clause and populate group by fields"""
        import re
        
        # Find GROUP BY clause
        group_match = re.search(r'GROUP\s+BY\s+(.*?)(?:\s+(?:HAVING|ORDER\s+BY|LIMIT)|$)', query_upper)
        if group_match:
            group_part = query[group_match.start(1):group_match.end(1)].strip()
            
            # Split fields by comma
            fields = self.split_sql_list(group_part)
            
            self.group_by_list.clear()
            for field in fields:
                field = field.strip()
                if field:
                    self.group_by_list.addItem(field)
                    
    def parse_having_clause(self, query, query_upper):
        """Parse HAVING clause and populate having conditions"""
        import re
        
        # Find HAVING clause
        having_match = re.search(r'HAVING\s+(.*?)(?:\s+(?:ORDER\s+BY|LIMIT)|$)', query_upper)
        if having_match:
            having_part = query[having_match.start(1):having_match.end(1)].strip()
            
            # Split by AND/OR (simple parsing)
            conditions = re.split(r'\s+(?:AND|OR)\s+', having_part, flags=re.IGNORECASE)
            
            self.having_list.clear()
            for condition in conditions:
                condition = condition.strip()
                if condition:
                    self.having_list.addItem(condition)
                    
    def parse_order_by_clause(self, query, query_upper):
        """Parse ORDER BY clause and populate order by fields"""
        import re
        
        # Find ORDER BY clause
        order_match = re.search(r'ORDER\s+BY\s+(.*?)(?:\s+LIMIT|$)', query_upper)
        if order_match:
            order_part = query[order_match.start(1):order_match.end(1)].strip()
            
            # Split fields by comma
            fields = self.split_sql_list(order_part)
            
            self.order_by_list.clear()
            for field in fields:
                field = field.strip()
                if field:
                    self.order_by_list.addItem(field)
                    
    def split_sql_list(self, text):
        """Split SQL list by comma, respecting parentheses"""
        parts = []
        current_part = ''
        paren_count = 0
        
        for char in text:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                parts.append(current_part.strip())
                current_part = ''
                continue
                
            current_part += char
            
        if current_part.strip():
            parts.append(current_part.strip())
            
        return parts
                
    def format_field_name(self, field_name):
        """Format field name, wrapping multi-word names in square brackets"""
        # Check if field name contains spaces or special characters
        if ' ' in field_name or any(char in field_name for char in ['-', '+', '*', '/', '(', ')', '.']):
            # Only wrap in brackets if not already wrapped
            if not (field_name.startswith('[') and field_name.endswith(']')):
                return f'[{field_name}]'
        return field_name
        
    def format_qualified_field_name(self, table_name, field_name):
        """Format qualified field name with proper bracketing"""
        formatted_table = self.format_field_name(table_name)
        formatted_field = self.format_field_name(field_name)
        return f'{formatted_table}.{formatted_field}'