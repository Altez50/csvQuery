# VSCode-Style CSV and SQLite Editor

A modern, VSCode-inspired application for CSV editing and SQLite database querying built with PyQt5.

## Features

### 🎨 VSCode-Like Interface
- **Central Editor Tabs**: Switch between CSV Editor, SQL Query Editor, Python Code Editor, and AI Assistant
- **Left Dock Panel**: File Explorer, Table Manager, Query History, Code Snippets
- **Right Dock Panel**: Table Structure, Query Results Info
- **Bottom Dock Panel**: Terminal, Problems List
- **Status Bar**: Real-time application status
- **Toolbar**: Quick access to common operations

### 📊 CSV Editor
- Load and edit CSV files with advanced table view
- Add/delete rows and columns
- Advanced search with multiple modes (any, all, exact, regex)
- Case-sensitive search options
- Import CSV data directly into SQLite database
- Automatic header cleaning for SQLite compatibility

### 🗄️ SQL Query Editor
- Syntax-highlighted SQL editor with QScintilla
- Execute queries against SQLite databases
- Query parameter management
- Query history tracking
- Results display in tabular format
- Find and replace functionality
- SQL formatting and field insertion
- Task number tracking

### 🐍 Python Code Editor
- Full Python code editor with syntax highlighting
- Execute Python code with access to application variables
- Code snippet management system
- Integration with CSV and SQL editors
- Capture and display execution output
- Save and load code snippets by category

### 🤖 AI Assistant
- Integration with OpenAI API (configurable)
- Context-aware assistance based on current data
- Chat history management
- Extract code from AI responses to Python editor
- Configurable AI model settings (temperature, max tokens)
- Save and load chat sessions

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

## Usage

### Getting Started
1. Launch the application
2. Use **File > New Database** to create a new SQLite database
3. Load CSV data using the CSV Editor tab
4. Import CSV data to database using the "Import to DB" button
5. Write and execute SQL queries in the SQL Query Editor
6. Use Python Code Editor for data analysis and automation
7. Configure AI Assistant for intelligent help (requires OpenAI API key)

### Key Shortcuts
- **F5**: Execute Python code
- **Ctrl+Enter**: Send AI prompt
- **Ctrl+N**: New database
- **Ctrl+O**: Open database
- **Ctrl+S**: Save session
- **Ctrl+Q**: Quit application

### Available Python Variables
When writing Python code, you have access to:
- `main_window`: Main application window
- `sql_editor`: SQL query editor instance
- `csv_editor`: CSV editor instance
- `results_table`: Query results table
- `csv_table`: CSV data table

## File Structure

```
src/
├── main.py                 # Application entry point
├── vscode_main_window.py    # Main window implementation
├── csv_editor.py           # CSV editing functionality
├── sql_query_editor.py     # SQL querying functionality
├── python_code_editor.py   # Python code editor
├── ai_assistant.py         # AI assistant integration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Configuration Files

The application creates several configuration files:
- `../ai_config.json`: AI assistant settings
- `../chat_history.json`: AI chat history
- `../python_snippets.json`: Python code snippets
- `../query_history.json`: SQL query history
- `../editor_settings.json`: SQL editor settings

## Dependencies

- **PyQt5**: GUI framework
- **QScintilla**: Advanced text editor component
- **pandas**: Data manipulation (for Python code execution)
- **numpy**: Numerical computing (for Python code execution)
- **sqlite3**: Database operations (built-in)

## Notes

- The AI Assistant requires an OpenAI API key for full functionality
- Without an API key, the AI Assistant will show mock responses
- All data is stored locally in SQLite databases
- The application supports session management for preserving work state

## License

This project is open source and available under the MIT License.