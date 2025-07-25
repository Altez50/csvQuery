from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QPushButton, QLineEdit, QFileDialog, QInputDialog
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QIcon
import json
import os

class QueryTreeDialog(QDialog):
    def __init__(self, sql_query_page):
        super().__init__(sql_query_page)     #super().__init__(parent)
        self.setWindowTitle('Дерево запросов')
        self.setMinimumWidth(500)
        self.sql_query_page = sql_query_page
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
        self.search_edit.setPlaceholderText('Поиск по дереву запросов...')
        self.search_edit.textChanged.connect(self.filter_history)
        layout.addWidget(self.search_edit)
        tree_layout = QHBoxLayout()
        # tree_layout.addWidget(QLabel("Дерево запросов:"))
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["Группа", "Запрос"])
        self.history_tree.setColumnCount(2)
        self.history_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.history_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.history_tree.setDefaultDropAction(Qt.MoveAction)
        self.history_tree.setDragEnabled(True)
        self.history_tree.setAcceptDrops(True)
        self.history_tree.setDropIndicatorShown(True)
        self.history_tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.history_tree.itemChanged.connect(self.sql_query_page.on_history_item_changed)
        self.history_tree.installEventFilter(self)
        tree_layout.addWidget(self.history_tree, 1)
        layout.addLayout(tree_layout)
        self.setLayout(layout)
        self.update_history_tree()
        self._settings = QSettings('csvQuery', 'QueryTreeDialog')
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
    def update_history_tree(self):
        self.history_tree.blockSignals(True)
        self.history_tree.clear()
        for group_idx, group in enumerate(self.sql_query_page.history):
            group_item = QTreeWidgetItem([group.get('name', ''), ''])
            group_item.setFlags(group_item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
            for q_idx, query in enumerate(group.get('queries', [])):
                label = query.get('query', '').strip().replace('\n', ' ')[:40]
                if query.get('task_numbers'):
                    label += f" [{query['task_numbers']}]"
                query_item = QTreeWidgetItem(['', label])
                query_item.setFlags(query_item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled)
                group_item.addChild(query_item)
            self.history_tree.addTopLevelItem(group_item)
        self.history_tree.expandAll()
        self.history_tree.blockSignals(False)
    def filter_history(self, text):
        for i in range(self.history_tree.topLevelItemCount()):
            group_item = self.history_tree.topLevelItem(i)
            group_visible = False
            for j in range(group_item.childCount()):
                query_item = group_item.child(j)
                visible = text.lower() in query_item.text(1).lower()
                query_item.setHidden(not visible)
                if visible:
                    group_visible = True
            group_item.setHidden(not group_visible)
    def eventFilter(self, obj, event):
        if obj == self.history_tree and event.type() == event.KeyPress:
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
        self.sql_query_page.history.append({'name': name, 'query': '', 'task_numbers': '', 'params': {}, 'queries': []})
        self.sql_query_page.save_history()
        self.update_history_tree()
    def delete_selected(self):
        item = self.history_tree.currentItem()
        if not item:
            return
        parent = item.parent()
        if parent:
            group_idx = self.history_tree.indexOfTopLevelItem(parent)
            query_idx = parent.indexOfChild(item)
            del self.sql_query_page.history[group_idx]['queries'][query_idx]
            if not self.sql_query_page.history[group_idx]['queries']:
                del self.sql_query_page.history[group_idx]
        else:
            group_idx = self.history_tree.indexOfTopLevelItem(item)
            del self.sql_query_page.history[group_idx]
        self.sql_query_page.save_history()
        self.update_history_tree()
    def rename_selected(self):
        item = self.history_tree.currentItem()
        if item:
            col = 0 if not item.parent() else 1
            self.history_tree.editItem(item, col)
    def save_tree_to_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить дерево запросов", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.sql_query_page.history, f, ensure_ascii=False, indent=2)
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")
    def load_tree_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Загрузить дерево запросов", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.sql_query_page.history = json.load(f)
                self.sql_query_page.save_history()
                self.update_history_tree()
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {e}")
    def on_tree_selection_changed(self):
        self.sql_query_page.on_history_selected(self.history_tree) 