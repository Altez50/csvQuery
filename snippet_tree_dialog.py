from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QLineEdit, QFileDialog, QInputDialog
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QIcon
import json

class SnippetTreeDialog(QDialog):
    def __init__(self, python_page):
        super().__init__(python_page)
        self.setWindowTitle('Дерево сниппетов')
        self.setMinimumWidth(500)
        self.python_page = python_page
        layout = QVBoxLayout(self)
        # --- Панель инструментов ---
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton()
        self.add_btn.setIcon(QIcon('icons/add.png'))
        self.add_btn.setToolTip('Добавить группу (Insert)')
        self.add_btn.setShortcut('Insert')
        self.add_btn.clicked.connect(self.add_group)
        toolbar.addWidget(self.add_btn)
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon('icons/delete.png'))
        self.delete_btn.setToolTip('Удалить (Delete)')
        self.delete_btn.setShortcut('Delete')
        self.delete_btn.clicked.connect(self.delete_selected)
        toolbar.addWidget(self.delete_btn)
        self.rename_btn = QPushButton()
        self.rename_btn.setIcon(QIcon('icons/edit.png'))
        self.rename_btn.setToolTip('Переименовать (F2)')
        self.rename_btn.setShortcut('F2')
        self.rename_btn.clicked.connect(self.rename_selected)
        toolbar.addWidget(self.rename_btn)
        self.save_btn = QPushButton()
        self.save_btn.setIcon(QIcon('icons/save.png'))
        self.save_btn.setToolTip('Сохранить дерево в файл')
        self.save_btn.clicked.connect(self.save_tree_to_file)
        toolbar.addWidget(self.save_btn)
        self.load_btn = QPushButton()
        self.load_btn.setIcon(QIcon('icons/load.png'))
        self.load_btn.setToolTip('Загрузить дерево из файла')
        self.load_btn.clicked.connect(self.load_tree_from_file)
        toolbar.addWidget(self.load_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        # Поисковое поле
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Поиск по дереву сниппетов...')
        self.search_edit.textChanged.connect(self.filter_snippets)
        layout.addWidget(self.search_edit)
        tree_layout = QHBoxLayout()
        self.snippet_tree = QTreeWidget()
        self.snippet_tree.setHeaderLabels(["Группа", "Сниппет"])
        self.snippet_tree.setColumnCount(2)
        self.snippet_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.snippet_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.snippet_tree.setDefaultDropAction(Qt.MoveAction)
        self.snippet_tree.setDragEnabled(True)
        self.snippet_tree.setAcceptDrops(True)
        self.snippet_tree.setDropIndicatorShown(True)
        self.snippet_tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.snippet_tree.itemChanged.connect(self.python_page.on_snippet_item_changed)
        self.snippet_tree.installEventFilter(self)
        tree_layout.addWidget(self.snippet_tree, 1)
        layout.addLayout(tree_layout)
        self.setLayout(layout)
        self.update_snippet_tree()
        self._settings = QSettings('csvQuery', 'SnippetTreeDialog')
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

    def update_snippet_tree(self):
        self.snippet_tree.blockSignals(True)
        self.snippet_tree.clear()
        for group_idx, group in enumerate(self.python_page.snippets):
            group_item = QTreeWidgetItem([group.get('name', ''), ''])
            group_item.setFlags(group_item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
            for s_idx, snippet in enumerate(group.get('snippets', [])):
                label = snippet.get('code', '').strip().replace('\n', ' ')[:40]
                snippet_item = QTreeWidgetItem(['', label])
                snippet_item.setFlags(snippet_item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled)
                group_item.addChild(snippet_item)
            self.snippet_tree.addTopLevelItem(group_item)
        self.snippet_tree.expandAll()
        self.snippet_tree.blockSignals(False)

    def filter_snippets(self, text):
        for i in range(self.snippet_tree.topLevelItemCount()):
            group_item = self.snippet_tree.topLevelItem(i)
            group_visible = False
            for j in range(group_item.childCount()):
                snippet_item = group_item.child(j)
                visible = text.lower() in snippet_item.text(1).lower()
                snippet_item.setHidden(not visible)
                if visible:
                    group_visible = True
            group_item.setHidden(not group_visible)

    def eventFilter(self, obj, event):
        if obj == self.snippet_tree and event.type() == event.KeyPress:
            if event.key() == Qt.Key_F2:
                self.rename_selected()
                return True
            elif event.key() == Qt.Key_Insert:
                self.add_group()
                return True
            elif event.key() == Qt.Key_Delete:
                self.delete_selected()
                return True
        return super().eventFilter(obj, event)

    def add_group(self):
        name, ok = QInputDialog.getText(self, "Добавить группу", "Имя новой группы:")
        if not ok or not name.strip():
            return
        name = name.strip()
        self.python_page.snippets.append({'name': name, 'snippets': []})
        self.python_page.save_snippets()
        self.update_snippet_tree()

    def delete_selected(self):
        item = self.snippet_tree.currentItem()
        if not item:
            return
        parent = item.parent()
        if parent:
            group_idx = self.snippet_tree.indexOfTopLevelItem(parent)
            snippet_idx = parent.indexOfChild(item)
            del self.python_page.snippets[group_idx]['snippets'][snippet_idx]
            if not self.python_page.snippets[group_idx]['snippets']:
                del self.python_page.snippets[group_idx]
        else:
            group_idx = self.snippet_tree.indexOfTopLevelItem(item)
            del self.python_page.snippets[group_idx]
        self.python_page.save_snippets()
        self.update_snippet_tree()

    def rename_selected(self):
        item = self.snippet_tree.currentItem()
        if item:
            col = 0 if not item.parent() else 1
            self.snippet_tree.editItem(item, col)

    def save_tree_to_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить дерево сниппетов", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.python_page.snippets, f, ensure_ascii=False, indent=2)
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")

    def load_tree_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Загрузить дерево сниппетов", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.python_page.snippets = json.load(f)
                self.python_page.save_snippets()
                self.update_snippet_tree()
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {e}")

    def on_tree_selection_changed(self):
        self.python_page.on_snippet_selected(self.snippet_tree) 