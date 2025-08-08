from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QLineEdit, QPushButton, QDialogButtonBox, QGroupBox,
                             QRadioButton, QButtonGroup, QTextEdit)
from PyQt5.QtCore import Qt

class SQLJoinDialog(QDialog):
    def __init__(self, available_tables, available_fields, parent=None):
        super().__init__(parent)
        self.available_tables = available_tables
        self.available_fields = available_fields
        
        self.setWindowTitle('Добавить JOIN')
        self.setMinimumWidth(500)
        
        self.setup_ui()
        self.populate_tables()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # JOIN type selection
        join_type_group = QGroupBox('Тип JOIN')
        join_type_layout = QHBoxLayout(join_type_group)
        
        self.join_type_group = QButtonGroup()
        
        join_types = [
            ('INNER JOIN', 'INNER JOIN'),
            ('LEFT JOIN', 'LEFT JOIN'),
            ('RIGHT JOIN', 'RIGHT JOIN'),
            ('FULL OUTER JOIN', 'FULL OUTER JOIN')
        ]
        
        for i, (label, value) in enumerate(join_types):
            radio = QRadioButton(label)
            if i == 0:  # Default to INNER JOIN
                radio.setChecked(True)
            self.join_type_group.addButton(radio, i)
            radio.setProperty('join_type', value)
            join_type_layout.addWidget(radio)
            
        layout.addWidget(join_type_group)
        
        # Table selection
        table_group = QGroupBox('Таблица для присоединения')
        table_layout = QVBoxLayout(table_group)
        
        table_select_layout = QHBoxLayout()
        table_select_layout.addWidget(QLabel('Таблица:'))
        
        self.table_combo = QComboBox()
        self.table_combo.currentTextChanged.connect(self.on_table_changed)
        table_select_layout.addWidget(self.table_combo)
        
        table_layout.addLayout(table_select_layout)
        
        # Alias
        alias_layout = QHBoxLayout()
        alias_layout.addWidget(QLabel('Псевдоним (опционально):'))
        
        self.alias_edit = QLineEdit()
        self.alias_edit.setPlaceholderText('Например: t2')
        alias_layout.addWidget(self.alias_edit)
        
        table_layout.addLayout(alias_layout)
        
        layout.addWidget(table_group)
        
        # JOIN condition
        condition_group = QGroupBox('Условие JOIN')
        condition_layout = QVBoxLayout(condition_group)
        
        # Condition type selection
        condition_type_layout = QHBoxLayout()
        
        self.condition_type_group = QButtonGroup()
        
        self.simple_condition_radio = QRadioButton('Простое условие')
        self.simple_condition_radio.setChecked(True)
        self.simple_condition_radio.toggled.connect(self.on_condition_type_changed)
        self.condition_type_group.addButton(self.simple_condition_radio, 0)
        condition_type_layout.addWidget(self.simple_condition_radio)
        
        self.custom_condition_radio = QRadioButton('Пользовательское условие')
        self.custom_condition_radio.toggled.connect(self.on_condition_type_changed)
        self.condition_type_group.addButton(self.custom_condition_radio, 1)
        condition_type_layout.addWidget(self.custom_condition_radio)
        
        condition_layout.addLayout(condition_type_layout)
        
        # Simple condition panel
        self.simple_condition_panel = self.create_simple_condition_panel()
        condition_layout.addWidget(self.simple_condition_panel)
        
        # Custom condition panel
        self.custom_condition_panel = self.create_custom_condition_panel()
        self.custom_condition_panel.setVisible(False)
        condition_layout.addWidget(self.custom_condition_panel)
        
        layout.addWidget(condition_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def create_simple_condition_panel(self):
        panel = QGroupBox('Простое условие')
        layout = QVBoxLayout(panel)
        
        # Left field (from existing tables)
        left_layout = QHBoxLayout()
        left_layout.addWidget(QLabel('Левое поле:'))
        
        self.left_field_combo = QComboBox()
        self.left_field_combo.setEditable(True)
        left_layout.addWidget(self.left_field_combo)
        
        layout.addLayout(left_layout)
        
        # Operator
        operator_layout = QHBoxLayout()
        operator_layout.addWidget(QLabel('Оператор:'))
        
        self.operator_combo = QComboBox()
        self.operator_combo.addItems(['=', '!=', '<>', '<', '>', '<=', '>='])
        operator_layout.addWidget(self.operator_combo)
        
        layout.addLayout(operator_layout)
        
        # Right field (from joining table)
        right_layout = QHBoxLayout()
        right_layout.addWidget(QLabel('Правое поле:'))
        
        self.right_field_combo = QComboBox()
        self.right_field_combo.setEditable(True)
        right_layout.addWidget(self.right_field_combo)
        
        layout.addLayout(right_layout)
        
        return panel
        
    def create_custom_condition_panel(self):
        panel = QGroupBox('Пользовательское условие')
        layout = QVBoxLayout(panel)
        
        layout.addWidget(QLabel('Введите условие ON:'))
        
        self.custom_condition_edit = QTextEdit()
        self.custom_condition_edit.setMaximumHeight(80)
        self.custom_condition_edit.setPlaceholderText('Например: table1.id = table2.table1_id AND table1.status = "active"')
        layout.addWidget(self.custom_condition_edit)
        
        return panel
        
    def populate_tables(self):
        """Populate table combo with available tables"""
        self.table_combo.clear()
        self.table_combo.addItems(self.available_tables)
        
        # Populate left field combo with all available fields
        self.populate_left_fields()
        
    def populate_left_fields(self):
        """Populate left field combo with fields from all existing tables"""
        self.left_field_combo.clear()
        
        for table_name, fields in self.available_fields.items():
            for field_name, field_type in fields:
                qualified_name = self.format_qualified_field_name(table_name, field_name)
                self.left_field_combo.addItem(qualified_name)
                
    def on_table_changed(self):
        """Handle table selection change to update right field combo"""
        table_name = self.table_combo.currentText()
        if not table_name:
            return
            
        self.populate_right_fields(table_name)
        
    def populate_right_fields(self, table_name):
        """Populate right field combo with fields from selected table"""
        self.right_field_combo.clear()
        
        if table_name in self.available_fields:
            alias = self.alias_edit.text().strip()
            table_ref = alias if alias else table_name
            
            for field_name, field_type in self.available_fields[table_name]:
                qualified_name = self.format_qualified_field_name(table_ref, field_name)
                self.right_field_combo.addItem(qualified_name)
                
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
        is_simple = self.simple_condition_radio.isChecked()
        self.simple_condition_panel.setVisible(is_simple)
        self.custom_condition_panel.setVisible(not is_simple)
        
    def get_join_clause(self):
        """Get the constructed JOIN clause"""
        # Get JOIN type
        join_type = 'INNER JOIN'  # Default
        for button in self.join_type_group.buttons():
            if button.isChecked():
                join_type = button.property('join_type')
                break
                
        # Get table name and alias
        table_name = self.table_combo.currentText()
        if not table_name:
            return ''
            
        alias = self.alias_edit.text().strip()
        formatted_table = self.format_field_name(table_name)
        table_clause = f'{formatted_table} {alias}' if alias else formatted_table
        
        # Get condition
        if self.custom_condition_radio.isChecked():
            condition = self.custom_condition_edit.toPlainText().strip()
        else:
            # Simple condition
            left_field = self.left_field_combo.currentText()
            operator = self.operator_combo.currentText()
            right_field = self.right_field_combo.currentText()
            
            if not left_field or not right_field:
                return ''
                
            condition = f'{left_field} {operator} {right_field}'
            
        if not condition:
            return ''
            
        return f'{join_type} {table_clause} ON {condition}'