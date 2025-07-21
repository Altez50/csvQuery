from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QFileDialog, QMenu, QAction
import pandas as pd
from PyQt5.QtCore import QSettings

class GroupByDialog(QDialog):
    def __init__(self, group_col, groups, headers, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Группировка по: {group_col}')
        self.resize(800, 600)
        self.groups = groups
        self.headers = headers
        self.group_col = group_col
        layout = QVBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([group_col] + headers)
        self._populate_tree(groups, self.tree, headers)
        self.tree.expandAll()
        layout.addWidget(self.tree)
        # --- Export buttons ---
        btns = QHBoxLayout()
        export_csv_btn = QPushButton('Экспорт в CSV')
        export_csv_btn.clicked.connect(self.export_csv)
        btns.addWidget(export_csv_btn)
        export_excel_btn = QPushButton('Экспорт в Excel')
        export_excel_btn.clicked.connect(self.export_excel)
        btns.addWidget(export_excel_btn)
        btns.addStretch()
        layout.addLayout(btns)
        # --- GroupBy submenu ---
        self.tree.setContextMenuPolicy(3)  # Qt.CustomContextMenu
        self.tree.customContextMenuRequested.connect(self.show_groupby_menu)
        self._settings = QSettings('csvQuery', 'GroupByDialog')
        self.restore_geometry()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ... существующий код ...
        self._settings = QSettings('csvQuery', 'GroupByDialog')
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

    def _populate_tree(self, groups, tree_widget, headers, parent_item=None):
        for group_val, rows in groups.items():
            group_item = QTreeWidgetItem([str(group_val)] + [''] * len(headers))
            for row in rows:
                if isinstance(row, dict) and '__group__' in row:
                    # Вложенная группа
                    self._populate_tree(row['__group__'], tree_widget, headers, group_item)
                else:
                    child = QTreeWidgetItem([''] + [str(cell) for cell in row])
                    group_item.addChild(child)
            if parent_item:
                parent_item.addChild(group_item)
            else:
                tree_widget.addTopLevelItem(group_item)

    def show_groupby_menu(self, pos):
        menu = QMenu(self)
        groupby_menu = menu.addMenu('GroupBy')
        for idx, col in enumerate(self.headers):
            if col == self.group_col:
                continue
            action = QAction(col, self)
            action.triggered.connect(lambda checked, idx=idx: self.nested_groupby(idx))
            groupby_menu.addAction(action)
        menu.exec_(self.tree.viewport().mapToGlobal(pos))

    def nested_groupby(self, col_idx):
        # Для каждой текущей группы сгруппировать по новой колонке
        new_groups = {}
        for group_val, rows in self.groups.items():
            # rows: list of lists (только видимые колонки)
            subgroups = {}
            last_val = None
            for row in rows:
                val = row[col_idx] if col_idx < len(row) and row[col_idx] else last_val
                if not val:
                    val = last_val
                else:
                    last_val = val
                subgroups.setdefault(val, []).append(row)
            # Для вложенности: сохраняем как dict с ключом '__group__'
            new_groups[group_val] = [{"__group__": subgroups}]
        dlg = GroupByDialog(self.headers[col_idx], new_groups, self.headers, self)
        dlg.exec_()

    def export_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить как CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow([self.tree.headerItem().text(i) for i in range(self.tree.columnCount())])
            self._write_tree_to_csv(self.tree, writer)

    def _write_tree_to_csv(self, tree, writer, parent_item=None):
        items = tree.topLevelItemCount() if parent_item is None else parent_item.childCount()
        for i in range(items):
            item = tree.topLevelItem(i) if parent_item is None else parent_item.child(i)
            writer.writerow([item.text(j) for j in range(tree.columnCount())])
            self._write_tree_to_csv(tree, writer, item)

    def export_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить как Excel", "", "Excel Files (*.xlsx)")
        if not file_path:
            return
        rows = []
        rows.append([self.tree.headerItem().text(i) for i in range(self.tree.columnCount())])
        self._collect_tree_rows(self.tree, rows)
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df.to_excel(file_path, index=False)

    def _collect_tree_rows(self, tree, rows, parent_item=None):
        items = tree.topLevelItemCount() if parent_item is None else parent_item.childCount()
        for i in range(items):
            item = tree.topLevelItem(i) if parent_item is None else parent_item.child(i)
            rows.append([item.text(j) for j in range(tree.columnCount())])
            self._collect_tree_rows(tree, rows, item) 