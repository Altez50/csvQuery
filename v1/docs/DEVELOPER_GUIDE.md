# Руководство разработчика csvQuery

## Содержание

1. [Архитектура проекта](#архитектура-проекта)
2. [Структура кода](#структура-кода)
3. [Настройка среды разработки](#настройка-среды-разработки)
4. [Сборка проекта](#сборка-проекта)
5. [Основные компоненты](#основные-компоненты)
6. [API и интерфейсы](#api-и-интерфейсы)
7. [Работа с данными](#работа-с-данными)
8. [Система плагинов](#система-плагинов)
9. [Тестирование](#тестирование)
10. [Развертывание](#развертывание)
11. [Участие в разработке](#участие-в-разработке)

## Архитектура проекта

### Общая архитектура

csvQuery построен на основе PyQt5 и использует модульную архитектуру:

```
┌─────────────────┐
│   UI Layer      │  ← PyQt5 виджеты и диалоги
├─────────────────┤
│ Business Logic  │  ← Обработка данных, SQL
├─────────────────┤
│   Data Layer    │  ← SQLite, pandas, файловые операции
└─────────────────┘
```

### Принципы проектирования

1. **Модульность** - каждый компонент имеет четко определенную ответственность
2. **Расширяемость** - легко добавлять новые функции
3. **Переиспользование** - общие компоненты выделены в отдельные модули
4. **Тестируемость** - бизнес-логика отделена от UI

### Технологический стек

- **Python 3.8+** - основной язык
- **PyQt5** - графический интерфейс
- **pandas** - обработка данных
- **SQLite** - встроенная база данных
- **QScintilla** - редактор кода с подсветкой
- **requests** - HTTP запросы
- **PyInstaller** - создание исполняемых файлов

## Структура кода

### Основные файлы

```
csvQuery/
├── main.py                 # Точка входа
├── ui_mainwindow.py        # Главное окно и основные виджеты
├── sql_query_constructor.py # SQL редактор и выполнение запросов
├── sql_query_page.py       # Страница SQL запросов
├── table_edit_dialog.py    # Диалог редактирования таблиц
├── table_compare_dialog.py # Сравнение таблиц
├── group_by_dialog.py      # Группировка данных
├── results_dialog.py       # Отображение результатов
├── notification_widget.py  # Уведомления
├── version_info.py         # Информация о версии
├── requirements.txt        # Зависимости
├── build.cmd              # Скрипт сборки
└── docs/                  # Документация
    ├── USER_GUIDE.md
    ├── DEVELOPER_GUIDE.md
    └── RELEASE_NOTES.md
```

### Модули и их назначение

#### `ui_mainwindow.py`
- **MainWindow** - главное окно приложения
- **RecentFilesWidget** - виджет недавних файлов
- **AdvancedSearchWidget** - расширенный поиск
- **TableManagerWidget** - управление таблицами
- **DraggableTableWidget** - таблица с drag&drop

#### `sql_query_constructor.py`
- **SqlQueryConstructor** - основной класс SQL редактора
- **QueryHistoryWidget** - история запросов
- **ParameterDialog** - диалог параметров запросов

#### Вспомогательные функции
- `clean_header()` - очистка заголовков таблиц
- `make_unique_headers()` - создание уникальных заголовков
- `get_last_modification_date()` - получение даты модификации

## Настройка среды разработки

### Требования

- Python 3.8 или новее
- pip (менеджер пакетов Python)
- Git
- IDE (рекомендуется PyCharm или VSCode)

### Установка зависимостей

```bash
# Клонирование репозитория
git clone <repository_url>
cd csvQuery

# Создание виртуального окружения
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Установка зависимостей
pip install -r requirements.txt
```

### Настройка IDE

#### PyCharm
1. Откройте проект в PyCharm
2. Настройте интерпретатор Python (виртуальное окружение)
3. Установите плагины для PyQt5
4. Настройте форматирование кода (PEP 8)

#### VSCode
1. Установите расширения:
   - Python
   - PyQt Integration
   - Python Docstring Generator
2. Настройте `settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true
}
```

### Запуск в режиме разработки

```bash
# Активация виртуального окружения
venv\Scripts\activate

# Запуск приложения
python main.py

# Запуск с отладочной информацией
python main.py --debug
```

## Сборка проекта

### Автоматическая сборка

```bash
# Сборка исполняемого файла
.\build.cmd

# Сборка с очисткой
.\build_with_cleanup.cmd
```

### Ручная сборка

```bash
# Установка PyInstaller
pip install pyinstaller

# Создание исполняемого файла
pyinstaller --onefile --windowed --name csvQuery main.py

# С дополнительными параметрами
pyinstaller --onefile --windowed --name csvQuery \
    --add-data "icons;icons" \
    --add-data "templates;templates" \
    main.py
```

### Настройка сборки

Файл `build.cmd` автоматически:
1. Получает текущую дату и время
2. Создает исполняемый файл с временной меткой
3. Копирует файл в папку `dist`
4. Очищает временные файлы

## Основные компоненты

### MainWindow

Главное окно приложения, наследуется от `QMainWindow`.

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        pass
    
    def setup_connections(self):
        """Настройка сигналов и слотов"""
        pass
```

#### Основные методы:
- `open_session_file()` - открытие файлов сессий
- `load_csv_file_direct()` - прямая загрузка CSV
- `load_excel_file_direct()` - прямая загрузка Excel
- `save_session()` - сохранение сессии
- `export_data()` - экспорт данных

### SqlQueryConstructor

Основной класс для работы с SQL запросами.

```python
class SqlQueryConstructor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()
        self.setup_database()
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Выполнение SQL запроса"""
        pass
    
    def save_query_to_history(self, query: str, name: str):
        """Сохранение запроса в историю"""
        pass
```

#### Ключевые возможности:
- Подсветка синтаксиса SQL
- Автодополнение
- Выполнение запросов
- Управление историей
- Параметризованные запросы

### RecentFilesWidget

Виджет для управления недавними файлами.

```python
class RecentFilesWidget(QWidget):
    file_selected = pyqtSignal(str)  # Сигнал выбора файла
    
    def add_recent_file(self, file_path: str):
        """Добавление файла в список"""
        pass
    
    def load_recent_files(self) -> List[str]:
        """Загрузка списка из файла"""
        pass
    
    def save_recent_files(self):
        """Сохранение списка в файл"""
        pass
```

## API и интерфейсы

### Работа с файлами

#### Интерфейс FileHandler

```python
from abc import ABC, abstractmethod

class FileHandler(ABC):
    @abstractmethod
    def can_handle(self, file_path: str) -> bool:
        """Проверка возможности обработки файла"""
        pass
    
    @abstractmethod
    def load_file(self, file_path: str) -> pd.DataFrame:
        """Загрузка файла"""
        pass
    
    @abstractmethod
    def save_file(self, data: pd.DataFrame, file_path: str):
        """Сохранение файла"""
        pass
```

#### Реализации

```python
class CsvHandler(FileHandler):
    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith('.csv')
    
    def load_file(self, file_path: str) -> pd.DataFrame:
        # Определение кодировки
        encoding = self.detect_encoding(file_path)
        return pd.read_csv(file_path, encoding=encoding)

class ExcelHandler(FileHandler):
    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.xlsx', '.xls', '.ods'))
    
    def load_file(self, file_path: str) -> pd.DataFrame:
        return pd.read_excel(file_path)
```

### Система событий

#### Основные сигналы

```python
# В MainWindow
data_loaded = pyqtSignal(pd.DataFrame)  # Данные загружены
query_executed = pyqtSignal(str, pd.DataFrame)  # Запрос выполнен
file_opened = pyqtSignal(str)  # Файл открыт

# В SqlQueryConstructor
query_changed = pyqtSignal(str)  # Запрос изменен
history_updated = pyqtSignal()  # История обновлена

# В RecentFilesWidget
file_selected = pyqtSignal(str)  # Файл выбран
list_cleared = pyqtSignal()  # Список очищен
```

## Работа с данными

### Модель данных

Приложение использует pandas DataFrame как основную структуру данных:

```python
class DataManager:
    def __init__(self):
        self.current_data: pd.DataFrame = None
        self.original_data: pd.DataFrame = None
        self.filtered_data: pd.DataFrame = None
    
    def load_data(self, data: pd.DataFrame):
        """Загрузка новых данных"""
        self.original_data = data.copy()
        self.current_data = data.copy()
        self.apply_filters()
    
    def apply_filters(self):
        """Применение фильтров"""
        # Логика фильтрации
        pass
    
    def get_column_info(self) -> Dict[str, Any]:
        """Получение информации о колонках"""
        return {
            'columns': list(self.current_data.columns),
            'types': self.current_data.dtypes.to_dict(),
            'null_counts': self.current_data.isnull().sum().to_dict()
        }
```

### SQL выполнение

```python
import sqlite3
import pandas as pd

class SqlExecutor:
    def __init__(self):
        self.connection = sqlite3.connect(':memory:')
    
    def load_dataframe(self, df: pd.DataFrame, table_name: str = 'imported_data'):
        """Загрузка DataFrame в SQLite"""
        df.to_sql(table_name, self.connection, if_exists='replace', index=False)
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Выполнение SQL запроса"""
        try:
            result = pd.read_sql_query(query, self.connection)
            return result
        except Exception as e:
            raise SqlExecutionError(f"Ошибка выполнения запроса: {e}")
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """Получение информации о таблице"""
        query = f"PRAGMA table_info({table_name})"
        return pd.read_sql_query(query, self.connection).to_dict('records')
```

### Обработка ошибок

```python
class CsvQueryError(Exception):
    """Базовый класс ошибок приложения"""
    pass

class FileLoadError(CsvQueryError):
    """Ошибка загрузки файла"""
    pass

class SqlExecutionError(CsvQueryError):
    """Ошибка выполнения SQL"""
    pass

class DataValidationError(CsvQueryError):
    """Ошибка валидации данных"""
    pass
```

## Система плагинов

### Архитектура плагинов

```python
from abc import ABC, abstractmethod

class Plugin(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """Название плагина"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Версия плагина"""
        pass
    
    @abstractmethod
    def initialize(self, main_window):
        """Инициализация плагина"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Очистка ресурсов"""
        pass

class PluginManager:
    def __init__(self):
        self.plugins: List[Plugin] = []
    
    def load_plugin(self, plugin_path: str):
        """Загрузка плагина"""
        pass
    
    def unload_plugin(self, plugin_name: str):
        """Выгрузка плагина"""
        pass
```

### Пример плагина

```python
class ExportPlugin(Plugin):
    def get_name(self) -> str:
        return "Advanced Export"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def initialize(self, main_window):
        # Добавление пункта меню
        export_action = QAction("Export to JSON", main_window)
        export_action.triggered.connect(self.export_to_json)
        main_window.file_menu.addAction(export_action)
    
    def export_to_json(self):
        # Логика экспорта
        pass
```

## Тестирование

### Структура тестов

```
tests/
├── unit/
│   ├── test_data_manager.py
│   ├── test_sql_executor.py
│   └── test_file_handlers.py
├── integration/
│   ├── test_file_loading.py
│   └── test_query_execution.py
└── ui/
    ├── test_main_window.py
    └── test_dialogs.py
```

### Примеры тестов

#### Unit тесты

```python
import unittest
import pandas as pd
from csvquery.data_manager import DataManager

class TestDataManager(unittest.TestCase):
    def setUp(self):
        self.data_manager = DataManager()
        self.test_data = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['New York', 'London', 'Paris']
        })
    
    def test_load_data(self):
        self.data_manager.load_data(self.test_data)
        self.assertIsNotNone(self.data_manager.current_data)
        self.assertEqual(len(self.data_manager.current_data), 3)
    
    def test_get_column_info(self):
        self.data_manager.load_data(self.test_data)
        info = self.data_manager.get_column_info()
        self.assertIn('columns', info)
        self.assertEqual(len(info['columns']), 3)
```

#### Integration тесты

```python
import unittest
import tempfile
import os
from csvquery.main_window import MainWindow
from PyQt5.QtWidgets import QApplication

class TestFileLoading(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])
    
    def setUp(self):
        self.main_window = MainWindow()
        
        # Создание тестового CSV файла
        self.test_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.test_csv.write('name,age,city\n')
        self.test_csv.write('Alice,25,New York\n')
        self.test_csv.write('Bob,30,London\n')
        self.test_csv.close()
    
    def tearDown(self):
        os.unlink(self.test_csv.name)
    
    def test_load_csv_file(self):
        self.main_window.load_csv_file_direct(self.test_csv.name)
        # Проверка загрузки данных
        self.assertIsNotNone(self.main_window.current_data)
        self.assertEqual(len(self.main_window.current_data), 2)
```

### Запуск тестов

```bash
# Все тесты
python -m pytest tests/

# Только unit тесты
python -m pytest tests/unit/

# С покрытием кода
python -m pytest tests/ --cov=csvquery --cov-report=html

# Конкретный тест
python -m pytest tests/unit/test_data_manager.py::TestDataManager::test_load_data
```

## Развертывание

### Создание релиза

1. **Обновление версии**
   ```python
   # В version_info.py
   VERSION = "1.1.0"
   ```

2. **Обновление CHANGELOG**
   ```markdown
   ## [1.1.0] - 2025-02-01
   ### Added
   - Новая функция экспорта
   ### Fixed
   - Исправлена ошибка загрузки
   ```

3. **Сборка**
   ```bash
   .\build_with_cleanup.cmd
   ```

4. **Тестирование**
   ```bash
   # Запуск всех тестов
   python -m pytest tests/
   
   # Ручное тестирование
   dist\csvQuery_YYYY-MM-DD_HH-MM.exe
   ```

### CI/CD Pipeline

```yaml
# .github/workflows/build.yml
name: Build and Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        python -m pytest tests/ --cov=csvquery
    - name: Build executable
      run: |
        .\build.cmd
    - name: Upload artifact
      uses: actions/upload-artifact@v2
      with:
        name: csvQuery-executable
        path: dist/*.exe
```

## Участие в разработке

### Процесс разработки

1. **Fork репозитория**
2. **Создание ветки для функции**
   ```bash
   git checkout -b feature/new-export-format
   ```
3. **Разработка и тестирование**
4. **Создание Pull Request**
5. **Code Review**
6. **Merge в main**

### Стандарты кодирования

#### Python код
- Следуйте PEP 8
- Используйте type hints
- Документируйте функции docstrings
- Максимальная длина строки: 88 символов

```python
def process_data(data: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Обработка данных по указанным колонкам.
    
    Args:
        data: Исходные данные
        columns: Список колонок для обработки
    
    Returns:
        Обработанные данные
    
    Raises:
        DataValidationError: Если данные некорректны
    """
    if data.empty:
        raise DataValidationError("Данные не могут быть пустыми")
    
    return data[columns].copy()
```

#### Commit сообщения

Используйте Conventional Commits:

```
feat: добавлена поддержка экспорта в JSON
fix: исправлена ошибка загрузки больших файлов
docs: обновлена документация API
test: добавлены тесты для SqlExecutor
refactor: рефакторинг класса DataManager
```

### Настройка pre-commit hooks

```bash
# Установка pre-commit
pip install pre-commit

# Настройка hooks
pre-commit install
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
```

### Отладка

#### Логирование

```python
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('csvquery.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Использование
logger.debug("Загрузка файла: %s", file_path)
logger.info("Данные успешно загружены")
logger.warning("Обнаружены дубликаты заголовков")
logger.error("Ошибка выполнения запроса: %s", str(e))
```

#### Профилирование

```python
import cProfile
import pstats

def profile_function(func):
    """Декоратор для профилирования функций"""
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()
        
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
        
        return result
    return wrapper

# Использование
@profile_function
def load_large_file(file_path):
    return pd.read_csv(file_path)
```

---

**Версия документа**: 1.0  
**Дата обновления**: Январь 2025  
**Применимо к**: csvQuery v1.0+