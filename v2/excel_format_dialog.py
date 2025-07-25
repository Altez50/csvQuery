from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, 
                             QLabel, QPushButton, QGroupBox, QDialogButtonBox,
                             QComboBox, QSpinBox)
from PyQt5.QtCore import Qt

class ExcelFormatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Excel Import Options')
        self.setModal(True)
        self.resize(400, 300)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel('Choose formatting options for Excel import:')
        title_label.setStyleSheet('font-weight: bold; font-size: 12px;')
        layout.addWidget(title_label)
        
        # Cell formatting group
        format_group = QGroupBox('Cell Formatting')
        format_layout = QVBoxLayout(format_group)
        
        self.apply_background_colors = QCheckBox('Apply background colors')
        self.apply_background_colors.setChecked(True)
        format_layout.addWidget(self.apply_background_colors)
        
        self.apply_text_colors = QCheckBox('Apply text colors')
        self.apply_text_colors.setChecked(True)
        format_layout.addWidget(self.apply_text_colors)
        
        self.apply_borders = QCheckBox('Apply cell borders')
        self.apply_borders.setChecked(False)
        format_layout.addWidget(self.apply_borders)
        
        layout.addWidget(format_group)
        
        # Font formatting group
        font_group = QGroupBox('Font Formatting')
        font_layout = QVBoxLayout(font_group)
        
        self.apply_font_family = QCheckBox('Apply font family')
        self.apply_font_family.setChecked(True)
        font_layout.addWidget(self.apply_font_family)
        
        self.apply_font_size = QCheckBox('Apply font size')
        self.apply_font_size.setChecked(True)
        font_layout.addWidget(self.apply_font_size)
        
        self.apply_font_style = QCheckBox('Apply font style (bold, italic)')
        self.apply_font_style.setChecked(True)
        font_layout.addWidget(self.apply_font_style)
        
        layout.addWidget(font_group)
        
        # Data options group
        data_group = QGroupBox('Data Options')
        data_layout = QVBoxLayout(data_group)
        
        self.preserve_formulas = QCheckBox('Preserve formulas (show as text)')
        self.preserve_formulas.setChecked(False)
        data_layout.addWidget(self.preserve_formulas)
        
        self.convert_dates = QCheckBox('Convert date formats to text')
        self.convert_dates.setChecked(True)
        data_layout.addWidget(self.convert_dates)
        
        layout.addWidget(data_group)
        
        # Performance warning
        warning_label = QLabel('Note: Applying formatting may slow down loading for large files')
        warning_label.setStyleSheet('color: #666; font-style: italic;')
        layout.addWidget(warning_label)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Quick presets
        presets_layout = QHBoxLayout()
        
        all_formatting_btn = QPushButton('All Formatting')
        all_formatting_btn.clicked.connect(self.enable_all_formatting)
        presets_layout.addWidget(all_formatting_btn)
        
        no_formatting_btn = QPushButton('No Formatting')
        no_formatting_btn.clicked.connect(self.disable_all_formatting)
        presets_layout.addWidget(no_formatting_btn)
        
        basic_formatting_btn = QPushButton('Basic Only')
        basic_formatting_btn.clicked.connect(self.enable_basic_formatting)
        presets_layout.addWidget(basic_formatting_btn)
        
        layout.insertLayout(-2, presets_layout)  # Insert before buttons
        
    def enable_all_formatting(self):
        """Enable all formatting options"""
        self.apply_background_colors.setChecked(True)
        self.apply_text_colors.setChecked(True)
        self.apply_borders.setChecked(True)
        self.apply_font_family.setChecked(True)
        self.apply_font_size.setChecked(True)
        self.apply_font_style.setChecked(True)
        self.preserve_formulas.setChecked(True)
        self.convert_dates.setChecked(True)
        
    def disable_all_formatting(self):
        """Disable all formatting options"""
        self.apply_background_colors.setChecked(False)
        self.apply_text_colors.setChecked(False)
        self.apply_borders.setChecked(False)
        self.apply_font_family.setChecked(False)
        self.apply_font_size.setChecked(False)
        self.apply_font_style.setChecked(False)
        self.preserve_formulas.setChecked(False)
        self.convert_dates.setChecked(False)
        
    def enable_basic_formatting(self):
        """Enable only basic formatting options"""
        self.apply_background_colors.setChecked(True)
        self.apply_text_colors.setChecked(True)
        self.apply_borders.setChecked(False)
        self.apply_font_family.setChecked(False)
        self.apply_font_size.setChecked(False)
        self.apply_font_style.setChecked(True)
        self.preserve_formulas.setChecked(False)
        self.convert_dates.setChecked(True)
        
    def get_options(self):
        """Get selected formatting options"""
        return {
            'apply_background_colors': self.apply_background_colors.isChecked(),
            'apply_text_colors': self.apply_text_colors.isChecked(),
            'apply_borders': self.apply_borders.isChecked(),
            'apply_font_family': self.apply_font_family.isChecked(),
            'apply_font_size': self.apply_font_size.isChecked(),
            'apply_font_style': self.apply_font_style.isChecked(),
            'preserve_formulas': self.preserve_formulas.isChecked(),
            'convert_dates': self.convert_dates.isChecked()
        }