from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel
from PyQt5.QtCore import QSettings
import traceback

class PythonExecDialog(QDialog):
    def __init__(self, results_table, csv_table, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Выполнение Python-кода')
        self.resize(700, 500)
        self.results_table = results_table
        self.csv_table = csv_table
        self._settings = QSettings('csvQuery', 'PythonExecDialog')
        layout = QVBoxLayout(self)
        self.code_edit = QTextEdit()
        self.code_edit.setPlaceholderText(
            '# Здесь вы можете писать Python-код.\n'
            '# Доступны переменные: results_table, csv_table (QTableWidget)\n'
            '# Например:\n'
            '# for row in range(results_table.rowCount()):\n'
            '#     print(results_table.item(row, 0).text())\n'
        )
        layout.addWidget(self.code_edit)
        btns = QHBoxLayout()
        self.run_btn = QPushButton('Выполнить')
        self.run_btn.clicked.connect(self.run_code)
        btns.addWidget(self.run_btn)
        btns.addStretch()
        layout.addLayout(btns)
        self.output_label = QLabel('')
        self.output_label.setStyleSheet('color: #005500; background: #f0f0f0; padding: 4px;')
        self.output_label.setWordWrap(True)
        layout.addWidget(self.output_label)
        self.restore_geometry()

    def run_code(self):
        code = self.code_edit.toPlainText()
        local_vars = {'results_table': self.results_table, 'csv_table': self.csv_table}
        try:
            exec(code, {}, local_vars)
            self.output_label.setText('Код выполнен успешно.')
            self.output_label.setStyleSheet('color: #005500; background: #f0fff0; padding: 4px;')
        except Exception as e:
            tb = traceback.format_exc()
            self.output_label.setText(f'Ошибка:\n{tb}')
            self.output_label.setStyleSheet('color: #aa0000; background: #fff0f0; padding: 4px;')

    def closeEvent(self, event):
        self.save_geometry()
        super().closeEvent(event)

    def save_geometry(self):
        self._settings.setValue('geometry', self.saveGeometry())

    def restore_geometry(self):
        geom = self._settings.value('geometry')
        if geom:
            self.restoreGeometry(geom) 