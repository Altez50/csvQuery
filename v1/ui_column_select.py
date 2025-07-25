from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QAbstractItemView, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QSettings

class ColumnSelectDialog(QDialog):
    """Dialog for selecting columns to export"""
    def __init__(self, columns, default_columns=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор столбцов для экспорта")
        self.columns = columns
        self.default_columns = default_columns or []
        self.selected_columns = []
        self._settings = QSettings('csvQuery', 'ColumnSelectDialog')
        self.restore_geometry()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget(self)
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        for col in self.columns:
            item = QListWidgetItem(col)
            self.list_widget.addItem(item)
            if col in self.default_columns:
                item.setSelected(True)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.invert_btn = QPushButton("Инвертировать выделение", self)
        self.invert_btn.clicked.connect(self.invert_selection)
        btn_layout.addWidget(self.invert_btn)
        layout.addLayout(btn_layout)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        ok_btn = QPushButton("OK", self)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)

    def invert_selection(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setSelected(not item.isSelected())

    def accept(self):
        self.selected_columns = [self.list_widget.item(i).text() for i in range(self.list_widget.count()) if self.list_widget.item(i).isSelected()]
        super().accept()

    def closeEvent(self, event):
        self.save_geometry()
        super().closeEvent(event)

    def save_geometry(self):
        self._settings.setValue('geometry', self.saveGeometry())

    def restore_geometry(self):
        geom = self._settings.value('geometry')
        if geom:
            self.restoreGeometry(geom) 