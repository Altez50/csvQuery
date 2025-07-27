#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демонстрация функциональности формул в CSV Editor
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from csv_editor import CSVEditor

class FormulaTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Formula Demo - CSV Editor")
        self.setGeometry(100, 100, 800, 600)
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Добавляем методы для совместимости
        self.sqlite_conn = None
        
        # Создаем заглушку для row_count_label
        class MockLabel:
            def setText(self, text):
                pass
        
        self.row_count_label = MockLabel()
        
        # Создаем CSV Editor
        self.csv_editor = CSVEditor(self)
        layout.addWidget(self.csv_editor)
        
        # Загружаем тестовые данные с числами для формул
        self.load_test_data()
        
    def load_test_data(self):
        """Загружает тестовые данные для демонстрации формул"""
        headers = ['A', 'B', 'C', 'D', 'E']
        data = [
            [10, 20, '', '', ''],
            [5, 15, '', '', ''],
            [8, 12, '', '', ''],
            ['', '', '', '', ''],
            ['Сумма:', '', '', '', '']
        ]
        
        self.csv_editor.load_data(headers, data)
        
    def log_message(self, message):
        """Заглушка для логирования"""
        print(f"Log: {message}")
        
    def setWindowTitle(self, title):
        """Переопределяем для совместимости"""
        super().setWindowTitle(title)

def main():
    app = QApplication(sys.argv)
    
    window = FormulaTestWindow()
    window.show()
    
    print("\n=== Демонстрация функциональности формул ===")
    print("1. В ячейку C1 введите: =A1+B1")
    print("2. В ячейку C2 введите: =A2*B2")
    print("3. В ячейку C3 введите: =MAX(A3,B3)")
    print("4. В ячейку E5 введите: =SUM(A1:A3)")
    print("5. Двойной клик по ячейке с формулой покажет саму формулу для редактирования")
    print("6. Ячейки с формулами имеют зеленый фон")
    print("7. При наведении курсора показывается tooltip с формулой и результатом")
    print("\nЗакройте окно для завершения демонстрации.")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()