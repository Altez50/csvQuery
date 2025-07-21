import tempfile
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QMessageBox, QInputDialog
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from PyQt5.QtCore import Qt, QSettings
import sqlite3

class TableEditDialog(QDialog):
    def __init__(self, sqlite_conn, table_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Редактирование таблицы: {table_name}')
        self.resize(800, 500)
        self.sqlite_conn = sqlite_conn
        self.table_name = table_name
        self._settings = QSettings('csvQuery', f'TableEditDialog_{table_name}')
        self._modified = False
        # --- Создаём временную файловую БД ---
        self._tmp_dbfile = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        self._tmp_dbfile.close()
        self._tmp_db_path = self._tmp_dbfile.name
        self._copy_table_to_temp_db()
        layout = QVBoxLayout(self)
        btns = QHBoxLayout()
        self.add_row_btn = QPushButton('Добавить строку')
        self.add_row_btn.clicked.connect(self.add_row)
        btns.addWidget(self.add_row_btn)
        self.del_row_btn = QPushButton('Удалить строку')
        self.del_row_btn.clicked.connect(self.delete_row)
        btns.addWidget(self.del_row_btn)
        self.add_col_btn = QPushButton('Добавить столбец')
        self.add_col_btn.clicked.connect(self.add_column)
        btns.addWidget(self.add_col_btn)
        self.del_col_btn = QPushButton('Удалить столбец')
        self.del_col_btn.clicked.connect(self.delete_column)
        btns.addWidget(self.del_col_btn)
        btns.addStretch()
        layout.addLayout(btns)
        # --- QSqlTableModel + QTableView ---
        self.db = QSqlDatabase.addDatabase('QSQLITE', f'edit_{id(self)}')
        self.db.setDatabaseName(self._tmp_db_path)
        self.db.open()
        print('QSqlTableModel DB path:', self.db.databaseName())
        print('Временный файл:', self._tmp_db_path)
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable(table_name)
        self.model.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.model.select()
        self.model.dataChanged.connect(self._mark_modified)
        self.model.rowsInserted.connect(self._mark_modified)
        self.model.rowsRemoved.connect(self._mark_modified)
        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.view.setSelectionMode(QTableView.SingleSelection)
        layout.addWidget(self.view)
        self.restore_geometry()

    def _mark_modified(self, *args, **kwargs):
        self._modified = True

    def _copy_table_to_temp_db(self):
        src = self.sqlite_conn
        dst = sqlite3.connect(self._tmp_dbfile.name)
        cur = src.cursor()
        dcur = dst.cursor()
        cur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (self.table_name,))
        create_sql = cur.fetchone()
        if not create_sql:
            dst.close()
            return
        dcur.execute(create_sql[0])
        dcur.execute(f'PRAGMA table_info("{self.table_name}")')
        schema = dcur.fetchall()
        print('Структура таблицы после создания:', schema)
        has_pk = any(row[5] == 1 for row in schema)
        if not has_pk:
            columns = [row[1] for row in schema]
            columns_sql = ', '.join([f'"{col}" TEXT' for col in columns])
            new_table = self.table_name + '_with_pk'
            dcur.execute(f'CREATE TABLE "{new_table}" (__rowid INTEGER PRIMARY KEY AUTOINCREMENT, {columns_sql})')
            col_names = ', '.join([f'"{col}"' for col in columns])
            dcur.execute(f'INSERT INTO "{new_table}" ({col_names}) SELECT {col_names} FROM "{self.table_name}"')
            dcur.execute(f'DROP TABLE "{self.table_name}"')
            dcur.execute(f'ALTER TABLE "{new_table}" RENAME TO "{self.table_name}"')
            print('Создана временная таблица с PRIMARY KEY')
        dcur.execute(f'PRAGMA table_info("{self.table_name}")')
        schema = dcur.fetchall()
        print('Структура таблицы после добавления PK:', schema)
        cur.execute(f'SELECT * FROM "{self.table_name}"')
        rows = cur.fetchall()
        print(f"Копируем {len(rows)} строк в {self.table_name}")
        try:
            if rows:
                # Вставлять только в исходные колонки (без __rowid)
                orig_columns = [row[1] for row in schema if row[1] != '__rowid']
                col_names = ', '.join([f'"{col}"' for col in orig_columns])
                placeholders = ','.join(['?'] * len(orig_columns))
                dcur.executemany(f'INSERT INTO "{self.table_name}" ({col_names}) VALUES ({placeholders})', rows)
        except Exception as e:
            print(f'Ошибка при вставке строк: {e}')
        dst.commit()
        dcur.execute(f'SELECT COUNT(*) FROM "{self.table_name}"')
        print('Строк во временной таблице:', dcur.fetchone()[0])
        dst.close()

    def _copy_table_back(self):
        # Копируем изменённую таблицу обратно в основную БД
        if not self._modified:
            return
        src = sqlite3.connect(self._tmp_dbfile.name)
        dst = self.sqlite_conn
        cur = dst.cursor()
        # Удалить старую таблицу
        cur.execute(f'DROP TABLE IF EXISTS "{self.table_name}"')
        # Получить SQL создания таблицы
        scur = src.cursor()
        scur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (self.table_name,))
        create_sql = scur.fetchone()
        if not create_sql:
            src.close()
            return
        cur.execute(create_sql[0])
        # Копировать данные
        scur.execute(f'SELECT * FROM "{self.table_name}"')
        rows = scur.fetchall()
        if rows:
            placeholders = ','.join(['?'] * len(rows[0]))
            cur.executemany(f'INSERT INTO "{self.table_name}" VALUES ({placeholders})', rows)
        dst.commit()
        src.close()

    def add_row(self):
        row = self.model.rowCount()
        self.model.insertRow(row)
        self.model.submitAll()
        self._mark_modified()

    def delete_row(self):
        idx = self.view.currentIndex()
        if not idx.isValid():
            QMessageBox.warning(self, 'Удаление строки', 'Выберите строку для удаления.')
            return
        self.model.removeRow(idx.row())
        self.model.submitAll()
        self._mark_modified()

    def add_column(self):
        col_name, ok = QInputDialog.getText(self, 'Добавить столбец', 'Имя нового столбца:')
        if not ok or not col_name:
            return
        try:
            db = sqlite3.connect(self._tmp_dbfile.name)
            cur = db.cursor()
            cur.execute(f'ALTER TABLE "{self.table_name}" ADD COLUMN "{col_name}" TEXT')
            db.commit()
            db.close()
            self.model.select()
            self._mark_modified()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось добавить столбец: {e}')

    def delete_column(self):
        col = self.view.currentIndex().column()
        if col == -1:
            QMessageBox.warning(self, 'Удаление столбца', 'Выберите столбец для удаления.')
            return
        col_name = self.model.headerData(col, Qt.Horizontal)
        reply = QMessageBox.question(self, 'Удалить столбец', f'Удалить столбец "{col_name}"? Это действие необратимо.', QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        QMessageBox.information(self, 'Удаление столбца', 'Удаление столбцов поддерживается только вручную через SQL.')

    def closeEvent(self, event):
        self.save_geometry()
        if self._modified:
            reply = QMessageBox.question(self, 'Сохранить изменения', 'Сохранить изменения в таблице?', QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self._copy_table_back()
        # Удалить временный файл
        try:
            os.unlink(self._tmp_dbfile.name)
        except Exception:
            pass
        super().closeEvent(event)

    def save_geometry(self):
        self._settings.setValue('geometry', self.saveGeometry())

    def restore_geometry(self):
        geom = self._settings.value('geometry')
        if geom:
            self.restoreGeometry(geom) 