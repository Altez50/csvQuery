from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QSpinBox, QScrollArea, QMessageBox, QToolButton
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QIcon
import requests
import json

class AIPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._settings = QSettings('csvQuery', 'AIPage')
        self.current_profile = None
        self.init_ui()
        self.load_profiles()
        self.load_settings()
        self.chat_history = []

    def init_ui(self):
        layout = QVBoxLayout(self)
        # --- Настройки AI ---
        settings_layout = QHBoxLayout()
        
        # AI Profile selection
        settings_layout.addWidget(QLabel('AI Profile:'))
        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        settings_layout.addWidget(self.profile_combo)
        
        # Gear button for AI options
        self.gear_btn = QToolButton()
        self.gear_btn.setIcon(QIcon("icons/settings.png"))
        self.gear_btn.setToolTip("AI Profile Settings")
        self.gear_btn.clicked.connect(self.open_ai_options)
        settings_layout.addWidget(self.gear_btn)
        
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
        selected_profile = self._settings.value('selected_profile', '')
        self.temp_spin.setValue(int(self._settings.value('temperature', 7)))
        
        # Set the selected profile in combobox
        if selected_profile and self.profile_combo.findText(selected_profile) >= 0:
            self.profile_combo.setCurrentText(selected_profile)
        elif self.profile_combo.count() > 0:
            self.profile_combo.setCurrentIndex(0)

    def save_settings(self, show_message=True):
        self._settings.setValue('selected_profile', self.profile_combo.currentText())
        self._settings.setValue('temperature', self.temp_spin.value())
        if show_message:
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
        profile_settings = self.get_current_profile_settings()
        url = profile_settings.get('url', 'https://openrouter.ai/api/v1/chat/completions')
        headers = {
            'Authorization': f'Bearer {profile_settings["token"].strip()}',
            'Content-Type': 'application/json'
        }
        messages = [
            {"role": "system", "content": "Ты пишешь только рабочий Python-код для обработки QTableWidget csv_table. Не добавляй комментарии и текст вне кода."},
            {"role": "user", "content": prompt}
        ]
        data = {
            "model": profile_settings["model"].strip(),
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

    def load_profiles(self):
        """Load AI profiles from settings"""
        profiles_settings = QSettings('csvQuery', 'AIProfiles')
        profiles_settings.beginGroup('profiles')
        profile_names = profiles_settings.childGroups()
        profiles_settings.endGroup()
        
        self.profile_combo.clear()
        for name in profile_names:
            self.profile_combo.addItem(name)
        
        # Add default profile if no profiles exist
        if not profile_names:
            self.profile_combo.addItem('Default')

    def on_profile_changed(self, profile_name):
        """Handle profile selection change"""
        if not profile_name:
            return
            
        self.current_profile = profile_name
        self.save_settings(show_message=False)

    def open_ai_options(self):
        """Open AI profile settings dialog"""
        from ai_options_dialog import AIOptionsDialog
        dialog = AIOptionsDialog(self)
        if dialog.exec_() == dialog.Accepted:
            # Reload profiles after changes
            current_text = self.profile_combo.currentText()
            self.load_profiles()
            # Try to restore selection
            index = self.profile_combo.findText(current_text)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
            elif self.profile_combo.count() > 0:
                self.profile_combo.setCurrentIndex(0)

    def get_current_profile_settings(self):
        """Get settings for current profile"""
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            return {'model': 'gpt-3.5-turbo', 'token': '', 'url': 'https://openrouter.ai/api/v1/chat/completions'}
            
        profiles_settings = QSettings('csvQuery', 'AIProfiles')
        profiles_settings.beginGroup(f'profiles/{profile_name}')
        model = profiles_settings.value('model', 'gpt-3.5-turbo')
        token = profiles_settings.value('token', '')
        url = profiles_settings.value('url', 'https://openrouter.ai/api/v1/chat/completions')
        profiles_settings.endGroup()
        
        return {'model': model, 'token': token, 'url': url}