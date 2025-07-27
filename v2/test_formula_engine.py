#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование FormulaEngine - движка для оценки Excel формул.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from formula_engine import FormulaEngine

def test_formula_engine():
    """Тестирует основные функции FormulaEngine."""
    
    # Создаем тестовые данные (5x5 таблица)
    test_data = [
        [10, 20, 30, 40, 50],      # Строка 1: A1=10, B1=20, C1=30, D1=40, E1=50
        [5, 15, 25, 35, 45],       # Строка 2: A2=5, B2=15, C2=25, D2=35, E2=45
        [2, 4, 6, 8, 10],          # Строка 3: A3=2, B3=4, C3=6, D3=8, E3=10
        [100, 200, 300, 400, 500], # Строка 4: A4=100, B4=200, C4=300, D4=400, E4=500
        [1, 3, 5, 7, 9]            # Строка 5: A5=1, B5=3, C5=5, D5=7, E5=9
    ]
    
    # Создаем экземпляр FormulaEngine
    engine = FormulaEngine(test_data)
    
    print("=== Тестирование FormulaEngine ===")
    print("\nТестовые данные:")
    print("   A   B   C   D   E")
    for i, row in enumerate(test_data, 1):
        print(f"{i}: {row}")
    
    print("\n=== Тестирование базовых функций ===")
    
    # Тест 1: SUM функция
    print("\n1. Тестирование SUM:")
    test_cases = [
        "=SUM(A1:A5)",  # Сумма столбца A: 10+5+2+100+1 = 118
        "=SUM(A1:E1)",  # Сумма строки 1: 10+20+30+40+50 = 150
        "=SUM(A1,B1,C1)",  # Сумма отдельных ячеек: 10+20+30 = 60
        "=SUM(A1:B2)",  # Сумма диапазона 2x2: 10+20+5+15 = 50
    ]
    
    for formula in test_cases:
        result = engine.evaluate_formula(formula)
        print(f"  {formula} = {result}")
    
    # Тест 2: AVG функция
    print("\n2. Тестирование AVG:")
    test_cases = [
        "=AVG(A1:A5)",  # Среднее столбца A: 118/5 = 23.6
        "=AVG(A1:E1)",  # Среднее строки 1: 150/5 = 30
        "=AVERAGE(A4:E4)",  # Среднее строки 4: 1500/5 = 300
    ]
    
    for formula in test_cases:
        result = engine.evaluate_formula(formula)
        print(f"  {formula} = {result}")
    
    # Тест 3: COUNT функция
    print("\n3. Тестирование COUNT:")
    test_cases = [
        "=COUNT(A1:A5)",  # Количество чисел в столбце A: 5
        "=COUNT(A1:E5)",  # Количество чисел во всей таблице: 25
    ]
    
    for formula in test_cases:
        result = engine.evaluate_formula(formula)
        print(f"  {formula} = {result}")
    
    # Тест 4: MAX и MIN функции
    print("\n4. Тестирование MAX и MIN:")
    test_cases = [
        "=MAX(A1:A5)",  # Максимум в столбце A: 100
        "=MIN(A1:A5)",  # Минимум в столбце A: 1
        "=MAX(A1:E1)",  # Максимум в строке 1: 50
        "=MIN(A1:E1)",  # Минимум в строке 1: 10
    ]
    
    for formula in test_cases:
        result = engine.evaluate_formula(formula)
        print(f"  {formula} = {result}")
    
    # Тест 5: IF функция
    print("\n5. Тестирование IF:")
    test_cases = [
        "=IF(A1>5,\"Больше 5\",\"Меньше или равно 5\")",  # A1=10 > 5, результат: "Больше 5"
        "=IF(A3>5,\"Больше 5\",\"Меньше или равно 5\")",  # A3=2 <= 5, результат: "Меньше или равно 5"
    ]
    
    for formula in test_cases:
        result = engine.evaluate_formula(formula)
        print(f"  {formula} = {result}")
    
    # Тест 6: Математические выражения
    print("\n6. Тестирование математических выражений:")
    test_cases = [
        "=A1+B1",      # 10+20 = 30
        "=A1*B1",      # 10*20 = 200
        "=A4/A1",      # 100/10 = 10
        "=A1+B1*C1",   # 10+20*30 = 10+600 = 610
        "=(A1+B1)*C1", # (10+20)*30 = 30*30 = 900
    ]
    
    for formula in test_cases:
        result = engine.evaluate_formula(formula)
        print(f"  {formula} = {result}")
    
    # Тест 7: Логические функции
    print("\n7. Тестирование логических функций:")
    test_cases = [
        "=AND(A1>5,B1>15)",  # AND(10>5, 20>15) = AND(True, True) = True
        "=OR(A1>50,B1>15)",  # OR(10>50, 20>15) = OR(False, True) = True
        "=NOT(A1>50)",       # NOT(10>50) = NOT(False) = True
    ]
    
    for formula in test_cases:
        result = engine.evaluate_formula(formula)
        print(f"  {formula} = {result}")
    
    # Тест 8: Ссылки на ячейки
    print("\n8. Тестирование ссылок на ячейки:")
    test_cases = [
        "=A1",   # Значение ячейки A1: 10
        "=B2",   # Значение ячейки B2: 15
        "=E5",   # Значение ячейки E5: 9
    ]
    
    for formula in test_cases:
        result = engine.evaluate_formula(formula)
        print(f"  {formula} = {result}")
    
    print("\n=== Тестирование завершено ===")

