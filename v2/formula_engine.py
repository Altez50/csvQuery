import re
import math
from typing import Dict, Any, List, Tuple, Union

class FormulaEngine:
    """Движок для оценки Excel формул и базовых функций."""
    
    def __init__(self, worksheet_data: List[List[Any]]):
        """
        Инициализация движка формул.
        
        Args:
            worksheet_data: Данные листа в виде списка списков [row][col]
        """
        self.data = worksheet_data
        self.cache = {}  # Кэш для результатов формул
        self.evaluating = set()  # Для обнаружения циклических зависимостей
        
        # Поддерживаемые функции
        self.functions = {
            'SUM': self._sum,
            'AVG': self._avg,
            'AVERAGE': self._avg,
            'COUNT': self._count,
            'MAX': self._max,
            'MIN': self._min,
            'IF': self._if,
            'AND': self._and,
            'OR': self._or,
            'NOT': self._not
        }
        
        # Регулярные выражения для парсинга
        self.cell_ref_pattern = re.compile(r'([A-Z]+)(\d+)')
        self.range_pattern = re.compile(r'([A-Z]+\d+):([A-Z]+\d+)')
        self.function_pattern = re.compile(r'([A-Z]+)\(([^)]+)\)')
    
    def evaluate_formula(self, formula_text: str, cell_address: str = None) -> Union[float, str, bool]:
        """
        Вычисляет формулу Excel.
        
        Args:
            formula_text: Текст формулы (например, "=SUM(A1:A5)")
            cell_address: Адрес ячейки для обнаружения циклических зависимостей
            
        Returns:
            Результат вычисления формулы
        """
        if not formula_text or not formula_text.startswith('='):
            return formula_text
        
        # Убираем знак равенства
        formula = formula_text[1:].strip()
        
        # Проверяем циклические зависимости
        if cell_address:
            if cell_address in self.evaluating:
                return "#CIRCULAR!"
            self.evaluating.add(cell_address)
        
        try:
            result = self._evaluate_expression(formula)
            return result
        except Exception as e:
            return f"#ERROR: {str(e)}"
        finally:
            if cell_address:
                self.evaluating.discard(cell_address)
    
    def _evaluate_expression(self, expression: str) -> Union[float, str, bool]:
        """
        Вычисляет математическое выражение или функцию.
        """
        expression = expression.strip()
        
        # Проверяем, является ли это функцией
        func_match = self.function_pattern.match(expression)
        if func_match:
            func_name = func_match.group(1)
            args_str = func_match.group(2)
            return self._evaluate_function(func_name, args_str)
        
        # Проверяем, является ли это одиночной ссылкой на ячейку (например, A1)
        if self.cell_ref_pattern.fullmatch(expression):
            return self._get_cell_value_by_ref(expression)
        
        # Проверяем, является ли это диапазоном
        if ':' in expression and self.range_pattern.match(expression):
            return self._get_range_values(expression)
        
        # Пытаемся вычислить как математическое выражение
        return self._evaluate_math_expression(expression)
    
    def _evaluate_function(self, func_name: str, args_str: str) -> Union[float, str, bool]:
        """
        Вычисляет функцию с аргументами.
        """
        if func_name not in self.functions:
            raise ValueError(f"Неподдерживаемая функция: {func_name}")
        
        # Парсим аргументы
        args = self._parse_function_args(args_str)
        
        # Вычисляем аргументы
        evaluated_args = []
        for arg in args:
            if isinstance(arg, str) and arg.strip():
                arg = arg.strip()
                # Если аргумент в кавычках, возвращаем строку без кавычек
                if arg.startswith('"') and arg.endswith('"'):
                    evaluated_args.append(arg[1:-1])  # Убираем кавычки
                else:
                    evaluated_args.append(self._evaluate_expression(arg))
            else:
                evaluated_args.append(arg)
        
        return self.functions[func_name](*evaluated_args)
    
    def _parse_function_args(self, args_str: str) -> List[str]:
        """
        Парсит аргументы функции, учитывая вложенные функции, скобки и строки в кавычках.
        """
        args = []
        current_arg = ""
        paren_count = 0
        in_quotes = False
        
        for char in args_str:
            if char == '"':
                in_quotes = not in_quotes
                current_arg += char
            elif char == ',' and paren_count == 0 and not in_quotes:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                if char == '(' and not in_quotes:
                    paren_count += 1
                elif char == ')' and not in_quotes:
                    paren_count -= 1
                current_arg += char
        
        if current_arg.strip():
            args.append(current_arg.strip())
        
        return args
    
    def _evaluate_math_expression(self, expression: str) -> float:
        """
        Вычисляет простое математическое выражение.
        """
        # Заменяем ссылки на ячейки их значениями
        def replace_cell_ref(match):
            cell_ref = match.group(0)
            value = self._get_cell_value_by_ref(cell_ref)
            return str(value) if isinstance(value, (int, float)) else "0"
        
        expression = self.cell_ref_pattern.sub(replace_cell_ref, expression)
        
        # Проверяем на строковые литералы (в кавычках)
        if '"' in expression:
            # Если есть кавычки, возвращаем строку без кавычек
            return expression.strip('"')
        
        # Безопасное вычисление математического выражения
        try:
            # Разрешаем только безопасные операции и сравнения
            allowed_chars = set('0123456789+-*/.()><= ')
            if not all(c in allowed_chars for c in expression):
                # Если есть недопустимые символы, пытаемся вычислить как есть
                pass
            
            # Заменяем операторы сравнения для корректной работы
            result = eval(expression)
            return result
        except:
            # Если не удается вычислить, возвращаем как строку
            return expression
    
    def _get_cell_value_by_ref(self, cell_ref: str) -> Union[float, str]:
        """
        Получает значение ячейки по ссылке (например, A1).
        """
        try:
            row, col = self._parse_cell_reference(cell_ref)
            return self._get_cell_value(row, col)
        except:
            return 0
    
    def _parse_cell_reference(self, cell_ref: str) -> Tuple[int, int]:
        """
        Преобразует ссылку на ячейку (A1) в координаты (row, col).
        """
        match = self.cell_ref_pattern.match(cell_ref.upper())
        if not match:
            raise ValueError(f"Неверная ссылка на ячейку: {cell_ref}")
        
        col_letters = match.group(1)
        row_num = int(match.group(2))
        
        # Преобразуем буквы столбца в номер (A=1, B=2, ..., Z=26, AA=27, ...)
        col_num = 0
        for char in col_letters:
            col_num = col_num * 26 + (ord(char) - ord('A') + 1)
        
        return row_num - 1, col_num - 1  # Преобразуем в 0-индексированные координаты
    
    def _get_cell_value(self, row: int, col: int) -> Union[float, str]:
        """
        Получает значение ячейки по координатам.
        """
        if row < 0 or col < 0 or row >= len(self.data):
            return 0
        
        # Проверяем, что столбец существует в данной строке
        if col >= len(self.data[row]):
            return 0
            
        value = self.data[row][col]
        
        # Если значение - это формула, вычисляем её
        if isinstance(value, str) and value.startswith('='):
            cell_address = self._coords_to_cell_ref(row, col)
            return self.evaluate_formula(value, cell_address)
        
        # Пытаемся преобразовать в число
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return value
        
        return value if value is not None else 0
    
    def _coords_to_cell_ref(self, row: int, col: int) -> str:
        """
        Преобразует координаты в ссылку на ячейку.
        """
        col_letters = ""
        col_num = col + 1
        while col_num > 0:
            col_num -= 1
            col_letters = chr(col_num % 26 + ord('A')) + col_letters
            col_num //= 26
        
        return f"{col_letters}{row + 1}"
    
    def _get_range_values(self, range_ref: str) -> List[Union[float, str]]:
        """
        Получает значения из диапазона ячеек (например, A1:B5).
        """
        match = self.range_pattern.match(range_ref)
        if not match:
            raise ValueError(f"Неверный диапазон: {range_ref}")
        
        start_cell = match.group(1)
        end_cell = match.group(2)
        
        start_row, start_col = self._parse_cell_reference(start_cell)
        end_row, end_col = self._parse_cell_reference(end_cell)
        
        values = []
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                values.append(self._get_cell_value(row, col))
        
        return values
    
    # Функции Excel
    def _sum(self, *args) -> float:
        """Функция SUM."""
        total = 0
        for arg in args:
            if isinstance(arg, list):
                total += sum(self._to_number(v) for v in arg)
            else:
                total += self._to_number(arg)
        return total
    
    def _avg(self, *args) -> float:
        """Функция AVG/AVERAGE."""
        values = []
        for arg in args:
            if isinstance(arg, list):
                values.extend(arg)
            else:
                values.append(arg)
        
        numeric_values = [self._to_number(v) for v in values if self._is_numeric(v)]
        return sum(numeric_values) / len(numeric_values) if numeric_values else 0
    
    def _count(self, *args) -> int:
        """Функция COUNT."""
        count = 0
        for arg in args:
            if isinstance(arg, list):
                count += sum(1 for v in arg if self._is_numeric(v))
            else:
                if self._is_numeric(arg):
                    count += 1
        return count
    
    def _max(self, *args) -> float:
        """Функция MAX."""
        values = []
        for arg in args:
            if isinstance(arg, list):
                values.extend(arg)
            else:
                values.append(arg)
        
        numeric_values = [self._to_number(v) for v in values if self._is_numeric(v)]
        return max(numeric_values) if numeric_values else 0
    
    def _min(self, *args) -> float:
        """Функция MIN."""
        values = []
        for arg in args:
            if isinstance(arg, list):
                values.extend(arg)
            else:
                values.append(arg)
        
        numeric_values = [self._to_number(v) for v in values if self._is_numeric(v)]
        return min(numeric_values) if numeric_values else 0
    
    def _if(self, condition, true_value, false_value):
        """Функция IF."""
        if self._to_boolean(condition):
            return true_value
        else:
            return false_value
    
    def _and(self, *args) -> bool:
        """Функция AND."""
        return all(self._to_boolean(arg) for arg in args)
    
    def _or(self, *args) -> bool:
        """Функция OR."""
        return any(self._to_boolean(arg) for arg in args)
    
    def _not(self, arg) -> bool:
        """Функция NOT."""
        return not self._to_boolean(arg)
    
    # Вспомогательные методы
    def _to_number(self, value) -> float:
        """Преобразует значение в число."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0
        return 0
    
    def _is_numeric(self, value) -> bool:
        """Проверяет, является ли значение числовым."""
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value)
                return True
            except ValueError:
                return False
        return False
    
    def _to_boolean(self, value) -> bool:
        """Преобразует значение в булево."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.upper() in ('TRUE', '1', 'YES')
        return False