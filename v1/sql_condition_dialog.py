from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QLineEdit, QPushButton, QDialogButtonBox, QCheckBox,
                             QTextEdit, QGroupBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt

class SQLConditionDialog(QDialog):
    def __init__(self, available_fields, condition_type='WHERE', parent=None):
        super().__init__(parent)
        self.available_fields = available_fields
        self.condition_type = condition_type
        
        self.setWindowTitle(f'Добавить {condition_type} условие')
        self.setMinimumWidth(400)
        
        self.setup_ui()
        self.populate_fields()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Condition type selection
        type_group = QGroupBox('Тип условия')
        type_layout = QVBoxLayout(type_group)
        
        self.condition_type_group = QButtonGroup()
        
        self.simple_radio = QRadioButton('Простое условие')
        self.simple_radio.setChecked(True)
        self.simple_radio.toggled.connect(self.on_condition_type_changed)
        self.condition_type_group.addButton(self.simple_radio, 0)
        type_layout.addWidget(self.simple_radio)
        
        self.custom_radio = QRadioButton('Пользовательское условие')
        self.custom_radio.toggled.connect(self.on_condition_type_changed)
        self.condition_type_group.addButton(self.custom_radio, 1)
        type_layout.addWidget(self.custom_radio)
        
        layout.addWidget(type_group)
        
        # Simple condition panel
        self.simple_panel = self.create_simple_condition_panel()
        layout.addWidget(self.simple_panel)
        
        # Custom condition panel
        self.custom_panel = self.create_custom_condition_panel()
        self.custom_panel.setVisible(False)
        layout.addWidget(self.custom_panel)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def create_simple_condition_panel(self):
        panel = QGroupBox('Простое условие')
        layout = QVBoxLayout(panel)
        
        # Field selection
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel('Поле:'))
        
        self.field_combo = QComboBox()
        self.field_combo.setEditable(True)
        field_layout.addWidget(self.field_combo)
        
        layout.addLayout(field_layout)
        
        # Operator selection
        operator_layout = QHBoxLayout()
        operator_layout.addWidget(QLabel('Оператор:'))
        
        self.operator_combo = QComboBox()
        operators = ['=', '!=', '<>', '<', '>', '<=', '>=', 'LIKE', 'NOT LIKE', 
                    'IN', 'NOT IN', 'BETWEEN', 'NOT BETWEEN', 'IS NULL', 'IS NOT NULL']
        self.operator_combo.addItems(operators)
        self.operator_combo.currentTextChanged.connect(self.on_operator_changed)
        operator_layout.addWidget(self.operator_combo)
        
        layout.addLayout(operator_layout)
        
        # Value input
        value_layout = QVBoxLayout()
        value_layout.addWidget(QLabel('Значение:'))
        
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText('Введите значение...')
        value_layout.addWidget(self.value_edit)
        
        # Second value for BETWEEN
        self.value2_label = QLabel('Второе значение:')
        self.value2_label.setVisible(False)
        value_layout.addWidget(self.value2_label)
        
        self.value2_edit = QLineEdit()
        self.value2_edit.setPlaceholderText('Введите второе значение...')
        self.value2_edit.setVisible(False)
        value_layout.addWidget(self.value2_edit)
        
        layout.addLayout(value_layout)
        
        # Options
        self.quote_checkbox = QCheckBox('Заключить значение в кавычки')
        self.quote_checkbox.setChecked(True)
        layout.addWidget(self.quote_checkbox)
        
        return panel
        
    def create_custom_condition_panel(self):
        panel = QGroupBox('Пользовательское условие')
        layout = QVBoxLayout(panel)
        
        layout.addWidget(QLabel('Введите условие:'))
        
        self.custom_edit = QTextEdit()
        self.custom_edit.setMaximumHeight(100)
        self.custom_edit.setPlaceholderText('Например: table1.field1 = table2.field2 OR table1.field3 > 100')
        layout.addWidget(self.custom_edit)
        
        return panel
        
    def populate_fields(self):
        """Populate field combo with available fields"""
        self.field_combo.clear()
        
        for table_name, fields in self.available_fields.items():
            for field_name, field_type in fields:
                qualified_name = self.format_qualified_field_name(table_name, field_name)
                self.field_combo.addItem(qualified_name)
                
    def format_field_name(self, field_name):
        """Format field name, wrapping multi-word names in square brackets"""
        # Check if field name contains spaces or special characters
        if ' ' in field_name or any(char in field_name for char in ['-', '+', '*', '/', '(', ')', '.']):
            # Only wrap in brackets if not already wrapped
            if not (field_name.startswith('[') and field_name.endswith(']')):
                return f'[{field_name}]'
        return field_name
        
    def format_qualified_field_name(self, table_name, field_name):
        """Format qualified field name with proper bracketing"""
        formatted_table = self.format_field_name(table_name)
        formatted_field = self.format_field_name(field_name)
        return f'{formatted_table}.{formatted_field}'
                
    def on_condition_type_changed(self):
        """Handle condition type change"""
        is_simple = self.simple_radio.isChecked()
        self.simple_panel.setVisible(is_simple)
        self.custom_panel.setVisible(not is_simple)
        
    def on_operator_changed(self):
        """Handle operator change to show/hide second value field"""
        operator = self.operator_combo.currentText()
        
        # Show second value field for BETWEEN
        is_between = operator in ['BETWEEN', 'NOT BETWEEN']
        self.value2_label.setVisible(is_between)
        self.value2_edit.setVisible(is_between)
        
        # Hide value fields for NULL checks
        is_null_check = operator in ['IS NULL', 'IS NOT NULL']
        self.value_edit.setVisible(not is_null_check)
        self.quote_checkbox.setVisible(not is_null_check)
        
    def get_condition(self):
        """Get the constructed condition string"""
        if self.custom_radio.isChecked():
            return self.custom_edit.toPlainText().strip()
            
        # Simple condition
        field = self.field_combo.currentText()
        operator = self.operator_combo.currentText()
        
        if not field:
            return ''
            
        if operator in ['IS NULL', 'IS NOT NULL']:
            return f'{field} {operator}'
            
        value = self.value_edit.text().strip()
        if not value:
            return ''
            
        # Quote value if needed
        if self.quote_checkbox.isChecked() and not value.startswith("'") and not value.startswith('"'):
            value = f"'{value}'"
            
        if operator in ['BETWEEN', 'NOT BETWEEN']:
            value2 = self.value2_edit.text().strip()
            if not value2:
                return ''
                
            if self.quote_checkbox.isChecked() and not value2.startswith("'") and not value2.startswith('"'):
                value2 = f"'{value2}'"
                
            return f'{field} {operator} {value} AND {value2}'
        elif operator in ['IN', 'NOT IN']:
            # Handle IN operator - value should be comma-separated
            if not value.startswith('('):
                # Split by comma and quote each value if needed
                values = [v.strip() for v in value.split(',')]
                if self.quote_checkbox.isChecked():
                    values = [f"'{v}'" if not v.startswith("'") and not v.startswith('"') else v for v in values]
                value = f"({', '.join(values)})"
            return f'{field} {operator} {value}'
        else:
            return f'{field} {operator} {value}'