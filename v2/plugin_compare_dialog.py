import sys
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QTextEdit, QSplitter, QPushButton, QComboBox, QGroupBox,
    QProgressBar, QMessageBox, QTabWidget, QWidget, QHeaderView,
    QAbstractItemView, QMenu, QAction, QFileDialog, QCheckBox, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon
import pandas as pd
from typing import Dict, Any, List, Optional

# Add parent directory to path to import plugins
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.plugin_loader import PluginLoader

def get_plugin_loader():
    """Get plugin loader instance."""
    return PluginLoader()

class ComparisonWorker(QThread):
    """Worker thread for running plugin comparisons."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    comparison_finished = pyqtSignal(dict)
    comparison_failed = pyqtSignal(str)
    
    def __init__(self, plugin, df1, df2, parameters):
        super().__init__()
        self.plugin = plugin
        self.df1 = df1
        self.df2 = df2
        self.parameters = parameters
    
    def run(self):
        """Run the comparison in a separate thread."""
        try:
            self.status_updated.emit(f"Running {self.plugin.get_name()}...")
            self.progress_updated.emit(25)
            
            # Run the comparison
            result = self.plugin.compare(self.df1, self.df2, **self.parameters)
            
            self.progress_updated.emit(100)
            self.status_updated.emit("Comparison completed")
            self.comparison_finished.emit(result)
            
        except Exception as e:
            self.comparison_failed.emit(str(e))

class HighlightedTableWidget(QTableWidget):
    """Table widget with support for highlighting differences."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        
        # Colors for different types of differences
        self.colors = {
            'same': QColor(240, 255, 240),      # Light green
            'different': QColor(255, 240, 240), # Light red
            'only_in_a': QColor(255, 255, 200), # Light yellow
            'only_in_b': QColor(200, 255, 255), # Light cyan
            'header': QColor(220, 220, 220)     # Light gray
        }
    
    def populate_from_dataframe(self, df: pd.DataFrame, highlight_column: str = '_diff_type'):
        """Populate table from DataFrame with optional highlighting."""
        if df.empty:
            self.setRowCount(0)
            self.setColumnCount(0)
            return
        
        # Set up table dimensions
        self.setRowCount(len(df))
        
        # Determine columns to display (exclude internal columns)
        display_columns = [col for col in df.columns if not col.startswith('_')]
        self.setColumnCount(len(display_columns))
        self.setHorizontalHeaderLabels(display_columns)
        
        # Populate data
        for row_idx, (_, row) in enumerate(df.iterrows()):
            # Determine highlight type
            highlight_type = 'same'
            if highlight_column in df.columns:
                highlight_type = row.get(highlight_column, 'same')
            
            for col_idx, col_name in enumerate(display_columns):
                value = row[col_name]
                
                # Convert value to string
                if pd.isna(value):
                    display_value = ''
                else:
                    display_value = str(value)
                
                # Create table item
                item = QTableWidgetItem(display_value)
                
                # Apply highlighting
                if highlight_type in self.colors:
                    item.setBackground(self.colors[highlight_type])
                
                # Make item read-only
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                
                self.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        self.resizeColumnsToContents()
    
    def setup_context_menu(self):
        """Set up context menu for the table."""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        """Show context menu."""
        menu = QMenu(self)
        
        # Export actions
        export_csv_action = QAction("Export to CSV", self)
        export_csv_action.triggered.connect(self.export_to_csv)
        menu.addAction(export_csv_action)
        
        export_excel_action = QAction("Export to Excel", self)
        export_excel_action.triggered.connect(self.export_to_excel)
        menu.addAction(export_excel_action)
        
        menu.addSeparator()
        
        # View actions
        fit_columns_action = QAction("Fit Columns to Content", self)
        fit_columns_action.triggered.connect(self.resizeColumnsToContents)
        menu.addAction(fit_columns_action)
        
        menu.exec_(self.mapToGlobal(position))
    
    def export_to_csv(self):
        """Export table data to CSV."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export to CSV", "", "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                df = self.to_dataframe()
                df.to_csv(filename, index=False)
                QMessageBox.information(self, "Export Successful", f"Data exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
    
    def export_to_excel(self):
        """Export table data to Excel."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel", "", "Excel Files (*.xlsx)"
        )
        
        if filename:
            try:
                df = self.to_dataframe()
                df.to_excel(filename, index=False)
                QMessageBox.information(self, "Export Successful", f"Data exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert table data back to DataFrame."""
        data = []
        headers = []
        
        # Get headers
        for col in range(self.columnCount()):
            headers.append(self.horizontalHeaderItem(col).text())
        
        # Get data
        for row in range(self.rowCount()):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else '')
            data.append(row_data)
        
        return pd.DataFrame(data, columns=headers)

