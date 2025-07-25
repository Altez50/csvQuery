import json
import os
import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QFormLayout, QMessageBox, QSplitter, QListWidget,
    QListWidgetItem, QToolBar, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon

CONFIG_FILE = '../ai_config.json'
CHAT_HISTORY_FILE = '../chat_history.json'

class AIRequestThread(QThread):
    """Thread for making AI API requests"""
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_key, model, prompt, temperature, max_tokens):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.prompt = prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        
    def run(self):
        try:
            # Note: This is a placeholder for OpenAI API integration
            # In a real implementation, you would use the openai library
            # import openai
            # openai.api_key = self.api_key
            # response = openai.ChatCompletion.create(...)
            
            # For now, return a mock response
            mock_response = f"""This is a mock AI response for the prompt: "{self.prompt[:50]}..."
            
Here's some example Python code that might be helpful:

```python
# Example: Data analysis with pandas
import pandas as pd
import numpy as np

# Load data from CSV editor
if csv_editor.csv_data and csv_editor.csv_headers:
    df = pd.DataFrame(csv_editor.csv_data, columns=csv_editor.csv_headers)
    print(f"Dataset shape: {df.shape}")
    print(df.head())
else:
    print("No CSV data available")
```

To use this code:
1. Copy the code block
2. Paste it into the Python editor
3. Execute it with F5

Note: This is a mock response. To use real AI, configure your OpenAI API key in the settings."""
            
            self.response_received.emit(mock_response)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class AIAssistant(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.config = self.load_config()
        self.chat_history = self.load_chat_history()
        self.current_thread = None
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(20, 20))
        
        self.clear_chat_btn = QPushButton("Clear Chat")
        self.clear_chat_btn.clicked.connect(self.clear_chat)
        toolbar.addWidget(self.clear_chat_btn)
        
        toolbar.addSeparator()
        
        self.save_history_btn = QPushButton("Save History")
        self.save_history_btn.clicked.connect(self.save_chat_history)
        toolbar.addWidget(self.save_history_btn)
        
        self.load_history_btn = QPushButton("Load History")
        self.load_history_btn.clicked.connect(self.load_chat_history_dialog)
        toolbar.addWidget(self.load_history_btn)
        
        layout.addWidget(toolbar)
        
        # Configuration panel
        config_group = QGroupBox("AI Configuration")
        config_layout = QFormLayout(config_group)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setText(self.config.get('api_key', ''))
        self.api_key_edit.setPlaceholderText("Enter your OpenAI API key")
        config_layout.addRow("API Key:", self.api_key_edit)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo-preview",
            "gpt-3.5-turbo-16k"
        ])
        self.model_combo.setCurrentText(self.config.get('model', 'gpt-3.5-turbo'))
        config_layout.addRow("Model:", self.model_combo)
        
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(self.config.get('temperature', 0.7))
        config_layout.addRow("Temperature:", self.temperature_spin)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 4000)
        self.max_tokens_spin.setValue(self.config.get('max_tokens', 1000))
        config_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        self.save_config_btn = QPushButton("Save Config")
        self.save_config_btn.clicked.connect(self.save_config)
        config_layout.addRow(self.save_config_btn)
        
        layout.addWidget(config_group)
        
        # Main chat area
        splitter = QSplitter(Qt.Vertical)
        
        # Chat history
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))
        splitter.addWidget(self.chat_display)
        
        # Input area
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        
        input_layout.addWidget(QLabel("Your prompt:"))
        
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setMaximumHeight(100)
        self.prompt_edit.setPlaceholderText(
            "Enter your question or request here...\n\n"
            "Examples:\n"
            "- Analyze the CSV data and show basic statistics\n"
            "- Create a SQL query to find duplicates\n"
            "- Generate Python code to visualize the data"
        )
        input_layout.addWidget(self.prompt_edit)
        
        # Send button
        button_layout = QHBoxLayout()
        self.send_btn = QPushButton("Send (Ctrl+Enter)")
        self.send_btn.clicked.connect(self.send_prompt)
        self.send_btn.setShortcut('Ctrl+Return')
        button_layout.addWidget(self.send_btn)
        
        self.extract_code_btn = QPushButton("Extract Code to Python Editor")
        self.extract_code_btn.clicked.connect(self.extract_code_to_editor)
        button_layout.addWidget(self.extract_code_btn)
        
        button_layout.addStretch()
        input_layout.addLayout(button_layout)
        
        splitter.addWidget(input_widget)
        splitter.setSizes([300, 150])
        
        layout.addWidget(splitter)
        
        # Load chat history
        self.update_chat_display()
        
    def load_config(self):
        """Load AI configuration"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'api_key': '',
            'model': 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
    def save_config(self):
        """Save AI configuration"""
        self.config = {
            'api_key': self.api_key_edit.text(),
            'model': self.model_combo.currentText(),
            'temperature': self.temperature_spin.value(),
            'max_tokens': self.max_tokens_spin.value()
        }
        
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Success", "Configuration saved successfully")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save configuration: {e}")
            
    def load_chat_history(self):
        """Load chat history"""
        if os.path.exists(CHAT_HISTORY_FILE):
            try:
                with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []
        
    def save_chat_history(self):
        """Save chat history"""
        try:
            with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Success", "Chat history saved successfully")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save chat history: {e}")
            
    def load_chat_history_dialog(self):
        """Load chat history from file dialog"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Chat History", "", "JSON files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.chat_history = json.load(f)
                self.update_chat_display()
                QMessageBox.information(self, "Success", "Chat history loaded successfully")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load chat history: {e}")
                
    def update_chat_display(self):
        """Update chat display with history"""
        self.chat_display.clear()
        
        for entry in self.chat_history:
            timestamp = entry.get('timestamp', 'Unknown time')
            prompt = entry.get('prompt', '')
            response = entry.get('response', '')
            
            self.chat_display.append(f"<b>[{timestamp}] User:</b>")
            self.chat_display.append(prompt)
            self.chat_display.append("")
            self.chat_display.append(f"<b>AI Assistant:</b>")
            self.chat_display.append(response)
            self.chat_display.append("-" * 50)
            self.chat_display.append("")
            
    def send_prompt(self):
        """Send prompt to AI"""
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Warning", "Please enter a prompt")
            return
            
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(
                self, "Warning", 
                "Please enter your OpenAI API key in the configuration section"
            )
            return
            
        # Disable send button
        self.send_btn.setEnabled(False)
        self.send_btn.setText("Sending...")
        
        # Add context about current state
        context_info = self.get_context_info()
        full_prompt = f"{context_info}\n\nUser request: {prompt}"
        
        # Start AI request thread
        self.current_thread = AIRequestThread(
            api_key=api_key,
            model=self.model_combo.currentText(),
            prompt=full_prompt,
            temperature=self.temperature_spin.value(),
            max_tokens=self.max_tokens_spin.value()
        )
        
        self.current_thread.response_received.connect(self.on_response_received)
        self.current_thread.error_occurred.connect(self.on_error_occurred)
        self.current_thread.start()
        
    def get_context_info(self):
        """Get context information about current state"""
        context = "Current application state:\n"
        
        # CSV data info
        if hasattr(self.main_window, 'csv_editor') and self.main_window.csv_editor.csv_data:
            rows = len(self.main_window.csv_editor.csv_data)
            cols = len(self.main_window.csv_editor.csv_headers) if self.main_window.csv_editor.csv_headers else 0
            context += f"- CSV data loaded: {rows} rows, {cols} columns\n"
            if self.main_window.csv_editor.csv_headers:
                context += f"- CSV headers: {', '.join(self.main_window.csv_editor.csv_headers[:5])}{'...' if len(self.main_window.csv_editor.csv_headers) > 5 else ''}\n"
        else:
            context += "- No CSV data loaded\n"
            
        # Database info
        if hasattr(self.main_window, 'sqlite_conn') and self.main_window.sqlite_conn:
            context += "- SQLite database connected\n"
        else:
            context += "- No database connection\n"
            
        # Current SQL query
        if hasattr(self.main_window, 'sql_editor') and self.main_window.sql_editor.sql_edit.text().strip():
            query = self.main_window.sql_editor.sql_edit.text().strip()[:100]
            context += f"- Current SQL query: {query}{'...' if len(query) == 100 else ''}\n"
            
        context += "\nPlease provide helpful assistance based on this context."
        return context
        
    def on_response_received(self, response):
        """Handle AI response"""
        import datetime
        
        # Add to chat history
        self.chat_history.append({
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'prompt': self.prompt_edit.toPlainText(),
            'response': response
        })
        
        # Update display
        self.update_chat_display()
        
        # Clear prompt
        self.prompt_edit.clear()
        
        # Re-enable send button
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send (Ctrl+Enter)")
        
        # Log to main window
        self.main_window.log_message("AI response received")
        
    def on_error_occurred(self, error):
        """Handle AI request error"""
        QMessageBox.warning(self, "AI Request Error", f"Failed to get AI response: {error}")
        
        # Re-enable send button
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send (Ctrl+Enter)")
        
        # Log to main window
        self.main_window.log_message(f"AI request failed: {error}")
        
    def extract_code_to_editor(self):
        """Extract Python code from AI response and insert into Python editor"""
        if not self.chat_history:
            QMessageBox.information(self, "Info", "No chat history available")
            return
            
        # Get the last AI response
        last_response = self.chat_history[-1].get('response', '')
        
        # Extract code blocks
        code_blocks = re.findall(r'```python\n(.*?)\n```', last_response, re.DOTALL)
        if not code_blocks:
            code_blocks = re.findall(r'```\n(.*?)\n```', last_response, re.DOTALL)
            
        if not code_blocks:
            QMessageBox.information(self, "Info", "No code blocks found in the last AI response")
            return
            
        # If multiple code blocks, use the first one
        code = code_blocks[0].strip()
        
        # Insert into Python editor
        if hasattr(self.main_window, 'python_editor'):
            current_code = self.main_window.python_editor.get_code_text()
            if current_code.strip():
                # Append to existing code
                new_code = current_code + "\n\n# Code from AI Assistant:\n" + code
            else:
                new_code = "# Code from AI Assistant:\n" + code
                
            self.main_window.python_editor.set_code_text(new_code)
            
            # Switch to Python editor tab
            self.main_window.editor_tabs.setCurrentWidget(self.main_window.python_editor)
            
            QMessageBox.information(self, "Success", "Code extracted and inserted into Python editor")
        else:
            QMessageBox.warning(self, "Error", "Python editor not available")
            
    def clear_chat(self):
        """Clear chat history"""
        reply = QMessageBox.question(
            self, "Clear Chat", 
            "Are you sure you want to clear the chat history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.chat_history.clear()
            self.chat_display.clear()
            self.main_window.log_message("Chat history cleared")