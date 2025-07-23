from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QSpinBox, QScrollArea, QMessageBox
from PyQt5.QtCore import QSettings, Qt
import requests
import json

class AIPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._settings = QSettings('csvQuery', 'AIPage')
        self.init_ui()
        self.load_settings()
        self.chat_history = []

    def init_ui(self):
        layout = QVBoxLayout(self)
        # --- Настройки OpenAI ---
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel('Model:'))
        self.model_edit = QLineEdit()
        self.model_edit.setText('gpt-3.5-turbo')
        settings_layout.addWidget(self.model_edit)
        settings_layout.addWidget(QLabel('Token:'))
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.Password)
        settings_layout.addWidget(self.token_edit)
        settings_layout.addWidget(QLabel('Temperature:'))
        self.temp_spin = QSpinBox()
        self.temp_spin.setRange(0, 20)
        self.temp_spin.setValue(7)
        settings_layout.addWidget(self.temp_spin)
        save_btn = QPushButton('Сохранить')
        save_btn.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_btn)
        layout.addLayout(settings_layout)
        # --- История чата ---
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        layout.addWidget(self.chat_area, 1)
        # --- Ввод запроса ---
        input_layout = QHBoxLayout()
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText('Введите запрос к ChatGPT...')
        self.prompt_edit.setFixedHeight(60)
        input_layout.addWidget(self.prompt_edit, 1)
        self.send_btn = QPushButton('Отправить')
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)
        # --- Вывод кода и вставка ---
        self.code_label = QLabel('<b>Сгенерированный код:</b>')
        layout.addWidget(self.code_label)
        self.code_area = QTextEdit()
        self.code_area.setReadOnly(True)
        self.code_area.setStyleSheet('font-family: monospace; background: #f8f8f8;')
        layout.addWidget(self.code_area)
        self.insert_btn = QPushButton('Вставить код в Python-редактор')
        self.insert_btn.clicked.connect(self.insert_code_to_python)
        layout.addWidget(self.insert_btn)

    def load_settings(self):
        self.model_edit.setText(self._settings.value('model', 'gpt-3.5-turbo'))
        self.token_edit.setText(self._settings.value('token', ''))
        self.temp_spin.setValue(int(self._settings.value('temperature', 7)))

    def save_settings(self):
        self._settings.setValue('model', self.model_edit.text())
        self._settings.setValue('token', self.token_edit.text())
        self._settings.setValue('temperature', self.temp_spin.value())
        QMessageBox.information(self, 'Настройки', 'Настройки сохранены.')

    def send_message(self):
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            return
        self.append_chat('Вы', prompt)
        self.prompt_edit.clear()
        try:
            code = self.ask_openai(prompt)
            self.append_chat('ChatGPT', code)
            self.code_area.setPlainText(code)
        except Exception as e:
            self.append_chat('ChatGPT', f'Ошибка: {e}')
            self.code_area.setPlainText(f'Ошибка: {e}')

    def append_chat(self, who, text):
        self.chat_area.append(f'<b>{who}:</b>')
        self.chat_area.append(text)
        self.chat_area.append('')

    def ask_openai(self, prompt):
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.token_edit.text().strip()}',
            'Content-Type': 'application/json'
        }
        messages = [
            {"role": "system", "content": "Ты пишешь только рабочий Python-код для обработки QTableWidget csv_table. Не добавляй комментарии и текст вне кода."},
            {"role": "user", "content": prompt}
        ]
        data = {
            "model": self.model_edit.text().strip(),
            "messages": messages,
            "temperature": self.temp_spin.value() / 10.0
        }
        resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=60)
        if resp.status_code != 200:
            raise Exception(f'Ошибка OpenAI: {resp.status_code} {resp.text}')
        result = resp.json()
        code = result['choices'][0]['message']['content']
        # Оставить только код (если вдруг LLM добавил текст)
        code = self.extract_code(code)
        return code

    def extract_code(self, text):
        # Извлечь только код из markdown или текста
        import re
        code_blocks = re.findall(r'```(?:python)?\n([\s\S]+?)```', text)
        if code_blocks:
            return code_blocks[0].strip()
        return text.strip()

    def insert_code_to_python(self):
        code = self.code_area.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, 'Нет кода', 'Нет сгенерированного кода для вставки.')
            return
        # Вставить в PythonPage
        if hasattr(self.main_window, 'python_tab'):
            self.main_window.python_tab.code_edit.setText(code)
            self.main_window.tabs.setCurrentWidget(self.main_window.python_tab)
            self.main_window.python_tab.raise_()
            self.main_window.python_tab.activateWindow()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Python-редактор не найден.') 