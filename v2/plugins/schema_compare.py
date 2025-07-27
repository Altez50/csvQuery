from .base_compare import BaseComparePlugin
import pandas as pd
from pandas import DataFrame
from typing import Dict, Any, List, Set

class SchemaComparePlugin(BaseComparePlugin):
    """Plugin for schema comparison of DataFrames."""
    
    def get_name(self) -> str:
        return "Schema Comparison"
    
    def get_description(self) -> str:
        return "Compare DataFrame schemas including column names, types, and constraints"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            'check_column_order': {
                'type': 'bool',
                'default': True,
                'description': 'Check if column order is the same'
            },
            'check_data_types': {
                'type': 'bool',
                'default': True,
                'description': 'Compare data types of columns'
            },
            'check_nullable': {
                'type': 'bool',
                'default': True,
                'description': 'Check for null value presence'
            },
            'check_index': {
                'type': 'bool',
                'default': False,
                'description': 'Compare index schemas'
            },
            'type_compatibility': {
                'type': 'list',
                'default': 'strict',
                'description': 'Type comparison mode',
                'options': ['strict', 'compatible', 'loose']
            }
        }
    
    def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
        """Compare DataFrame schemas."""
        # Validate inputs
        validation_error = self.validate_dataframes(df1, df2)
        if validation_error:
            return {
                'is_equal': False,
                'details': f"Validation error: {validation_error}",
                'highlights': pd.DataFrame(),
                'metadata': {'error': validation_error}
            }
        
        # Get parameters
        check_column_order = kwargs.get('check_column_order', True)
        check_data_types = kwargs.get('check_data_types', True)
        check_nullable = kwargs.get('check_nullable', True)
        check_index = kwargs.get('check_index', False)
        type_compatibility = kwargs.get('type_compatibility', 'strict')
        
        # Perform schema comparison
        comparison_results = {
            'column_names': self._compare_column_names(df1, df2, check_column_order),
            'data_types': self._compare_data_types(df1, df2, type_compatibility) if check_data_types else None,
            'nullable_info': self._compare_nullable(df1, df2) if check_nullable else None,
            'index_schema': self._compare_index_schema(df1, df2) if check_index else None,
            'shape': self._compare_shape(df1, df2)
        }
        
        # Determine if schemas are equal
        is_equal = self._determine_equality(comparison_results)
        
        # Generate highlights and details
        highlights = self._create_highlights(comparison_results)
        details = self._generate_details(comparison_results)
        
        return {
            'is_equal': is_equal,
            'details': details,
            'highlights': highlights,
            'metadata': {
                'comparison_results': comparison_results,
                'parameters': {
                    'check_column_order': check_column_order,
                    'check_data_types': check_data_types,
                    'check_nullable': check_nullable,
                    'check_index': check_index,
                    'type_compatibility': type_compatibility
                }
            }
        }
    
    def _compare_column_names(self, df1: DataFrame, df2: DataFrame, check_order: bool) -> Dict[str, Any]:
        """Compare column names and optionally their order."""
        cols1 = list(df1.columns)
        cols2 = list(df2.columns)
        
        # Find differences
        only_in_df1 = set(cols1) - set(cols2)
        only_in_df2 = set(cols2) - set(cols1)
        common_columns = set(cols1) & set(cols2)
        
        # Check order if requested
        order_matches = True
        if check_order and set(cols1) == set(cols2):
            order_matches = cols1 == cols2
        
        return {
            'df1_columns': cols1,
            'df2_columns': cols2,
            'only_in_df1': list(only_in_df1),
            'only_in_df2': list(only_in_df2),
            'common_columns': list(common_columns),
            'order_matches': order_matches,
            'check_order': check_order,
            'names_equal': len(only_in_df1) == 0 and len(only_in_df2) == 0 and (not check_order or order_matches)
        }
    
    def _compare_data_types(self, df1: DataFrame, df2: DataFrame, compatibility_mode: str) -> Dict[str, Any]:
        """Compare data types of columns."""
        common_columns = set(df1.columns) & set(df2.columns)
        type_differences = {}
        compatible_types = {}
        
        for col in common_columns:
            dtype1 = df1[col].dtype
            dtype2 = df2[col].dtype
            
            # Check strict equality
            strict_equal = dtype1 == dtype2
            
            # Check compatibility based on mode
            compatible = self._are_types_compatible(dtype1, dtype2, compatibility_mode)
            
            type_differences[col] = {
                'df1_type': str(dtype1),
                'df2_type': str(dtype2),
                'strict_equal': strict_equal,
                'compatible': compatible
            }
            
            if not strict_equal:
                compatible_types[col] = {
                    'df1_type': str(dtype1),
                    'df2_type': str(dtype2),
                    'compatible': compatible
                }
        
        return {
            'type_differences': type_differences,
            'incompatible_types': {k: v for k, v in compatible_types.items() if not v['compatible']},
            'compatibility_mode': compatibility_mode,
            'all_types_compatible': all(info['compatible'] for info in type_differences.values())
        }
    
    def _are_types_compatible(self, dtype1, dtype2, mode: str) -> bool:
        """Check if two data types are compatible based on the specified mode."""
        if dtype1 == dtype2:
            return True
        
        if mode == 'strict':
            return False
        
        # Convert to string for easier comparison
        str1, str2 = str(dtype1), str(dtype2)
        
        if mode == 'compatible':
            # Numeric types are compatible with each other
            numeric_types = {'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64',
                           'float16', 'float32', 'float64', 'complex64', 'complex128'}
            
            if any(nt in str1 for nt in numeric_types) and any(nt in str2 for nt in numeric_types):
                return True
            
            # String types are compatible
            string_types = {'object', 'string', 'category'}
            if any(st in str1 for st in string_types) and any(st in str2 for st in string_types):
                return True
            
            # Datetime types are compatible
            datetime_types = {'datetime', 'timedelta'}
            if any(dt in str1 for dt in datetime_types) and any(dt in str2 for dt in datetime_types):
                return True
        
        elif mode == 'loose':
            # In loose mode, most types are considered compatible except for very different ones
            incompatible_pairs = [
                (['datetime', 'timedelta'], ['int', 'float', 'object']),
                (['bool'], ['datetime', 'timedelta']),
                (['complex'], ['datetime', 'timedelta', 'bool'])
            ]
            
            for group1, group2 in incompatible_pairs:
                if (any(g in str1 for g in group1) and any(g in str2 for g in group2)) or \
                   (any(g in str1 for g in group2) and any(g in str2 for g in group1)):
                    return False
            
            return True
        
        return False
    
    def _compare_nullable(self, df1: DataFrame, df2: DataFrame) -> Dict[str, Any]:
        """Compare nullable information (presence of null values)."""
        common_columns = set(df1.columns) & set(df2.columns)
        nullable_info = {}
        
        for col in common_columns:
            has_nulls_df1 = df1[col].isnull().any()
            has_nulls_df2 = df2[col].isnull().any()
            null_count_df1 = df1[col].isnull().sum()
            null_count_df2 = df2[col].isnull().sum()
            
            nullable_info[col] = {
                'df1_has_nulls': has_nulls_df1,
                'df2_has_nulls': has_nulls_df2,
                'df1_null_count': int(null_count_df1),
                'df2_null_count': int(null_count_df2),
                'nullable_matches': has_nulls_df1 == has_nulls_df2
            }
        
        return {
            'nullable_info': nullable_info,
            'all_nullable_matches': all(info['nullable_matches'] for info in nullable_info.values())
        }
    
    def _compare_index_schema(self, df1: DataFrame, df2: DataFrame) -> Dict[str, Any]:
        """Compare index schemas."""
        return {
            'df1_index_name': df1.index.name,
            'df2_index_name': df2.index.name,
            'df1_index_dtype': str(df1.index.dtype),
            'df2_index_dtype': str(df2.index.dtype),
            'df1_index_length': len(df1.index),
            'df2_index_length': len(df2.index),
            'index_names_match': df1.index.name == df2.index.name,
            'index_dtypes_match': df1.index.dtype == df2.index.dtype,
            'index_lengths_match': len(df1.index) == len(df2.index)
        }
    
    def _compare_shape(self, df1: DataFrame, df2: DataFrame) -> Dict[str, Any]:
        """Compare DataFrame shapes."""
        return {
            'df1_shape': df1.shape,
            'df2_shape': df2.shape,
            'shapes_match': df1.shape == df2.shape,
            'rows_match': df1.shape[0] == df2.shape[0],
            'columns_match': df1.shape[1] == df2.shape[1]
        }
    
    def _determine_equality(self, results: Dict[str, Any]) -> bool:
        """Determine if schemas are equal based on comparison results."""
        # Check column names
        if not results['column_names']['names_equal']:
            return False
        
        # Check data types if compared
        if results['data_types'] and not results['data_types']['all_types_compatible']:
            return False
        
        # Check nullable info if compared
        if results['nullable_info'] and not results['nullable_info']['all_nullable_matches']:
            return False
        
        # Check index schema if compared
        if results['index_schema']:
            index_equal = (results['index_schema']['index_names_match'] and 
                          results['index_schema']['index_dtypes_match'] and 
                          results['index_schema']['index_lengths_match'])
            if not index_equal:
                return False
        
        # Check shape
        if not results['shape']['shapes_match']:
            return False
        
        return True
    
    def _create_highlights(self, results: Dict[str, Any]) -> DataFrame:
        """Create highlights DataFrame from comparison results."""
        highlights_data = []
        
        # Shape differences
        if not results['shape']['shapes_match']:
            highlights_data.append({
                'Category': 'Shape',
                'Item': 'DataFrame dimensions',
                'DataFrame 1': str(results['shape']['df1_shape']),
                'DataFrame 2': str(results['shape']['df2_shape']),
                'Status': 'Different',
                '_diff_type': 'different'
            })
        else:
            highlights_data.append({
                'Category': 'Shape',
                'Item': 'DataFrame dimensions',
                'DataFrame 1': str(results['shape']['df1_shape']),
                'DataFrame 2': str(results['shape']['df2_shape']),
                'Status': 'Same',
                '_diff_type': 'same'
            })
        
        # Column name differences
        col_results = results['column_names']
        if col_results['only_in_df1']:
            for col in col_results['only_in_df1']:
                highlights_data.append({
                    'Category': 'Columns',
                    'Item': col,
                    'DataFrame 1': 'Present',
                    'DataFrame 2': 'Missing',
                    'Status': 'Only in DF1',
                    '_diff_type': 'only_in_a'
                })
        
        if col_results['only_in_df2']:
            for col in col_results['only_in_df2']:
                highlights_data.append({
                    'Category': 'Columns',
                    'Item': col,
                    'DataFrame 1': 'Missing',
                    'DataFrame 2': 'Present',
                    'Status': 'Only in DF2',
                    '_diff_type': 'only_in_b'
                })
        
        # Column order
        if col_results['check_order'] and not col_results['order_matches']:
            highlights_data.append({
                'Category': 'Columns',
                'Item': 'Column order',
                'DataFrame 1': 'Different order',
                'DataFrame 2': 'Different order',
                'Status': 'Order differs',
                '_diff_type': 'different'
            })
        
        # Data type differences
        if results['data_types']:
            for col, type_info in results['data_types']['incompatible_types'].items():
                highlights_data.append({
                    'Category': 'Data Types',
                    'Item': col,
                    'DataFrame 1': type_info['df1_type'],
                    'DataFrame 2': type_info['df2_type'],
                    'Status': 'Incompatible',
                    '_diff_type': 'different'
                })
        
        # Nullable differences
        if results['nullable_info']:
            for col, null_info in results['nullable_info']['nullable_info'].items():
                if not null_info['nullable_matches']:
                    highlights_data.append({
                        'Category': 'Nullable',
                        'Item': col,
                        'DataFrame 1': f"Nulls: {null_info['df1_null_count']}",
                        'DataFrame 2': f"Nulls: {null_info['df2_null_count']}",
                        'Status': 'Different null patterns',
                        '_diff_type': 'different'
                    })
        
        # Index differences
        if results['index_schema']:
            idx_results = results['index_schema']
            if not idx_results['index_names_match']:
                highlights_data.append({
                    'Category': 'Index',
                    'Item': 'Index name',
                    'DataFrame 1': str(idx_results['df1_index_name']),
                    'DataFrame 2': str(idx_results['df2_index_name']),
                    'Status': 'Different',
                    '_diff_type': 'different'
                })
            
            if not idx_results['index_dtypes_match']:
                highlights_data.append({
                    'Category': 'Index',
                    'Item': 'Index data type',
                    'DataFrame 1': idx_results['df1_index_dtype'],
                    'DataFrame 2': idx_results['df2_index_dtype'],
                    'Status': 'Different',
                    '_diff_type': 'different'
                })
        
        return pd.DataFrame(highlights_data)
    
    def _generate_details(self, results: Dict[str, Any]) -> str:
        """Generate human-readable details."""
        details = "Schema Comparison Results:\n\n"
        
        # Shape comparison
        shape_results = results['shape']
        details += f"Shape: {shape_results['df1_shape']} vs {shape_results['df2_shape']}"
        if shape_results['shapes_match']:
            details += " ✓\n"
        else:
            details += " ✗\n"
        
        # Column comparison
        col_results = results['column_names']
        details += f"\nColumns: {len(col_results['df1_columns'])} vs {len(col_results['df2_columns'])}"
        if col_results['names_equal']:
            details += " ✓\n"
        else:
            details += " ✗\n"
            
            if col_results['only_in_df1']:
                details += f"  - Only in DataFrame 1: {col_results['only_in_df1']}\n"
            if col_results['only_in_df2']:
                details += f"  - Only in DataFrame 2: {col_results['only_in_df2']}\n"
            if col_results['check_order'] and not col_results['order_matches']:
                details += "  - Column order differs\n"
        
        # Data types
        if results['data_types']:
            type_results = results['data_types']
            details += f"\nData Types ({type_results['compatibility_mode']} mode):"
            if type_results['all_types_compatible']:
                details += " ✓\n"
            else:
                details += " ✗\n"
                for col, type_info in type_results['incompatible_types'].items():
                    details += f"  - {col}: {type_info['df1_type']} vs {type_info['df2_type']}\n"
        
        # Nullable info
        if results['nullable_info']:
            null_results = results['nullable_info']
            details += "\nNullable patterns:"
            if null_results['all_nullable_matches']:
                details += " ✓\n"
            else:
                details += " ✗\n"
                for col, null_info in null_results['nullable_info'].items():
                    if not null_info['nullable_matches']:
                        details += f"  - {col}: {null_info['df1_null_count']} vs {null_info['df2_null_count']} nulls\n"
        
        # Index schema
        if results['index_schema']:
            idx_results = results['index_schema']
            details += "\nIndex schema:"
            index_match = (idx_results['index_names_match'] and 
                          idx_results['index_dtypes_match'] and 
                          idx_results['index_lengths_match'])
            if index_match:
                details += " ✓\n"
            else:
                details += " ✗\n"
                if not idx_results['index_names_match']:
                    details += f"  - Names: {idx_results['df1_index_name']} vs {idx_results['df2_index_name']}\n"
                if not idx_results['index_dtypes_match']:
                    details += f"  - Types: {idx_results['df1_index_dtype']} vs {idx_results['df2_index_dtype']}\n"
                if not idx_results['index_lengths_match']:
                    details += f"  - Lengths: {idx_results['df1_index_length']} vs {idx_results['df2_index_length']}\n"
        
        return details