class PluginCompareDialog(QDialog):
    """Dialog for comparing DataFrames using plugins."""
    
    def __init__(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                 df1_name: str = "DataFrame 1", df2_name: str = "DataFrame 2", parent=None):
        super().__init__(parent)
        self.df1 = df1
        self.df2 = df2
        self.df1_name = df1_name
        self.df2_name = df2_name
        
        self.plugin_loader = get_plugin_loader()
        self.plugins = self.plugin_loader.load_plugins()
        
        self.comparison_worker = None
        self.current_result = None
        
        self.init_ui()
        self.load_plugins()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Plugin-based Table Comparison")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Top section: Plugin selection and parameters
        top_section = self.create_top_section()
        main_layout.addWidget(top_section)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        # Results section
        results_section = self.create_results_section()
        main_layout.addWidget(results_section)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.compare_button = QPushButton("Run Comparison")
        self.compare_button.clicked.connect(self.run_comparison)
        button_layout.addWidget(self.compare_button)
        
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def create_top_section(self) -> QWidget:
        """Create the top section with plugin selection and parameters."""
        group_box = QGroupBox("Comparison Settings")
        layout = QVBoxLayout()
        
        # Plugin selection
        plugin_layout = QHBoxLayout()
        plugin_layout.addWidget(QLabel("Plugin:"))
        
        self.plugin_combo = QComboBox()
        self.plugin_combo.currentTextChanged.connect(self.on_plugin_changed)
        plugin_layout.addWidget(self.plugin_combo)
        
        plugin_layout.addStretch()
        
        refresh_button = QPushButton("Refresh Plugins")
        refresh_button.clicked.connect(self.load_plugins)
        plugin_layout.addWidget(refresh_button)
        
        layout.addLayout(plugin_layout)
        
        # Plugin description
        self.plugin_description = QLabel("Select a plugin to see its description.")
        self.plugin_description.setWordWrap(True)
        layout.addWidget(self.plugin_description)
        
        # Parameters section (will be populated dynamically)
        self.parameters_widget = QWidget()
        self.parameters_layout = QVBoxLayout(self.parameters_widget)
        layout.addWidget(self.parameters_widget)
        
        group_box.setLayout(layout)
        return group_box
    
    def create_results_section(self) -> QWidget:
        """Create the results section with tabs."""
        self.results_tabs = QTabWidget()
        
        # Summary tab
        self.summary_tab = QTextEdit()
        self.summary_tab.setReadOnly(True)
        self.results_tabs.addTab(self.summary_tab, "Summary")
        
        # Highlights tab
        self.highlights_table = HighlightedTableWidget()
        self.highlights_table.setup_context_menu()
        self.results_tabs.addTab(self.highlights_table, "Differences")
        
        # Side-by-side comparison tab
        side_by_side_widget = QWidget()
        side_by_side_layout = QHBoxLayout(side_by_side_widget)
        
        # Left table (DataFrame 1)
        left_group = QGroupBox(self.df1_name)
        left_layout = QVBoxLayout(left_group)
        self.left_table = HighlightedTableWidget()
        self.left_table.setup_context_menu()
        left_layout.addWidget(self.left_table)
        side_by_side_layout.addWidget(left_group)
        
        # Right table (DataFrame 2)
        right_group = QGroupBox(self.df2_name)
        right_layout = QVBoxLayout(right_group)
        self.right_table = HighlightedTableWidget()
        self.right_table.setup_context_menu()
        right_layout.addWidget(self.right_table)
        side_by_side_layout.addWidget(right_group)
        
        self.results_tabs.addTab(side_by_side_widget, "Side-by-Side")
        
        # Populate initial data
        self.left_table.populate_from_dataframe(self.df1)
        self.right_table.populate_from_dataframe(self.df2)
        
        return self.results_tabs
    
    def load_plugins(self):
        """Load available plugins into the combo box."""
        self.plugin_combo.clear()
        
        try:
            self.plugins = self.plugin_loader.reload_plugins()
            
            if not self.plugins:
                self.plugin_combo.addItem("No plugins available")
                self.compare_button.setEnabled(False)
                return
            
            for plugin in self.plugins:
                try:
                    plugin_name = plugin.get_name()
                    self.plugin_combo.addItem(plugin_name)
                except Exception as e:
                    print(f"Error getting plugin name: {e}")
            
            self.compare_button.setEnabled(True)
            
            # Show plugin errors if any
            errors = self.plugin_loader.get_plugin_errors()
            if errors:
                error_msg = "Plugin loading errors:\n\n"
                for file_path, error in errors.items():
                    error_msg += f"{file_path}: {error}\n"
                
                QMessageBox.warning(self, "Plugin Loading Warnings", error_msg)
        
        except Exception as e:
            QMessageBox.critical(self, "Plugin Loading Error", f"Failed to load plugins: {str(e)}")
            self.compare_button.setEnabled(False)
    
    def on_plugin_changed(self):
        """Handle plugin selection change."""
        plugin_name = self.plugin_combo.currentText()
        
        if plugin_name == "No plugins available":
            return
        
        # Find the selected plugin
        selected_plugin = None
        for plugin in self.plugins:
            try:
                if plugin.get_name() == plugin_name:
                    selected_plugin = plugin
                    break
            except Exception:
                continue
        
        if not selected_plugin:
            return
        
        # Update description
        try:
            description = selected_plugin.get_description()
            version = selected_plugin.get_version()
            self.plugin_description.setText(f"{description} (Version: {version})")
        except Exception as e:
            self.plugin_description.setText(f"Error getting plugin info: {e}")
        
        # Update parameters
        self.update_parameters_ui(selected_plugin)
    
    def update_parameters_ui(self, plugin):
        """Update the parameters UI based on the selected plugin."""
        # Clear existing parameters
        for i in reversed(range(self.parameters_layout.count())):
            child = self.parameters_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        try:
            parameters = plugin.get_parameters()
            
            if not parameters:
                label = QLabel("This plugin has no configurable parameters.")
                self.parameters_layout.addWidget(label)
                return
            
            # Create parameter controls
            for param_name, param_info in parameters.items():
                param_layout = QHBoxLayout()
                
                # Parameter label
                label = QLabel(f"{param_name}:")
                label.setToolTip(param_info.get('description', ''))
                param_layout.addWidget(label)
                
                # Parameter control based on type
                param_type = param_info.get('type', 'str')
                default_value = param_info.get('default', '')
                
                if param_type == 'bool':
                    control = QCheckBox()
                    control.setChecked(default_value)
                elif param_type == 'list':
                    control = QComboBox()
                    options = param_info.get('options', [])
                    control.addItems([str(opt) for opt in options])
                    if default_value in options:
                        control.setCurrentText(str(default_value))
                else:
                    control = QLineEdit()
                    control.setText(str(default_value))
                
                control.setObjectName(param_name)
                param_layout.addWidget(control)
                
                param_layout.addStretch()
                
                widget = QWidget()
                widget.setLayout(param_layout)
                self.parameters_layout.addWidget(widget)
        
        except Exception as e:
            error_label = QLabel(f"Error loading parameters: {e}")
            self.parameters_layout.addWidget(error_label)
    
    def get_current_parameters(self) -> Dict[str, Any]:
        """Get current parameter values from the UI."""
        parameters = {}
        
        for i in range(self.parameters_layout.count()):
            widget = self.parameters_layout.itemAt(i).widget()
            if not widget:
                continue
            
            # Find parameter controls
            for control in widget.findChildren((QCheckBox, QComboBox, QLineEdit)):
                param_name = control.objectName()
                if not param_name:
                    continue
                
                if isinstance(control, QCheckBox):
                    parameters[param_name] = control.isChecked()
                elif isinstance(control, QComboBox):
                    text = control.currentText()
                    # Try to convert to appropriate type
                    try:
                        if text.lower() in ['true', 'false']:
                            parameters[param_name] = text.lower() == 'true'
                        elif text.isdigit():
                            parameters[param_name] = int(text)
                        elif '.' in text and text.replace('.', '').isdigit():
                            parameters[param_name] = float(text)
                        else:
                            parameters[param_name] = text
                    except ValueError:
                        parameters[param_name] = text
                elif isinstance(control, QLineEdit):
                    text = control.text()
                    # Try to convert to appropriate type
                    try:
                        if text.lower() in ['true', 'false']:
                            parameters[param_name] = text.lower() == 'true'
                        elif text.isdigit():
                            parameters[param_name] = int(text)
                        elif '.' in text and text.replace('.', '').isdigit():
                            parameters[param_name] = float(text)
                        else:
                            parameters[param_name] = text
                    except ValueError:
                        parameters[param_name] = text
        
        return parameters
    
    def run_comparison(self):
        """Run the selected plugin comparison."""
        plugin_name = self.plugin_combo.currentText()
        
        if plugin_name == "No plugins available":
            QMessageBox.warning(self, "No Plugin", "No plugin selected for comparison.")
            return
        
        # Find the selected plugin
        selected_plugin = None
        for plugin in self.plugins:
            try:
                if plugin.get_name() == plugin_name:
                    selected_plugin = plugin
                    break
            except Exception:
                continue
        
        if not selected_plugin:
            QMessageBox.critical(self, "Plugin Error", "Selected plugin not found.")
            return
        
        # Get parameters
        parameters = self.get_current_parameters()
        
        # Disable UI during comparison
        self.compare_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start comparison worker
        self.comparison_worker = ComparisonWorker(
            selected_plugin, self.df1, self.df2, parameters
        )
        
        self.comparison_worker.progress_updated.connect(self.progress_bar.setValue)
        self.comparison_worker.status_updated.connect(self.status_label.setText)
        self.comparison_worker.comparison_finished.connect(self.on_comparison_finished)
        self.comparison_worker.comparison_failed.connect(self.on_comparison_failed)
        
        self.comparison_worker.start()
    
    def on_comparison_finished(self, result: Dict[str, Any]):
        """Handle successful comparison completion."""
        self.current_result = result
        
        # Update summary
        details = result.get('details', 'No details available')
        is_equal = result.get('is_equal', False)
        
        summary_text = f"Comparison Result: {'EQUAL' if is_equal else 'DIFFERENT'}\n\n"
        summary_text += details
        
        # Add metadata if available
        metadata = result.get('metadata', {})
        if metadata:
            summary_text += "\n\nMetadata:\n"
            for key, value in metadata.items():
                if key != 'analysis':  # Skip complex analysis data
                    summary_text += f"- {key}: {value}\n"
        
        self.summary_tab.setText(summary_text)
        
        # Update highlights table
        highlights = result.get('highlights', pd.DataFrame())
        self.highlights_table.populate_from_dataframe(highlights)
        
        # Reset UI
        self.compare_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Comparison completed")
        
        # Switch to summary tab
        self.results_tabs.setCurrentIndex(0)
    
    def on_comparison_failed(self, error_message: str):
        """Handle comparison failure."""
        QMessageBox.critical(self, "Comparison Error", f"Comparison failed: {error_message}")
        
        # Reset UI
        self.compare_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Comparison failed")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Stop any running comparison
        if self.comparison_worker and self.comparison_worker.isRunning():
            self.comparison_worker.terminate()
            self.comparison_worker.wait()
        
        event.accept()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create sample data for testing
    df1 = pd.DataFrame({
        'A': [1, 2, 3, 4],
        'B': ['a', 'b', 'c', 'd'],
        'C': [1.1, 2.2, 3.3, 4.4]
    })
    
    df2 = pd.DataFrame({
        'A': [1, 2, 5, 4],
        'B': ['a', 'b', 'x', 'd'],
        'C': [1.1, 2.2, 5.5, 4.4]
    })
    
    dialog = PluginCompareDialog(df1, df2, "Table 1", "Table 2")
    dialog.show()
    
    sys.exit(app.exec_())