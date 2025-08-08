from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QLineEdit, QLabel, QHBoxLayout, QCheckBox, QListWidget, QListWidgetItem, QRadioButton, QButtonGroup, QDialog, QDialogButtonBox, QApplication, QInputDialog, QComboBox, QMenu, QAction, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QSplitter, QMenuBar, QCheckBox as QtCheckBox, QToolBar, QToolButton, QMenu, QAction, QSizePolicy, QWidget, QDockWidget, QShortcut
from ui_column_select import ColumnSelectDialog
from sql_query_page import SQLQueryPage
from version_info import get_version_string
from notification_widget import NotificationManager
import sqlite3
import csv
import pandas as pd
import re
from PyQt5.QtCore import Qt, QSize, QSettings, QMimeData, QPoint
from PyQt5.QtGui import QKeySequence, QIcon, QColor, QDrag

import os
import zipfile
import json
import colorsys
from collections import defaultdict
SETTINGS_FILE = 'settings.json'

# Helper to make headers unique and valid for SQLite

def clean_header(header):
    h = header.strip().lower()
    h = re.sub(r'[\s\n\r\t]+', ' ', h) # Replace all whitespace characters with a single space
    h = re.sub(r'[^\w\s\(\)\-\.,:;\[\]]', '', h) # Remove all non-alphanumeric characters except space, parentheses, hyphens, periods, colons, semicolons, and square brackets
    h = ''.join(ch for ch in h if ch.isprintable()) # Remove all non-printable characters
    h = re.sub(r' +', ' ', h) # Replace multiple spaces with a single space
    return h or 'col'   # If the header is empty, return 'col'

def make_unique_headers(headers):
    seen = {}
    result = []
    for idx, h in enumerate(headers):
        h_clean = clean_header(h)
        if h_clean in seen:
            seen[h_clean] += 1
            new_h = f"{h_clean}_{seen[h_clean]}" # If the header is already in the dictionary, add a number to the end of the header
            print(f"[WARNING] Duplicate column name detected: '{h_clean}' at index {idx}. Renamed to '{new_h}'")
        else:
            seen[h_clean] = 0
            new_h = h_clean
        result.append(new_h)
    return result

class RecentFilesWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.recent_files = []
        self.max_recent_files = 10
        self.setup_ui()
        self.load_recent_files()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel('Недавние файлы')
        title_label.setStyleSheet('font-weight: bold; padding: 5px;')
        layout.addWidget(title_label)
        
        # Recent files list
        self.recent_files_list = QListWidget()
        self.recent_files_list.setMaximumHeight(200)
        self.recent_files_list.itemDoubleClicked.connect(self.open_recent_file)
        layout.addWidget(self.recent_files_list)
        
        # Clear button
        clear_btn = QPushButton('Очистить список')
        clear_btn.clicked.connect(self.clear_recent_files)
        layout.addWidget(clear_btn)
        
    def add_recent_file(self, file_path):
        """Add a file to recent files list"""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        
        # Keep only max_recent_files
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
            
        self.save_recent_files()
        self.update_recent_files_display()
        
    def open_recent_file(self, item):
        """Open a recent file when double-clicked"""
        file_path = item.data(Qt.UserRole)
        if file_path:
            if os.path.exists(file_path):
                # Call the main window's open session method
                self.main_window.open_session_file(file_path)
            else:
                # File doesn't exist, show notification and remove from recent files
                self.main_window.notification_manager.show_notification(
                    f'Файл не найден: {file_path}', 
                    'Ошибка', 
                    3000, 
                    'warning', 
                    self.main_window
                )
                if file_path in self.recent_files:
                    self.recent_files.remove(file_path)
                    self.save_recent_files()
                    self.update_recent_files_display()
                
    def clear_recent_files(self):
        """Clear all recent files"""
        self.recent_files.clear()
        self.save_recent_files()
        self.update_recent_files_display()
        
    def update_recent_files_display(self):
        """Update the display of recent files"""
        self.recent_files_list.clear()
        
        for file_path in self.recent_files:
            file_name = os.path.basename(file_path)
            item = QListWidgetItem()
            
            if os.path.exists(file_path):
                item.setText(file_name)
                item.setToolTip(file_path)
            else:
                item.setText(f"{file_name} (недоступен)")
                item.setToolTip(f"{file_path} (файл не найден)")
                item.setForeground(QColor('gray'))
                
            item.setData(Qt.UserRole, file_path)
            self.recent_files_list.addItem(item)
            
    def load_recent_files(self):
        """Load recent files from settings"""
        settings_file = 'recent_files.json'
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    self.recent_files = json.load(f)
                self.update_recent_files_display()
            except Exception:
                self.recent_files = []
                
    def save_recent_files(self):
        """Save recent files to settings"""
        settings_file = 'recent_files.json'
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_files, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

class AdvancedSearchWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        # Buttons for select/invert and apply
        btns_layout = QHBoxLayout()

        # Apply button moved to top
        self.apply_btn = QPushButton('Применить')
        self.apply_btn.clicked.connect(self.apply_search)
        self.apply_btn.setStyleSheet('QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 5px 10px; border-radius: 3px; } QPushButton:hover { background-color: #45a049; }')
        self.select_all_btn = QPushButton('Выделить все')
        self.select_all_btn.clicked.connect(self.select_all)
        self.invert_btn = QPushButton('Инвертировать выделение')
        self.invert_btn.clicked.connect(self.invert_selection)       
        btns_layout.addWidget(self.apply_btn)
        btns_layout.addWidget(self.select_all_btn)
        btns_layout.addWidget(self.invert_btn)
        layout.addLayout(btns_layout)
        # Columns
        layout.addWidget(QLabel('Искать по колонкам:'))
        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.columns_list)
        # Search mode
        layout.addWidget(QLabel('Режим поиска:'))
        self.mode_group = QButtonGroup(self)
        self.mode_any = QRadioButton('Любое слово')
        self.mode_all = QRadioButton('Все слова')
        self.mode_exact = QRadioButton('Точное совпадение')
        self.mode_regex = QRadioButton('Регулярное выражение')
        self.mode_group.addButton(self.mode_any, 0)
        self.mode_group.addButton(self.mode_all, 1)
        self.mode_group.addButton(self.mode_exact, 2)
        self.mode_group.addButton(self.mode_regex, 3)
        layout.addWidget(self.mode_any)
        layout.addWidget(self.mode_all)
        layout.addWidget(self.mode_exact)
        layout.addWidget(self.mode_regex)
        self.mode_any.setChecked(True)
        # Case sensitivity
        self.case_checkbox = QCheckBox('Учитывать регистр')
        layout.addWidget(self.case_checkbox)
        
        # Active filters section
        layout.addWidget(QLabel('Активные фильтры:'))
        self.filters_widget = QWidget()
        self.filters_layout = QVBoxLayout(self.filters_widget)
        self.filters_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.filters_widget)
        
        # Clear all filters button
        self.clear_all_btn = QPushButton('Очистить все фильтры')
        self.clear_all_btn.clicked.connect(self.clear_all_filters)
        self.clear_all_btn.setVisible(False)
        layout.addWidget(self.clear_all_btn)
        
        # Update filters display initially
        self.update_filters_display()
        
    def update_headers(self, headers, settings=None):
        self.columns_list.clear()
        for col in headers:
            item = QListWidgetItem(col)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if (not settings or col in settings.get('columns', headers)) else Qt.Unchecked)
            self.columns_list.addItem(item)
        if settings:
            mode = settings.get('mode', 'any')
            if mode == 'all': self.mode_all.setChecked(True)
            elif mode == 'exact': self.mode_exact.setChecked(True)
            elif mode == 'regex': self.mode_regex.setChecked(True)
            else: self.mode_any.setChecked(True)
            self.case_checkbox.setChecked(settings.get('case', False))
            
    def get_settings(self):
        columns = [self.columns_list.item(i).text() for i in range(self.columns_list.count()) if self.columns_list.item(i).checkState() == Qt.Checked]
        mode = 'any'
        if self.mode_all.isChecked(): mode = 'all'
        elif self.mode_exact.isChecked(): mode = 'exact'
        elif self.mode_regex.isChecked(): mode = 'regex'
        return {
            'columns': columns,
            'mode': mode,
            'case': self.case_checkbox.isChecked()
        }
        
    def set_settings(self, settings):
        """Set search settings"""
        if not settings:
            return
        self.update_headers(self.main_window.csv_headers, settings)
        
    def apply_search(self):
        self.main_window.advanced_search_settings = self.get_settings()
        self.main_window.filter_csv_table()
        
    def select_all(self):
        for i in range(self.columns_list.count()):
            self.columns_list.item(i).setCheckState(Qt.Checked)
            
    def invert_selection(self):
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)
    
    def update_filters_display(self):
        """Update the display of active filters"""
        # Clear existing filter widgets
        for i in reversed(range(self.filters_layout.count())):
            child = self.filters_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Get active filters from main window
        active_filters = getattr(self.main_window, 'active_filters', {})
        
        if not active_filters:
            no_filters_label = QLabel('Нет активных фильтров')
            no_filters_label.setStyleSheet('color: gray; font-style: italic;')
            self.filters_layout.addWidget(no_filters_label)
            self.clear_all_btn.setVisible(False)
        else:
            for col_name, filter_value in active_filters.items():
                filter_widget = QWidget()
                filter_layout = QHBoxLayout(filter_widget)
                filter_layout.setContentsMargins(5, 2, 5, 2)
                
                # Filter description
                filter_label = QLabel(f'{col_name}: "{filter_value}"')
                filter_label.setStyleSheet('background-color: #e6f3ff; padding: 2px 5px; border-radius: 3px;')
                filter_layout.addWidget(filter_label)
                
                # Clear button for this filter
                clear_btn = QPushButton('✕')
                clear_btn.setFixedSize(20, 20)
                clear_btn.setStyleSheet('QPushButton { background-color: #ff6b6b; color: white; border: none; border-radius: 10px; font-weight: bold; } QPushButton:hover { background-color: #ff5252; }')
                clear_btn.clicked.connect(lambda checked, col=col_name: self.clear_single_filter(col))
                filter_layout.addWidget(clear_btn)
                
                self.filters_layout.addWidget(filter_widget)
            
            self.clear_all_btn.setVisible(True)
    
    def clear_single_filter(self, column_name):
        """Clear a single filter"""
        if hasattr(self.main_window, 'active_filters') and column_name in self.main_window.active_filters:
            del self.main_window.active_filters[column_name]
            self.main_window.apply_filters()
            self.update_filters_display()
    
    def clear_all_filters(self):
        """Clear all active filters"""
        if hasattr(self.main_window, 'active_filters'):
            self.main_window.active_filters.clear()
            self.main_window.apply_filters()
            self.update_filters_display()

class AdvancedSearchDialog(QDialog):
    def __init__(self, headers, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Расширенный поиск')
        self.resize(400, 350)
        layout = QVBoxLayout(self)
        # Buttons for select/invert
        btns_layout = QHBoxLayout()
        self.select_all_btn = QPushButton('Выделить все')
        self.select_all_btn.clicked.connect(self.select_all)
        self.invert_btn = QPushButton('Инвертировать выделение')
        self.invert_btn.clicked.connect(self.invert_selection)
        btns_layout.addWidget(self.select_all_btn)
        btns_layout.addWidget(self.invert_btn)
        layout.addLayout(btns_layout)
        # Columns
        layout.addWidget(QLabel('Искать по колонкам:'))
        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(QListWidget.MultiSelection)
        for col in headers:
            item = QListWidgetItem(col)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if (not settings or col in settings.get('columns', headers)) else Qt.Unchecked)
            self.columns_list.addItem(item)
        layout.addWidget(self.columns_list)
        # Search mode
        layout.addWidget(QLabel('Режим поиска:'))
        self.mode_group = QButtonGroup(self)
        self.mode_any = QRadioButton('Любое слово')
        self.mode_all = QRadioButton('Все слова')
        self.mode_exact = QRadioButton('Точное совпадение')
        self.mode_regex = QRadioButton('Регулярное выражение')
        self.mode_group.addButton(self.mode_any, 0)
        self.mode_group.addButton(self.mode_all, 1)
        self.mode_group.addButton(self.mode_exact, 2)
        self.mode_group.addButton(self.mode_regex, 3)
        layout.addWidget(self.mode_any)
        layout.addWidget(self.mode_all)
        layout.addWidget(self.mode_exact)
        layout.addWidget(self.mode_regex)
        mode = (settings or {}).get('mode', 'any')
        if mode == 'all': self.mode_all.setChecked(True)
        elif mode == 'exact': self.mode_exact.setChecked(True)
        elif mode == 'regex': self.mode_regex.setChecked(True)
        else: self.mode_any.setChecked(True)
        # Case sensitivity
        self.case_checkbox = QCheckBox('Учитывать регистр')
        self.case_checkbox.setChecked((settings or {}).get('case', False))
        layout.addWidget(self.case_checkbox)
        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    def get_settings(self):
        columns = [self.columns_list.item(i).text() for i in range(self.columns_list.count()) if self.columns_list.item(i).checkState() == Qt.Checked]
        mode = 'any'
        if self.mode_all.isChecked(): mode = 'all'
        elif self.mode_exact.isChecked(): mode = 'exact'
        elif mode == 'regex': self.mode_regex.setChecked(True)
        return {
            'columns': columns,
            'mode': mode,
            'case': self.case_checkbox.isChecked()
        }
    def select_all(self):
        for i in range(self.columns_list.count()):
            self.columns_list.item(i).setCheckState(Qt.Checked)
    def invert_selection(self):
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)

