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
        self.parent_window = parent
        
        self.init_ui()
        self.load_default_settings()
        
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
        
        # Formula evaluation group
        formula_group = QGroupBox('Formula Evaluation')
        formula_layout = QVBoxLayout(formula_group)
        
        self.evaluate_formulas = QCheckBox('Evaluate formulas and show results')
        self.evaluate_formulas.setChecked(True)
        formula_layout.addWidget(self.evaluate_formulas)
        
        self.show_formula_indicators = QCheckBox('Show indicators for cells with formulas')
        self.show_formula_indicators.setChecked(True)
        formula_layout.addWidget(self.show_formula_indicators)
        
        # Formula functions support
        functions_label = QLabel('Supported functions:')
        functions_label.setStyleSheet('font-weight: bold; margin-top: 5px;')
        formula_layout.addWidget(functions_label)
        
        self.support_basic_math = QCheckBox('Basic math (SUM, AVG, COUNT, MAX, MIN)')
        self.support_basic_math.setChecked(True)
        formula_layout.addWidget(self.support_basic_math)
        
        self.support_logical = QCheckBox('Logical functions (IF, AND, OR, NOT)')
        self.support_logical.setChecked(True)
        formula_layout.addWidget(self.support_logical)
        
        layout.addWidget(formula_group)
        
        # Connect preserve_formulas to disable formula evaluation
        self.preserve_formulas.toggled.connect(self._on_preserve_formulas_changed)
        self._on_preserve_formulas_changed(self.preserve_formulas.isChecked())
        
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
        self.preserve_formulas.setChecked(False)  # Changed to False for formula evaluation
        self.convert_dates.setChecked(True)
        self.evaluate_formulas.setChecked(True)
        self.show_formula_indicators.setChecked(True)
        self.support_basic_math.setChecked(True)
        self.support_logical.setChecked(True)
        
    def disable_all_formatting(self):
        """Disable all formatting options"""
        self.apply_background_colors.setChecked(False)
        self.apply_text_colors.setChecked(False)
        self.apply_borders.setChecked(False)
        self.apply_font_family.setChecked(False)
        self.apply_font_size.setChecked(False)
        self.apply_font_style.setChecked(False)
        self.preserve_formulas.setChecked(True)  # Preserve formulas when no formatting
        self.convert_dates.setChecked(False)
        self.evaluate_formulas.setChecked(False)
        self.show_formula_indicators.setChecked(False)
        self.support_basic_math.setChecked(False)
        self.support_logical.setChecked(False)
        
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
        self.evaluate_formulas.setChecked(True)
        self.show_formula_indicators.setChecked(False)
        self.support_basic_math.setChecked(True)
        self.support_logical.setChecked(False)
    
    def _on_preserve_formulas_changed(self, checked):
        """Handle changes to preserve_formulas checkbox"""
        # When preserve_formulas is checked, disable formula evaluation
        # When unchecked, enable formula evaluation
        self.evaluate_formulas.setEnabled(not checked)
        self.show_formula_indicators.setEnabled(not checked)
        self.support_basic_math.setEnabled(not checked)
        self.support_logical.setEnabled(not checked)
        
        if checked:
            # If preserving formulas, disable evaluation
            self.evaluate_formulas.setChecked(False)
        else:
            # If not preserving, enable evaluation by default
            self.evaluate_formulas.setChecked(True)
        
    def load_default_settings(self):
        """Load default settings from parent window"""
        if self.parent_window and hasattr(self.parent_window, 'settings'):
            settings = self.parent_window.settings
            
            # Load Excel import settings with defaults
            self.apply_background_colors.setChecked(
                settings.get('excel_default_apply_background_colors', True))
            self.apply_text_colors.setChecked(
                settings.get('excel_default_apply_text_colors', True))
            self.apply_borders.setChecked(
                settings.get('excel_default_apply_borders', False))
            self.apply_font_family.setChecked(
                settings.get('excel_default_apply_font_family', True))
            self.apply_font_size.setChecked(
                settings.get('excel_default_apply_font_size', True))
            self.apply_font_style.setChecked(
                settings.get('excel_default_apply_font_style', True))
            self.preserve_formulas.setChecked(
                settings.get('excel_default_preserve_formulas', False))
            self.convert_dates.setChecked(
                settings.get('excel_default_convert_dates', True))
            
            # Load formula evaluation settings
            self.evaluate_formulas.setChecked(
                settings.get('excel_default_evaluate_formulas', True))
            self.show_formula_indicators.setChecked(
                settings.get('excel_default_show_formula_indicators', True))
            self.support_basic_math.setChecked(
                settings.get('excel_default_support_basic_math', True))
            self.support_logical.setChecked(
                settings.get('excel_default_support_logical', True))
            
            # Apply preserve_formulas logic
            self._on_preserve_formulas_changed(self.preserve_formulas.isChecked())
    
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
            'convert_dates': self.convert_dates.isChecked(),
            'evaluate_formulas': self.evaluate_formulas.isChecked(),
            'show_formula_indicators': self.show_formula_indicators.isChecked(),
            'support_basic_math': self.support_basic_math.isChecked(),
            'support_logical': self.support_logical.isChecked()
        }
        
    def get_default_options(self):
        """Get default formatting options from settings without showing dialog"""
        if self.parent_window and hasattr(self.parent_window, 'settings'):
            settings = self.parent_window.settings
            return {
                'apply_background_colors': settings.get('excel_default_apply_background_colors', True),
                'apply_text_colors': settings.get('excel_default_apply_text_colors', True),
                'apply_borders': settings.get('excel_default_apply_borders', False),
                'apply_font_family': settings.get('excel_default_apply_font_family', True),
                'apply_font_size': settings.get('excel_default_apply_font_size', True),
                'apply_font_style': settings.get('excel_default_apply_font_style', True),
                'preserve_formulas': settings.get('excel_default_preserve_formulas', False),
                'convert_dates': settings.get('excel_default_convert_dates', True),
                'evaluate_formulas': settings.get('excel_default_evaluate_formulas', True),
                'show_formula_indicators': settings.get('excel_default_show_formula_indicators', True),
                'support_basic_math': settings.get('excel_default_support_basic_math', True),
                'support_logical': settings.get('excel_default_support_logical', True)
            }
        else:
            # Fallback defaults if no settings available
            return {
                'apply_background_colors': True,
                'apply_text_colors': True,
                'apply_borders': False,
                'apply_font_family': True,
                'apply_font_size': True,
                'apply_font_style': True,
                'preserve_formulas': False,
                'convert_dates': True,
                'evaluate_formulas': True,
                'show_formula_indicators': True,
                'support_basic_math': True,
                'support_logical': True
            }