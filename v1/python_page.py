from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
import json
import os
import traceback
from snippet_tree_dialog import SnippetTreeDialog

SNIPPETS_FILE = 'python_snippets.json'

class PythonPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.snippets = []
        self.current_group_idx = -1
        self.current_snippet_idx = -1
        self.load_snippets()
        
        layout = QVBoxLayout(self)
        
        # --- Toolbar ---
        toolbar = QHBoxLayout()
        self.execute_btn = QPushButton("Выполнить (F5)")
        self.execute_btn.setShortcut('F5')
        self.execute_btn.clicked.connect(self.execute_code)
        toolbar.addWidget(self.execute_btn)
        
        self.open_snippet_tree_btn = QPushButton("Дерево сниппетов...")
        self.open_snippet_tree_btn.clicked.connect(self.open_snippet_dialog)
        toolbar.addWidget(self.open_snippet_tree_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # --- Code Editor ---
        self.hint_label = QLabel(
            '<b>Доступны переменные:</b> results_table, csv_table (QTableWidget), main_window (MainWindow), sql_page (SQLQueryPage)'
        )
        layout.addWidget(self.hint_label)
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
        # self.code_edit.SendScintilla(QsciScintilla.SCI_SETPLACEHOLDER, bytearray(placeholder, 'utf-8'))
        layout.addWidget(self.code_edit)
        
        # --- Bottom panel ---
        bottom_panel = QHBoxLayout()
        bottom_panel.addWidget(QLabel("После выполнения активировать:"))
        self.activation_selector = QComboBox()
        self.activation_selector.addItems(["MainWindow", "SQLQueryPage"])
        bottom_panel.addWidget(self.activation_selector)
        bottom_panel.addStretch()
        layout.addLayout(bottom_panel)
        
        self.output_label = QLabel('')
        self.output_label.setStyleSheet('color: #005500; background: #f0f0f0; padding: 4px;')
        self.output_label.setWordWrap(True)
        layout.addWidget(self.output_label)

        self.snippet_tree_dialog = None

    def load_snippets(self):
        if os.path.exists(SNIPPETS_FILE):
            try:
                with open(SNIPPETS_FILE, 'r', encoding='utf-8') as f:
                    self.snippets = json.load(f)
            except Exception:
                self.snippets = []
        else:
            self.snippets = []

    def save_snippets(self):
        try:
            with open(SNIPPETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.snippets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.output_label.setText(f"Не удалось сохранить сниппеты: {e}")
            self.output_label.setStyleSheet('color: #aa0000;')

    def execute_code(self):
        code = self.code_edit.text()
        local_vars = {
            'main_window': self.main_window,
            'sql_page': self.main_window.sql_tab,
            'results_table': self.main_window.sql_tab.results_table,
            'csv_table': self.main_window.csv_table
        }
        try:
            exec(code, {}, local_vars)
            self.output_label.setText('Код выполнен успешно.')
            self.output_label.setStyleSheet('color: #005500; background: #f0fff0; padding: 4px;')
            
            # Activate window
            target = self.activation_selector.currentText()
            if target == "MainWindow":
                self.main_window.raise_()
                self.main_window.activateWindow()
            elif target == "SQLQueryPage":
                self.main_window.tabs.setCurrentWidget(self.main_window.sql_tab)
                self.main_window.sql_tab.raise_()
                self.main_window.sql_tab.activateWindow()

        except Exception:
            tb = traceback.format_exc()
            self.output_label.setText(f'Ошибка:\n{tb}')
            self.output_label.setStyleSheet('color: #aa0000; background: #fff0f0; padding: 4px;')

    def open_snippet_dialog(self):
        if self.snippet_tree_dialog is None:
            self.snippet_tree_dialog = SnippetTreeDialog(self)
        self.snippet_tree_dialog.update_snippet_tree()
        self.snippet_tree_dialog.show()
        self.snippet_tree_dialog.raise_()
        self.snippet_tree_dialog.activateWindow()

    def on_snippet_selected(self, tree):
        item = tree.currentItem()
        if not item or not item.parent():
            return
        
        group_idx = tree.indexOfTopLevelItem(item.parent())
        snippet_idx = item.parent().indexOfChild(item)

        if 0 <= group_idx < len(self.snippets) and 0 <= snippet_idx < len(self.snippets[group_idx]['snippets']):
            self.current_group_idx = group_idx
            self.current_snippet_idx = snippet_idx
            snippet = self.snippets[group_idx]['snippets'][snippet_idx]
            self.code_edit.setText(snippet.get('code', ''))

    def on_snippet_item_changed(self, item, column):
        if not item: return

        # Определяем, что было изменено: группа или сниппет
        if item.parent(): # Сниппет
            group_idx = self.snippet_tree_dialog.snippet_tree.indexOfTopLevelItem(item.parent())
            snippet_idx = item.parent().indexOfChild(item)
            if column == 1: # Имя/код сниппета
                 # Для простоты, пусть имя будет таким же, как код
                self.snippets[group_idx]['snippets'][snippet_idx]['code'] = item.text(1)
        else: # Группа
            group_idx = self.snippet_tree_dialog.snippet_tree.indexOfTopLevelItem(item)
            if column == 0: # Имя группы
                self.snippets[group_idx]['name'] = item.text(0)
        
        self.save_snippets() 