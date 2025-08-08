from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox, 
                             QFormLayout, QGroupBox)
from PyQt5.QtCore import QSettings, Qt
import json

class AIOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('AI Profile Settings')
        self.setModal(True)
        self.resize(600, 400)
        self._settings = QSettings('csvQuery', 'AIOptions')
        self.profiles = self.load_profiles()
        self.init_ui()
        self.update_profile_list()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Profile list section
        list_group = QGroupBox('AI Profiles')
        list_layout = QVBoxLayout(list_group)
        
        self.profile_list = QListWidget()
        self.profile_list.itemSelectionChanged.connect(self.on_profile_selected)
        list_layout.addWidget(self.profile_list)
        
        # Profile list buttons
        list_buttons = QHBoxLayout()
        self.add_btn = QPushButton('Add Profile')
        self.add_btn.clicked.connect(self.add_profile)
        self.delete_btn = QPushButton('Delete Profile')
        self.delete_btn.clicked.connect(self.delete_profile)
        self.delete_btn.setEnabled(False)
        
        list_buttons.addWidget(self.add_btn)
        list_buttons.addWidget(self.delete_btn)
        list_buttons.addStretch()
        list_layout.addLayout(list_buttons)
        
        layout.addWidget(list_group)
        
        # Profile details section
        details_group = QGroupBox('Profile Details')
        details_layout = QFormLayout(details_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_profile_changed)
        details_layout.addRow('Profile Name:', self.name_edit)
        
        self.model_edit = QLineEdit()
        self.model_edit.textChanged.connect(self.on_model_changed)
        details_layout.addRow('Model:', self.model_edit)
        
        self.url_edit = QLineEdit()
        self.url_edit.textChanged.connect(self.on_profile_changed)
        details_layout.addRow('API URL:', self.url_edit)
        
        self.token_edit = QLineEdit()
        self.token_edit.textChanged.connect(self.on_profile_changed)
        details_layout.addRow('API Token:', self.token_edit)
        
        layout.addWidget(details_group)
        
        # Dialog buttons
        buttons = QHBoxLayout()
        self.save_btn = QPushButton('Save')
        self.save_btn.clicked.connect(self.save_profiles)
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons.addStretch()
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)
        
        # Initially disable details
        self.set_details_enabled(False)
        
    def load_profiles(self):
        """Load AI profiles from settings"""
        profiles_json = self._settings.value('profiles', '[]')
        try:
            profiles = json.loads(profiles_json)
            # Ensure we have at least one default profile
            if not profiles:
                profiles = self.create_default_profile()
            return profiles
        except json.JSONDecodeError:
            return self.create_default_profile()
    
    def create_default_profile(self):
        """Create a default AI profile"""
        return [{
            'name': 'Default',
            'model': 'deepseek/deepseek-r1-0528-qwen3-8b',
            'url': 'https://openrouter.ai/api/v1/chat/completions',
            'token': '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'
        }]
    
    def save_profiles_to_settings(self):
        """Save profiles to settings"""
        profiles_json = json.dumps(self.profiles, ensure_ascii=False, indent=2)
        self._settings.setValue('profiles', profiles_json)
        
    def update_profile_list(self):
        """Update the profile list widget"""
        self.profile_list.clear()
        for profile in self.profiles:
            item = QListWidgetItem(profile['name'])
            item.setData(Qt.UserRole, profile)
            self.profile_list.addItem(item)
            
    def on_profile_selected(self):
        """Handle profile selection"""
        items = self.profile_list.selectedItems()
        if items:
            profile = items[0].data(Qt.UserRole)
            self.name_edit.setText(profile['name'])
            self.model_edit.setText(profile['model'])
            self.url_edit.setText(profile['url'])
            self.token_edit.setText(profile['token'])
            self.set_details_enabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.clear_details()
            self.set_details_enabled(False)
            self.delete_btn.setEnabled(False)
            
    def on_profile_changed(self):
        """Handle profile details change"""
        items = self.profile_list.selectedItems()
        if items:
            profile = items[0].data(Qt.UserRole)
            profile['name'] = self.name_edit.text()
            profile['model'] = self.model_edit.text()
            profile['url'] = self.url_edit.text()
            profile['token'] = self.token_edit.text()
            items[0].setText(profile['name'])
    
    def on_model_changed(self):
        """Handle model change and update profile name"""
        model_text = self.model_edit.text().strip()
        if model_text:
            # Extract model name from full model path (e.g., "deepseek/deepseek-r1" -> "deepseek-r1")
            model_name = model_text.split('/')[-1] if '/' in model_text else model_text
            # Capitalize first letter for better readability
            profile_name = model_name.replace('-', ' ').title()
            self.name_edit.setText(profile_name)
        
        # Call the original profile changed handler
        self.on_profile_changed()
            
    def add_profile(self):
        """Add a new profile"""
        default_model = 'gpt-3.5-turbo'
        # Generate profile name from model
        model_name = default_model.split('/')[-1] if '/' in default_model else default_model
        profile_name = model_name.replace('-', ' ').title()
        
        new_profile = {
            'name': profile_name,
            'model': default_model,
            'url': 'https://api.openai.com/v1/chat/completions',
            'token': ''
        }
        self.profiles.append(new_profile)
        self.update_profile_list()
        # Select the new profile
        self.profile_list.setCurrentRow(len(self.profiles) - 1)
        
    def delete_profile(self):
        """Delete selected profile"""
        items = self.profile_list.selectedItems()
        if not items:
            return
            
        if len(self.profiles) <= 1:
            QMessageBox.warning(self, 'Warning', 'Cannot delete the last profile.')
            return
            
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                   f'Delete profile "{items[0].text()}"?',
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            row = self.profile_list.currentRow()
            del self.profiles[row]
            self.update_profile_list()
            self.clear_details()
            self.set_details_enabled(False)
            self.delete_btn.setEnabled(False)
            
    def clear_details(self):
        """Clear profile details"""
        self.name_edit.clear()
        self.model_edit.clear()
        self.url_edit.clear()
        self.token_edit.clear()
        
    def set_details_enabled(self, enabled):
        """Enable/disable profile details"""
        self.name_edit.setEnabled(enabled)
        self.model_edit.setEnabled(enabled)
        self.url_edit.setEnabled(enabled)
        self.token_edit.setEnabled(enabled)
        
    def save_profiles(self):
        """Save profiles and close dialog"""
        # Validate profiles
        for profile in self.profiles:
            if not profile['name'].strip():
                QMessageBox.warning(self, 'Validation Error', 'Profile name cannot be empty.')
                return
            if not profile['model'].strip():
                QMessageBox.warning(self, 'Validation Error', 'Model cannot be empty.')
                return
                
        self.save_profiles_to_settings()
        QMessageBox.information(self, 'Success', 'AI profiles saved successfully.')
        self.accept()