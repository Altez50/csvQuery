# Plugin Developer Reference Guide

## Overview

This guide provides comprehensive documentation for developing custom comparison plugins for the CSV Query Tool. The plugin system allows developers to extend the application with specialized data comparison algorithms.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Plugin Architecture](#plugin-architecture)
3. [Base Plugin Class](#base-plugin-class)
4. [Plugin Interface](#plugin-interface)
5. [Parameter System](#parameter-system)
6. [Result Format](#result-format)
7. [Error Handling](#error-handling)
8. [Testing and Debugging](#testing-and-debugging)
9. [Distribution](#distribution)
10. [Best Practices](#best-practices)
11. [API Reference](#api-reference)
12. [Examples](#examples)

## Getting Started

### Prerequisites

- Python 3.7+
- pandas library
- Basic understanding of DataFrame operations
- Familiarity with object-oriented programming

### Development Environment Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd venvcsvQuery
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create your plugin directory**:
   ```bash
   mkdir plugins/my_plugin
   ```

### Quick Start Example

```python
# plugins/my_simple_plugin.py
from .base_compare import BaseComparePlugin
from pandas import DataFrame
from typing import Dict, Any

class SimpleComparePlugin(BaseComparePlugin):
    def get_name(self) -> str:
        return "Simple Comparison"
    
    def get_description(self) -> str:
        return "A simple example plugin that compares DataFrame shapes"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
        shape_equal = df1.shape == df2.shape
        
        return {
            'is_equal': shape_equal,
            'details': {
                'summary': f"Shape comparison: {df1.shape} vs {df2.shape}",
                'df1_shape': df1.shape,
                'df2_shape': df2.shape
            },
            'highlights': {},
            'metadata': {
                'plugin_name': self.get_name(),
                'plugin_version': self.get_version()
            }
        }
```

## Plugin Architecture

### Plugin Discovery

The plugin system automatically discovers plugins in the `plugins/` directory:

- **Python files**: `.py` files containing plugin classes
- **ZIP packages**: `.zip` files with plugin code and dependencies
- **Subdirectories**: Nested directories with `__init__.py` files

### Plugin Loading Process

1. **Discovery**: Scan `plugins/` directory for valid plugin files
2. **Import**: Import Python modules and extract ZIP packages
3. **Class Detection**: Find classes inheriting from `BaseComparePlugin`
4. **Instantiation**: Create plugin instances
5. **Validation**: Verify plugin interface compliance
6. **Registration**: Add to available plugins list

### Plugin Lifecycle

```
Discovery → Import → Validation → Registration → Usage → Cleanup
```

## Base Plugin Class

### Abstract Methods

All plugins must inherit from `BaseComparePlugin` and implement these methods:

```python
from abc import ABC, abstractmethod
from pandas import DataFrame
from typing import Dict, Any, List

class BaseComparePlugin(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """Return the plugin name (displayed in UI)"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return a brief description of the plugin"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Return the plugin version (semantic versioning recommended)"""
        pass
    
    @abstractmethod
    def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
        """Perform the comparison and return results"""
        pass
```

### Optional Methods

```python
def get_parameters(self) -> Dict[str, Dict[str, Any]]:
    """Return configurable parameters for the plugin"""
    return {}

def validate_dataframes(self, df1: DataFrame, df2: DataFrame) -> List[str]:
    """Validate input DataFrames and return error messages"""
    errors = []
    if df1.empty:
        errors.append("First DataFrame is empty")
    if df2.empty:
        errors.append("Second DataFrame is empty")
    return errors

def get_author(self) -> str:
    """Return plugin author information"""
    return "Unknown"

def get_license(self) -> str:
    """Return plugin license information"""
    return "Unknown"

def get_dependencies(self) -> List[str]:
    """Return list of required dependencies"""
    return []
```

## Plugin Interface

### Method Signatures

#### `get_name() -> str`
- **Purpose**: Provide a human-readable name for the plugin
- **Requirements**: Must be unique across all plugins
- **Example**: `"Row-by-Row Comparison"`

#### `get_description() -> str`
- **Purpose**: Describe what the plugin does
- **Requirements**: Should be concise but informative
- **Example**: `"Compares DataFrames row by row to identify changes"`

#### `get_version() -> str`
- **Purpose**: Version information for compatibility and updates
- **Requirements**: Semantic versioning recommended (MAJOR.MINOR.PATCH)
- **Example**: `"1.2.3"`

#### `compare(df1, df2, **kwargs) -> Dict[str, Any]`
- **Purpose**: Main comparison logic
- **Parameters**:
  - `df1`: First DataFrame to compare
  - `df2`: Second DataFrame to compare
  - `**kwargs`: Plugin-specific parameters
- **Returns**: Standardized result dictionary

### Input Validation

```python
def validate_dataframes(self, df1: DataFrame, df2: DataFrame) -> List[str]:
    errors = []
    
    # Check for empty DataFrames
    if df1.empty:
        errors.append("First DataFrame is empty")
    if df2.empty:
        errors.append("Second DataFrame is empty")
    
    # Check for required columns
    required_columns = ['id', 'name']  # Example
    for col in required_columns:
        if col not in df1.columns:
            errors.append(f"Column '{col}' missing in first DataFrame")
        if col not in df2.columns:
            errors.append(f"Column '{col}' missing in second DataFrame")
    
    # Check data types
    if not df1.dtypes.equals(df2.dtypes):
        errors.append("DataFrames have different column types")
    
    return errors
```

## Parameter System

### Parameter Definition

Plugins can define configurable parameters through the `get_parameters()` method:

```python
def get_parameters(self) -> Dict[str, Dict[str, Any]]:
    return {
        'case_sensitive': {
            'type': 'bool',
            'default': True,
            'description': 'Perform case-sensitive comparison'
        },
        'tolerance': {
            'type': 'float',
            'default': 0.001,
            'min': 0.0,
            'max': 1.0,
            'description': 'Numerical tolerance for comparisons'
        },
        'key_columns': {
            'type': 'list',
            'default': [],
            'description': 'Columns to use as keys for matching rows'
        },
        'comparison_mode': {
            'type': 'str',
            'default': 'strict',
            'options': ['strict', 'fuzzy', 'statistical'],
            'description': 'Comparison algorithm to use'
        },
        'max_rows': {
            'type': 'int',
            'default': 10000,
            'min': 1,
            'max': 1000000,
            'description': 'Maximum number of rows to process'
        }
    }
```

### Parameter Types

| Type | Description | Additional Properties |
|------|-------------|----------------------|
| `bool` | Boolean value | `default` |
| `int` | Integer value | `default`, `min`, `max` |
| `float` | Floating point value | `default`, `min`, `max` |
| `str` | String value | `default`, `options` (for dropdown) |
| `list` | List of values | `default` |

### Using Parameters

```python
def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
    # Extract parameters with defaults
    case_sensitive = kwargs.get('case_sensitive', True)
    tolerance = kwargs.get('tolerance', 0.001)
    key_columns = kwargs.get('key_columns', [])
    
    # Use parameters in comparison logic
    if not case_sensitive:
        df1 = df1.apply(lambda x: x.str.lower() if x.dtype == 'object' else x)
        df2 = df2.apply(lambda x: x.str.lower() if x.dtype == 'object' else x)
    
    # ... comparison logic
```

## Result Format

### Required Structure

All plugins must return a dictionary with these keys:

```python
{
    'is_equal': bool,        # Whether DataFrames are considered equal
    'details': dict,         # Detailed comparison results
    'highlights': dict,      # Visual highlighting information
    'metadata': dict         # Plugin and comparison metadata
}
```

### Details Section

```python
'details': {
    'summary': str,                    # Brief summary of comparison
    'total_rows_df1': int,            # Row count in first DataFrame
    'total_rows_df2': int,            # Row count in second DataFrame
    'matching_rows': int,             # Number of matching rows
    'added_rows': int,                # Rows only in df2
    'removed_rows': int,              # Rows only in df1
    'modified_rows': int,             # Rows with differences
    'differences': List[Dict],        # Detailed difference information
    'statistics': Dict,               # Statistical information
    'errors': List[str],              # Any errors encountered
    'warnings': List[str]             # Any warnings
}
```

### Highlights Section

```python
'highlights': {
    'added_rows': List[int],          # Row indices for added rows
    'removed_rows': List[int],        # Row indices for removed rows
    'modified_rows': List[int],       # Row indices for modified rows
    'modified_cells': Dict[int, List[str]],  # {row_index: [column_names]}
    'color_map': Dict[str, str]       # Color coding for different types
}
```

### Metadata Section

```python
'metadata': {
    'plugin_name': str,               # Plugin name
    'plugin_version': str,            # Plugin version
    'comparison_time': float,         # Time taken for comparison (seconds)
    'parameters_used': Dict,          # Parameters used in comparison
    'algorithm': str,                 # Algorithm description
    'memory_usage': int               # Memory used (bytes)
}
```

### Example Complete Result

```python
result = {
    'is_equal': False,
    'details': {
        'summary': 'Found 3 differences in 100 rows',
        'total_rows_df1': 100,
        'total_rows_df2': 98,
        'matching_rows': 95,
        'added_rows': 0,
        'removed_rows': 2,
        'modified_rows': 3,
        'differences': [
            {
                'row_index': 5,
                'column': 'age',
                'old_value': 25,
                'new_value': 26,
                'change_type': 'modified'
            }
        ]
    },
    'highlights': {
        'removed_rows': [10, 15],
        'modified_rows': [5, 12, 23],
        'modified_cells': {
            5: ['age'],
            12: ['name', 'city'],
            23: ['salary']
        }
    },
    'metadata': {
        'plugin_name': 'Row-by-Row Comparison',
        'plugin_version': '1.0.0',
        'comparison_time': 0.125,
        'parameters_used': {
            'case_sensitive': True,
            'key_columns': ['id']
        }
    }
}
```

## Error Handling

### Exception Handling

```python
def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
    try:
        # Validation
        errors = self.validate_dataframes(df1, df2)
        if errors:
            return self._create_error_result(errors)
        
        # Main comparison logic
        result = self._perform_comparison(df1, df2, **kwargs)
        return result
        
    except MemoryError:
        return self._create_error_result(["Insufficient memory for comparison"])
    except ValueError as e:
        return self._create_error_result([f"Value error: {str(e)}"])
    except Exception as e:
        return self._create_error_result([f"Unexpected error: {str(e)}"])

def _create_error_result(self, errors: List[str]) -> Dict[str, Any]:
    return {
        'is_equal': False,
        'details': {
            'summary': 'Comparison failed',
            'errors': errors
        },
        'highlights': {},
        'metadata': {
            'plugin_name': self.get_name(),
            'plugin_version': self.get_version(),
            'status': 'error'
        }
    }
```

### Common Error Scenarios

1. **Empty DataFrames**
2. **Memory limitations**
3. **Invalid parameters**
4. **Missing columns**
5. **Data type mismatches**
6. **Encoding issues**

## Testing and Debugging

### Unit Testing

```python
# test_my_plugin.py
import unittest
import pandas as pd
from plugins.my_plugin import MyPlugin

class TestMyPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = MyPlugin()
        self.df1 = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35]
        })
        self.df2 = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [26, 30, 35]
        })
    
    def test_plugin_interface(self):
        self.assertIsInstance(self.plugin.get_name(), str)
        self.assertIsInstance(self.plugin.get_description(), str)
        self.assertIsInstance(self.plugin.get_version(), str)
    
    def test_comparison(self):
        result = self.plugin.compare(self.df1, self.df2)
        
        # Check result structure
        self.assertIn('is_equal', result)
        self.assertIn('details', result)
        self.assertIn('highlights', result)
        self.assertIn('metadata', result)
        
        # Check types
        self.assertIsInstance(result['is_equal'], bool)
        self.assertIsInstance(result['details'], dict)
    
    def test_parameters(self):
        params = self.plugin.get_parameters()
        self.assertIsInstance(params, dict)
        
        # Test with parameters
        result = self.plugin.compare(self.df1, self.df2, case_sensitive=False)
        self.assertIsInstance(result, dict)

if __name__ == '__main__':
    unittest.main()
```

### Debug Logging

```python
import logging

class MyPlugin(BaseComparePlugin):
    def __init__(self):
        self.logger = logging.getLogger(f"plugin.{self.get_name()}")
    
    def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
        self.logger.info(f"Starting comparison: {df1.shape} vs {df2.shape}")
        
        try:
            result = self._perform_comparison(df1, df2, **kwargs)
            self.logger.info(f"Comparison completed: equal={result['is_equal']}")
            return result
        except Exception as e:
            self.logger.error(f"Comparison failed: {e}")
            raise
```

### Performance Testing

```python
import time
import psutil
import pandas as pd

def test_plugin_performance():
    plugin = MyPlugin()
    
    # Create large test data
    df1 = pd.DataFrame({
        'id': range(100000),
        'value': range(100000)
    })
    df2 = df1.copy()
    df2.loc[50000, 'value'] = 999999  # Introduce one difference
    
    # Measure performance
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss
    
    result = plugin.compare(df1, df2)
    
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss
    
    print(f"Time: {end_time - start_time:.2f} seconds")
    print(f"Memory: {(end_memory - start_memory) / 1024 / 1024:.2f} MB")
    print(f"Result: {result['is_equal']}")
```

## Distribution

### Single File Plugin

For simple plugins, create a single `.py` file:

```
plugins/
└── my_simple_plugin.py
```

### Package Plugin

For complex plugins with dependencies:

```
plugins/
└── my_complex_plugin/
    ├── __init__.py
    ├── main.py
    ├── utils.py
    └── requirements.txt
```

### ZIP Distribution

For distribution, create a ZIP file:

```
my_plugin.zip
├── my_plugin.py
├── requirements.txt
├── README.md
└── tests/
    └── test_my_plugin.py
```

### Plugin Metadata

Include metadata in your plugin:

```python
class MyPlugin(BaseComparePlugin):
    def get_author(self) -> str:
        return "Your Name <your.email@example.com>"
    
    def get_license(self) -> str:
        return "MIT"
    
    def get_dependencies(self) -> List[str]:
        return ["numpy>=1.19.0", "scipy>=1.5.0"]
    
    def get_homepage(self) -> str:
        return "https://github.com/yourname/my-plugin"
```

## Best Practices

### Performance

1. **Use vectorized operations** instead of loops
2. **Process data in chunks** for large datasets
3. **Implement early termination** for obvious differences
4. **Cache expensive computations**
5. **Use appropriate data types**

```python
# Good: Vectorized operation
def compare_columns_vectorized(self, col1, col2):
    return (col1 == col2).all()

# Bad: Loop-based operation
def compare_columns_loop(self, col1, col2):
    for i in range(len(col1)):
        if col1.iloc[i] != col2.iloc[i]:
            return False
    return True
```

### Memory Management

```python
def compare_large_dataframes(self, df1: DataFrame, df2: DataFrame, **kwargs):
    chunk_size = kwargs.get('chunk_size', 10000)
    
    # Process in chunks to manage memory
    for start in range(0, len(df1), chunk_size):
        end = min(start + chunk_size, len(df1))
        chunk1 = df1.iloc[start:end]
        chunk2 = df2.iloc[start:end] if start < len(df2) else pd.DataFrame()
        
        # Process chunk
        chunk_result = self._compare_chunk(chunk1, chunk2)
        
        # Aggregate results
        # ...
```

### User Experience

1. **Provide clear parameter descriptions**
2. **Use sensible defaults**
3. **Include progress indicators for long operations**
4. **Return meaningful error messages**
5. **Support cancellation for long operations**

### Code Quality

1. **Follow PEP 8 style guidelines**
2. **Use type hints**
3. **Write comprehensive docstrings**
4. **Include unit tests**
5. **Handle edge cases**

```python
def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
    """
    Compare two DataFrames using the plugin's algorithm.
    
    Args:
        df1: First DataFrame to compare
        df2: Second DataFrame to compare
        **kwargs: Plugin-specific parameters
            - case_sensitive (bool): Whether to perform case-sensitive comparison
            - tolerance (float): Numerical tolerance for floating-point comparisons
    
    Returns:
        Dict containing comparison results with keys:
        - is_equal: Boolean indicating if DataFrames are equal
        - details: Detailed comparison information
        - highlights: Visual highlighting data
        - metadata: Plugin and comparison metadata
    
    Raises:
        ValueError: If DataFrames have incompatible structures
        MemoryError: If comparison requires too much memory
    """
    # Implementation...
```

## API Reference

### BaseComparePlugin Class

```python
class BaseComparePlugin(ABC):
    """Abstract base class for all comparison plugins."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the plugin name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return the plugin description."""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Return the plugin version."""
        pass
    
    @abstractmethod
    def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
        """Perform comparison and return results."""
        pass
    
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Return configurable parameters."""
        return {}
    
    def validate_dataframes(self, df1: DataFrame, df2: DataFrame) -> List[str]:
        """Validate input DataFrames."""
        return []
    
    def get_author(self) -> str:
        """Return plugin author."""
        return "Unknown"
    
    def get_license(self) -> str:
        """Return plugin license."""
        return "Unknown"
    
    def get_dependencies(self) -> List[str]:
        """Return required dependencies."""
        return []
```

### PluginLoader Class

```python
class PluginLoader:
    """Utility class for loading and managing plugins."""
    
    def __init__(self, plugin_dir: str = "plugins"):
        """Initialize plugin loader."""
        pass
    
    def load_plugins(self) -> List[BaseComparePlugin]:
        """Load all plugins from directory."""
        pass
    
    def get_available_plugins(self) -> Dict[str, type]:
        """Get mapping of plugin names to classes."""
        pass
    
    def get_plugin_by_name(self, name: str) -> Optional[BaseComparePlugin]:
        """Get plugin instance by name."""
        pass
    
    def get_plugin_info(self) -> List[Dict[str, str]]:
        """Get information about loaded plugins."""
        pass
    
    def reload_plugins(self) -> List[BaseComparePlugin]:
        """Reload all plugins."""
        pass
```

## Examples

### Simple Comparison Plugin

```python
from .base_compare import BaseComparePlugin
from pandas import DataFrame
from typing import Dict, Any

class ShapeComparePlugin(BaseComparePlugin):
    """Plugin that compares DataFrame shapes and basic statistics."""
    
    def get_name(self) -> str:
        return "Shape Comparison"
    
    def get_description(self) -> str:
        return "Compares DataFrame shapes and basic statistics"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
        # Compare shapes
        shape_equal = df1.shape == df2.shape
        
        # Compare column names
        columns_equal = list(df1.columns) == list(df2.columns)
        
        # Basic statistics
        stats1 = df1.describe() if not df1.empty else None
        stats2 = df2.describe() if not df2.empty else None
        
        is_equal = shape_equal and columns_equal
        
        return {
            'is_equal': is_equal,
            'details': {
                'summary': f"Shape: {df1.shape} vs {df2.shape}, Columns: {'✓' if columns_equal else '✗'}",
                'shape_equal': shape_equal,
                'columns_equal': columns_equal,
                'df1_shape': df1.shape,
                'df2_shape': df2.shape,
                'df1_columns': list(df1.columns),
                'df2_columns': list(df2.columns),
                'statistics': {
                    'df1': stats1.to_dict() if stats1 is not None else None,
                    'df2': stats2.to_dict() if stats2 is not None else None
                }
            },
            'highlights': {},
            'metadata': {
                'plugin_name': self.get_name(),
                'plugin_version': self.get_version()
            }
        }
```

### Advanced Plugin with Parameters

```python
from .base_compare import BaseComparePlugin
from pandas import DataFrame
from typing import Dict, Any, List
import numpy as np

class FuzzyComparePlugin(BaseComparePlugin):
    """Plugin that performs fuzzy string matching comparison."""
    
    def get_name(self) -> str:
        return "Fuzzy String Comparison"
    
    def get_description(self) -> str:
        return "Compares text data using fuzzy string matching algorithms"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            'similarity_threshold': {
                'type': 'float',
                'default': 0.8,
                'min': 0.0,
                'max': 1.0,
                'description': 'Minimum similarity score to consider strings as matching'
            },
            'algorithm': {
                'type': 'str',
                'default': 'levenshtein',
                'options': ['levenshtein', 'jaro_winkler', 'soundex'],
                'description': 'Fuzzy matching algorithm to use'
            },
            'case_sensitive': {
                'type': 'bool',
                'default': False,
                'description': 'Perform case-sensitive comparison'
            }
        }
    
    def get_dependencies(self) -> List[str]:
        return ['fuzzywuzzy>=0.18.0', 'python-levenshtein>=0.12.0']
    
    def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
        try:
            from fuzzywuzzy import fuzz
        except ImportError:
            return self._create_error_result(["fuzzywuzzy library not installed"])
        
        # Extract parameters
        threshold = kwargs.get('similarity_threshold', 0.8)
        algorithm = kwargs.get('algorithm', 'levenshtein')
        case_sensitive = kwargs.get('case_sensitive', False)
        
        # Validate inputs
        errors = self.validate_dataframes(df1, df2)
        if errors:
            return self._create_error_result(errors)
        
        # Perform fuzzy comparison
        results = self._fuzzy_compare(df1, df2, threshold, algorithm, case_sensitive)
        
        return results
    
    def _fuzzy_compare(self, df1: DataFrame, df2: DataFrame, 
                      threshold: float, algorithm: str, case_sensitive: bool) -> Dict[str, Any]:
        from fuzzywuzzy import fuzz
        
        # Implementation of fuzzy comparison logic
        # This is a simplified example
        
        total_cells = df1.size
        matching_cells = 0
        differences = []
        
        for col in df1.columns:
            if col in df2.columns:
                for idx in df1.index:
                    if idx in df2.index:
                        val1 = str(df1.loc[idx, col])
                        val2 = str(df2.loc[idx, col])
                        
                        if not case_sensitive:
                            val1 = val1.lower()
                            val2 = val2.lower()
                        
                        # Calculate similarity based on algorithm
                        if algorithm == 'levenshtein':
                            similarity = fuzz.ratio(val1, val2) / 100.0
                        elif algorithm == 'jaro_winkler':
                            similarity = fuzz.WRatio(val1, val2) / 100.0
                        else:  # soundex or other
                            similarity = fuzz.ratio(val1, val2) / 100.0
                        
                        if similarity >= threshold:
                            matching_cells += 1
                        else:
                            differences.append({
                                'row': idx,
                                'column': col,
                                'value1': val1,
                                'value2': val2,
                                'similarity': similarity
                            })
        
        match_percentage = (matching_cells / total_cells) * 100 if total_cells > 0 else 0
        is_equal = match_percentage >= (threshold * 100)
        
        return {
            'is_equal': is_equal,
            'details': {
                'summary': f"Fuzzy match: {match_percentage:.1f}% similarity",
                'total_cells': total_cells,
                'matching_cells': matching_cells,
                'match_percentage': match_percentage,
                'differences': differences[:100],  # Limit to first 100 differences
                'algorithm_used': algorithm,
                'threshold_used': threshold
            },
            'highlights': {
                'low_similarity_cells': [(d['row'], d['column']) for d in differences]
            },
            'metadata': {
                'plugin_name': self.get_name(),
                'plugin_version': self.get_version(),
                'parameters_used': {
                    'similarity_threshold': threshold,
                    'algorithm': algorithm,
                    'case_sensitive': case_sensitive
                }
            }
        }
    
    def _create_error_result(self, errors: List[str]) -> Dict[str, Any]:
        return {
            'is_equal': False,
            'details': {
                'summary': 'Comparison failed',
                'errors': errors
            },
            'highlights': {},
            'metadata': {
                'plugin_name': self.get_name(),
                'plugin_version': self.get_version(),
                'status': 'error'
            }
        }
```

---

## Conclusion

This guide provides a comprehensive foundation for developing custom comparison plugins. The plugin system is designed to be flexible and extensible while maintaining consistency in the user interface and result format.

For additional support or questions, please refer to the main project documentation or contact the development team.

## Version History

- **1.0.0** (2024): Initial plugin system implementation
- **1.1.0** (TBD): Enhanced parameter system and validation
- **1.2.0** (TBD): Plugin repository and distribution system