def test_with_formulas_in_cells():
    """Тестирует работу с формулами в ячейках."""
    
    print("\n=== Тестирование формул в ячейках ===")
    
    # Создаем данные с формулами
    test_data = [
        [10, 20, "=A1+B1", 40, "=SUM(A1:D1)"],  # C1 = 30, E1 = 100
        [5, 15, "=A2*B2", 35, "=AVG(A2:D2)"],   # C2 = 75, E2 = 18.75
        [2, 4, "=MAX(A3,B3)", 8, "=MIN(A3:D3)"], # C3 = 4, E3 = 2
    ]
    
    engine = FormulaEngine(test_data)
    
    print("\nДанные с формулами:")
    for i, row in enumerate(test_data, 1):
        print(f"{i}: {row}")
    
    print("\nВычисленные значения:")
    for row_idx in range(len(test_data)):
        computed_row = []
        for col_idx in range(len(test_data[row_idx])):
            value = test_data[row_idx][col_idx]
            if isinstance(value, str) and value.startswith('='):
                cell_ref = engine._coords_to_cell_ref(row_idx, col_idx)
                computed_value = engine.evaluate_formula(value, cell_ref)
                computed_row.append(f"{value} → {computed_value}")
            else:
                computed_row.append(str(value))
        print(f"{row_idx + 1}: {computed_row}")

def test_error_handling():
    """Тестирует обработку ошибок."""
    
    print("\n=== Тестирование обработки ошибок ===")
    
    test_data = [[10, 20, 30], [5, 15, 25], [2, 4, 6]]
    engine = FormulaEngine(test_data)
    
    error_cases = [
        "=UNKNOWN_FUNCTION(A1)",  # Неизвестная функция
        "=SUM(Z99:Z100)",         # Ссылка на несуществующие ячейки
        "=A1/0",                  # Деление на ноль
        "=SUM(",                  # Неправильный синтаксис
        "=A1+B1+",               # Неполное выражение
    ]
    
    for formula in error_cases:
        result = engine.evaluate_formula(formula)
        print(f"  {formula} = {result}")

if __name__ == "__main__":
    test_formula_engine()
    test_with_formulas_in_cells()
    test_error_handling()
    
    print("\n=== Все тесты завершены ===")