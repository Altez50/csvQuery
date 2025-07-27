Вот дерево связей основных классов вашего проекта (csvQuery):

```mermaid
classDiagram
    MainWindow <|-- TableManagerDialog
    MainWindow <|-- SQLQueryPage
    MainWindow <|-- ColumnSelectDialog
    MainWindow <|-- OptionsDialog
    MainWindow <|-- TableEditDialog
    VSCodeMainWindow <|-- MainWindow
    SQLQueryPage <|-- QueryTreeDialog
    SQLQueryPage <|-- ResultsDialog
    TableManagerDialog <|-- TableEditDialog
    SQLQueryPage <|-- ColumnSelectDialog
    SQLQueryPage <|-- GroupByDialog

    class VSCodeMainWindow {
        +QFileSystemModel file_model
        +QTreeView file_tree
        +QLineEdit address_bar
        +QComboBox file_filter
        +QPushButton up_button
        +QPushButton home_button
        +navigate_to_path()
        +navigate_up()
        +navigate_home()
        +update_address_bar()
        +apply_file_filter()
    }
    class MainWindow {
        +QTabWidget tabs
        +sqlite_conn
        +table_manager_dialog
        +csv_tab
        +sql_tab
    }
    class TableManagerDialog {
        +main_window
        +table_tree
    }
    class SQLQueryPage {
        +conn
        +history
        +query_tree_dialog
        +results_dialog
    }
    class TableEditDialog {
        +sqlite_conn
        +table_name
    }
    class QueryTreeDialog {
        +sql_query_page
    }
    class ResultsDialog {
        +parent
    }
    class ColumnSelectDialog {
        +columns
        +selected_columns
    }
    class GroupByDialog {
        +group_col
        +groups
        +headers
    }
    class OptionsDialog {
        +confirm_exit_checkbox
    }
```

**Пояснения:**
- `VSCodeMainWindow` — расширенное главное окно с файловым проводником, наследует от `MainWindow` и добавляет:
  - Файловый проводник с деревом файлов (`QFileSystemModel` + `QTreeView`)
  - Адресную строку для навигации по директориям (`QLineEdit`)
  - Фильтрацию файлов по типу (`QComboBox`)
  - Кнопки навигации "Вверх" и "Домой" (`QPushButton`)
  - Методы для навигации и обновления интерфейса
- `MainWindow` — базовое главное окно приложения, содержит вкладки, менеджер таблиц, соединение с БД и т.д.
- `TableManagerDialog` — диалог управления таблицами, вызывается из `MainWindow`.
- `TableEditDialog` — диалог редактирования таблицы, вызывается из `TableManagerDialog` и использует соединение с БД.
- `SQLQueryPage` — страница для работы с SQL-запросами, одна из вкладок в `MainWindow`.
- `QueryTreeDialog` и `ResultsDialog` — вспомогательные диалоги для работы с историей запросов и результатами, используются в `SQLQueryPage`.
- `ColumnSelectDialog` — диалог выбора столбцов, используется в разных местах.
- `GroupByDialog` — диалог группировки данных, вызывается из SQL-запросов.
- `OptionsDialog` — диалог настроек, вызывается из `MainWindow`.