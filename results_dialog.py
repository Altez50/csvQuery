#import sys
import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QComboBox, QPushButton, QFileDialog, QTableWidgetItem, QApplication
from PyQt5.QtCore import Qt, QSettings, QByteArray

class ResultsDialog(QWidget):
    def __init__(self, sql_query_page=None):
        super().__init__()
        self.setWindowTitle('Результаты запроса1')
        self.setMinimumWidth(700)
        self.sql_query_page = sql_query_page
        layout = QVBoxLayout(self)

        self.results_selector = QComboBox()
        self.results_selector.currentIndexChanged.connect(self.on_result_selection) 
        layout.addWidget(self.results_selector)
        self.results_table = QTableWidget()
        layout.addWidget(self.results_table)
        self.records_label = QLabel("")
        layout.addWidget(self.records_label)
        export_layout = QHBoxLayout()
        self.export_excel_btn = QPushButton("Экспорт в Excel")
        self.export_excel_btn.setFixedWidth(120)
        self.export_excel_btn.clicked.connect(self.export_to_excel)
        self.export_csv_btn = QPushButton("Экспорт в CSV")
        self.export_csv_btn.setFixedWidth(120)
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        self.copy_btn = QPushButton("Копировать")
        self.copy_btn.setFixedWidth(100)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.to_table_btn = QPushButton("Поместить в таблицу")
        self.to_table_btn.setFixedWidth(180)
        self.to_table_btn.clicked.connect(self.place_results_to_table)
        export_layout.addWidget(self.export_excel_btn)
        export_layout.addWidget(self.export_csv_btn)
        export_layout.addWidget(self.copy_btn)
        export_layout.addWidget(self.to_table_btn)
        export_layout.addStretch()
        layout.addLayout(export_layout)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #005500; padding: 2px;")
        layout.addWidget(self.status_label)
        self.setLayout(layout)
        self.update_results_view()
        self._settings = QSettings('csvQuery', 'ResultsDialog')
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

    def on_result_selection(self, index):
        if self.sql_query_page:
            self.sql_query_page.on_result_selection(index)

    def export_to_excel(self):
        if self.sql_query_page:
            self.sql_query_page.export_to_excel()

    def export_to_csv(self):
        if self.sql_query_page:
            self.sql_query_page.export_to_csv()

    def copy_to_clipboard(self):
        if self.sql_query_page:
            self.sql_query_page.copy_to_clipboard()

    def place_results_to_table(self):
        if self.sql_query_page:
            self.sql_query_page.place_results_to_table()

    def update_results_view(self):
        self.results_selector.blockSignals(True)
        self.results_selector.clear()
        if hasattr(self.sql_query_page, '_all_results') and self.sql_query_page._all_results:
            self.results_selector.addItems([f"Результат {i+1}" for i in range(len(self.sql_query_page._all_results))])
            self.results_selector.setCurrentIndex(self.sql_query_page._current_result_idx)
        self.results_selector.blockSignals(False)
        if hasattr(self.sql_query_page, 'results_table'):
            self.results_table.setRowCount(self.sql_query_page.results_table.rowCount())
            self.results_table.setColumnCount(self.sql_query_page.results_table.columnCount())
            self.results_table.setHorizontalHeaderLabels([
                self.sql_query_page.results_table.horizontalHeaderItem(i).text() if self.sql_query_page.results_table.horizontalHeaderItem(i) else ''
                for i in range(self.sql_query_page.results_table.columnCount())
            ])
            for i in range(self.sql_query_page.results_table.rowCount()):
                for j in range(self.sql_query_page.results_table.columnCount()):
                    item = self.sql_query_page.results_table.item(i, j)
                    self.results_table.setItem(i, j, QTableWidgetItem(item.text() if item else ''))
        if hasattr(self.sql_query_page, 'records_label'):
            self.records_label.setText(self.sql_query_page.records_label.text())
        if hasattr(self.sql_query_page, 'status_label'):
            self.status_label.setText(self.sql_query_page.status_label.text())
            self.status_label.setStyleSheet(self.sql_query_page.status_label.styleSheet())