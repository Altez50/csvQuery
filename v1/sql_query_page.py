from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QHBoxLayout, QComboBox, QLineEdit, QSizePolicy, QDialog, QFontComboBox, QSpinBox, QDialogButtonBox, QInputDialog, QComboBox, QMenu, QTreeWidget, QTreeWidgetItem, QAction
from PyQt5.QtCore import Qt, QFileSystemWatcher, QProcess, QEvent
import sqlite3
import pandas as pd
from ui_column_select import ColumnSelectDialog
from PyQt5.QtGui import QClipboard, QFont, QIcon
from PyQt5.QtWidgets import QApplication
import json
import os
from PyQt5.Qsci import QsciScintilla, QsciLexerSQL
import re
from query_tree_dialog import QueryTreeDialog
from results_dialog import ResultsDialog
import tempfile
from PyQt5.QtWidgets import QMessageBox
from sql_query_constructor import SQLQueryConstructorDialog

HISTORY_FILE = 'query_history.json'
EDITOR_SETTINGS_FILE = 'editor_settings.json'

class EditorOptionsDialog(QDialog):
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle('Опции редактора SQL')
        self.resize(400, 200)
        layout = QVBoxLayout(self)
        # Font family
        layout.addWidget(QLabel('Шрифт:'))
        self.font_combo = QFontComboBox()
        layout.addWidget(self.font_combo)
        # Font size
        layout.addWidget(QLabel('Размер шрифта:'))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 48)
        layout.addWidget(self.font_size_spin)
        # Color scheme
        layout.addWidget(QLabel('Цветовая схема:'))
        self.scheme_combo = QComboBox()
        self.scheme_combo.addItems(['Светлая', 'Тёмная'])
        layout.addWidget(self.scheme_combo)
        # Editor path
        layout.addWidget(QLabel('Внешний редактор (путь):'))
        self.editor_path_edit = QLineEdit()
        layout.addWidget(self.editor_path_edit)
        # Hotkeys info (read-only)
        layout.addWidget(QLabel('Горячие клавиши поиска/замены:'))
        self.hotkeys_label = QLabel('Поиск: Ctrl+F   Замена: Ctrl+H   Перейти к строке: Ctrl+G')
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
        self.setWindowTitle('Параметры запроса')
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
        self.add_btn = QPushButton('Добавить параметр')
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
        self.setWindowTitle('Текст запроса с параметрами')
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(query_text)
        layout.addWidget(text)
        btn = QPushButton('Закрыть')
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class SQLQueryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = None  # SQLite connection
        self.history = []  # List of dicts: {"name": str, "queries": [query_dicts]}
        self.current_group_idx = -1
        self.current_query_idx = -1
        self.editor_settings = self.load_editor_settings()
        self.query_params = {'task_numbers': ''}
        self.load_history()
        layout = QVBoxLayout(self)
        # --- Toolbar with main actions ---
        main_toolbar = QHBoxLayout()
        self.execute_btn = QPushButton("Выполнить (F7)")
        self.execute_btn.setFixedWidth(110)
        self.execute_btn.clicked.connect(self.execute_query)
        main_toolbar.addWidget(self.execute_btn)
        self.params_btn = QPushButton("Параметры запроса")
        self.params_btn.setFixedWidth(140)
        self.params_btn.clicked.connect(self.edit_query_params)
        main_toolbar.addWidget(self.params_btn)
        main_toolbar.addStretch()  # <-- Разделитель
        self.open_query_tree_btn = QPushButton("Дерево запросов...")
        self.open_query_tree_btn.clicked.connect(self.open_history_dialog)
        main_toolbar.addWidget(self.open_query_tree_btn)
        self.open_results_btn = QPushButton("Результаты запроса...")
        self.open_results_btn.clicked.connect(self.open_results_dialog)
        main_toolbar.addWidget(self.open_results_btn)
        layout.addLayout(main_toolbar)
        # --- Toolbar for SQL editor ---
        sql_toolbar = QHBoxLayout()
        self.find_btn = QPushButton("Поиск")
        self.find_btn.setFixedWidth(70)
        self.find_btn.clicked.connect(self.open_find_dialog)
        self.replace_btn = QPushButton("Замена")
        self.replace_btn.setFixedWidth(70)
        self.replace_btn.clicked.connect(self.open_replace_dialog)
        self.insert_field_btn = QPushButton("Вставить поле")
        self.insert_field_btn.setFixedWidth(110)
        self.insert_field_btn.clicked.connect(self.insert_field_name)
        self.add_cte_selects_btn = QPushButton("SELECT для CTE")
        self.add_cte_selects_btn.setFixedWidth(120)
        self.add_cte_selects_btn.clicked.connect(self.add_cte_selects)
        self.query_constructor_btn = QPushButton("Конструктор запросов")
        self.query_constructor_btn.setFixedWidth(150)
        self.query_constructor_btn.clicked.connect(self.open_query_constructor)
        sql_toolbar.addWidget(self.find_btn)
        sql_toolbar.addWidget(self.replace_btn)
        sql_toolbar.addWidget(self.insert_field_btn)
        sql_toolbar.addWidget(self.add_cte_selects_btn)
        sql_toolbar.addWidget(self.query_constructor_btn)
        sql_toolbar.addStretch()
        
        # SQL Editor Settings gear button
        self.sql_settings_btn = QPushButton()
        self.sql_settings_btn.setIcon(QIcon("icons/settings-gear.svg"))
        self.sql_settings_btn.setFixedSize(30, 30)
        self.sql_settings_btn.setToolTip("Настройки редактора SQL")
        self.sql_settings_btn.clicked.connect(self.open_editor_options)
        sql_toolbar.addWidget(self.sql_settings_btn)
        
        layout.addLayout(sql_toolbar)
        # SQL editor and task numbers side by side
        sql_task_layout = QHBoxLayout()
        sql_editor_layout = QVBoxLayout()
        self.label = QLabel("Введите SQL-запрос:")
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
        sql_editor_layout.addWidget(self.sql_edit)
        self.apply_editor_settings()
        sql_task_layout.addLayout(sql_editor_layout, 7)
        # Task numbers multi-line
        task_layout = QVBoxLayout()
        task_layout.addWidget(QLabel("Task numbers:"))
        self.task_numbers_edit = QTextEdit()
        self.task_numbers_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        task_layout.addWidget(self.task_numbers_edit)
        sql_task_layout.addLayout(task_layout, 1)
        layout.addLayout(sql_task_layout)
        self.setLayout(layout)
        self.query_tree_dialog = None
        self.results_dialog = None
        self.results_selector = QComboBox()
        self.results_table = QTableWidget()
        self.records_label = QLabel("")
        self.export_excel_btn = QPushButton()
        self.export_csv_btn = QPushButton()
        self.copy_btn = QPushButton()
        self.to_table_btn = QPushButton()
        self.status_label = QLabel()
        self._all_results = []
        self._current_result_idx = 0
        self._watcher = None
        self._watched_file = None
        self._editor_proc = None
        self._query_dirty = False
        self.sql_edit.textChanged.connect(self.mark_query_dirty)
        self.task_numbers_edit.textChanged.connect(self.mark_query_dirty)
        # --- Контекстное меню редактора ---
        self.sql_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sql_edit.customContextMenuRequested.connect(self.show_sql_context_menu)
        # --- F7 hotkey ---
        self.sql_edit.installEventFilter(self)

    def set_status(self, msg, color="#005500"):
        self.status_label.setText(msg)
        self.status_label.setStyleSheet(f"color: {color}; padding: 2px;")

    def set_connection(self, conn):
        self.conn = conn

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []
        else:
            self.history = []

    def save_history(self):
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.set_status(f"Не удалось сохранить историю: {e}", color="#aa0000")

    def update_history_tree(self):
        if self.query_tree_dialog:
            self.query_tree_dialog.update_history_tree()

    def on_history_selected(self, history_tree):
        if self._query_dirty:
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(self, 'Сохранить изменения?', 'Сохранить изменения в текущем запросе?', QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_query_to_history()
            elif reply == QMessageBox.Cancel:
                # Оставить всё как есть, не менять выбор
                # Программно сбросить выделение
                history_tree.blockSignals(True)
                if self.current_group_idx >= 0 and self.current_query_idx >= 0:
                    group_item = history_tree.topLevelItem(self.current_group_idx)
                    if group_item and group_item.childCount() > self.current_query_idx:
                        history_tree.setCurrentItem(group_item.child(self.current_query_idx))
                history_tree.blockSignals(False)
                return
            # Если No — просто продолжаем, не сохраняем
        item = history_tree.currentItem()
        if not item:
            return
        parent = item.parent()
        if parent:  # Query selected
            group_idx = history_tree.indexOfTopLevelItem(parent)
            query_idx = parent.indexOfChild(item)
            self.current_group_idx = group_idx
            self.current_query_idx = query_idx
            query = self.history[group_idx]['queries'][query_idx]
            self.sql_edit.setText(query.get('query', ''))
            self.task_numbers_edit.setPlainText(query.get('task_numbers', ''))
            self.query_params = query.get('params', {'task_numbers': ''}).copy()
        else:  # Group selected
            self.current_group_idx = history_tree.indexOfTopLevelItem(item)
            self.current_query_idx = -1
            group = self.history[self.current_group_idx]
            self.sql_edit.setText(group.get('query', ''))
            self.task_numbers_edit.setPlainText(group.get('task_numbers', ''))
            self.query_params = group.get('params', {'task_numbers': ''}).copy()
        self._query_dirty = False

    def save_current_history(self):
        if self.current_group_idx >= 0:
            if self.current_query_idx >= 0:
                query = {
                    'query': self.sql_edit.text(),
                    'task_numbers': self.task_numbers_edit.toPlainText(),
                    'params': self.query_params.copy()
                }
                self.history[self.current_group_idx]['queries'][self.current_query_idx] = query
                self.save_history()
                self.update_history_tree()
                self.set_status("Текущий элемент истории обновлен.", color="#005500")
            else:
                # Save group fields
                group = self.history[self.current_group_idx]
                group['query'] = self.sql_edit.text()
                group['task_numbers'] = self.task_numbers_edit.toPlainText()
                group['params'] = self.query_params.copy()
                self.save_history()
                self.update_history_tree()
                self.set_status("Группа обновлена.", color="#005500")

    def delete_current_history(self):
        if self.current_group_idx >= 0 and self.current_query_idx >= 0:
            del self.history[self.current_group_idx]['queries'][self.current_query_idx]
            if not self.history[self.current_group_idx]['queries']:
                del self.history[self.current_group_idx]
                self.current_group_idx = -1
                self.current_query_idx = -1
            self.save_history()
            self.update_history_tree()
            self.set_status("Элемент истории удален.", color="#005500")

    def add_new_group(self):
        name, ok = QInputDialog.getText(self, "Новая группа", "Имя группы:")
        if ok and name:
            self.history.append({'name': name, 'query': '', 'task_numbers': '', 'params': {}, 'queries': []})
            self.save_history()
            self.update_history_tree()
            self.set_status(f"Группа '{name}' добавлена.", color="#005500")

    def add_new_query_to_group(self):
        if self.current_group_idx < 0 or self.current_group_idx >= len(self.history):
            self.set_status("Сначала выберите группу для добавления запроса.", color="#aa0000")
            return
        query = {
            'query': self.sql_edit.text(),
            'task_numbers': self.task_numbers_edit.toPlainText(),
            'params': self.query_params.copy()
        }
        self.history[self.current_group_idx]['queries'].append(query)
        self.save_history()
        self.update_history_tree()
        self.set_status("Запрос добавлен в выбранную группу.", color="#005500")

    def eventFilter(self, obj, event):
        if obj == self.sql_edit and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_F7:
                self.execute_query()
                return True
            # --- Toggle comment Ctrl+/ ---
            if event.key() == Qt.Key_Slash and event.modifiers() == Qt.ControlModifier:
                self.toggle_line_comment()
                return True
            # --- Toggle | Ctrl+\ ---
            if event.key() == Qt.Key_Backslash and event.modifiers() == Qt.ControlModifier:
                self.toggle_pipe_string()
                return True
        return super().eventFilter(obj, event)

    def toggle_line_comment(self):
        # Получить выделение
        editor = self.sql_edit
        start_line, start_index, end_line, end_index = editor.getSelection() if editor.hasSelectedText() else (*editor.getCursorPosition(), *editor.getCursorPosition())
        if start_line > end_line:
            start_line, end_line = end_line, start_line
        # Определить, все ли строки уже закомментированы
        all_commented = True
        for line in range(start_line, end_line + 1):
            text = editor.text(line).lstrip()
            if not text.startswith('--'):
                all_commented = False
                break
        # Комментировать или раскомментировать
        for line in range(start_line, end_line + 1):
            orig = editor.text(line)
            if all_commented:
                # Удалить --
                idx = orig.find('--')
                if idx != -1:
                    new = orig[:idx] + orig[idx+2:]
                    editor.setSelection(line, 0, line, len(orig))
                    editor.replaceSelectedText(new.lstrip())
            else:
                # Добавить --
                editor.setSelection(line, 0, line, 0)
                editor.insert('--')
        # Сбросить выделение
        editor.setSelection(start_line, 0, end_line, len(editor.text(end_line)))

    def toggle_pipe_string(self):
        editor = self.sql_edit
        # Получить выделение
        if editor.hasSelectedText():
            start_line, _, end_line, _ = editor.getSelection()
        else:
            start_line, _ = editor.getCursorPosition()
            end_line = start_line
        if start_line > end_line:
            start_line, end_line = end_line, start_line
        # Определить, все ли строки уже начинаются с |
        all_piped = True
        for line in range(start_line, end_line + 1):
            text = editor.text(line)
            if not text.lstrip().startswith('|'):
                all_piped = False
                break
        for line in range(start_line, end_line + 1):
            orig = editor.text(line)
            leading_ws = len(orig) - len(orig.lstrip())
            if all_piped:
                # Удалить | и заменить "" на "
                lstr = orig.lstrip()
                if lstr.startswith('|'):
                    new = orig[:leading_ws] + lstr[1:].replace('""', '"')
                    editor.setSelection(line, 0, line, len(orig))
                    editor.replaceSelectedText(new)
            else:
                # Добавить | и заменить " на ""
                lstr = orig.lstrip()
                new = orig[:leading_ws] + '|' + lstr.replace('"', '""')
                editor.setSelection(line, 0, line, len(orig))
                editor.replaceSelectedText(new)
        # Сбросить выделение
        editor.setSelection(start_line, 0, end_line, len(editor.text(end_line)))

    def update_history_tree(self):
        if self.query_tree_dialog:
            self.query_tree_dialog.update_history_tree()

    def rename_selected_history_item(self):
        item = self.history_tree.currentItem()
        if item:
            self.history_tree.editItem(item, 0 if not item.parent() else 1)

    def on_history_item_changed(self, item, column):
        history_tree = self.query_tree_dialog.history_tree if self.query_tree_dialog else None
        if not history_tree:
            return
        parent = item.parent()
        if parent:  # Query renamed
            group_idx = history_tree.indexOfTopLevelItem(parent)
            query_idx = parent.indexOfChild(item)
            if 0 <= group_idx < len(self.history) and 0 <= query_idx < len(self.history[group_idx]['queries']):
                # Only update label for display, not the SQL itself
                pass
        else:  # Group renamed
            group_idx = history_tree.indexOfTopLevelItem(item)
            if 0 <= group_idx < len(self.history):
                self.history[group_idx]['name'] = item.text(0)
                self.save_history()

    def dropEvent(self, event):
        # After drag-and-drop, update the history data structure
        super(QTreeWidget, self.history_tree).dropEvent(event)
        self.sync_history_from_tree()
        self.save_history()

    def sync_history_from_tree(self):
        # Rebuild self.history from the current tree structure
        new_history = []
        for i in range(self.history_tree.topLevelItemCount()):
            group_item = self.history_tree.topLevelItem(i)
            group_name = group_item.text(0)
            queries = []
            for j in range(group_item.childCount()):
                # Find the original query dict by label (could be improved)
                label = group_item.child(j).text(1)
                # Try to find matching query in old history
                found = None
                for q in self.history[i]['queries'] if i < len(self.history) else []:
                    qlabel = q.get('query', '').strip().replace('\n', ' ')[:40]
                    if q.get('task_numbers'):
                        qlabel += f" [{q['task_numbers']}]"
                    if qlabel == label:
                        found = q
                        break
                if found:
                    queries.append(found)
                else:
                    # If not found, create a minimal query dict
                    queries.append({'query': '', 'task_numbers': '', 'params': {}})
            new_history.append({'name': group_name, 'query': '', 'task_numbers': '', 'params': {}, 'queries': queries})
        self.history = new_history

    def execute_query(self):
        # Сохраняем запрос в историю перед выполнением
        self.save_query_to_history()
        # Показываем окно результатов всегда при попытке выполнить запрос
        if self.results_dialog is None:
            self.results_dialog = ResultsDialog(self)
        self.results_dialog.update_results_view()
        self.results_dialog.show()
        self.results_dialog.raise_()
        self.results_dialog.activateWindow()
        # Проверка подключения к базе данных
        if not self.conn:
            try:
                import sqlite3
                self.conn = sqlite3.connect(':memory:')
                self.set_status("Создано временное подключение к базе данных (in-memory)", color="#ffaa00")
                if self.results_dialog:
                    self.results_dialog.status_label.setText("Создано временное подключение к базе данных (in-memory)")
                    self.results_dialog.status_label.setStyleSheet("color: #ffaa00; padding: 2px;")
            except Exception as e:
                self.set_status("Не удалось создать подключение к базе данных.", color="#aa0000")
                if self.results_dialog:
                    self.results_dialog.status_label.setText("Не удалось создать подключение к базе данных.")
                    self.results_dialog.status_label.setStyleSheet("color: #aa0000; padding: 2px;")
                return
        query = self.get_query_with_params().strip()
        print("[SQL EXECUTE]", query)
        if not query:
            self.set_status("Введите SQL-запрос.", color="#aa0000")
            return
        try:
            cursor = self.conn.cursor()
            statements = [q.strip() for q in query.split(';') if q.strip()]
            self._all_results = []
            for stmt in statements:
                cursor.execute(stmt)
                if stmt.lower().startswith("select"):
                    rows = cursor.fetchall()
                    headers = [desc[0] for desc in cursor.description]
                    self._all_results.append((headers, rows))
                else:
                    self.conn.commit()
            if self._all_results:
                self.results_selector.clear()
                for i, (headers, rows) in enumerate(self._all_results):
                    self.results_selector.addItem(f"Результат {i+1}")
                self.results_selector.setCurrentIndex(0)
                self.results_selector.setVisible(len(self._all_results) > 1)
                self.show_selected_result(0)
                if len(self._all_results) == 1:
                    self.set_status("Выполнен только один SELECT. Для просмотра промежуточных результатов добавьте отдельные SELECT.", color="#aa0000")
            else:
                self.results_selector.hide()
                self.results_table.clear()
                self.records_label.setText("")
            # Статус теперь обновляется в show_selected_result
            if self.results_dialog is not None:
                self.results_dialog.update_results_view()
        except Exception as e:
            self.set_status(f"Ошибка выполнения запроса: {e}", color="#aa0000")

    def on_result_selection(self, idx):
        self.show_selected_result(idx)

    def show_selected_result(self, idx):
        if 0 <= idx < len(self._all_results):
            headers, rows = self._all_results[idx]
            self.display_results(headers, rows)
            self.records_label.setText(f"Записей: {len(rows)}")
            self.set_status(f"Результат: {len(rows)} строк", color="#005500" if rows else "#aa0000")
            if self.results_dialog is not None:
                self.results_dialog.update_results_view()
        else:
            self.results_table.clear()
            self.records_label.setText("")
            self.set_status("Результат: 0 строк", color="#aa0000")
            if self.results_dialog is not None:
                self.results_dialog.update_results_view()

    def display_results(self, headers, rows):
        self.results_table.clear()
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        self.results_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.results_table.setItem(i, j, QTableWidgetItem(str(val)))
        if self.results_dialog is not None:
            self.results_dialog.update_results_view()

    def get_current_results(self):
        headers = [self.results_table.horizontalHeaderItem(i).text() for i in range(self.results_table.columnCount())]
        data = []
        for row in range(self.results_table.rowCount()):
            data.append([
                self.results_table.item(row, col).text() if self.results_table.item(row, col) else ''
                for col in range(self.results_table.columnCount())
            ])
        return headers, data

    def export_to_excel(self):
        headers, data = self.get_current_results()
        if not headers or not data:
            self.set_status("Нет данных для экспорта.", color="#aa0000")
            return
        dialog = ColumnSelectDialog(headers, headers, self)
        if dialog.exec_() != dialog.Accepted or not dialog.selected_columns:
            return
        selected_indices = [headers.index(col) for col in dialog.selected_columns]
        export_headers = pd.Index([str(headers[i]) for i in selected_indices])
        export_data = [[str(row[i]) for i in selected_indices] for row in data]
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить как Excel", "", "Excel Files (*.xlsx)")
        if file_path:
            try:
                df = pd.DataFrame(export_data, columns=export_headers)
                df.to_excel(file_path, index=False)
                self.set_status(f"Данные экспортированы в {file_path}", color="#005500")
            except Exception as e:
                self.set_status(f"Ошибка экспорта: {e}", color="#aa0000")

    def export_to_csv(self):
        headers, data = self.get_current_results()
        if not headers or not data:
            self.set_status("Нет данных для экспорта.", color="#aa0000")
            return
        dialog = ColumnSelectDialog(headers, headers, self)
        if dialog.exec_() != dialog.Accepted or not dialog.selected_columns:
            return
        selected_indices = [headers.index(col) for col in dialog.selected_columns]
        export_headers = [str(headers[i]) for i in selected_indices]
        export_data = [[str(row[i]) for i in selected_indices] for row in data]
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить как CSV", "", "CSV Files (*.csv)")
        if file_path:
            import csv
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(export_headers)
                    writer.writerows(export_data)
                self.set_status(f"Данные экспортированы в {file_path}", color="#005500")
            except Exception as e:
                self.set_status(f"Ошибка экспорта: {e}", color="#aa0000")

    def copy_to_clipboard(self):
        headers, data = self.get_current_results()
        if not headers or not data:
            self.set_status("Нет данных для копирования.", color="#aa0000")
            return
        lines = ['\t'.join(headers)]
        for row in data:
            lines.append('\t'.join(row))
        text = '\n'.join(lines)
        clipboard = QApplication.instance().clipboard()
        clipboard.setText(text)
        self.set_status("Данные скопированы в буфер обмена.", color="#005500")

    def open_editor_options(self):
        dlg = EditorOptionsDialog(self, self.editor_settings)
        if dlg.exec_() == QDialog.Accepted:
            self.editor_settings = dlg.get_settings()
            self.save_editor_settings()
            self.apply_editor_settings()

    def apply_editor_settings(self):
        font = QFont(self.editor_settings.get('font_family', 'Consolas'), self.editor_settings.get('font_size', 12))
        self.sql_edit.setFont(font)
        self.sql_edit.setMarginsFont(font)
        lexer = self.sql_edit.lexer()
        if lexer:
            lexer.setFont(font)
        # Color scheme
        if self.editor_settings.get('color_scheme', 'light') == 'dark':
            self.sql_edit.setPaper(Qt.black)
            self.sql_edit.setColor(Qt.white)
            if lexer:
                lexer.setDefaultPaper(Qt.black)
                lexer.setDefaultColor(Qt.white)
        else:
            self.sql_edit.setPaper(Qt.white)
            self.sql_edit.setColor(Qt.black)
            if lexer:
                lexer.setDefaultPaper(Qt.white)
                lexer.setDefaultColor(Qt.black)

    def save_editor_settings(self):
        try:
            with open(EDITOR_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.editor_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.set_status(f"Ошибка сохранения настроек редактора: {e}", color="#aa0000")

    def load_editor_settings(self):
        if os.path.exists(EDITOR_SETTINGS_FILE):
            try:
                with open(EDITOR_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def edit_query_params(self):
        dlg = ParamsDialog(self.query_params, self)
        if dlg.exec_() == QDialog.Accepted:
            self.query_params = dlg.get_params()
            self.set_status("Параметры запроса обновлены.", color="#005500")

    def show_query_preview(self):
        preview = self.get_query_with_params()
        dlg = QueryPreviewDialog(preview, self)
        dlg.exec_()

    def get_query_with_params(self):
        query = self.sql_edit.text()
        params = self.query_params.copy()
        # Always sync 'task_numbers' param with the field
        params['task_numbers'] = self.task_numbers_edit.toPlainText().replace('\n', ',')
        for key, value in params.items():
            query = query.replace(f'{{{key}}}', value)
        return query

    def open_find_dialog(self):
        text, ok = QInputDialog.getText(self, "Поиск", "Найти:")
        if ok and text:
            self.sql_edit.findFirst(text, False, False, False, True)

    def open_replace_dialog(self):
        find_text, ok1 = QInputDialog.getText(self, "Замена", "Найти:")
        if not ok1 or not find_text:
            return
        replace_text, ok2 = QInputDialog.getText(self, "Замена", "Заменить на:")
        if not ok2:
            return
        # Replace all occurrences in the editor
        self.sql_edit.setSelection(0, 0, 0, 0)
        while self.sql_edit.findFirst(find_text, False, False, False, True):
            self.sql_edit.replace(replace_text)

    def insert_field_name(self):
        if not self.conn:
            self.set_status("Нет подключения к базе данных.", color="#aa0000")
            # return
        
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        
        if not tables:
            self.set_status("В базе данных нет таблиц.", color="#aa0000")
            return

        menu = QMenu(self)
        for table_name in tables:
            table_menu = menu.addMenu(table_name)
            try:
                cur.execute(f'PRAGMA table_info("{table_name}")')
                columns = [row[1] for row in cur.fetchall()]
                for col in columns:
                    action = table_menu.addAction(col)
                    action.triggered.connect(lambda checked, t=table_name, c=col: self._insert_text_at_cursor(f'"{t}"."{c}"'))
            except Exception as e:
                print(f'Error fetching columns for table {table_name}: {e}')

        menu.exec_(self.insert_field_btn.mapToGlobal(self.insert_field_btn.rect().bottomLeft()))

    def _insert_text_at_cursor(self, text):
        pos = self.sql_edit.getCursorPosition()
        self.sql_edit.insert(text)
        self.sql_edit.setCursorPosition(pos[0], pos[1] + len(text))

    def add_cte_selects(self):
        sql = self.sql_edit.text()
        cte_names = []
        # Поиск WITH ... AS ( ... ), ...
        with_match = re.search(r'with\s+(.+?)\s+select', sql, re.IGNORECASE | re.DOTALL)
        if with_match:
            cte_defs = with_match.group(1)
            # Разбиваем по запятым вне скобок
            depth = 0
            name = ''
            for i, ch in enumerate(cte_defs):
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                elif ch == ',' and depth == 0:
                    if name:
                        cte_names.append(name.strip().split()[0])
                        name = ''
                    continue
                name += ch
            if name:
                cte_names.append(name.strip().split()[0])
        if cte_names:
            to_add = '\n'.join([f'SELECT * FROM {n};' for n in cte_names])
            self.sql_edit.append(f'\n-- SELECT для отладки CTE:\n{to_add}\n')
            self.set_status(f"Добавлены SELECT для: {', '.join(cte_names)}", color="#005500")
        else:
            self.set_status("CTE не найдены в текущем запросе.", color="#aa0000")

    def place_results_to_table(self):
        # Помещает содержимое results_table в sqlite-таблицу 'tt1' и активирует MainWindow
        if not self.conn:
            self.set_status("Нет подключения к базе данных.", color="#aa0000")
            return
        headers = [self.results_table.horizontalHeaderItem(i).text() if self.results_table.horizontalHeaderItem(i) else f"col{i+1}" for i in range(self.results_table.columnCount())]
        data = []
        for row in range(self.results_table.rowCount()):
            data.append([
                self.results_table.item(row, col).text() if self.results_table.item(row, col) else ''
                for col in range(self.results_table.columnCount())
            ])
        if not headers or not data:
            self.set_status("Нет данных для помещения в таблицу.", color="#aa0000")
            return
        try:
            cur = self.conn.cursor()
            cur.execute('DROP TABLE IF EXISTS tt1')
            col_defs = ', '.join([f'"{h}" TEXT' for h in headers])
            cur.execute(f'CREATE TABLE tt1 ({col_defs})')
            placeholders = ','.join(['?'] * len(headers))
            cur.executemany(f'INSERT INTO tt1 VALUES ({placeholders})', data)
            self.conn.commit()
            self.set_status("Результаты помещены в таблицу tt1", color="#005500")
            # Активировать MainWindow и показать tt1
            mw = self.get_mainwindow()
            if mw:
                mw.update_table_selector()
                idx = mw.table_selector.findText('tt1')
                if idx != -1:
                    mw.table_selector.setCurrentIndex(idx)
                mw.raise_()
                mw.activateWindow()
        except Exception as e:
            self.set_status(f"Ошибка помещения в таблицу: {e}", color="#aa0000")

    def get_mainwindow(self):
        # Поиск главного окна приложения
        for widget in QApplication.topLevelWidgets():
            if widget.__class__.__name__ == 'MainWindow':
                return widget
        return None 

    def open_history_dialog(self):
        if not hasattr(self, 'query_tree_dialog') or self.query_tree_dialog is None:
            self.query_tree_dialog = QueryTreeDialog(self)
        self.query_tree_dialog.update_history_tree()
        self.query_tree_dialog.show()
        self.query_tree_dialog.raise_()
        self.query_tree_dialog.activateWindow() 

    def open_results_dialog(self):
        if self.results_dialog is None:
            self.results_dialog = ResultsDialog(self)
        self.results_dialog.update_results_view()
        self.results_dialog.show()
        self.results_dialog.raise_()
        self.results_dialog.activateWindow()

    def open_query_constructor(self):
        """Open the SQL Query Constructor dialog"""
        if not self.conn:
            self.set_status("Нет подключения к базе данных. Сначала загрузите таблицы.", color="#aa0000")
            return
        
        constructor_dialog = SQLQueryConstructorDialog(self.conn, self)
        constructor_dialog.query_generated.connect(self.on_query_generated)
        constructor_dialog.exec_()
    
    def on_query_generated(self, query):
        """Handle the generated query from the constructor"""
        self.sql_edit.setText(query)
        self.set_status("Запрос сгенерирован конструктором", color="#005500") 

    def show_sql_context_menu(self, pos):
        menu = self.sql_edit.createStandardContextMenu()
        generate_menu = QMenu('Генерировать', menu)
        gen_select_action = generate_menu.addAction('Выборка с заданным порядком колонок')
        gen_select_action.triggered.connect(self.generate_select_with_column_order)
        menu.addMenu(generate_menu)
        # --- Следить за изменениями ---
        watch_action = QAction('Следить за изменениями', self)
        watch_action.triggered.connect(self.watch_external_edit)
        menu.addAction(watch_action)
        menu.exec_(self.sql_edit.mapToGlobal(pos))

    def generate_select_with_column_order(self):
        # 1. Получить имя текущей таблицы (например, из соединения или по умолчанию 'data')
        table_name = self.get_current_table_name_for_generation()
        if not table_name:
            self.set_status('Не удалось определить имя таблицы для генерации SELECT.', color='#aa0000')
            return
        # 2. Получить список колонок из БД
        try:
            cur = self.conn.cursor()
            cur.execute(f'PRAGMA table_info("{table_name}")')
            columns = [row[1] for row in cur.fetchall()]
        except Exception:
            columns = []
        if not columns:
            self.set_status('Нет данных о колонках таблицы.', color='#aa0000')
            return
        # 3. Открыть диалог для ColumnsOrder и выбора разделителя
        dlg = ColumnsOrderDialog(columns, self)
        if dlg.exec_() != dlg.Accepted:
            return
        order, delimiter = dlg.get_order_and_delimiter()
        # 4. Сгенерировать SELECT
        select_lines = []
        for col in order:
            if col in columns:
                select_lines.append(col)
        commented = [col for col in columns if col not in order]
        for col in commented:
            select_lines.append(f'-- {col}')
        sep = delimiter
        if sep == '<CR>':
            sep = '\n'
        elif sep == 'tab':
            sep = '\t'
        select_expr = (sep + ', ').join(select_lines)
        query = f'SELECT {sep.join(select_lines)}\nFROM {table_name};'
        self.sql_edit.setText(query)

    def get_current_table_name_for_generation(self):
        # Попробовать получить имя таблицы из соединения или по умолчанию
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 1")
            row = cur.fetchone()
            if row:
                return row[0]
        except Exception:
            pass
        return 'data'

    def watch_external_edit(self):
        # Сохраняем текст во временный файл
        if self._watched_file is None:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.sql', mode='w', encoding='utf-8')
            tmp.write(self.sql_edit.text())
            tmp.close()
            self._watched_file = tmp.name
        else:
            with open(self._watched_file, 'w', encoding='utf-8') as f:
                f.write(self.sql_edit.text())
        # Запускаем внешний редактор
        editor_path = self.editor_settings.get('editor_path', 'code')
        self._editor_proc = QProcess(self)
        started = self._editor_proc.startDetached(editor_path, [self._watched_file])
        if not started:
            # Попробовать найти code.exe в стандартных путях
            possible_paths = [
                os.path.expandvars(r'%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\Code.exe'),
                os.path.expandvars(r'%ProgramFiles%\\Microsoft VS Code\\Code.exe'),
                os.path.expandvars(r'%ProgramFiles(x86)%\\Microsoft VS Code\\Code.exe'),
            ]
            found = None
            for path in possible_paths:
                if os.path.exists(path):
                    found = path
                    break
            if found:
                started = self._editor_proc.startDetached(found, [self._watched_file])
                if started:
                    self.set_status(f'VSCode найден и запущен: {found}', color='#005599')
                else:
                    QMessageBox.warning(self, 'Ошибка', f'Не удалось запустить редактор: {found}')
            else:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось запустить VSCode. Укажите путь к редактору в настройках.')
        # Слежение за изменениями
        if self._watcher is None:
            self._watcher = QFileSystemWatcher(self)
            self._watcher.fileChanged.connect(self.on_watched_file_changed)
        self._watcher.addPath(self._watched_file)
        self.set_status(f'Следим за {self._watched_file}', color='#005599')

    def on_watched_file_changed(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            self.sql_edit.setText(text)
            self.set_status('Текст запроса обновлен из внешнего редактора.', color='#005599')
        except Exception as e:
            self.set_status(f'Ошибка чтения файла: {e}', color='#aa0000')

    def mark_query_dirty(self):
        self._query_dirty = True

    def save_query_to_history(self):
        query = self.sql_edit.text()
        task_numbers = self.task_numbers_edit.toPlainText()
        params = self.query_params.copy()
        if self.current_group_idx >= 0:
            if self.current_query_idx >= 0:
                self.history[self.current_group_idx]['queries'][self.current_query_idx] = {
                    'query': query,
                    'task_numbers': task_numbers,
                    'params': params
                }
            else:
                self.history[self.current_group_idx]['queries'].append({
                    'query': query,
                    'task_numbers': task_numbers,
                    'params': params
                })
                self.current_query_idx = len(self.history[self.current_group_idx]['queries']) - 1
        else:
            self.history.append({'name': 'Группа 1', 'query': '', 'task_numbers': '', 'params': {}, 'queries': [
                {'query': query, 'task_numbers': task_numbers, 'params': params}
            ]})
            self.current_group_idx = len(self.history) - 1
            self.current_query_idx = 0
        self.save_history()
        if self.query_tree_dialog:
            self.query_tree_dialog.update_history_tree()
        self._query_dirty = False

# --- Диалог для ColumnsOrder и выбора разделителя ---
class ColumnsOrderDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Порядок колонок и разделитель')
        self.resize(400, 150)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Порядок колонок (через разделитель):'))
        self.order_edit = QLineEdit(','.join(columns))
        layout.addWidget(self.order_edit)
        layout.addWidget(QLabel('Разделитель:'))
        self.delim_combo = QComboBox()
        self.delim_combo.addItems(['tab', '<CR>', ',', ';', 'Свой символ...'])
        layout.addWidget(self.delim_combo)
        self.custom_delim_edit = QLineEdit()
        self.custom_delim_edit.setPlaceholderText('Введите свой символ')
        self.custom_delim_edit.setEnabled(False)
        layout.addWidget(self.custom_delim_edit)
        self.delim_combo.currentIndexChanged.connect(self.on_delim_changed)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
    def on_delim_changed(self, idx):
        self.custom_delim_edit.setEnabled(self.delim_combo.currentText() == 'Свой символ...')
    def get_order_and_delimiter(self):
        order = [s.strip() for s in self.order_edit.text().split(',') if s.strip()]
        delim = self.delim_combo.currentText()
        if delim == 'Свой символ...':
            delim = self.custom_delim_edit.text() or ','
        return order, delim