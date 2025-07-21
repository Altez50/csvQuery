from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QLineEdit, QLabel, QHBoxLayout, QCheckBox, QListWidget, QListWidgetItem, QRadioButton, QButtonGroup, QDialog, QDialogButtonBox, QApplication, QInputDialog, QComboBox, QMenu, QAction, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QSplitter, QMenuBar, QMessageBox, QCheckBox as QtCheckBox, QToolBar, QToolButton, QMenu, QAction, QSizePolicy, QWidget
from ui_column_select import ColumnSelectDialog
from sql_query_page import SQLQueryPage
import sqlite3
import csv
import pandas as pd
import re
from PyQt5.QtCore import Qt, QSize, QSettings
from PyQt5.QtGui import QKeySequence, QIcon, QColor
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
        layout.addWidget(self.table_tree, 1)
        self.setLayout(layout)
        self.update_table_selector()
        # --- Geometry persistence ---
        self._settings = QSettings('csvQuery', 'TableManagerDialog')
        self.restore_geometry()

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
            item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table_tree.addTopLevelItem(item)
        self.table_tree.blockSignals(False)

class OptionsDialog(QDialog):
    def __init__(self, parent, confirm_on_exit):
        super().__init__(parent)
        self.setWindowTitle('Опции')
        layout = QVBoxLayout(self)
        self.confirm_exit_checkbox = QtCheckBox('Запрашивать подтверждение при выходе')
        self.confirm_exit_checkbox.setChecked(confirm_on_exit)
        layout.addWidget(self.confirm_exit_checkbox)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
    def get_confirm_on_exit(self):
        return self.confirm_exit_checkbox.isChecked()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Query Tool (PyQt5)")
        self.resize(900, 600)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.confirm_on_exit = True
        self.load_settings()
        self.init_toolbar()
        self.init_tabs()
        self.sqlite_conn = None
        self.csv_data = []  # All rows (excluding header)
        self.csv_headers = []
        self.filtered_indices = []  # Indices of rows currently shown
        self.visible_columns = []  # Indices of columns currently visible
        self.advanced_search_settings = None
        self.table_manager_dialog = None

    def init_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QSize(20, 20))
        # Кнопки для вкладок CSV/SQL
        self.csv_tab_btn = QPushButton('CSV')
        self.csv_tab_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        toolbar.addWidget(self.csv_tab_btn)
        self.sql_tab_btn = QPushButton('SQL')
        self.sql_tab_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        toolbar.addWidget(self.sql_tab_btn)
        # Spacer to push menu to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        # Кнопка меню
        menu_btn = QToolButton()
        menu_btn.setText('Меню')
        menu_btn.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(menu_btn)
        # --- Подменю Файл ---
        file_menu = QMenu('Файл', menu)
        new_action = QAction('Новая сессия', self)
        new_action.triggered.connect(self.new_session)
        file_menu.addAction(new_action)
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
        menu.addMenu(file_menu)
        # --- Настройки и О программе ---
        settings_action = QAction('Настройки', self)
        settings_action.triggered.connect(self.open_options_dialog)
        about_action = QAction('О программе', self)
        about_action.triggered.connect(self.show_about_dialog)
        menu.addAction(settings_action)
        menu.addAction(about_action)
        # --- Подменю Опции ---
        options_menu = QMenu('Опции', menu)
        editor_opts_action = QAction('Настройки редактора SQL...', self)
        editor_opts_action.triggered.connect(lambda: getattr(self, 'sql_tab', None) and self.sql_tab.open_editor_options())
        options_menu.addAction(editor_opts_action)
        menu.addMenu(options_menu)
        menu_btn.setMenu(menu)
        toolbar.addWidget(menu_btn)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

    def show_about_dialog(self):
        QMessageBox.information(self, 'О программе', 'CSV Query Tool\nВерсия: 1.0')

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.confirm_on_exit = bool(data.get('confirm_on_exit', True))
            except Exception:
                self.confirm_on_exit = True
    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump({'confirm_on_exit': self.confirm_on_exit}, f, ensure_ascii=False, indent=2)
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
        reply = QMessageBox.question(self, 'Подтвердите', 'Вы действительно хотите начать новую сессию? Все несохранённые данные будут потеряны.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
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
            QMessageBox.information(self, 'Новая сессия', 'Сессия сброшена. Можно начинать работу с чистого листа.')
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
                QMessageBox.information(self, 'Сохранение', 'Сессия успешно сохранена!')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка при сохранении сессии: {e}')
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
                    os.remove(db_path)
                sql_page = getattr(self, 'sql_tab', None)
                if sql_page and os.path.exists(history_path):
                    with open(history_path, "r", encoding="utf-8") as f:
                        sql_page.history = json.load(f)
                    if hasattr(sql_page, 'history_dialog') and sql_page.history_dialog:
                        sql_page.history_dialog.update_history_tree()
                    if hasattr(sql_page, 'results_dialog') and sql_page.results_dialog:
                        sql_page.results_dialog.update_results_view()
                    os.remove(history_path)
                # Переключить на вкладку SQL, если есть
                if hasattr(self, 'tabs') and hasattr(self, 'sql_tab'):
                    idx = self.tabs.indexOf(self.sql_tab)
                    if idx != -1:
                        self.tabs.setCurrentIndex(idx)
                QMessageBox.information(self, 'Открытие', 'Сессия успешно загружена!')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка при открытии сессии: {e}')
    def closeEvent(self, event):
        self.save_settings()
        if self.confirm_on_exit:
            reply = QMessageBox.question(self, 'Выход', 'Выйти из программы?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def init_tabs(self):
        self.csv_tab = QWidget()
        self.sql_tab = SQLQueryPage()
        self.tabs.addTab(self.csv_tab, "CSV")
        self.tabs.addTab(self.sql_tab, "SQL")
        self.init_csv_tab()

    def init_csv_tab(self):
        # --- Верхний блок: кнопки и дерево таблиц ---
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        self.open_table_manager_btn = QPushButton("Таблицы...")
        self.open_table_manager_btn.clicked.connect(self.open_table_manager_dialog)
        top_layout.addWidget(self.open_table_manager_btn)
        # --- Кнопка Импорт из Excel/ODS ---
        self.excel_import_btn = QPushButton("Импорт из Excel/ODS")
        self.excel_import_btn.clicked.connect(self.import_excel)
        top_layout.addWidget(self.excel_import_btn)
        # --- Кнопка Импорт из CSV ---
        self.csv_import_btn = QPushButton("Импортировать CSV")
        self.csv_import_btn.clicked.connect(self.import_csv)
        top_layout.addWidget(self.csv_import_btn)
        # --- Кнопка Поместить в таблицу ---
        self.place_to_table_btn = QPushButton("Поместить в таблицу")
        self.place_to_table_btn.clicked.connect(self.place_to_sqlite_table)
        top_layout.addWidget(self.place_to_table_btn)
        # --- Нижний блок: всё остальное ---
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        # --- Создаём таблицу ДО installEventFilter ---
        self.csv_table = QTableWidget()
        self.csv_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.csv_table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.csv_table.installEventFilter(self)
        # --- Кнопки поиска, импорта, экспорта, видимости столбцов ---
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.filter_csv_table)
        search_layout.addWidget(self.search_edit)
        self.adv_search_btn = QPushButton("Расширенный поиск")
        self.adv_search_btn.clicked.connect(self.open_advanced_search)
        search_layout.addWidget(self.adv_search_btn)
        self.column_visibility_btn = QPushButton("Видимость столбцов")
        self.column_visibility_btn.clicked.connect(self.open_column_visibility_dialog)
        search_layout.addWidget(self.column_visibility_btn)
        self.csv_export_excel_btn = QPushButton("Экспорт в Excel")
        self.csv_export_excel_btn.clicked.connect(self.export_csv_to_excel)
        search_layout.addWidget(self.csv_export_excel_btn)
        self.csv_export_csv_btn = QPushButton("Экспорт в CSV")
        self.csv_export_csv_btn.clicked.connect(self.export_csv_to_csv)
        search_layout.addWidget(self.csv_export_csv_btn)
        search_layout.addStretch()
        bottom_layout.addLayout(search_layout)
        # --- Элемент управления фильтрами ---
        self.filter_bar = QHBoxLayout()
        self.filter_labels = []
        bottom_layout.addLayout(self.filter_bar)
        bottom_layout.addWidget(self.csv_table)
        # --- Splitter между верхом и низом ---
        splitter = QSplitter()
        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        splitter.setSizes([100, 900])  # Пропорция 20%/80% (примерно)
        main_layout = QVBoxLayout(self.csv_tab)
        main_layout.addWidget(splitter)
        self.csv_tab.setLayout(main_layout)
        self.active_filters = {}  # {column_name: value}
        if not hasattr(self, 'sqlite_conn'):
            self.sqlite_conn = None
        self.update_table_selector()

    def update_table_selector(self):
        if hasattr(self, 'table_manager_dialog') and self.table_manager_dialog is not None:
            self.table_manager_dialog.update_table_selector()

    def on_table_selected(self):
        items = self.table_manager_dialog.table_tree.selectedItems()
        if items:
            table = items[0].text(0)
            self.load_sqlite_table_to_widget(table)

    def get_selected_table_name(self):
        if not hasattr(self, 'table_manager_dialog') or self.table_manager_dialog is None:
            return None
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

    def eventFilter(self, source, event):
        if not hasattr(self, 'csv_table'):
            return super().eventFilter(source, event)
        table_tree = getattr(self.table_manager_dialog, 'table_tree', None) if hasattr(self, 'table_manager_dialog') else None
        if table_tree is not None and source == table_tree and event.type() == event.KeyPress:
            if event.key() == Qt.Key_F2:
                self.rename_current_table()
                return True
        if source == self.csv_table:
            if event.type() == event.KeyPress:
                if event.matches(QKeySequence.Copy):
                    self.copy_table_selection()
                    return True
                elif event.matches(QKeySequence.Paste):
                    self.paste_table_selection()
                    return True
                elif event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_Minus or event.key() == 0x1000004d): #KeypadSubstract
                    self.delete_selected_area()
                    return True
                elif event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_Plus or event.key() == 0x1000004b): #KeypadAdd
                    self.add_selected_area()
                    return True
        return super().eventFilter(source, event)

    def delete_selected_area(self):
        sel = self.csv_table.selectedRanges()
        if not sel:
            return
        rng = sel[0]
        # Если ширина >= высоты — удалять строки, иначе столбцы
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
        max_row = start_row + len(data)
        max_col = start_col + max(len(r) for r in data)
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
                for i in range(self.table_manager_dialog.table_tree.topLevelItemCount()):
                    item = self.table_manager_dialog.table_tree.topLevelItem(i)
                    if item.text(0) == table_name:
                        self.table_manager_dialog.table_tree.setCurrentItem(item)
                        break
                self.load_sqlite_table_to_widget(table_name)

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
        # Цвета для переходов (темно-синий, темно-коричневый и т.п.)
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
            for row_pos, row_idx in enumerate(self.filtered_indices):
                item = self.csv_table.item(row_idx, vis_col)
                if not item:
                    continue
                val = item.text()
                if row_pos == 0:
                    prev_val = val
                    item.setForeground(Qt.black)
                    continue
                if val != prev_val:
                    color = transition_colors[color_idx % len(transition_colors)]
                    item.setForeground(color)
                    color_idx += 1
                else:
                    item.setForeground(Qt.black)
                prev_val = val

    def open_group_by_dialog(self, real_col, visual_col):
        # Использовать только видимые колонки
        visible_headers = [self.csv_headers[i] for i in self.visible_columns]
        # --- Forward fill ---
        data = []
        last_val = None
        for row_idx in self.filtered_indices:
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
        dlg = GroupByDialog(visible_headers[visual_col], groups, visible_headers, self)
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
                # Выделить новую таблицу
                for i in range(self.table_manager_dialog.table_tree.topLevelItemCount()):
                    item = self.table_manager_dialog.table_tree.topLevelItem(i)
                    if item.text(0) == new_name:
                        self.table_manager_dialog.table_tree.setCurrentItem(item)
                        break
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Ошибка", f"Не удалось переименовать таблицу: {e}")

    def delete_current_table(self):
        name = self.get_selected_table_name()
        if not name:
            return
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Удалить таблицу", f"Удалить таблицу '{name}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            cur = self.sqlite_conn.cursor()
            try:
                cur.execute(f'DROP TABLE IF EXISTS "{name}"')
                self.sqlite_conn.commit()
                self.update_table_selector()
                # Выделить первую таблицу, если есть
                if self.table_manager_dialog.table_tree.topLevelItemCount() > 0:
                    self.table_manager_dialog.table_tree.setCurrentItem(self.table_manager_dialog.table_tree.topLevelItem(0))
                else:
                    self.csv_table.clear()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить таблицу: {e}") 

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
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать таблицу: {e}") 

    def open_table_manager_dialog(self):
        if self.table_manager_dialog is None:
            self.table_manager_dialog = TableManagerDialog(self)
        self.table_manager_dialog.update_table_selector()
        self.table_manager_dialog.show()
        self.table_manager_dialog.raise_()
        self.table_manager_dialog.activateWindow() 

    def open_options_dialog(self):
        dlg = OptionsDialog(self, self.confirm_on_exit)
        if dlg.exec_() == QDialog.Accepted:
            self.confirm_on_exit = dlg.get_confirm_on_exit()
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
                for i in range(self.table_manager_dialog.table_tree.topLevelItemCount()):
                    item = self.table_manager_dialog.table_tree.topLevelItem(i)
                    if item.text(0) == table_name:
                        self.table_manager_dialog.table_tree.setCurrentItem(item)
                        break
                self.load_sqlite_table_to_widget(table_name)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка импорта Excel/ODS: {e}") 

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
        QMessageBox.information(self, "Готово", f"Данные помещены в таблицу '{name}'") 

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