# CSV Query Tool - Plugin System

This directory contains the plugin system for advanced data comparison functionality in the CSV Query Tool.

## Overview

The plugin system allows you to extend the application with custom comparison algorithms. Each plugin implements a specific comparison strategy and can be used through the file tree context menu.

## Available Plugins

### 1. Row-by-Row Comparison (`row_compare.py`)
- **Purpose**: Compares DataFrames row by row to identify added, removed, and modified records
- **Best for**: Detailed change tracking, audit trails, version comparison
- **Features**:
  - Key column selection for matching rows
  - Case-sensitive/insensitive comparison
  - Whitespace handling options
  - Detailed change tracking

### 2. Column-wise Statistical Comparison (`column_compare.py`)
- **Purpose**: Performs statistical analysis and comparison of columns
- **Best for**: Data quality assessment, statistical validation
- **Features**:
  - Statistical summaries (mean, median, std, etc.)
  - Null value analysis
  - Data type comparison
  - Configurable tolerance for numerical comparisons

### 3. Hash-based Comparison (`hash_compare.py`)
- **Purpose**: Quick checksum-based comparison for large datasets
- **Best for**: Fast equality checks, data integrity verification
- **Features**:
  - Multiple hash algorithms (MD5, SHA1, SHA256)
  - Chunk-based processing for large files
  - Optional detailed analysis when hashes differ
  - Index inclusion options

### 4. Schema Comparison (`schema_compare.py`)
- **Purpose**: Compares DataFrame structures and metadata
- **Best for**: Schema validation, structure analysis
- **Features**:
  - Column name comparison
  - Data type analysis
  - Nullability checks
  - Column order validation
  - Index schema comparison

## How to Use

### Through the GUI

1. **Open the CSV Query Tool**
2. **Navigate to files** in the left file tree
3. **Right-click on a CSV/Excel file**
4. **Select "📋 Add to Comparison"** to add files to your comparison set
5. **Right-click again** and choose **"🔍 Compare With..."**
6. **Select a plugin** from the submenu (e.g., "📊 Row-by-Row Comparison")
7. **Configure parameters** in the comparison dialog
8. **View results** in the tabbed interface

### Programmatically

```python
from utils.plugin_loader import PluginLoader
from plugins.row_compare import RowComparePlugin
import pandas as pd

# Load data
df1 = pd.read_csv('file1.csv')
df2 = pd.read_csv('file2.csv')

# Use a plugin
plugin = RowComparePlugin()
result = plugin.compare(df1, df2, key_columns=['id'])

# Access results
print(f"Equal: {result['is_equal']}")
print(f"Summary: {result['details']['summary']}")
```

## Creating Custom Plugins

### 1. Create a Plugin Class

Create a new Python file in the `plugins/` directory:

```python
from .base_compare import BaseComparePlugin
from pandas import DataFrame
from typing import Dict, Any

class MyCustomPlugin(BaseComparePlugin):
    def get_name(self) -> str:
        return "My Custom Comparison"
    
    def get_description(self) -> str:
        return "Description of what this plugin does"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            'my_param': {
                'type': 'bool',
                'default': True,
                'description': 'Enable my feature'
            }
        }
    
    def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
        # Your comparison logic here
        return {
            'is_equal': True,  # or False
            'details': {
                'summary': 'Comparison summary',
                # ... other details
            },
            'highlights': {
                # Visual highlighting information
            },
            'metadata': {
                'plugin_name': self.get_name(),
                'plugin_version': self.get_version()
            }
        }
```

### 2. Plugin Requirements

All plugins must:
- Inherit from `BaseComparePlugin`
- Implement all abstract methods
- Return results in the specified format
- Handle errors gracefully

### 3. Result Format

Plugins must return a dictionary with these keys:
- `is_equal` (bool): Whether the DataFrames are considered equal
- `details` (dict): Detailed comparison results
- `highlights` (dict): Information for visual highlighting
- `metadata` (dict): Plugin and comparison metadata

## Plugin Parameters

Plugins can define configurable parameters through the `get_parameters()` method:

```python
def get_parameters(self) -> Dict[str, Dict[str, Any]]:
    return {
        'parameter_name': {
            'type': 'bool|int|float|str|list',
            'default': default_value,
            'description': 'Parameter description',
            'options': [list_of_options],  # For list type
            'min': min_value,  # For numeric types
            'max': max_value   # For numeric types
        }
    }
```

## Installation and Distribution

### Installing Plugins

1. **Python files**: Place `.py` files directly in the `plugins/` directory
2. **ZIP packages**: Place `.zip` files containing plugin code in the `plugins/` directory
3. **From URL**: Use the plugin downloader utility (if implemented)

### Plugin Structure for ZIP Distribution

```
my_plugin.zip
├── my_plugin.py
├── requirements.txt (optional)
└── README.md (optional)
```

## Troubleshooting

### Common Issues

1. **Plugin not loading**:
   - Check that the file is in the `plugins/` directory
   - Verify the plugin inherits from `BaseComparePlugin`
   - Check for syntax errors in the plugin code

2. **Import errors**:
   - Ensure all required dependencies are installed
   - Check that relative imports use the correct syntax

3. **Runtime errors**:
   - Implement proper error handling in your plugin
   - Validate input DataFrames before processing
   - Use the `validate_dataframes()` method

### Debug Mode

To debug plugin loading:

```python
from utils.plugin_loader import PluginLoader

loader = PluginLoader()
plugins = loader.load_plugins()
errors = loader.get_plugin_errors()

print("Loaded plugins:", len(plugins))
print("Errors:", errors)
```

## API Reference

### BaseComparePlugin

Abstract base class for all comparison plugins.

#### Required Methods

- `get_name() -> str`: Return plugin name
- `get_description() -> str`: Return plugin description  
- `get_version() -> str`: Return plugin version
- `compare(df1, df2, **kwargs) -> Dict`: Perform comparison

#### Optional Methods

- `get_parameters() -> Dict`: Return configurable parameters
- `validate_dataframes(df1, df2) -> List[str]`: Validate input data

### PluginLoader

Utility class for loading and managing plugins.

#### Key Methods

- `load_plugins() -> List`: Load all plugins from directory
- `get_available_plugins() -> Dict[str, type]`: Get plugin name to class mapping
- `get_plugin_by_name(name) -> Plugin`: Get plugin instance by name
- `get_plugin_info() -> List[Dict]`: Get information about loaded plugins
- `reload_plugins() -> List`: Reload all plugins

## Contributing

To contribute new plugins:

1. Fork the repository
2. Create your plugin following the guidelines above
3. Test your plugin thoroughly
4. Submit a pull request with documentation

## License

Plugins should be compatible with the main application's license.