# --- Add import for TableEditDialog ---
try:
    from table_edit_dialog import TableEditDialog
except ImportError:
    TableEditDialog = None

from group_by_dialog import GroupByDialog
from python_page import PythonPage
from ai_page import AIPage

class TableManagerWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        # --- Toolbar ---
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(20, 20))
        self.add_table_btn = toolbar.addAction(QIcon('icons/add.png'), "Добавить таблицу")
        self.add_table_btn.setToolTip("Добавить таблицу")
        self.add_table_btn.triggered.connect(self.main_window.add_new_table)
        self.rename_table_btn = toolbar.addAction(QIcon('icons/edit.png'), "Переименовать таблицу")
        self.rename_table_btn.setToolTip("Переименовать таблицу")
        self.rename_table_btn.triggered.connect(self.main_window.rename_current_table)
        self.delete_table_btn = toolbar.addAction(QIcon('icons/delete.png'), "Удалить таблицу")
        self.delete_table_btn.setToolTip("Удалить таблицу")
        self.delete_table_btn.triggered.connect(self.main_window.delete_current_table)
        self.edit_table_btn = toolbar.addAction(QIcon('icons/table-card.png'), "Редактировать таблицу")
        self.edit_table_btn.setToolTip("Редактировать таблицу")
        self.edit_table_btn.triggered.connect(self.open_table_edit_dialog)
        layout.addWidget(toolbar)
        self.table_tree = QTreeWidget()
        self.table_tree.setHeaderLabels(["Таблицы"])
        self.table_tree.setMinimumHeight(80)
        self.table_tree.setMaximumHeight(16777215)
        self.table_tree.itemSelectionChanged.connect(self.main_window.on_table_selected)
        self.table_tree.installEventFilter(self.main_window)
        
        # Настройка перетаскивания элементов
        self.table_tree.setDragEnabled(True)
        self.table_tree.setAcceptDrops(True)
        self.table_tree.setDropIndicatorShown(True)
        self.table_tree.setDragDropMode(QTreeWidget.InternalMove)
        
        # Настройка контекстного меню
        self.table_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table_tree, 1)
        
        # Сохранение информации о перетаскиваемом элементе
        self.drag_source_item = None
        
    def open_table_edit_dialog(self):
        table_name = self.main_window.get_selected_table_name()
        if not table_name or TableEditDialog is None:
            return
        dlg = TableEditDialog(self.main_window.sqlite_conn, table_name, self)
        dlg.exec_()

    def update_table_selector(self):
        self.table_tree.blockSignals(True)
        self.table_tree.clear()
        if not self.main_window.sqlite_conn:
            self.table_tree.blockSignals(False)
            return
        cur = self.main_window.sqlite_conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        for t in tables:
            item = QTreeWidgetItem([t])
            item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
            self.table_tree.addTopLevelItem(item)
        self.table_tree.blockSignals(False)
        
    def show_context_menu(self, position):
        items = self.table_tree.selectedItems()
        if not items:
            return
            
        # Создаем контекстное меню
        menu = QMenu()
        
        # Добавляем действия для работы с таблицами
        edit_action = menu.addAction("Редактировать таблицу")
        rename_action = menu.addAction("Переименовать таблицу")
        delete_action = menu.addAction("Удалить таблицу")
        
        # Добавляем разделитель
        menu.addSeparator()
        
        # Добавляем действие для сравнения таблиц
        compare_action = None
        if len(items) == 2:
            compare_action = menu.addAction("Сравнить таблицы")
        elif len(self.table_tree.selectedItems()) == 1:
            # Подменю для выбора второй таблицы для сравнения
            compare_submenu = menu.addMenu("Сравнить с...")
            current_table = items[0].text(0)
            
            # Получаем список всех таблиц
            all_tables = []
            for i in range(self.table_tree.topLevelItemCount()):
                table_name = self.table_tree.topLevelItem(i).text(0)
                if table_name != current_table:
                    all_tables.append(table_name)
            
            # Добавляем действия для каждой таблицы
            compare_actions = {}
            for table in all_tables:
                compare_actions[table] = compare_submenu.addAction(table)
        
        # Показываем меню и получаем выбранное действие
        action = menu.exec_(self.table_tree.mapToGlobal(position))
        
        # Обрабатываем выбранное действие
        if action == edit_action:
            self.open_table_edit_dialog()
        elif action == rename_action:
            self.main_window.rename_current_table()
        elif action == delete_action:
            self.main_window.delete_current_table()
        elif compare_action and action == compare_action:
            # Сравнение двух выбранных таблиц
            table_a = items[0].text(0)
            table_b = items[1].text(0)
            self.main_window.compare_tables(table_a, table_b)
        elif action in compare_actions.values() if 'compare_actions' in locals() else []:
            # Сравнение с выбранной таблицей из подменю
            table_a = items[0].text(0)
            table_b = [t for t, a in compare_actions.items() if a == action][0]
            self.main_window.compare_tables(table_a, table_b)

class TableManagerDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setWindowTitle("Управление таблицами")
        self.setMinimumWidth(300)
        self.main_window = main_window
        layout = QVBoxLayout(self)
        # --- Toolbar ---
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(20, 20))
        self.add_table_btn = toolbar.addAction(QIcon('icons/add.png'), "Добавить таблицу")
        self.add_table_btn.setToolTip("Добавить таблицу")
        self.add_table_btn.triggered.connect(self.main_window.add_new_table)
        self.rename_table_btn = toolbar.addAction(QIcon('icons/edit.png'), "Переименовать таблицу")
        self.rename_table_btn.setToolTip("Переименовать таблицу")
        self.rename_table_btn.triggered.connect(self.main_window.rename_current_table)
        self.delete_table_btn = toolbar.addAction(QIcon('icons/delete.png'), "Удалить таблицу")
        self.delete_table_btn.setToolTip("Удалить таблицу")
        self.delete_table_btn.triggered.connect(self.main_window.delete_current_table)
        self.edit_table_btn = toolbar.addAction(QIcon('icons/table-card.png'), "Редактировать таблицу")
        self.edit_table_btn.setToolTip("Редактировать таблицу")
        self.edit_table_btn.triggered.connect(self.open_table_edit_dialog)
        layout.addWidget(toolbar)
        self.table_tree = QTreeWidget()
        self.table_tree.setHeaderLabels(["Таблицы"])
        self.table_tree.setMinimumHeight(80)
        self.table_tree.setMaximumHeight(16777215)
        self.table_tree.itemSelectionChanged.connect(self.main_window.on_table_selected)
        self.table_tree.installEventFilter(self.main_window)
        
        # Настройка перетаскивания элементов
        self.table_tree.setDragEnabled(True)
        self.table_tree.setAcceptDrops(True)
        self.table_tree.setDropIndicatorShown(True)
        self.table_tree.setDragDropMode(QTreeWidget.InternalMove)
        
        # Настройка контекстного меню
        self.table_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table_tree, 1)
        self.setLayout(layout)
        self.update_table_selector()
        # --- Geometry persistence ---
        self._settings = QSettings('csvQuery', 'TableManagerDialog')
        self.restore_geometry()
        
        # Сохранение информации о перетаскиваемом элементе
        self.drag_source_item = None

    def closeEvent(self, event):
        self.save_geometry()
        super().closeEvent(event)

    def save_geometry(self):
        self._settings.setValue('geometry', self.saveGeometry())

    def restore_geometry(self):
        geom = self._settings.value('geometry')
        if geom:
            self.restoreGeometry(geom)

    def open_table_edit_dialog(self):
        table_name = self.main_window.get_selected_table_name()
        if not table_name or TableEditDialog is None:
            return
        dlg = TableEditDialog(self.main_window.sqlite_conn, table_name, self)
        dlg.exec_()

    def update_table_selector(self):
        self.table_tree.blockSignals(True)
        self.table_tree.clear()
        if not self.main_window.sqlite_conn:
            self.table_tree.blockSignals(False)
            return
        cur = self.main_window.sqlite_conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        for t in tables:
            item = QTreeWidgetItem([t])
            item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
            self.table_tree.addTopLevelItem(item)
        self.table_tree.blockSignals(False)
        
    def show_context_menu(self, position):
        items = self.table_tree.selectedItems()
        if not items:
            return
            
        # Создаем контекстное меню
        menu = QMenu()
        
        # Добавляем действия для работы с таблицами
        edit_action = menu.addAction("Редактировать таблицу")
        rename_action = menu.addAction("Переименовать таблицу")
        delete_action = menu.addAction("Удалить таблицу")
        
        # Добавляем разделитель
        menu.addSeparator()
        
        # Добавляем действие для сравнения таблиц
        compare_action = None
        if len(items) == 2:
            compare_action = menu.addAction("Сравнить таблицы")
        elif len(self.table_tree.selectedItems()) == 1:
            # Подменю для выбора второй таблицы для сравнения
            compare_submenu = menu.addMenu("Сравнить с...")
            current_table = items[0].text(0)
            
            # Получаем список всех таблиц
            all_tables = []
            for i in range(self.table_tree.topLevelItemCount()):
                table_name = self.table_tree.topLevelItem(i).text(0)
                if table_name != current_table:
                    all_tables.append(table_name)
            
            # Добавляем действия для каждой таблицы
            compare_actions = {}
            for table in all_tables:
                compare_actions[table] = compare_submenu.addAction(table)
        
        # Показываем меню и получаем выбранное действие
        action = menu.exec_(self.table_tree.mapToGlobal(position))
        
        # Обрабатываем выбранное действие
        if action == edit_action:
            self.open_table_edit_dialog()
        elif action == rename_action:
            self.main_window.rename_current_table()
        elif action == delete_action:
            self.main_window.delete_current_table()
        elif compare_action and action == compare_action:
            # Сравнение двух выбранных таблиц
            table_a = items[0].text(0)
            table_b = items[1].text(0)
            self.main_window.compare_tables(table_a, table_b)
        elif action in compare_actions.values() if 'compare_actions' in locals() else []:
            # Сравнение с выбранной таблицей из подменю
            table_a = items[0].text(0)
            table_b = [t for t, a in compare_actions.items() if a == action][0]
            self.main_window.compare_tables(table_a, table_b)

class OptionsDialog(QDialog):
    def __init__(self, parent, confirm_on_exit, convert_first_row_to_headers=False, dark_theme=False):
        super().__init__(parent)
        self.setWindowTitle('Опции')
        layout = QVBoxLayout(self)
        self.confirm_exit_checkbox = QtCheckBox('Запрашивать подтверждение при выходе')
        self.confirm_exit_checkbox.setChecked(confirm_on_exit)
        layout.addWidget(self.confirm_exit_checkbox)
        
        self.convert_headers_checkbox = QtCheckBox('Преобразовывать первую строку в имена колонок при вставке')
        self.convert_headers_checkbox.setChecked(convert_first_row_to_headers)
        layout.addWidget(self.convert_headers_checkbox)
        
        self.dark_theme_checkbox = QtCheckBox('Тёмная цветовая схема')
        self.dark_theme_checkbox.setChecked(dark_theme)
        layout.addWidget(self.dark_theme_checkbox)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
    def get_confirm_on_exit(self):
        return self.confirm_exit_checkbox.isChecked()
        
    def get_convert_first_row_to_headers(self):
        return self.convert_headers_checkbox.isChecked()
        
    def get_dark_theme(self):
        return self.dark_theme_checkbox.isChecked()

class DraggableTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.drag_start_position = None
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
            
        if not self.drag_start_position:
            return
            
        if ((event.pos() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
            
        # Get selected ranges
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            return
            
        # Create drag object
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Collect selected data
        drag_data = []
        for range_item in selected_ranges:
            for row in range(range_item.topRow(), range_item.bottomRow() + 1):
                row_data = []
                for col in range(range_item.leftColumn(), range_item.rightColumn() + 1):
                    item = self.item(row, col)
                    row_data.append(item.text() if item else "")
                drag_data.append(row_data)
        
        # Store data as JSON
        import json
        mime_data.setText(json.dumps(drag_data))
        drag.setMimeData(mime_data)
        
        # Determine action based on modifiers
        if event.modifiers() & Qt.ControlModifier:
            # Copy on Ctrl+drag
            drop_action = drag.exec_(Qt.CopyAction)
        else:
            # Move on normal drag
            drop_action = drag.exec_(Qt.MoveAction)
            
        # If move action was successful, clear the original selection
        if drop_action == Qt.MoveAction:
            self.clear_selected_cells()
            
    def clear_selected_cells(self):
        """Clear the content of selected cells after a move operation"""
        selected_ranges = self.selectedRanges()
        for range_item in selected_ranges:
            for row in range(range_item.topRow(), range_item.bottomRow() + 1):
                for col in range(range_item.leftColumn(), range_item.rightColumn() + 1):
                    item = self.item(row, col)
                    if item:
                        item.setText("")
                        
    def dropEvent(self, event):
        if not event.mimeData().hasText():
            return
            
        try:
            import json
            drag_data = json.loads(event.mimeData().text())
        except:
            return
            
        # Get drop position
        drop_item = self.itemAt(event.pos())
        if not drop_item:
            return
            
        drop_row = drop_item.row()
        drop_col = drop_item.column()
        
        # Insert the data at drop position
        for i, row_data in enumerate(drag_data):
            target_row = drop_row + i
            if target_row >= self.rowCount():
                break
                
            for j, cell_data in enumerate(row_data):
                target_col = drop_col + j
                if target_col >= self.columnCount():
                    break
                    
                # Create or update item
                item = self.item(target_row, target_col)
                if not item:
                    item = QTableWidgetItem()
                    self.setItem(target_row, target_col, item)
                item.setText(str(cell_data))
                
        event.accept()
        
        # Emit signal that table was modified
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'mark_table_modified'):
            main_window = main_window.parent()
        if main_window and hasattr(main_window, 'mark_table_modified'):
            main_window.mark_table_modified()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            version_info = get_version_string()
            self.setWindowTitle(f"CSV Query Tool (PyQt5) - {version_info}")
        except Exception:
            self.setWindowTitle("CSV Query Tool (PyQt5)")
        self.resize(900, 600)
        self.tabs = QTabWidget()
        self.tabs.tabBar().hide()
        self.setCentralWidget(self.tabs)
        self.confirm_on_exit = True
        self.dark_theme = False
        self.load_settings()
        self.apply_theme()
        self.init_toolbar()
        self.init_tabs()
        self.init_dock_widgets()
        
        # Initialize notification manager
        self.notification_manager = NotificationManager()
    
    def apply_theme(self):
        """Apply light or dark theme to the application"""
        if self.dark_theme:
            # Dark theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #555555;
                    background-color: #2b2b2b;
                }
                QTabBar::tab {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 4px 8px;
                }
                QTabBar::tab:selected {
                    background-color: #4a4a4a;
                }
                QTableWidget {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    gridline-color: #555555;
                    selection-background-color: #0078d4;
                }
                QHeaderView::section {
                    background-color: #4a4a4a;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QPushButton {
                     background-color: #4a4a4a;
                     color: #000000;
                     border: 1px solid #666666;
                     padding: 4px 8px;
                     border-radius: 3px;
                 }
                 QPushButton:hover {
                     background-color: #5a5a5a;
                 }
                 QPushButton:pressed {
                     background-color: #3a3a3a;
                 }
                QLineEdit, QTextEdit, QPlainTextEdit {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #666666;
                }
                QComboBox {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #666666;
                }
                QMenuBar {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #4a4a4a;
                }
                QMenu {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #666666;
                }
                QMenu::item:selected {
                    background-color: #0078d4;
                }
            """)
        else:
            # Light theme (default)
            self.setStyleSheet("")
        self.sqlite_conn = None
        self.csv_data = []  # All rows (excluding header)
        self.csv_headers = []
        self.filtered_indices = []  # Indices of rows currently shown
        self.visible_columns = []  # Indices of columns currently visible
        self.advanced_search_settings = None
        self.table_manager_dialog = None
        self.compare_dialog = None  # Для хранения ссылки на окно сравнения таблиц

    def init_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QSize(20, 20))
        # Кнопки для вкладок CSV/SQL
        self.csv_tab_btn = QPushButton('CSV')
        self.csv_tab_btn.clicked.connect(lambda: self.switch_to_tab(0))
        toolbar.addWidget(self.csv_tab_btn)
        self.sql_tab_btn = QPushButton('SQL')
        self.sql_tab_btn.clicked.connect(lambda: self.switch_to_tab(1))
        toolbar.addWidget(self.sql_tab_btn)
        self.python_tab_btn = QPushButton('Python')
        self.python_tab_btn.clicked.connect(lambda: self.switch_to_tab(2))
        toolbar.addWidget(self.python_tab_btn)
        self.ai_tab_btn = QPushButton('AI')
        self.ai_tab_btn.clicked.connect(lambda: self.switch_to_tab(3))
        toolbar.addWidget(self.ai_tab_btn)
        
        # Store tab buttons for highlighting
        self.tab_buttons = [self.csv_tab_btn, self.sql_tab_btn, self.python_tab_btn, self.ai_tab_btn]
        # Spacer to push menu to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # Recent files button
        recent_files_btn = QPushButton('📁')
        recent_files_btn.setFixedSize(30, 30)
        recent_files_btn.setToolTip('Недавние файлы')
        recent_files_btn.clicked.connect(self.toggle_recent_files_widget)
        toolbar.addWidget(recent_files_btn)
        
        # Кнопка меню
        menu_btn = QToolButton()
        menu_btn.setText('Меню')
        menu_btn.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(menu_btn)
        
        # Flat menu structure with VSCode icons
        new_action = QAction('Новая сессия', self)
        new_action.triggered.connect(self.new_session)
        menu.addAction(new_action)

        open_action = QAction('Открыть сессию', self)
        open_action.setIcon(QIcon("icons/folder-open.svg"))
        open_action.triggered.connect(self.open_session)
        menu.addAction(open_action)        
        
        save_action = QAction('Сохранить сессию', self)
        save_action.setIcon(QIcon("icons/file-save.svg"))
        save_action.triggered.connect(self.save_session)
        menu.addAction(save_action)
        
        menu.addSeparator()
        
        settings_action = QAction('Настройки', self)
        settings_action.setIcon(QIcon("icons/settings-gear.svg"))
        settings_action.triggered.connect(self.open_options_dialog)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        about_action = QAction('О программе', self)
        about_action.triggered.connect(self.show_about_dialog)
        menu.addAction(about_action)
        
        exit_action = QAction('Выход', self)
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)
        menu_btn.setMenu(menu)
        toolbar.addWidget(menu_btn)
        self.addToolBar(Qt.TopToolBarArea, toolbar)
        
    def init_dock_widgets(self):
        """Initialize dock widgets for table manager, advanced search, and recent files"""
        # Table Manager Dock Widget (left side)
        self.table_manager_widget = TableManagerWidget(self)
        self.table_manager_dock = QDockWidget("Table Manager", self)
        self.table_manager_dock.setWidget(self.table_manager_widget)
        self.table_manager_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.table_manager_dock)
        
        # Recent Files Dock Widget (left side, below table manager)
        self.recent_files_widget = RecentFilesWidget(self)
        self.recent_files_dock = QDockWidget("Недавние файлы", self)
        self.recent_files_dock.setWidget(self.recent_files_widget)
        self.recent_files_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.recent_files_dock)
        
        # Advanced Search Dock Widget (right side)
        self.advanced_search_widget = AdvancedSearchWidget(self)
        self.advanced_search_dock = QDockWidget("Advanced Search", self)
        self.advanced_search_dock.setWidget(self.advanced_search_widget)
        self.advanced_search_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.advanced_search_dock)
        
        # Show table manager by default (open on session load), hide others initially
        self.table_manager_dock.show()
        self.recent_files_dock.hide()
        self.advanced_search_dock.hide()
        
        # Connect to session load events to update table manager
        # This will be called when a session is loaded or database connection is established

    def toggle_recent_files_widget(self):
        """Toggle the visibility of the recent files dock widget"""
        if self.recent_files_dock.isVisible():
            self.recent_files_dock.hide()
        else:
            self.recent_files_dock.show()
            
    def open_session_file(self, file_path):
        """Open a session file from the recent files widget"""
        if os.path.exists(file_path):
            # Determine file type by extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                # Load CSV file directly
                self.load_csv_file_direct(file_path)
            elif file_ext in ['.xlsx', '.xls', '.ods']:
                # Load Excel/ODS file directly
                self.load_excel_file_direct(file_path)
            elif file_ext == '.zip':
                # Load session file
                try:
                    with zipfile.ZipFile(file_path, "r") as zf:
                        zf.extractall()
                    db_path = "session_db.sqlite"
                    history_path = "history.json"
                    if os.path.exists(db_path):
                        if self.sqlite_conn:
                            self.sqlite_conn.close()
                        import sqlite3
                        self.sqlite_conn = sqlite3.connect(db_path)
                        # Set connection for SQL tab
                        if hasattr(self, 'sql_tab') and hasattr(self.sql_tab, 'set_connection'):
                            self.sql_tab.set_connection(self.sqlite_conn)
                        # Update table manager dock widget
                        if hasattr(self, 'table_manager_widget'):
                            self.table_manager_widget.update_table_selector()
                    sql_page = getattr(self, 'sql_tab', None)
                    if sql_page and os.path.exists(history_path):
                        with open(history_path, "r", encoding="utf-8") as f:
                            sql_page.history = json.load(f)
                        if hasattr(sql_page, 'history_dialog') and sql_page.history_dialog:
                            sql_page.history_dialog.update_history_tree()
                        if hasattr(sql_page, 'results_dialog') and sql_page.results_dialog:
                            sql_page.results_dialog.update_results_view()
                    
                    self.notification_manager.show_notification('Сессия успешно загружена!', 'Загрузка', 3000, 'success', self)
                except Exception as e:
                    self.notification_manager.show_notification(f'Ошибка при открытии сессии: {e}', 'Ошибка', 3000, 'error', self)
            else:
                # Try to load as JSON session (legacy format)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    # Load CSV file if specified in session
                    if 'csv_file' in session_data and session_data['csv_file']:
                        csv_file = session_data['csv_file']
                        if os.path.exists(csv_file):
                            self.load_csv_file_direct(csv_file)
                            
                            # Load other session data
                            if 'sql_queries' in session_data:
                                self.sql_query_page.load_queries(session_data['sql_queries'])
                            if 'python_code' in session_data:
                                self.python_page.load_code(session_data['python_code'])
                                
                            self.statusBar().showMessage(f'Сессия загружена: {os.path.basename(file_path)}', 3000)
                        else:
                            self.notification_manager.show_notification(f'CSV файл не найден: {csv_file}', 'Ошибка', 3000, 'warning', self)
                    else:
                        self.notification_manager.show_notification('В сессии не указан CSV файл', 'Ошибка', 3000, 'warning', self)
                        
                except Exception as e:
                    self.notification_manager.show_notification(f'Неподдерживаемый формат файла: {file_ext}', 'Ошибка', 3000, 'error', self)
        else:
            self.notification_manager.show_notification(f'Файл не найден: {file_path}', 'Ошибка', 3000, 'warning', self)

    def load_csv_file_direct(self, file_path):
        """Load CSV file directly"""
        try:
            with open(file_path, newline='', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
        except UnicodeDecodeError:
            try:
                with open(file_path, newline='', encoding='cp1251') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
            except Exception as e:
                self.notification_manager.show_notification(f'Ошибка чтения CSV файла: {e}', 'Ошибка', 3000, 'error', self)
                return
        
        if rows:
            from ui_mainwindow import make_unique_headers
            unique_headers = make_unique_headers(rows[0])
            self.csv_headers = unique_headers
            self.csv_data = rows[1:] if len(rows) > 1 else []
            self.filtered_indices = list(range(len(self.csv_data)))
            self.visible_columns = list(range(len(self.csv_headers)))
            self.update_csv_table()
            self.notification_manager.show_notification(f'CSV файл загружен: {os.path.basename(file_path)}', 'Загрузка', 3000, 'success', self)
        else:
            self.notification_manager.show_notification('CSV файл пуст', 'Ошибка', 3000, 'warning', self)

    def load_excel_file_direct(self, file_path):
        """Load Excel/ODS file directly"""
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            
            # Convert to CSV-like format
            headers = [str(col) for col in df.columns]
            data_rows = df.values.tolist()
            
            # Convert all values to strings
            for i, row in enumerate(data_rows):
                data_rows[i] = [str(val) if pd.notna(val) else '' for val in row]
            
            from ui_mainwindow import make_unique_headers
            unique_headers = make_unique_headers(headers)
            self.csv_headers = unique_headers
            self.csv_data = data_rows
            self.filtered_indices = list(range(len(self.csv_data)))
            self.visible_columns = list(range(len(self.csv_headers)))
            self.update_csv_table()
            self.notification_manager.show_notification(f'Excel файл загружен: {os.path.basename(file_path)}', 'Загрузка', 3000, 'success', self)
            
        except Exception as e:
            self.notification_manager.show_notification(f'Ошибка загрузки Excel файла: {e}', 'Ошибка', 3000, 'error', self)

    def show_about_dialog(self):
        try:
            version_info = get_version_string()
            message = f'CSV Query Tool\n{version_info}'
        except Exception:
            message = 'CSV Query Tool\nВерсия: 1.0'
        self.notification_manager.show_notification(message, 'О программе', 3000, 'info')

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.confirm_on_exit = bool(data.get('confirm_on_exit', True))
                self.convert_first_row_to_headers = bool(data.get('convert_first_row_to_headers', False))
                self.dark_theme = bool(data.get('dark_theme', False))
            except Exception:
                self.confirm_on_exit = True
                self.convert_first_row_to_headers = False
                self.dark_theme = False
        else:
            self.confirm_on_exit = True
            self.convert_first_row_to_headers = False
            self.dark_theme = False
    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'confirm_on_exit': self.confirm_on_exit,
                    'convert_first_row_to_headers': self.convert_first_row_to_headers,
                    'dark_theme': self.dark_theme
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    def init_menu(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        file_menu = menubar.addMenu('Файл')
        new_action = QAction('Новая сессия', self)
        new_action.triggered.connect(self.new_session)
        file_menu.addAction(new_action)
        file_menu.addSeparator()
        save_action = QAction('Сохранить сессию', self)
        save_action.triggered.connect(self.save_session)
        file_menu.addAction(save_action)
        open_action = QAction('Открыть сессию', self)
        open_action.triggered.connect(self.open_session)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        exit_action = QAction('Выход', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        options_menu = menubar.addMenu('Опции')
        options_action = QAction('Настройки...', self)
        options_action.triggered.connect(self.open_options_dialog)
        options_menu.addAction(options_action)
    def new_session(self):
        # Show confirmation notification instead of QMessageBox
        self.notification_manager.show_notification(
            "Вы действительно хотите начать новую сессию? Все несохранённые данные будут потеряны.", 
            "Подтвердите", 
            3000,
            "warning"
        )
        # For now, proceed with new session (in a real implementation, you'd want a callback)
        if True:  # Replace with proper confirmation logic
            if self.sqlite_conn:
                self.sqlite_conn.close()
            self.sqlite_conn = None
            self.csv_data = []
            self.csv_headers = []
            self.filtered_indices = []
            self.visible_columns = []
            sql_page = getattr(self, 'sql_tab', None)
            if sql_page:
                sql_page.history = []
                if hasattr(sql_page, 'history_dialog') and sql_page.history_dialog:
                    sql_page.history_dialog.update_history_tree()
                if hasattr(sql_page, 'results_dialog') and sql_page.results_dialog:
                    sql_page.results_dialog.update_results_view()
            self.notification_manager.show_notification('Сессия сброшена. Можно начинать работу с чистого листа.', 'Новая сессия', 3000, 'success')
    def save_session(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить сессию", "", "Session Files (*.zip)")
        if file_path:
            try:
                db_path = "temp_session_db.sqlite"
                if self.sqlite_conn:
                    import sqlite3
                    backup_conn = sqlite3.connect(db_path)
                    self.sqlite_conn.backup(backup_conn)
                    backup_conn.close()
                history = []
                sql_page = getattr(self, 'sql_tab', None)
                if sql_page and hasattr(sql_page, 'history'):
                    history = sql_page.history
                with open("temp_history.json", "w", encoding="utf-8") as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
                with zipfile.ZipFile(file_path, "w") as zf:
                    if os.path.exists(db_path):
                        zf.write(db_path, "session_db.sqlite")
                    zf.write("temp_history.json", "history.json")
                if os.path.exists(db_path):
                    os.remove(db_path)
                os.remove("temp_history.json")
                
                # Add to recent files
                if hasattr(self, 'recent_files_widget'):
                    self.recent_files_widget.add_recent_file(file_path)
                    
                self.notification_manager.show_notification('Сессия успешно сохранена!', 'Сохранение', 3000, 'success')
            except Exception as e:
                self.notification_manager.show_notification(f'Ошибка при сохранении сессии: {e}', 'Ошибка', 3000, 'error')
    def open_session(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть сессию", "", "Session Files (*.zip)")
        if file_path:
            try:
                with zipfile.ZipFile(file_path, "r") as zf:
                    zf.extractall()
                db_path = "session_db.sqlite"
                history_path = "history.json"
                if os.path.exists(db_path):
                    if self.sqlite_conn:
                        self.sqlite_conn.close()
                    import sqlite3
                    self.sqlite_conn = sqlite3.connect(db_path)
                    # Set connection for SQL tab
                    if hasattr(self, 'sql_tab') and hasattr(self.sql_tab, 'set_connection'):
                        self.sql_tab.set_connection(self.sqlite_conn)
                    # Update table manager dock widget
                    if hasattr(self, 'table_manager_widget'):
                        self.table_manager_widget.update_table_selector()
                    # Не удаляем файл базы данных, так как он нужен для работы приложения
                sql_page = getattr(self, 'sql_tab', None)
                if sql_page and os.path.exists(history_path):
                    with open(history_path, "r", encoding="utf-8") as f:
                        sql_page.history = json.load(f)
                    if hasattr(sql_page, 'history_dialog') and sql_page.history_dialog:
                        sql_page.history_dialog.update_history_tree()
                    if hasattr(sql_page, 'results_dialog') and sql_page.results_dialog:
                        sql_page.results_dialog.update_results_view()
                    # Не удаляем файл истории, так как он может понадобиться позже
                # Переключить на вкладку SQL, если есть
                # if hasattr(self, 'tabs') and hasattr(self, 'sql_tab'):
                #    idx = self.tabs.indexOf(self.sql_tab)
                #    if idx != -1:
                #        self.tabs.setCurrentIndex(idx)
                
                # Add to recent files
                if hasattr(self, 'recent_files_widget'):
                    self.recent_files_widget.add_recent_file(file_path)
                    
                self.notification_manager.show_notification('Сессия успешно загружена!', 'Загрузка', 3000, 'success', self)
            except Exception as e:
                self.notification_manager.show_notification(f'Ошибка при открытии сессии: {e}', 'Ошибка', 3000, 'error')
    def closeEvent(self, event):
        self.save_settings()
        if self.confirm_on_exit:
            # Show notification instead of QMessageBox
            self.notification_manager.show_notification(
                "Выйти из программы?", 
                "Выход", 
                3000,
                "warning"
            )
            # For now, accept the close event (in a real implementation, you'd want a callback)
            event.accept()
        else:
            event.accept()

    def init_tabs(self):
        self.csv_tab = QWidget()
        self.sql_tab = SQLQueryPage()
        self.python_tab = PythonPage(self)
        self.ai_tab = AIPage(self)
        self.tabs.addTab(self.csv_tab, "CSV")
        self.tabs.addTab(self.sql_tab, "SQL")
        self.tabs.addTab(self.python_tab, "Python")
        self.tabs.addTab(self.ai_tab, "AI")
        self.init_csv_tab()
        # Set initial highlighting
        self.update_tab_highlighting(0)
    
    def switch_to_tab(self, index):
        """Switch to tab and update highlighting"""
        self.tabs.setCurrentIndex(index)
        self.update_tab_highlighting(index)
    
    def update_tab_highlighting(self, current_index):
        """Update tab button highlighting with orange frame"""
        for i, button in enumerate(self.tab_buttons):
            if i == current_index:
                # Orange frame for current tab
                button.setStyleSheet("""
                    QPushButton {
                        border: 2px solid #FF8C00;
                        border-radius: 4px;
                        padding: 4px 8px;
                        background-color: #FFF8DC;
                    }
                    QPushButton:hover {
                        background-color: #FFE4B5;
                    }
                """)
            else:
                # Normal style for other tabs
                button.setStyleSheet("""
                    QPushButton {
                        border: 1px solid #CCCCCC;
                        border-radius: 4px;
                        padding: 4px 8px;
                        background-color: #F0F0F0;
                    }
                    QPushButton:hover {
                        background-color: #E0E0E0;
                    }
                """)

    def init_csv_tab(self):
        # --- Основной layout ---
        main_layout = QVBoxLayout(self.csv_tab)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        
        # --- Верхняя панель инструментов ---
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(1, 1, 1, 1)
        toolbar_layout.setSpacing(2)
        
        # Группа: Управление таблицами
        self.open_table_manager_btn = QPushButton()
        self.open_table_manager_btn.setIcon(QIcon("icons/database.svg"))
        self.open_table_manager_btn.setText("Таблицы")
        self.open_table_manager_btn.setToolTip("Управление таблицами")
        self.open_table_manager_btn.clicked.connect(self.open_table_manager_dialog)
        toolbar_layout.addWidget(self.open_table_manager_btn)
        
        # Группа: Сохранение
        self.place_to_table_btn = QPushButton()
        self.place_to_table_btn.setIcon(QIcon("icons/file-save.svg"))
        self.place_to_table_btn.setText("Сохранить")
        self.place_to_table_btn.setToolTip("Поместить данные в таблицу базы данных")
        self.place_to_table_btn.clicked.connect(self.place_to_sqlite_table)
        toolbar_layout.addWidget(self.place_to_table_btn)
        
        toolbar_layout.addWidget(self.create_separator())   

        # Группа: Импорт данных
        self.excel_import_btn = QPushButton()
        self.excel_import_btn.setIcon(QIcon("icons/file-excel.svg"))
        self.excel_import_btn.setText("Excel/ODS")
        self.excel_import_btn.setToolTip("Импорт данных из файлов Excel или OpenDocument Spreadsheet")
        self.excel_import_btn.clicked.connect(self.import_excel)
        toolbar_layout.addWidget(self.excel_import_btn)
        
        self.csv_import_btn = QPushButton()
        self.csv_import_btn.setIcon(QIcon("icons/file-csv.svg"))
        self.csv_import_btn.setText("CSV")
        self.csv_import_btn.setToolTip("Импорт данных из CSV файла")
        self.csv_import_btn.clicked.connect(self.import_csv)
        toolbar_layout.addWidget(self.csv_import_btn)
        
        toolbar_layout.addWidget(self.create_separator())
        
        # Группа: Экспорт
        self.csv_export_excel_btn = QPushButton()
        self.csv_export_excel_btn.setIcon(QIcon("icons/export.svg"))
        self.csv_export_excel_btn.setText("Excel")
        self.csv_export_excel_btn.setToolTip("Экспорт данных в файл Excel")
        self.csv_export_excel_btn.clicked.connect(self.export_csv_to_excel)
        toolbar_layout.addWidget(self.csv_export_excel_btn)
        
        self.csv_export_csv_btn = QPushButton()
        self.csv_export_csv_btn.setIcon(QIcon("icons/export.svg"))
        self.csv_export_csv_btn.setText("CSV")
        self.csv_export_csv_btn.setToolTip("Экспорт данных в CSV файл")
        self.csv_export_csv_btn.clicked.connect(self.export_csv_to_csv)
        toolbar_layout.addWidget(self.csv_export_csv_btn)
        
        toolbar_layout.addStretch()
        
        # Группа: Настройки отображения
        # Advanced search button (moved to left of Columns button)
        self.adv_search_btn_toolbar = QPushButton()
        self.adv_search_btn_toolbar.setIcon(QIcon("icons/search.svg"))
        self.adv_search_btn_toolbar.setToolTip("Расширенный поиск")
        self.adv_search_btn_toolbar.clicked.connect(self.open_advanced_search)
        # Add hover events for search widget
        self.adv_search_btn_toolbar.enterEvent = self.on_search_btn_enter
        self.adv_search_btn_toolbar.leaveEvent = self.on_search_btn_leave
        toolbar_layout.addWidget(self.adv_search_btn_toolbar)
        
        self.column_visibility_btn = QPushButton()
        self.column_visibility_btn.setIcon(QIcon("icons/settings.png"))
        self.column_visibility_btn.setText("Столбцы")
        self.column_visibility_btn.setToolTip("Настройка видимости столбцов таблицы")
        self.column_visibility_btn.clicked.connect(self.open_column_visibility_dialog)
        toolbar_layout.addWidget(self.column_visibility_btn)
        
        main_layout.addWidget(toolbar_widget)
        
        # --- Панель поиска (collapsible) ---
        self.search_widget = QWidget()
        search_layout = QHBoxLayout(self.search_widget)
        search_layout.setContentsMargins(2, 1, 2, 1)
        
        search_layout.addWidget(QLabel("🔍 Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Введите текст для поиска...")
        self.search_edit.textChanged.connect(self.filter_csv_table)
        search_layout.addWidget(self.search_edit)
        
        # Initially hide search widget
        self.search_widget.setVisible(False)
        main_layout.addWidget(self.search_widget)
        
        # Add Ctrl+F shortcut
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.toggle_search_widget)
        
        # --- Панель фильтров ---
        self.filter_bar = QHBoxLayout()
        self.filter_labels = []
        filter_widget = QWidget()
        filter_widget.setLayout(self.filter_bar)
        main_layout.addWidget(filter_widget)
        
        # --- Создаём таблицу ---
        self.csv_table = DraggableTableWidget()
        self.csv_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.csv_table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.csv_table.installEventFilter(self)
        # Отслеживание изменений в таблице
        self.csv_table.itemChanged.connect(self.on_table_item_changed)
        self.table_modified = False
        self.original_place_btn_text = "Поместить в таблицу"
        
        main_layout.addWidget(self.csv_table)
        
        self.csv_tab.setLayout(main_layout)
        self.active_filters = {}  # {column_name: value}
        if not hasattr(self, 'sqlite_conn'):
            self.sqlite_conn = None
        self.update_table_selector()
    
    def create_separator(self):
        """Создает визуальный разделитель для панели инструментов"""
        separator = QLabel("│")
        separator.setStyleSheet("color: #cccccc; margin: 0 5px;")
        return separator
    
    def toggle_search_widget(self):
        """Toggle search widget visibility and focus"""
        if self.search_widget.isVisible():
            self.search_widget.setVisible(False)
        else:
            self.search_widget.setVisible(True)
            self.search_edit.setFocus()
            self.search_edit.selectAll()
    
    def on_search_btn_enter(self, event):
        """Show search widget when hovering over search button"""
        self.search_widget.setVisible(True)
    
    def on_search_btn_leave(self, event):
        """Hide search widget when leaving search button"""
        self.search_widget.setVisible(False)

    def update_table_selector(self):
        if hasattr(self, 'table_manager_dialog') and self.table_manager_dialog is not None:
            self.table_manager_dialog.update_table_selector()

    def on_table_selected(self):
        # Try dock widget first, then fallback to dialog
        if hasattr(self, 'table_manager_widget'):
            items = self.table_manager_widget.table_tree.selectedItems()
        elif hasattr(self, 'table_manager_dialog') and self.table_manager_dialog is not None:
            items = self.table_manager_dialog.table_tree.selectedItems()
        else:
            items = []
            
        if items:
            table = items[0].text(0)
            self.load_sqlite_table_to_widget(table)

    def get_selected_table_name(self):
        # Try dock widget first, then fallback to dialog
        if hasattr(self, 'table_manager_widget'):
            items = self.table_manager_widget.table_tree.selectedItems()
            if items:
                return items[0].text(0)
        elif hasattr(self, 'table_manager_dialog') and self.table_manager_dialog is not None:
            items = self.table_manager_dialog.table_tree.selectedItems()
            if items:
                return items[0].text(0)
        return None

    def load_sqlite_table_to_widget(self, table_name):
        if not self.sqlite_conn:
            return
        cur = self.sqlite_conn.cursor()
        try:
            cur.execute(f'SELECT * FROM "{table_name}"')
            rows = cur.fetchall()
            headers = [desc[0] for desc in cur.description]
        except Exception as e:
            print(f"Ошибка загрузки таблицы: {e}")
            return
        self.csv_headers = headers
        self.csv_data = [list(map(str, row)) for row in rows]
        self.filtered_indices = list(range(len(self.csv_data)))
        self.visible_columns = list(range(len(self.csv_headers)))
        self.update_csv_table()
        # Update SQL tab connection when loading table data
        if hasattr(self, 'sql_tab') and hasattr(self.sql_tab, 'set_connection'):
            self.sql_tab.set_connection(self.sqlite_conn)
        # Сбросить флаг изменения при загрузке новой таблицы
        self.reset_table_modified()

    def eventFilter(self, source, event):
        if not hasattr(self, 'csv_table'):
            return super().eventFilter(source, event)
        table_tree = getattr(self.table_manager_dialog, 'table_tree', None) if hasattr(self, 'table_manager_dialog') else None
        
        # Обработка событий для дерева таблиц
        if table_tree is not None and source == table_tree:
            # Обработка нажатия клавиш
            if event.type() == event.KeyPress:
                if event.key() == Qt.Key_F2:
                    self.rename_current_table()
                    return True
            
            # Обработка событий мыши для перетаскивания
            elif event.type() == event.MouseButtonPress and event.button() == Qt.RightButton:
                # Запоминаем элемент, на котором была нажата правая кнопка мыши
                item = table_tree.itemAt(event.pos())
                if item:
                    self.table_manager_dialog.drag_source_item = item
                    return False  # Продолжаем обработку события для показа контекстного меню
            
            elif event.type() == event.MouseMove and event.buttons() & Qt.RightButton:
                # Если перетаскивание правой кнопкой мыши и есть исходный элемент
                if hasattr(self.table_manager_dialog, 'drag_source_item') and self.table_manager_dialog.drag_source_item:
                    # Можно добавить визуальные эффекты перетаскивания, если нужно
                    return False
            
            elif event.type() == event.MouseButtonRelease and event.button() == Qt.RightButton:
                # Если отпущена правая кнопка мыши и был исходный элемент
                if hasattr(self.table_manager_dialog, 'drag_source_item') and self.table_manager_dialog.drag_source_item:
                    # Получаем элемент, над которым отпущена кнопка
                    target_item = table_tree.itemAt(event.pos())
                    
                    # Если есть целевой элемент и он отличается от исходного
                    if target_item and target_item != self.table_manager_dialog.drag_source_item:
                        # Получаем имена таблиц
                        source_table = self.table_manager_dialog.drag_source_item.text(0)
                        target_table = target_item.text(0)
                        
                        # Сравниваем таблицы
                        self.compare_tables(source_table, target_table)
                    
                    # Сбрасываем исходный элемент
                    self.table_manager_dialog.drag_source_item = None
                    return True
        if source == self.csv_table:
            if event.type() == event.KeyPress:
                if event.matches(QKeySequence.Copy):
                    self.copy_table_selection()
                    return True
                elif event.matches(QKeySequence.Paste):
                    self.paste_table_selection()
                    return True
                elif event.key() == Qt.Key_Delete:
                    self.delete_selected_rows()
                    return True
                elif event.key() == Qt.Key_Insert:
                    self.insert_selected_rows()
                    return True
                elif event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_Minus or event.key() == 0x1000004d): #KeypadSubstract
                    self.delete_selected_rows()
                    return True
                elif event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_Plus or event.key() == 0x1000004b): #KeypadAdd
                    self.insert_selected_rows()
                    return True
        return super().eventFilter(source, event)

    def delete_selected_rows(self):
        sel = self.csv_table.selectedRanges()
        if not sel:
            return
        
        rng = sel[0]
        rows_to_delete = rng.bottomRow() - rng.topRow() + 1
        
        # Подтверждение удаления
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Удаление строк", 
                                   f"Удалить {rows_to_delete} строк(и)?", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        
        # Удаляем строки в обратном порядке
        for row in reversed(range(rng.topRow(), rng.bottomRow() + 1)):
            self.csv_table.removeRow(row)
        
        self.mark_table_modified()

    def insert_selected_rows(self):
        sel = self.csv_table.selectedRanges()
        if not sel:
            # Если ничего не выделено, добавить строку в конец
            if self.csv_table.columnCount() > 0:
                self.csv_table.insertRow(self.csv_table.rowCount())
                self.mark_table_modified()
            return
        
        rng = sel[0]
        rows_to_insert = rng.bottomRow() - rng.topRow() + 1
        
        # Вставляем строки после выделенной области
        insert_position = rng.bottomRow() + 1
        for i in range(rows_to_insert):
            self.csv_table.insertRow(insert_position + i)
        
        self.mark_table_modified()

    def on_table_item_changed(self, item):
        """Обработчик изменения элемента таблицы"""
        self.mark_table_modified()
    
    def mark_table_modified(self):
        """Отметить таблицу как измененную"""
        if not self.table_modified:
            self.table_modified = True
            self.place_to_table_btn.setText('Save *')
    
    def reset_table_modified(self):
        """Сбросить флаг изменения таблицы"""
        self.table_modified = False
        self.place_to_table_btn.setText(self.original_place_btn_text)

    #//М-Тех Глазунов В.А. 07.2025  VSMRTRTL-6  ((( 
    def delete_selected_area(self):
        sel = self.csv_table.selectedRanges()
        if not sel:
            return
        rng = sel[0]

        # 1st condition: if selected area height is entire column height, delete columns and return
        if rng.bottomRow() - rng.topRow() + 1 == self.csv_table.rowCount():
            for col in reversed(range(rng.leftColumn(), rng.rightColumn() + 1)):
                self.csv_table.removeColumn(col)
            return

        # Original condition: if width >= height, delete rows, else delete columns
        if rng.columnCount() >= rng.rowCount():
            for row in reversed(range(rng.topRow(), rng.bottomRow() + 1)):
                self.csv_table.removeRow(row)
        else:
            for col in reversed(range(rng.leftColumn(), rng.rightColumn() + 1)):
                self.csv_table.removeColumn(col)

    def add_selected_area(self):
        sel = self.csv_table.selectedRanges()
        if not sel:
            # Если ничего не выделено, но есть колонки — добавить строку
            if self.csv_table.columnCount() > 0:
                self.csv_table.insertRow(self.csv_table.rowCount())
            return
        rng = sel[0]
        # Если ширина >= высоты — добавлять строку, иначе столбец
        if rng.columnCount() >= rng.rowCount():
            insert_row = rng.bottomRow() + 1
            self.csv_table.insertRow(insert_row)
        else:
            insert_col = rng.rightColumn() + 1
            self.csv_table.insertColumn(insert_col)
            self.csv_table.setHorizontalHeaderItem(insert_col, QTableWidgetItem(f"col{insert_col+1}"))
            # Обновить visible_columns после добавления столбца
            self.visible_columns = list(range(self.csv_table.columnCount()))
    #//М-Тех Глазунов В.А. 07.2025  VSMRTRTL-6  )))

    def copy_table_selection(self):
        selection = self.csv_table.selectedRanges()
        if not selection:
            return
        s = ''
        for r in selection:
            for row in range(r.topRow(), r.bottomRow() + 1):
                row_data = []
                for col in range(r.leftColumn(), r.rightColumn() + 1):
                    item = self.csv_table.item(row, col)
                    row_data.append(item.text() if item else '')
                s += '\t'.join(row_data) + '\n'
        QApplication.clipboard().setText(s.strip())

    def paste_table_selection(self):
        clipboard = QApplication.clipboard().text()
        if not clipboard:
            return
        rows = clipboard.split('\n')
        data = [row.split('\t') for row in rows]
        # --- Используем выбранную таблицу ---
        table_name = self.get_selected_table_name() or "pasted_data"
        # Добавить строки/столбцы при необходимости
        start_row = self.csv_table.currentRow() if self.csv_table.currentRow() != -1 else 0
        start_col = self.csv_table.currentColumn() if self.csv_table.currentColumn() != -1 else 0
        
        # Проверяем, нужно ли преобразовать первую строку в заголовки
        if self.convert_first_row_to_headers and data and start_row == 0 and start_col == 0:
            # Получаем первую строку для использования в качестве заголовков
            headers_row = data[0]
            # Преобразуем заголовки в допустимые имена колонок SQLite
            valid_headers = make_unique_headers(headers_row)
            # Устанавливаем заголовки в таблицу
            max_col = start_col + len(valid_headers)
            if self.csv_table.columnCount() < max_col:
                self.csv_table.setColumnCount(max_col)
            for j, header in enumerate(valid_headers):
                self.csv_table.setHorizontalHeaderItem(start_col + j, QTableWidgetItem(header))
            # Используем оставшиеся строки как данные
            data = data[1:]
        
        max_row = start_row + len(data)
        max_col = start_col + max(len(r) for r in data) if data else 0
        if self.csv_table.rowCount() < max_row:
            self.csv_table.setRowCount(max_row)
        if self.csv_table.columnCount() < max_col:
            self.csv_table.setColumnCount(max_col)
        # Вставить данные в таблицу
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                self.csv_table.setItem(start_row + i, start_col + j, QTableWidgetItem(val))
        # Обновить внутренние данные и SQLite
        self.update_internal_data_from_table()
        self.load_table_to_sqlite(table_name)
        self.update_table_selector()
        # Проверяем, инициализирован ли table_manager_dialog перед использованием
        if hasattr(self, 'table_manager_dialog') and self.table_manager_dialog is not None and hasattr(self.table_manager_dialog, 'table_tree'):
            for i in range(self.table_manager_dialog.table_tree.topLevelItemCount()):
                item = self.table_manager_dialog.table_tree.topLevelItem(i)
                if item.text(0) == table_name:
                    self.table_manager_dialog.table_tree.setCurrentItem(item)
                    break
        self.load_sqlite_table_to_widget(table_name)

    def update_internal_data_from_table(self):
        # Обновить self.csv_data и self.csv_headers из QTableWidget
        row_count = self.csv_table.rowCount()
        col_count = self.csv_table.columnCount()
        self.csv_headers = [self.csv_table.horizontalHeaderItem(i).text() if self.csv_table.horizontalHeaderItem(i) else f"col{i+1}" for i in range(col_count)]
        self.csv_data = []
        for row in range(row_count):
            row_data = []
            for col in range(col_count):
                item = self.csv_table.item(row, col)
                row_data.append(item.text() if item else '')
            self.csv_data.append(row_data)
        self.filtered_indices = list(range(len(self.csv_data)))
        self.visible_columns = list(range(len(self.csv_headers)))

    def load_table_to_sqlite(self, table_name):
        if not self.csv_headers:
            return
        if not self.sqlite_conn:
            self.sqlite_conn = sqlite3.connect(":memory:")
        cur = self.sqlite_conn.cursor()
        # Drop table if exists
        cur.execute(f"DROP TABLE IF EXISTS '{table_name}'")
        # Create table
        col_defs = ', '.join([f'"{h}" TEXT' for h in self.csv_headers])
        cur.execute(f'CREATE TABLE "{table_name}" ({col_defs})')
        # Insert data
        if self.csv_data:
            placeholders = ','.join(['?'] * len(self.csv_headers))
            safe_rows = [row[:len(self.csv_headers)] + ['']*(len(self.csv_headers)-len(row)) for row in self.csv_data]
            cur.executemany(f'INSERT INTO "{table_name}" VALUES ({placeholders})', safe_rows)
        self.sqlite_conn.commit()
        # Pass connection to SQL tab (if needed)
        if hasattr(self.sql_tab, 'set_connection'):
            self.sql_tab.set_connection(self.sqlite_conn)

    def clean_cell_coloring(self):
        """Очистить раскраску ячеек таблицы"""
        for row in range(self.csv_table.rowCount()):
            for col in range(self.csv_table.columnCount()):
                item = self.csv_table.item(row, col)
                if item:
                    if self.dark_theme:
                        item.setBackground(QColor(60, 60, 60))  # Темный фон
                        item.setForeground(QColor(255, 255, 255))  # Белый текст
                    else:
                        item.setBackground(QColor(255, 255, 255))  # Белый фон
                        item.setForeground(QColor(0, 0, 0))  # Черный текст

    def display_different_values(self):
        """Показать различающиеся значения в выделенной области или колонке"""
        selected_ranges = self.csv_table.selectedRanges()
        if not selected_ranges:
            QMessageBox.information(self, "Информация", "Выберите область или ячейку")
            return
        
        # Получаем первый выделенный диапазон
        selected_range = selected_ranges[0]
        top_row = selected_range.topRow()
        bottom_row = selected_range.bottomRow()
        left_col = selected_range.leftColumn()
        right_col = selected_range.rightColumn()
        
        # Если выделена одна ячейка, работаем с колонкой
        if top_row == bottom_row and left_col == right_col:
            # Выделена одна ячейка - работаем с колонкой
            col = left_col
            values = set()
            for row in range(self.csv_table.rowCount()):
                item = self.csv_table.item(row, col)
                if item:
                    value = item.text().strip()
                    if value:  # Игнорируем пустые значения
                        values.add(value)
        else:
            # Выделена область - работаем с выделенными ячейками
            values = set()
            for row in range(top_row, bottom_row + 1):
                for col in range(left_col, right_col + 1):
                    item = self.csv_table.item(row, col)
                    if item:
                        value = item.text().strip()
                        if value:  # Игнорируем пустые значения
                            values.add(value)
        
        # Копируем уникальные значения в буфер обмена
        unique_values = sorted(list(values))
        if unique_values:
            clipboard_text = '\n'.join(unique_values)
            clipboard = QApplication.clipboard()
            clipboard.setText(clipboard_text)
            self.notification_manager.show_notification(f"Найдено {len(unique_values)} уникальных значений.\nСкопировано в буфер обмена.", 
                                  "Готово", 3000, "info")
        else:
            self.notification_manager.show_notification("Уникальные значения не найдены", "Информация", 3000, "info")

    def sort_by_column(self, real_col, ascending=True):
        """Sort data by specified column"""
        if not self.csv_data or real_col >= len(self.csv_headers):
            return
        
        # Sort the filtered indices based on the column values
        def get_sort_key(row_idx):
            if row_idx < len(self.csv_data) and real_col < len(self.csv_data[row_idx]):
                value = self.csv_data[row_idx][real_col]
                # Try to convert to number for proper sorting
                try:
                    return float(value) if value else 0
                except (ValueError, TypeError):
                    return str(value).lower() if value else ''
            return ''
        
        self.filtered_indices.sort(key=get_sort_key, reverse=not ascending)
        self.update_csv_table()

    def add_filter_for_column(self, real_col):
        """Add a filter for the specified column"""
        if real_col >= len(self.csv_headers):
            return
        
        col_name = self.csv_headers[real_col]
        
        # Get unique values from the column
        unique_values = set()
        for row_idx in range(len(self.csv_data)):
            if real_col < len(self.csv_data[row_idx]):
                value = self.csv_data[row_idx][real_col]
                if value and str(value).strip():
                    unique_values.add(str(value).strip())
        
        if not unique_values:
            self.notification_manager.show_notification("В колонке нет значений для фильтрации.", "Фильтр", 3000, "info")
            return
        
        # Show dialog to select filter value
        from PyQt5.QtWidgets import QInputDialog
        sorted_values = sorted(unique_values)
        value, ok = QInputDialog.getItem(self, "Добавить фильтр", 
                                       f"Выберите значение для фильтра по колонке '{col_name}':", 
                                       sorted_values, 0, False)
        
        if ok and value:
            self.active_filters[col_name] = value
            self.apply_filters()

    def remove_filter_for_column(self, real_col):
        """Remove filter for the specified column"""
        if real_col >= len(self.csv_headers):
            return
        
        col_name = self.csv_headers[real_col]
        if col_name in self.active_filters:
            del self.active_filters[col_name]
            self.apply_filters()

    def apply_filters(self):
        """Apply all active filters to the data"""
        if not self.active_filters:
            self.filtered_indices = list(range(len(self.csv_data)))
        else:
            self.filtered_indices = []
            for row_idx, row in enumerate(self.csv_data):
                match = True
                for col_name, filter_value in self.active_filters.items():
                    if col_name in self.csv_headers:
                        col_idx = self.csv_headers.index(col_name)
                        if col_idx < len(row):
                            cell_value = str(row[col_idx]).strip() if row[col_idx] else ''
                            if cell_value != filter_value:
                                match = False
                                break
                        else:
                            match = False
                            break
                if match:
                    self.filtered_indices.append(row_idx)
        
        # Also apply search filter if there's search text
        search_text = self.search_edit.text() if hasattr(self, 'search_edit') else ''
        if search_text:
            self.filter_csv_table()
        else:
            self.update_csv_table()
        
        # Update advanced search widget filter display if it exists
        if hasattr(self, 'advanced_search_widget'):
            self.advanced_search_widget.update_filters_display()
    
    def filter_by_value_context(self, row, col):
        """Filter the table by the value at the specified row and column"""
        if row >= len(self.csv_data) or col >= len(self.csv_data[row]):
            return
        
        filter_value = str(self.csv_data[row][col]).strip()
        if not filter_value:
            return
        
        # Get column name for the filter
        col_name = self.csv_headers[col] if col < len(self.csv_headers) else f"col{col+1}"
        
        # Add or update filter for this column
        self.active_filters[col_name] = filter_value
        
        # Apply the filters
        self.apply_filters()
        
        # Show a message about the applied filter
        self.notification_manager.show_notification(f"Применен фильтр по колонке '{col_name}' со значением '{filter_value}'", 
                              "Фильтр применен", 3000, "info")

    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите CSV файл", "", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, newline='', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
            except UnicodeDecodeError:
                with open(file_path, newline='', encoding='cp1251') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
            if rows:
                print('Headers:', rows[0])  # For debugging
                unique_headers = make_unique_headers(rows[0])
                print('Cleaned headers:', unique_headers)  # For debugging
                print('Cleaned headers set:', set(make_unique_headers(rows[0])))
                self.csv_headers = unique_headers
                self.csv_data = rows[1:] if len(rows) > 1 else []
                self.filtered_indices = list(range(len(self.csv_data)))
                self.visible_columns = list(range(len(self.csv_headers)))  # All columns visible by default
                self.update_csv_table()
                # --- Если не выбрана таблица, добавить новую ---
                table_name = self.get_selected_table_name()
                if not table_name:
                    # Сгенерировать уникальное имя
                    base = "imported_data"
                    idx = 1
                    existing = set()
                    if self.sqlite_conn:
                        cur = self.sqlite_conn.cursor()
                        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        existing = {row[0] for row in cur.fetchall()}
                    while f"{base}_{idx}" in existing:
                        idx += 1
                    table_name = f"{base}_{idx}" if existing else base
                    self.add_new_table(name=table_name)
                    # --- Гарантировать, что менеджер таблиц инициализирован ---
                    if not hasattr(self, 'table_manager_dialog') or self.table_manager_dialog is None:
                        self.open_table_manager_dialog()
                self.load_csv_to_sqlite(unique_headers, self.csv_data, table_name)
                self.update_table_selector()
                # --- После импорта сразу показываем таблицу ---
                if not hasattr(self, 'table_manager_dialog') or self.table_manager_dialog is None:
                    self.open_table_manager_dialog()
                # Ensure table_manager_dialog and table_tree exist before accessing
                if hasattr(self, 'table_manager_dialog') and self.table_manager_dialog is not None and hasattr(self.table_manager_dialog, 'table_tree'):
                    for i in range(self.table_manager_dialog.table_tree.topLevelItemCount()):
                        item = self.table_manager_dialog.table_tree.topLevelItem(i)
                        if item.text(0) == table_name:
                            self.table_manager_dialog.table_tree.setCurrentItem(item)
                            break
                self.load_sqlite_table_to_widget(table_name)
                # Add to recent files
                if hasattr(self, 'recent_files_widget'):
                    self.recent_files_widget.add_recent_file(file_path)

    def update_csv_table(self):
        self.csv_table.clear()
        # Only show visible columns
        visible_headers = [self.csv_headers[i] for i in self.visible_columns]
        self.csv_table.setColumnCount(len(visible_headers))
        self.csv_table.setHorizontalHeaderLabels(visible_headers)
        self.csv_table.setRowCount(len(self.filtered_indices))
        for i, data_idx in enumerate(self.filtered_indices):
            row = self.csv_data[data_idx]
            for col_pos, col_idx in enumerate(self.visible_columns):
                val = row[col_idx] if col_idx < len(row) else ''
                self.csv_table.setItem(i, col_pos, QTableWidgetItem(val))

    def filter_csv_table(self):
        text = self.search_edit.text()
        settings = self.advanced_search_settings or {}
        columns = settings.get('columns', self.csv_headers)
        mode = settings.get('mode', 'any')
        case = settings.get('case', False)
        if not text:
            self.filtered_indices = list(range(len(self.csv_data)))
        else:
            def match(row):
                values = [row[self.csv_headers.index(col)] if self.csv_headers.index(col) < len(row) else '' for col in columns]
                if not case:
                    values = [v.lower() for v in values]
                    t = text.lower()
                else:
                    t = text
                if mode == 'any':
                    return any(word in v for v in values for word in t.split())
                elif mode == 'all':
                    return all(any(word in v for v in values) for word in t.split())
                elif mode == 'exact':
                    return any(t == v for v in values)
                elif mode == 'regex':
                    import re
                    try:
                        return any(re.search(t, v) for v in values)
                    except Exception:
                        return False
                return False
            self.filtered_indices = [i for i, row in enumerate(self.csv_data) if match(row)]
        self.update_csv_table()

    def open_column_visibility_dialog(self):
        if not self.csv_headers:
            return
        current_visible = [self.csv_headers[i] for i in self.visible_columns]
        dialog = ColumnSelectDialog(self.csv_headers, current_visible, self)
        if dialog.exec_() == dialog.Accepted and dialog.selected_columns:
            self.visible_columns = [self.csv_headers.index(col) for col in dialog.selected_columns]
            self.update_csv_table()

    def open_advanced_search(self):
        """Toggle the advanced search dock widget"""
        if hasattr(self, 'advanced_search_dock'):
            if self.advanced_search_dock.isVisible():
                self.advanced_search_dock.hide()
            else:
                self.advanced_search_widget.update_headers(self.csv_headers)
                if self.advanced_search_settings:
                    self.advanced_search_widget.set_settings(self.advanced_search_settings)
                # Update filters display when opening
                self.advanced_search_widget.update_filters_display()
                self.advanced_search_dock.show()
                self.advanced_search_dock.raise_()
                # Also show search widget when advanced search is opened
                if not self.search_widget.isVisible():
                    self.search_widget.setVisible(True)
        else:
            # Fallback to old dialog if dock widget not initialized
            dlg = AdvancedSearchDialog(self.csv_headers, self.advanced_search_settings, self)
            if dlg.exec_() == QDialog.Accepted:
                self.advanced_search_settings = dlg.get_settings()
                self.filter_csv_table()

    def export_csv_to_excel(self):
        if not self.csv_headers or not self.filtered_indices:
            return
        dialog = ColumnSelectDialog(self.csv_headers, self.csv_headers, self)
        if dialog.exec_() != dialog.Accepted or not dialog.selected_columns:
            return
        selected_indices = [self.csv_headers.index(col) for col in dialog.selected_columns]
        import pandas as pd
        export_headers = pd.Index([str(self.csv_headers[i]) for i in selected_indices])
        export_data = [[str(self.csv_data[idx][i]) if i < len(self.csv_data[idx]) else '' for i in selected_indices] for idx in self.filtered_indices]
        df = pd.DataFrame(export_data, columns=export_headers)
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить как Excel", "", "Excel Files (*.xlsx)")
        if file_path:
            try:
                df.to_excel(file_path, index=False)
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Ошибка экспорта", str(e))

    def export_csv_to_csv(self):
        if not self.csv_headers or not self.filtered_indices:
            return
        dialog = ColumnSelectDialog(self.csv_headers, self.csv_headers, self)
        if dialog.exec_() != dialog.Accepted or not dialog.selected_columns:
            return
        selected_indices = [self.csv_headers.index(col) for col in dialog.selected_columns]
        export_headers = [self.csv_headers[i] for i in selected_indices]
        export_data = [[(self.csv_data[idx][i] if i < len(self.csv_data[idx]) else '') for i in selected_indices] for idx in self.filtered_indices]
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить как CSV", "", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(export_headers)
                    writer.writerows(export_data)
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Ошибка экспорта", str(e))

    def load_csv_to_sqlite(self, headers, data_rows, table_name="data"):
        if not headers:
            return
        if not self.sqlite_conn:
            self.sqlite_conn = sqlite3.connect(":memory:")
        cur = self.sqlite_conn.cursor()
        cur.execute(f"DROP TABLE IF EXISTS '{table_name}'")
        col_defs = ', '.join([f'"{h}" TEXT' for h in headers])
        cur.execute(f'CREATE TABLE "{table_name}" ({col_defs})')
        if data_rows:
            placeholders = ','.join(['?'] * len(headers))
            safe_rows = [row[:len(headers)] + ['']*(len(headers)-len(row)) for row in data_rows]
            cur.executemany(f'INSERT INTO "{table_name}" VALUES ({placeholders})', safe_rows)
        self.sqlite_conn.commit()
        if hasattr(self.sql_tab, 'set_connection'):
            self.sql_tab.set_connection(self.sqlite_conn)
        # Update table manager dock widget
        if hasattr(self, 'table_manager_widget'):
            self.table_manager_widget.update_table_selector()

    def show_column_select_dialog(self, columns, default_columns=None):
        dialog = ColumnSelectDialog(columns, default_columns, self)
        if dialog.exec_() == dialog.Accepted:
            return dialog.selected_columns
        return None 

    def show_table_context_menu(self, pos):
        menu = QMenu(self.csv_table)
        col = self.csv_table.columnAt(pos.x())
        row = self.csv_table.rowAt(pos.y())
        if col == -1:
            return
        real_col = self.visible_columns[col]
        col_name = self.csv_headers[real_col] if real_col < len(self.csv_headers) else f"col{real_col+1}"
        # --- Добавить/Удалить область ---
        add_area_action = QAction('Добавить область (+)', self)
        add_area_action.triggered.connect(self.add_selected_area)
        menu.addAction(add_area_action)
        del_area_action = QAction('Удалить область (-)', self)
        del_area_action.triggered.connect(self.delete_selected_area)
        menu.addAction(del_area_action)
        # --- Отбор по значению в текущей колонке ---
        filter_by_value = QAction(f"Отбор по значению (" + col_name + ")", self)
        filter_by_value.triggered.connect(lambda: self.filter_by_value_context(row, real_col))
        menu.addAction(filter_by_value)
        # --- Группировка по значению в колонке ---
        group_by_action = QAction(f"Сгруппировать по значению (" + col_name + ")", self)
        group_by_action.triggered.connect(lambda: self.open_group_by_dialog(real_col, col))
        menu.addAction(group_by_action)
        # --- Подменю Раскрасить ---
        color_menu = menu.addMenu('Раскрасить')
        highlight_action = QAction('Повторяющиеся значения', self)
        highlight_action.triggered.connect(self.highlight_duplicates)
        color_menu.addAction(highlight_action)
        transitions_action = QAction('Переходы между значениями', self)
        transitions_action.triggered.connect(self.highlight_transitions)
        color_menu.addAction(transitions_action)
          # --- New commands ---
        menu.addSeparator()
        clean_coloring_action = QAction('Очистить раскраску', self)
        clean_coloring_action.triggered.connect(self.clean_cell_coloring)
        color_menu.addAction(clean_coloring_action)      
        # --- Сортировка и фильтры ---
        sort_asc = QAction(f"Сортировать по возрастанию ({col_name})", self)
        sort_desc = QAction(f"Сортировать по убыванию ({col_name})", self)
        add_filter = QAction(f"Добавить отбор по колонке ({col_name})", self)
        remove_filter = QAction(f"Удалить отбор по колонке ({col_name})", self)
        sort_asc.triggered.connect(lambda: self.sort_by_column(real_col, True))
        sort_desc.triggered.connect(lambda: self.sort_by_column(real_col, False))
        add_filter.triggered.connect(lambda: self.add_filter_for_column(real_col))
        remove_filter.triggered.connect(lambda: self.remove_filter_for_column(real_col))
        menu.addAction(sort_asc)
        menu.addAction(sort_desc)
        menu.addSeparator()
        menu.addAction(add_filter)
        if col_name in self.active_filters:
            menu.addAction(remove_filter)
        

        
        display_different_action = QAction('Показать различающиеся значения', self)
        display_different_action.triggered.connect(lambda: self.display_different_values())
        menu.addAction(display_different_action)
        
        menu.exec_(self.csv_table.viewport().mapToGlobal(pos))

    def highlight_duplicates(self):
        # Для каждой видимой колонки
        for vis_col, real_col in enumerate(self.visible_columns):
            # Собираем значения колонки
            values = []
            for row_idx in self.filtered_indices:
                item = self.csv_table.item(row_idx, vis_col)
                val = item.text() if item else ''
                values.append(val)
            # Подсчет частот
            freq = defaultdict(int)
            for v in values:
                if v and v.strip():
                    freq[v] += 1
            # Кеш цветов
            color_cache = {}
            prev_val = None
            prev_color = None
            for row_pos, v in enumerate(values):
                item = self.csv_table.item(self.filtered_indices[row_pos], vis_col)
                if not item or not v or freq[v] <= 1:
                    if item:
                        item.setBackground(Qt.white)
                    continue
                # Генерируем цвет по хешу, но если значение подряд — другой оттенок
                if v not in color_cache:
                    base_hue = (hash(str(v)) % 360) / 360.0
                    # Если подряд, сдвигаем оттенок на 0.15 (54 градуса)
                    if prev_val == v and prev_color:
                        hue = (base_hue + 0.15) % 1.0
                    else:
                        hue = base_hue
                    r, g, b = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
                    color = QColor(int(r*255), int(g*255), int(b*255))
                    color_cache[v] = color
                else:
                    color = color_cache[v]
                item.setBackground(color)
                prev_val = v
                prev_color = color

    def highlight_transitions(self):
        # Цвета для переходов - адаптированы для темной и светлой темы
        if self.dark_theme:
            # Светлые цвета для темной темы
            transition_colors = [
                QColor(100, 150, 255),  # светло-синий
                QColor(255, 180, 100),  # светло-оранжевый
                QColor(200, 150, 255),  # светло-фиолетовый
                QColor(150, 255, 180),  # светло-зеленый
                QColor(255, 150, 150),  # светло-красный
                QColor(200, 200, 200),  # светло-серый
            ]
        else:
            # Темные цвета для светлой темы
            transition_colors = [
                QColor(30, 30, 120),   # темно-синий
                QColor(90, 60, 30),    # темно-коричневый
                QColor(60, 30, 90),    # темно-фиолетовый
                QColor(30, 90, 60),    # темно-зеленый
                QColor(120, 60, 30),   # темно-оранжевый
                QColor(60, 60, 60),    # темно-серый
            ]
        for vis_col, real_col in enumerate(self.visible_columns):
            prev_val = None
            color_idx = 0
            color = Qt.black
            for row_pos, row_idx in enumerate(self.filtered_indices):
                item = self.csv_table.item(row_idx, vis_col)
                if not item:
                    continue
                val = item.text()
                if row_pos == 0:
                    prev_val = val
                    item.setForeground(color)
                    continue
                if val != prev_val:
                    color = transition_colors[color_idx % len(transition_colors)]
                    item.setForeground(color)
                    color_idx += 1
                else:
                    item.setForeground(color)
                prev_val = val

    def open_group_by_dialog(self, real_col, visual_col):
        # Проверяем корректность индексов
        if not self.csv_headers or real_col >= len(self.csv_headers):
            return
        
        # Использовать только видимые колонки
        visible_headers = [self.csv_headers[i] for i in self.visible_columns]
        
        # Проверяем корректность visual_col
        if visual_col >= len(visible_headers):
            return
            
        # Получаем имя колонки для группировки
        group_col_name = visible_headers[visual_col]
        
        # --- Forward fill ---
        data = []
        last_val = None
        for row_idx in self.filtered_indices:
            if row_idx >= len(self.csv_data):
                continue
            row = self.csv_data[row_idx]
            val = row[real_col] if real_col < len(row) and row[real_col] else last_val
            if not val:
                val = last_val
            else:
                last_val = val
            # Только видимые колонки
            visible_row = [row[i] if i < len(row) else '' for i in self.visible_columns]
            data.append((val, visible_row))
        
        # --- Группировка ---
        groups = {}
        for val, row in data:
            groups.setdefault(val, []).append(row)
        
        from group_by_dialog import GroupByDialog
        dlg = GroupByDialog(group_col_name, groups, visible_headers, self)
        dlg.exec_()

    def rename_current_table(self):
        old_name = self.get_selected_table_name()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(self, "Переименовать таблицу", "Новое имя:", text=old_name)
        if ok and new_name and new_name != old_name:
            cur = self.sqlite_conn.cursor()
            try:
                cur.execute(f'ALTER TABLE "{old_name}" RENAME TO "{new_name}"')
                self.sqlite_conn.commit()
                self.update_table_selector()
                # Update table manager dock widget
                if hasattr(self, 'table_manager_widget'):
                    self.table_manager_widget.update_table_selector()
                # Выделить новую таблицу
                if hasattr(self, 'table_manager_dialog') and self.table_manager_dialog is not None and hasattr(self.table_manager_dialog, 'table_tree'):
                    for i in range(self.table_manager_dialog.table_tree.topLevelItemCount()):
                        item = self.table_manager_dialog.table_tree.topLevelItem(i)
                        if item.text(0) == new_name:
                            self.table_manager_dialog.table_tree.setCurrentItem(item)
                            break
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                self.notification_manager.show_notification(f"Не удалось переименовать таблицу: {e}", "Ошибка", 3000, "error")

    def delete_current_table(self):
        name = self.get_selected_table_name()
        if not name:
            return
        # Show confirmation notification instead of QMessageBox
        self.notification_manager.show_notification(
            f"Удалить таблицу '{name}'?", 
            "Удалить таблицу", 
            3000,
            "warning"
        )
        # For now, proceed with deletion (in a real implementation, you'd want a callback)
        if True:  # Replace with proper confirmation logic
            cur = self.sqlite_conn.cursor()
            try:
                cur.execute(f'DROP TABLE IF EXISTS "{name}"')
                self.sqlite_conn.commit()
                self.update_table_selector()
                # Выделить первую таблицу, если есть
                if hasattr(self, 'table_manager_dialog') and self.table_manager_dialog is not None and hasattr(self.table_manager_dialog, 'table_tree'):
                    if self.table_manager_dialog.table_tree.topLevelItemCount() > 0:
                        self.table_manager_dialog.table_tree.setCurrentItem(self.table_manager_dialog.table_tree.topLevelItem(0))
                    else:
                        self.csv_table.clear()
            except Exception as e:
                self.notification_manager.show_notification(f"Не удалось удалить таблицу: {e}", "Ошибка", 3000, "error") 

    def add_new_table(self, name=None):
        if name is None:
            name, ok = QInputDialog.getText(self, "Новая таблица", "Имя новой таблицы:")
            if not ok or not name or not name.strip():
                return
            name = name.strip()
        if not name or name is False:
            # Автоматически подобрать имя table_N
            base = "table"
            idx = 1
            existing = set()
            if self.sqlite_conn:
                cur = self.sqlite_conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing = {row[0] for row in cur.fetchall()}
            while f"{base}_{idx}" in existing:
                idx += 1
            name = f"{base}_{idx}" if existing else base
        if self.sqlite_conn is None:
            self.sqlite_conn = sqlite3.connect(":memory:")
        cur = self.sqlite_conn.cursor()
        try:
            col_defs = ', '.join([f'"col{i+1}" TEXT' for i in range(10)]) # Default columns for new table
            cur.execute(f'CREATE TABLE "{name}" ({col_defs})')
            self.sqlite_conn.commit()
            self.update_table_selector()
        except Exception as e:
            self.notification_manager.show_notification(f"Не удалось создать таблицу: {e}", "Ошибка", 3000, "error") 

    def open_table_manager_dialog(self):
        """Toggle the table manager dock widget"""
        if hasattr(self, 'table_manager_dock'):
            if self.table_manager_dock.isVisible():
                self.table_manager_dock.hide()
            else:
                self.table_manager_widget.update_table_selector()
                self.table_manager_dock.show()
                self.table_manager_dock.raise_()
        else:
            # Fallback to old dialog if dock widget not initialized
            if self.table_manager_dialog is None:
                self.table_manager_dialog = TableManagerDialog(self)
            self.table_manager_dialog.update_table_selector()
            self.table_manager_dialog.show()
            self.table_manager_dialog.raise_()
            self.table_manager_dialog.activateWindow() 
        
    def compare_tables(self, table_a, table_b):
        """Открывает диалог сравнения двух таблиц"""
        try:
            # Импортируем модуль для сравнения таблиц
            from table_compare_dialog import TableCompareDialog
            
            # Проверяем, что обе таблицы существуют
            if not self.sqlite_conn:
                self.notification_manager.show_notification("Нет активного соединения с базой данных", "Предупреждение", 3000, "warning")
                return
                
            cur = self.sqlite_conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN (?, ?)", (table_a, table_b))
            tables = [row[0] for row in cur.fetchall()]
            
            if len(tables) < 2:
                self.notification_manager.show_notification(f"Одна или обе таблицы не существуют: {table_a}, {table_b}", "Предупреждение", 3000, "warning")
                return
            
            # Создаем и показываем окно сравнения
            self.compare_dialog = TableCompareDialog(self.sqlite_conn, table_a, table_b, None)
            self.compare_dialog.show()  # Используем show() для немодального окна
            self.compare_dialog.raise_()
            self.compare_dialog.activateWindow()
            
        except Exception as e:
            self.notification_manager.show_notification(f"Не удалось открыть диалог сравнения таблиц: {str(e)}", "Ошибка", 3000, "error")
            import traceback
            traceback.print_exc()

    def open_options_dialog(self):
        dlg = OptionsDialog(self, self.confirm_on_exit, self.convert_first_row_to_headers, self.dark_theme)
        if dlg.exec_() == QDialog.Accepted:
            old_dark_theme = self.dark_theme
            self.confirm_on_exit = dlg.get_confirm_on_exit()
            self.convert_first_row_to_headers = dlg.get_convert_first_row_to_headers()
            self.dark_theme = dlg.get_dark_theme()
            if old_dark_theme != self.dark_theme:
                self.apply_theme()
            self.save_settings()

    def import_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите Excel/ODS файл", "", "Таблицы (*.xlsx *.xls *.ods)")
        if file_path:
            try:
                df = pd.read_excel(file_path, engine=None)
                headers = list(df.columns)
                data = df.values.tolist()
                self.csv_headers = make_unique_headers(headers)
                self.csv_data = data
                self.filtered_indices = list(range(len(self.csv_data)))
                self.visible_columns = list(range(len(self.csv_headers)))
                self.update_csv_table()
                # --- Если не выбрана таблица, добавить новую ---
                table_name = self.get_selected_table_name()
                if not table_name:
                    base = "imported_data"
                    idx = 1
                    existing = set()
                    if self.sqlite_conn:
                        cur = self.sqlite_conn.cursor()
                        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        existing = {row[0] for row in cur.fetchall()}
                    while f"{base}_{idx}" in existing:
                        idx += 1
                    table_name = f"{base}_{idx}" if existing else base
                    self.add_new_table(name=table_name)
                self.load_csv_to_sqlite(self.csv_headers, self.csv_data, table_name)
                self.update_table_selector()
                if hasattr(self, 'table_manager_dialog') and self.table_manager_dialog is not None and hasattr(self.table_manager_dialog, 'table_tree'):
                    for i in range(self.table_manager_dialog.table_tree.topLevelItemCount()):
                        item = self.table_manager_dialog.table_tree.topLevelItem(i)
                        if item.text(0) == table_name:
                            self.table_manager_dialog.table_tree.setCurrentItem(item)
                            break
                self.load_sqlite_table_to_widget(table_name)
                # Add to recent files
                if hasattr(self, 'recent_files_widget'):
                    self.recent_files_widget.add_recent_file(file_path)
            except Exception as e:
                self.notification_manager.show_notification(f"Ошибка импорта Excel/ODS: {e}", "Ошибка", 3000, "error") 

    def place_to_sqlite_table(self):
        # Получить текущее имя таблицы
        current_name = self.get_selected_table_name() or "data"
        name, ok = QInputDialog.getText(self, "Имя таблицы", "Введите имя целевой таблицы:", text=current_name)
        if not ok or not name or not name.strip():
            return
        name = name.strip()
        # Получить данные из QTableWidget
        row_count = self.csv_table.rowCount()
        col_count = self.csv_table.columnCount()
        headers = [self.csv_table.horizontalHeaderItem(i).text() if self.csv_table.horizontalHeaderItem(i) else f"col{i+1}" for i in range(col_count)]
        data = []
        for row in range(row_count):
            row_data = []
            for col in range(col_count):
                item = self.csv_table.item(row, col)
                row_data.append(item.text() if item else '')
            data.append(row_data)
        # Поместить в sqlite
        self.load_table_to_sqlite_with_data(name, headers, data)
        self.update_table_selector()
        # Сбросить флаг изменения таблицы
        self.reset_table_modified()
        self.notification_manager.show_notification(f"Данные помещены в таблицу '{name}'", "Готово", 3000, "success") 

    def load_table_to_sqlite_with_data(self, table_name, headers, data):
        if not headers:
            return
        if not self.sqlite_conn:
            self.sqlite_conn = sqlite3.connect(":memory:")
        cur = self.sqlite_conn.cursor()
        # Drop table if exists
        cur.execute(f"DROP TABLE IF EXISTS '{table_name}'")
        # Create table
        col_defs = ', '.join([f'"{h}" TEXT' for h in headers])
        cur.execute(f'CREATE TABLE "{table_name}" ({col_defs})')
        # Insert data
        if data:
            placeholders = ','.join(['?'] * len(headers))
            safe_rows = [row[:len(headers)] + ['']*(len(headers)-len(row)) for row in data]
            cur.executemany(f'INSERT INTO "{table_name}" VALUES ({placeholders})', safe_rows)
        self.sqlite_conn.commit()
        # Pass connection to SQL tab (if needed)
        if hasattr(self.sql_tab, 'set_connection'):
            self.sql_tab.set_connection(self.sqlite_conn)