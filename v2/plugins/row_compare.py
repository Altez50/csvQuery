from plugins.base_compare import BaseComparePlugin
import pandas as pd
from pandas import DataFrame
from typing import Dict, Any

class RowComparePlugin(BaseComparePlugin):
    """Plugin for row-by-row comparison of DataFrames."""
    
    def get_name(self) -> str:
        return "Row-by-Row Comparison"
    
    def get_description(self) -> str:
        return "Compares DataFrames row by row, identifying added, removed, and modified rows"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            'key_columns': {
                'type': 'list',
                'default': [],
                'description': 'Columns to use as primary key for row matching',
                'options': []  # Will be populated with actual column names
            },
            'ignore_case': {
                'type': 'bool',
                'default': False,
                'description': 'Ignore case when comparing string values'
            },
            'ignore_whitespace': {
                'type': 'bool',
                'default': False,
                'description': 'Ignore leading/trailing whitespace in string values'
            }
        }
    
    def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
        """Compare DataFrames row by row."""
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
        key_columns = kwargs.get('key_columns', [])
        ignore_case = kwargs.get('ignore_case', False)
        ignore_whitespace = kwargs.get('ignore_whitespace', False)
        
        # Prepare DataFrames for comparison
        df1_prep = self._prepare_dataframe(df1.copy(), ignore_case, ignore_whitespace)
        df2_prep = self._prepare_dataframe(df2.copy(), ignore_case, ignore_whitespace)
        
        # Add source indicators
        df1_prep['_source'] = 'df1'
        df2_prep['_source'] = 'df2'
        
        if key_columns:
            # Use specified key columns for matching
            result = self._compare_with_keys(df1_prep, df2_prep, key_columns)
        else:
            # Compare all rows without specific keys
            result = self._compare_without_keys(df1_prep, df2_prep)
        
        return result
    
    def _prepare_dataframe(self, df: DataFrame, ignore_case: bool, ignore_whitespace: bool) -> DataFrame:
        """Prepare DataFrame for comparison by applying transformations."""
        if ignore_case or ignore_whitespace:
            for col in df.select_dtypes(include=['object']).columns:
                if ignore_case:
                    df[col] = df[col].astype(str).str.lower()
                if ignore_whitespace:
                    df[col] = df[col].astype(str).str.strip()
        return df
    
    def _compare_with_keys(self, df1: DataFrame, df2: DataFrame, key_columns: list) -> Dict[str, Any]:
        """Compare DataFrames using specified key columns."""
        # Validate key columns exist
        missing_keys_df1 = [col for col in key_columns if col not in df1.columns]
        missing_keys_df2 = [col for col in key_columns if col not in df2.columns]
        
        if missing_keys_df1 or missing_keys_df2:
            error_msg = f"Key columns missing - DF1: {missing_keys_df1}, DF2: {missing_keys_df2}"
            return {
                'is_equal': False,
                'details': error_msg,
                'highlights': pd.DataFrame(),
                'metadata': {'error': error_msg}
            }
        
        # Create composite keys
        df1['_key'] = df1[key_columns].apply(lambda x: '|'.join(x.astype(str)), axis=1)
        df2['_key'] = df2[key_columns].apply(lambda x: '|'.join(x.astype(str)), axis=1)
        
        # Find differences
        keys_df1 = set(df1['_key'])
        keys_df2 = set(df2['_key'])
        
        only_in_df1 = keys_df1 - keys_df2
        only_in_df2 = keys_df2 - keys_df1
        common_keys = keys_df1 & keys_df2
        
        differences = []
        modified_rows = []
        
        # Check for modified rows in common keys
        for key in common_keys:
            row1 = df1[df1['_key'] == key].iloc[0]
            row2 = df2[df2['_key'] == key].iloc[0]
            
            # Compare non-key columns
            non_key_cols = [col for col in df1.columns if col not in key_columns + ['_source', '_key']]
            row_diff = False
            
            for col in non_key_cols:
                if col in df2.columns:
                    if str(row1[col]) != str(row2[col]):
                        row_diff = True
                        break
            
            if row_diff:
                modified_rows.append(key)
        
        # Create highlights DataFrame
        highlights = pd.DataFrame()
        
        # Add rows only in df1 (removed)
        if only_in_df1:
            removed_rows = df1[df1['_key'].isin(only_in_df1)].copy()
            removed_rows['_diff_type'] = 'removed'
            highlights = pd.concat([highlights, removed_rows], ignore_index=True)
        
        # Add rows only in df2 (added)
        if only_in_df2:
            added_rows = df2[df2['_key'].isin(only_in_df2)].copy()
            added_rows['_diff_type'] = 'added'
            highlights = pd.concat([highlights, added_rows], ignore_index=True)
        
        # Add modified rows
        if modified_rows:
            modified_df1 = df1[df1['_key'].isin(modified_rows)].copy()
            modified_df1['_diff_type'] = 'modified_old'
            modified_df2 = df2[df2['_key'].isin(modified_rows)].copy()
            modified_df2['_diff_type'] = 'modified_new'
            highlights = pd.concat([highlights, modified_df1, modified_df2], ignore_index=True)
        
        # Clean up temporary columns
        if '_key' in highlights.columns:
            highlights = highlights.drop('_key', axis=1)
        
        # Generate summary
        total_changes = len(only_in_df1) + len(only_in_df2) + len(modified_rows)
        is_equal = total_changes == 0
        
        details = f"Row comparison results:\n"
        details += f"- Rows only in first table: {len(only_in_df1)}\n"
        details += f"- Rows only in second table: {len(only_in_df2)}\n"
        details += f"- Modified rows: {len(modified_rows)}\n"
        details += f"- Total differences: {total_changes}"
        
        return {
            'is_equal': is_equal,
            'details': details,
            'highlights': highlights,
            'metadata': {
                'removed_count': len(only_in_df1),
                'added_count': len(only_in_df2),
                'modified_count': len(modified_rows),
                'total_changes': total_changes,
                'key_columns': key_columns
            }
        }
    
    def _compare_without_keys(self, df1: DataFrame, df2: DataFrame) -> Dict[str, Any]:
        """Compare DataFrames without specific key columns."""
        # Simple approach: find rows that exist in one but not the other
        df1_clean = df1.drop('_source', axis=1)
        df2_clean = df2.drop('_source', axis=1)
        
        # Find differences using pandas merge
        merged = pd.concat([df1_clean, df2_clean]).drop_duplicates(keep=False)
        
        is_equal = merged.empty and len(df1) == len(df2)
        
        details = f"Simple row comparison results:\n"
        details += f"- Total rows in first table: {len(df1)}\n"
        details += f"- Total rows in second table: {len(df2)}\n"
        details += f"- Different rows found: {len(merged)}\n"
        details += f"- Tables are equal: {is_equal}"
        
        # Add diff type for highlighting
        if not merged.empty:
            merged['_diff_type'] = 'different'
            merged['_source'] = 'unknown'
        
        return {
            'is_equal': is_equal,
            'details': details,
            'highlights': merged,
            'metadata': {
                'df1_rows': len(df1),
                'df2_rows': len(df2),
                'different_rows': len(merged)
            }
        }