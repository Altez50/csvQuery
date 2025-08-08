from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
                           QTableWidgetItem, QLabel, QComboBox, QListWidget, QListWidgetItem,
                           QSplitter, QMessageBox, QCheckBox, QStyledItemDelegate, QWidget,
                           QMenu, QAction, QFileDialog)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QColor, QBrush, QPen, QFont, QPainter, QIcon
from PyQt5.QtWidgets import QApplication, QDesktopWidget
import sqlite3
import pandas as pd


class ComparisonItemDelegate(QStyledItemDelegate):
    """Делегат для отображения ячеек с цветными рамками в таблице сравнения."""
    
    def paint(self, painter, option, index):
        # Получаем тип различия из данных ячейки
        diff_type = index.data(Qt.UserRole)
        
        # Сохраняем состояние художника
        painter.save()
        
        # Рисуем фон
        if diff_type == "different":
            # Синяя рамка - значения различаются
            painter.fillRect(option.rect, QBrush(QColor(238, 238, 255)))
        elif diff_type == "only_a":
            # Красная рамка - есть только в таблице A
            painter.fillRect(option.rect, QBrush(QColor(255, 238, 238)))
        elif diff_type == "only_b":
            # Зеленая рамка - есть только в таблице B
            painter.fillRect(option.rect, QBrush(QColor(238, 255, 238)))
        else:
            # Обычный фон для остальных ячеек
            painter.fillRect(option.rect, option.palette.base())
        
        # Рисуем рамку соответствующего цвета
        if diff_type == "different":
            pen = QPen(QColor(0, 0, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
        elif diff_type == "only_a":
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
        elif diff_type == "only_b":
            pen = QPen(QColor(0, 128, 0))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(option.rect.adjusted(1, 1, -1, -1))
        
        # Восстанавливаем состояние художника для рисования текста
        painter.restore()
        
        # Устанавливаем цвет текста в зависимости от типа различия
        if diff_type == "different":
            option.palette.setColor(option.palette.Text, QColor(0, 0, 204))
        elif diff_type == "only_a":
            option.palette.setColor(option.palette.Text, QColor(204, 0, 0))
        elif diff_type == "only_b":
            option.palette.setColor(option.palette.Text, QColor(0, 136, 0))
        
        # Рисуем текст с помощью базового класса
        super().paint(painter, option, index)

class TableCompareDialog(QWidget):
    def __init__(self, sqlite_conn, table_a_name, table_b_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Сравнение таблиц: {table_a_name} и {table_b_name}')
        self.setWindowIcon(QIcon('icons/main.png'))
        self.resize(1000, 700)
        self.sqlite_conn = sqlite_conn
        self.table_a_name = table_a_name
        self.table_b_name = table_b_name
        
        # Загрузка данных таблиц
        self.table_a_data = None
        self.table_b_data = None
        self.table_a_columns = []
        self.table_b_columns = []
        self.key_columns_a = []
        self.key_columns_b = []
        self.merged_data = None
        
        # Настройки для сохранения геометрии окна
        self._settings = QSettings('csvQuery', f'TableCompareDialog')
        
        # Флаги для отображения
        self.hide_unchanged_rows = False
        self.hide_empty_rows = True  # По умолчанию скрываем пустые строки
        
        # Инициализация UI
        self._init_ui()
        self._load_table_data()
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
            # Проверяем, что окно видимо на экране
            desktop = QApplication.desktop()
            screen_rect = desktop.availableGeometry()
            window_rect = self.geometry()
            
            # Если окно полностью за пределами экрана, перемещаем его
            if (window_rect.right() < screen_rect.left() or 
                window_rect.left() > screen_rect.right() or
                window_rect.bottom() < screen_rect.top() or
                window_rect.top() > screen_rect.bottom()):
                # Центрируем окно на экране
                self.move(screen_rect.center() - self.rect().center())
        else:
            # Если нет сохраненной геометрии, центрируем окно
            desktop = QApplication.desktop()
            screen_rect = desktop.availableGeometry()
            self.move(screen_rect.center() - self.rect().center())
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Добавляем кнопки управления в заголовок
        header_layout = QHBoxLayout()
        
        # Кнопка для скрытия/показа верхней панели
        self.toggle_panel_btn = QPushButton('▲')
        self.toggle_panel_btn.setToolTip('Скрыть/показать панель выбора колонок')
        self.toggle_panel_btn.setFixedSize(24, 24)
        self.toggle_panel_btn.clicked.connect(self.toggle_top_panel)
        header_layout.addWidget(self.toggle_panel_btn)
        
        # Заголовок
        header_layout.addWidget(QLabel(f'Сравнение таблиц: {self.table_a_name} и {self.table_b_name}'))
        header_layout.addStretch()
        
        # Кнопка максимизации/восстановления размера
        self.maximize_btn = QPushButton('🗖')
        self.maximize_btn.setToolTip('Развернуть/восстановить')
        self.maximize_btn.setFixedSize(24, 24)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        header_layout.addWidget(self.maximize_btn)
        
        layout.addLayout(header_layout)
        
        # Создаем виджет для верхней панели
        self.top_panel_widget = QWidget()
        top_panel_layout = QVBoxLayout(self.top_panel_widget)
        top_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Верхняя панель с выбором ключевых колонок
        top_panel = QHBoxLayout()
        
        # Выбор ключевых колонок для таблицы A
        table_a_panel = QVBoxLayout()
        table_a_panel.addWidget(QLabel(f'Ключевые колонки таблицы {self.table_a_name}:'))
        self.columns_a_list = QListWidget()
        self.columns_a_list.setSelectionMode(QListWidget.MultiSelection)
        table_a_panel.addWidget(self.columns_a_list)
        top_panel.addLayout(table_a_panel)
        
        # Выбор ключевых колонок для таблицы B
        table_b_panel = QVBoxLayout()
        table_b_panel.addWidget(QLabel(f'Ключевые колонки таблицы {self.table_b_name}:'))
        self.columns_b_list = QListWidget()
        self.columns_b_list.setSelectionMode(QListWidget.MultiSelection)
        table_b_panel.addWidget(self.columns_b_list)
        top_panel.addLayout(table_b_panel)
        
        top_panel_layout.addLayout(top_panel)
        
        # Добавляем верхнюю панель в основной макет
        layout.addWidget(self.top_panel_widget)
        
        # Создаем разделитель
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setHandleWidth(8)  # Делаем ручку разделителя шире для удобства
        
        # Создаем виджет для кнопки сравнения
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Кнопка для запуска сравнения
        compare_btn = QPushButton('Сравнить таблицы')
        compare_btn.clicked.connect(self.compare_tables)
        button_layout.addWidget(compare_btn)
        
        # Добавляем кнопку в разделитель
        self.splitter.addWidget(button_widget)
        
        # Создаем виджет для таблицы результатов
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Таблица для отображения результатов сравнения
        self.result_table = QTableWidget()
        self.result_table.setItemDelegate(ComparisonItemDelegate())
        self.result_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.result_table.customContextMenuRequested.connect(self.show_context_menu)
        table_layout.addWidget(self.result_table)
        
        # Добавляем таблицу в разделитель
        self.splitter.addWidget(table_widget)
        
        # Устанавливаем начальные размеры разделителя
        self.splitter.setSizes([100, 900])  # 10% для верхней части, 90% для таблицы
        
        # Добавляем разделитель в основной макет
        layout.addWidget(self.splitter)
        
        self.setLayout(layout)
    
    def _load_table_data(self):
        try:
            # Загрузка данных таблицы A
            query_a = f"""SELECT * FROM '{self.table_a_name}'"""
            self.table_a_data = pd.read_sql_query(query_a, self.sqlite_conn)
            self.table_a_columns = list(self.table_a_data.columns)
            
            # Загрузка данных таблицы B
            query_b = f"""SELECT * FROM '{self.table_b_name}'"""
            self.table_b_data = pd.read_sql_query(query_b, self.sqlite_conn)
            self.table_b_columns = list(self.table_b_data.columns)
            
            # Заполнение списков колонок
            self.columns_a_list.clear()
            for col in self.table_a_columns:
                self.columns_a_list.addItem(col)
            
            self.columns_b_list.clear()
            for col in self.table_b_columns:
                self.columns_b_list.addItem(col)
                
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить данные таблиц: {str(e)}')
    
    def compare_tables(self):
        # Получение выбранных ключевых колонок
        self.key_columns_a = [item.text() for item in self.columns_a_list.selectedItems()]
        self.key_columns_b = [item.text() for item in self.columns_b_list.selectedItems()]
        
        if not self.key_columns_a or not self.key_columns_b:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите ключевые колонки для обеих таблиц')
            return
        
        if len(self.key_columns_a) != len(self.key_columns_b):
            QMessageBox.warning(self, 'Предупреждение', 'Количество ключевых колонок должно совпадать')
            return
        
        try:
            # Создание копий данных с префиксами для колонок
            df_a = self.table_a_data.copy()
            df_b = self.table_b_data.copy()
            
            # Переименование колонок для избежания конфликтов
            df_a.columns = [f'A_{col}' for col in df_a.columns]
            df_b.columns = [f'B_{col}' for col in df_b.columns]
            
            # Создание ключей для объединения
            df_a['merge_key'] = df_a.apply(lambda row: '_'.join([str(row[f'A_{col}']) for col in self.key_columns_a]), axis=1)
            df_b['merge_key'] = df_b.apply(lambda row: '_'.join([str(row[f'B_{col}']) for col in self.key_columns_b]), axis=1)
            
            # Полное внешнее объединение
            self.merged_data = pd.merge(df_a, df_b, on='merge_key', how='outer')
            
            # Отображение результатов
            self._display_comparison_results()
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при сравнении таблиц: {str(e)}')
    
    def toggle_top_panel(self):
        """Скрывает или показывает верхнюю панель с выбором ключевых колонок"""
        if self.top_panel_widget.isVisible():
            self.top_panel_widget.hide()
            self.toggle_panel_btn.setText('▼')
            self.toggle_panel_btn.setToolTip('Показать панель выбора колонок')
        else:
            self.top_panel_widget.show()
            self.toggle_panel_btn.setText('▲')
            self.toggle_panel_btn.setToolTip('Скрыть панель выбора колонок')
    
    def toggle_maximize(self):
        """Разворачивает окно на весь экран или восстанавливает прежний размер"""
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText('🗖')
            self.maximize_btn.setToolTip('Развернуть')
        else:
            self.showMaximized()
            self.maximize_btn.setText('🗗')
            self.maximize_btn.setToolTip('Восстановить')
    
    def show_context_menu(self, position):
        """Показывает контекстное меню для таблицы результатов"""
        menu = QMenu()
        
        # Подменю для управления видимостью строк
        rows_menu = menu.addMenu('Строки')
        
        # Действие для скрытия/показа строк без изменений
        hide_unchanged_action = QAction('Скрыть строки без изменений' if not self.hide_unchanged_rows else 'Показать строки без изменений', self)
        hide_unchanged_action.triggered.connect(self.toggle_unchanged_rows)
        rows_menu.addAction(hide_unchanged_action)
        
        # Действие для скрытия/показа пустых строк
        hide_empty_action = QAction('Скрыть пустые строки' if not self.hide_empty_rows else 'Показать пустые строки', self)
        hide_empty_action.triggered.connect(self.toggle_empty_rows)
        rows_menu.addAction(hide_empty_action)
        
        # Подменю для управления видимостью колонок
        columns_menu = menu.addMenu('Колонки')
        
        # Добавляем действие для показа всех колонок
        show_all_columns = QAction('Показать все колонки', self)
        show_all_columns.triggered.connect(lambda: self.toggle_all_columns_visibility(True))
        columns_menu.addAction(show_all_columns)
        
        # Добавляем действие для скрытия всех колонок
        hide_all_columns = QAction('Скрыть все колонки', self)
        hide_all_columns.triggered.connect(lambda: self.toggle_all_columns_visibility(False))
        columns_menu.addAction(hide_all_columns)
        
        columns_menu.addSeparator()
        
        # Добавляем действия для каждой колонки
        for col_idx in range(self.result_table.columnCount()):
            col_name = self.result_table.horizontalHeaderItem(col_idx).text()
            is_visible = not self.result_table.isColumnHidden(col_idx)
            
            column_action = QAction(col_name, self)
            column_action.setCheckable(True)
            column_action.setChecked(is_visible)
            column_action.triggered.connect(lambda checked, idx=col_idx: self.toggle_column_visibility(idx, checked))
            columns_menu.addAction(column_action)
        
        # Действие для экспорта результатов
        export_menu = menu.addMenu('Экспорт результатов')
        export_csv = QAction('Экспорт в CSV', self)
        export_csv.triggered.connect(lambda: self.export_results('csv'))
        export_menu.addAction(export_csv)
        
        export_excel = QAction('Экспорт в Excel', self)
        export_excel.triggered.connect(lambda: self.export_results('excel'))
        export_menu.addAction(export_excel)
        
        menu.exec_(self.result_table.mapToGlobal(position))
    
    def toggle_unchanged_rows(self):
        """Скрывает или показывает строки без изменений"""
        self.hide_unchanged_rows = not self.hide_unchanged_rows
        self._display_comparison_results()
        
    def toggle_empty_rows(self):
        """Скрывает или показывает пустые строки"""
        self.hide_empty_rows = not self.hide_empty_rows
        self._display_comparison_results()
        
    def toggle_column_visibility(self, column_index, visible):
        """Скрывает или показывает указанную колонку"""
        self.result_table.setColumnHidden(column_index, not visible)
        
    def toggle_all_columns_visibility(self, visible):
        """Скрывает или показывает все колонки"""
        for col_idx in range(self.result_table.columnCount()):
            self.result_table.setColumnHidden(col_idx, not visible)
    
    def export_results(self, format_type):
        """Экспортирует результаты сравнения в CSV или Excel"""
        if self.merged_data is None:
            QMessageBox.warning(self, 'Предупреждение', 'Нет данных для экспорта')
            return
        
        # Получаем путь для сохранения файла
        file_filter = 'CSV файлы (*.csv)' if format_type == 'csv' else 'Excel файлы (*.xlsx)'
        file_ext = '.csv' if format_type == 'csv' else '.xlsx'
        file_path, _ = QFileDialog.getSaveFileName(self, 'Сохранить результаты', 
                                               f'comparison_{self.table_a_name}_{self.table_b_name}{file_ext}',
                                               file_filter)
        
        if not file_path:
            return
        
        try:
            # Создаем DataFrame для экспорта
            export_data = self.merged_data.copy()
            
            # Удаляем служебные колонки
            if 'merge_key' in export_data.columns:
                export_data = export_data.drop('merge_key', axis=1)
            
            # Экспортируем данные
            if format_type == 'csv':
                export_data.to_csv(file_path, index=False, encoding='utf-8-sig')
            else:
                export_data.to_excel(file_path, index=False)
            
            QMessageBox.information(self, 'Экспорт завершен', f'Данные успешно экспортированы в {file_path}')
        
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось экспортировать данные: {str(e)}')
    
    def _display_comparison_results(self):
        if self.merged_data is None:
            return
        
        # Определение всех колонок для отображения (без префиксов A_ и B_)
        all_columns = set()
        for col in self.table_a_columns:
            all_columns.add(col)
        for col in self.table_b_columns:
            all_columns.add(col)
        
        # Сохраняем состояние видимости колонок перед обновлением
        column_visibility = {}
        for col_idx in range(self.result_table.columnCount()):
            if col_idx < self.result_table.horizontalHeader().count():
                col_name = self.result_table.horizontalHeaderItem(col_idx).text()
                column_visibility[col_name] = not self.result_table.isColumnHidden(col_idx)
        
        # Настройка таблицы результатов
        self.result_table.clear()
        
        # Определяем, какие строки показывать
        rows_to_display = []
        for idx, row in enumerate(self.merged_data.itertuples()):
            has_difference = False
            has_non_empty_values = False
            
            # Проверяем, есть ли различия в строке и непустые значения
            for col_name in all_columns:
                a_col = f'A_{col_name}'
                b_col = f'B_{col_name}'
                
                a_value = getattr(row, a_col) if hasattr(row, a_col) and not pd.isna(getattr(row, a_col)) else None
                b_value = getattr(row, b_col) if hasattr(row, b_col) and not pd.isna(getattr(row, b_col)) else None
                
                # Если хотя бы одно значение не пустое, отмечаем строку как содержащую непустые значения
                if a_value is not None or b_value is not None:
                    has_non_empty_values = True
                
                # Если значения разные или одно из них отсутствует, то есть различие
                if a_value != b_value or (a_value is None) != (b_value is None):
                    has_difference = True
                    break
            
            # Проверяем условия для отображения строки:
            # 1. Если скрываем пустые строки, то строка должна содержать непустые значения
            # 2. Если скрываем строки без изменений, то в строке должны быть различия
            show_row = True
            
            if self.hide_empty_rows and not has_non_empty_values:
                show_row = False
            
            if self.hide_unchanged_rows and not has_difference:
                show_row = False
            
            if show_row:
                rows_to_display.append(idx)
        
        # Устанавливаем количество строк и колонок
        self.result_table.setRowCount(len(rows_to_display))
        self.result_table.setColumnCount(len(all_columns))
        
        # Установка заголовков
        self.result_table.setHorizontalHeaderLabels(list(all_columns))
        
        # Определение стилей для разных типов различий
        red_style = "QTableWidgetItem { border: 2px solid red; background-color: #ffeeee; color: #cc0000; }"
        green_style = "QTableWidgetItem { border: 2px solid green; background-color: #eeffee; color: #008800; }"
        blue_style = "QTableWidgetItem { border: 2px solid blue; background-color: #eeeeff; color: #0000cc; }"
        
        # Заполнение таблицы данными
        for display_idx, row_idx in enumerate(rows_to_display):
            row = self.merged_data.iloc[row_idx]
            
            for col_idx, col_name in enumerate(all_columns):
                a_col = f'A_{col_name}'
                b_col = f'B_{col_name}'
                
                # Создание ячейки
                item = QTableWidgetItem()
                
                # Определение значений из обеих таблиц
                a_value = row[a_col] if a_col in row.index and not pd.isna(row[a_col]) else None
                b_value = row[b_col] if b_col in row.index and not pd.isna(row[b_col]) else None
                
                # Установка значения и стиля в зависимости от результата сравнения
                if a_value is not None and b_value is not None:
                    # Есть в обеих таблицах
                    if str(a_value) == str(b_value):
                        # Значения равны
                        item.setText(str(a_value))
                    else:
                        # Значения различаются - синяя рамка
                        item.setText(f'{a_value} | {b_value}')
                        # Адаптивные цвета для темной/светлой темы
                        if hasattr(self.parent(), 'dark_theme') and self.parent().dark_theme:
                            item.setBackground(QColor(40, 40, 80))   # Темно-синий фон для темной темы
                            item.setForeground(QColor(120, 120, 255)) # Светло-синий текст для темной темы
                        else:
                            item.setBackground(QColor(238, 238, 255)) # Светло-синий фон для светлой темы
                            item.setForeground(QColor(0, 0, 204))     # Синий текст для светлой темы
                        item.setData(Qt.UserRole, "different")
                        item.setToolTip(f"Таблица A: {a_value}\nТаблица B: {b_value}")
                elif a_value is not None:
                    # Есть только в таблице A - красная рамка
                    item.setText(str(a_value))
                    # Адаптивные цвета для темной/светлой темы
                    if hasattr(self.parent(), 'dark_theme') and self.parent().dark_theme:
                        item.setBackground(QColor(80, 40, 40))    # Темно-красный фон для темной темы
                        item.setForeground(QColor(255, 120, 120)) # Светло-красный текст для темной темы
                    else:
                        item.setBackground(QColor(255, 238, 238)) # Светло-красный фон для светлой темы
                        item.setForeground(QColor(204, 0, 0))     # Красный текст для светлой темы
                    item.setData(Qt.UserRole, "only_a")
                    item.setToolTip(f"Только в таблице A: {a_value}")
                elif b_value is not None:
                    # Есть только в таблице B - зеленая рамка
                    item.setText(str(b_value))
                    # Адаптивные цвета для темной/светлой темы
                    if hasattr(self.parent(), 'dark_theme') and self.parent().dark_theme:
                        item.setBackground(QColor(40, 80, 40))    # Темно-зеленый фон для темной темы
                        item.setForeground(QColor(120, 255, 120)) # Светло-зеленый текст для темной темы
                    else:
                        item.setBackground(QColor(238, 255, 238)) # Светло-зеленый фон для светлой темы
                        item.setForeground(QColor(0, 136, 0))     # Зеленый текст для светлой темы
                    item.setData(Qt.UserRole, "only_b")
                    item.setToolTip(f"Только в таблице B: {b_value}")
                
                self.result_table.setItem(display_idx, col_idx, item)
        
        # Применение стилей к ячейкам с помощью делегата
        self.result_table.setStyleSheet("""
            QTableWidget::item[userRole="different"] { border: 2px solid blue; }
            QTableWidget::item[userRole="only_a"] { border: 2px solid red; }
            QTableWidget::item[userRole="only_b"] { border: 2px solid green; }
        """)
        
        # Восстанавливаем состояние видимости колонок
        for col_idx in range(self.result_table.columnCount()):
            col_name = self.result_table.horizontalHeaderItem(col_idx).text()
            if col_name in column_visibility:
                self.result_table.setColumnHidden(col_idx, not column_visibility[col_name])
        
        # Добавление легенды
        # Сначала удаляем старую легенду, если она есть
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)
            if isinstance(item, QHBoxLayout) and item.count() > 0 and isinstance(item.itemAt(0).widget(), QLabel) and item.itemAt(0).widget().text() == "Легенда:":
                # Удаляем все виджеты из макета
                while item.count():
                    widget = item.takeAt(0).widget()
                    if widget:
                        widget.deleteLater()
                # Удаляем сам макет
                self.layout().removeItem(item)
                break
        
        # Создаем новую легенду
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Легенда:"))
        
        # Адаптивные цвета для легенды в зависимости от темы
        if hasattr(self.parent(), 'dark_theme') and self.parent().dark_theme:
            red_bg = "#502828"    # Темно-красный для темной темы
            green_bg = "#285028"  # Темно-зеленый для темной темы
            blue_bg = "#282850"   # Темно-синий для темной темы
        else:
            red_bg = "#ffeeee"    # Светло-красный для светлой темы
            green_bg = "#eeffee"  # Светло-зеленый для светлой темы
            blue_bg = "#eeeeff"   # Светло-синий для светлой темы
        
        red_box = QLabel()
        red_box.setStyleSheet(f"background-color: {red_bg}; border: 2px solid red; min-width: 20px; min-height: 20px;")
        legend_layout.addWidget(red_box)
        legend_layout.addWidget(QLabel("Есть в A, нет в B"))
        
        green_box = QLabel()
        green_box.setStyleSheet(f"background-color: {green_bg}; border: 2px solid green; min-width: 20px; min-height: 20px;")
        legend_layout.addWidget(green_box)
        legend_layout.addWidget(QLabel("Есть в B, нет в A"))
        
        blue_box = QLabel()
        blue_box.setStyleSheet(f"background-color: {blue_bg}; border: 2px solid blue; min-width: 20px; min-height: 20px;")
        legend_layout.addWidget(blue_box)
        legend_layout.addWidget(QLabel("Есть в A и B, но не равны"))
        
        # Добавляем информацию о скрытых строках, если они есть
        if self.hide_unchanged_rows:
            hidden_count = len(self.merged_data) - len(rows_to_display)
            if hidden_count > 0:
                legend_layout.addStretch()
                legend_layout.addWidget(QLabel(f"Скрыто строк без изменений: {hidden_count}"))
        
        legend_layout.addStretch()
        
        # Добавляем легенду в основной макет
        self.layout().insertLayout(self.layout().count() - 1, legend_layout)
        
        # Автоматическая настройка размеров колонок
        self.result_table.resizeColumnsToContents()