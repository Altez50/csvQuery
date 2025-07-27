from plugins.base_compare import BaseComparePlugin
import pandas as pd
import numpy as np
from pandas import DataFrame
from typing import Dict, Any

class ColumnComparePlugin(BaseComparePlugin):
    """Plugin for statistical column-wise comparison of DataFrames."""
    
    def get_name(self) -> str:
        return "Column Statistical Comparison"
    
    def get_description(self) -> str:
        return "Compares DataFrames by analyzing statistical properties of each column"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            'include_nulls': {
                'type': 'bool',
                'default': True,
                'description': 'Include null value counts in comparison'
            },
            'include_stats': {
                'type': 'bool',
                'default': True,
                'description': 'Include statistical measures (mean, std, etc.)'
            },
            'tolerance': {
                'type': 'float',
                'default': 0.001,
                'description': 'Tolerance for numerical comparisons'
            }
        }
    
    def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
        """Compare DataFrames column by column."""
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
        include_nulls = kwargs.get('include_nulls', True)
        include_stats = kwargs.get('include_stats', True)
        tolerance = kwargs.get('tolerance', 0.001)
        
        # Get all columns from both DataFrames
        all_columns = set(df1.columns) | set(df2.columns)
        common_columns = set(df1.columns) & set(df2.columns)
        only_in_df1 = set(df1.columns) - set(df2.columns)
        only_in_df2 = set(df2.columns) - set(df1.columns)
        
        # Prepare results
        comparison_results = []
        differences_found = False
        
        # Compare common columns
        for col in common_columns:
            col_result = self._compare_column(df1[col], df2[col], col, include_nulls, include_stats, tolerance)
            comparison_results.append(col_result)
            if not col_result['is_equal']:
                differences_found = True
        
        # Handle columns only in df1
        for col in only_in_df1:
            col_result = {
                'column': col,
                'status': 'only_in_df1',
                'is_equal': False,
                'df1_stats': self._get_column_stats(df1[col], include_nulls, include_stats),
                'df2_stats': None,
                'differences': ['Column exists only in first DataFrame']
            }
            comparison_results.append(col_result)
            differences_found = True
        
        # Handle columns only in df2
        for col in only_in_df2:
            col_result = {
                'column': col,
                'status': 'only_in_df2',
                'is_equal': False,
                'df1_stats': None,
                'df2_stats': self._get_column_stats(df2[col], include_nulls, include_stats),
                'differences': ['Column exists only in second DataFrame']
            }
            comparison_results.append(col_result)
            differences_found = True
        
        # Create highlights DataFrame
        highlights = self._create_highlights_dataframe(comparison_results)
        
        # Generate summary
        is_equal = not differences_found
        details = self._generate_summary(comparison_results, len(common_columns), len(only_in_df1), len(only_in_df2))
        
        return {
            'is_equal': is_equal,
            'details': details,
            'highlights': highlights,
            'metadata': {
                'total_columns': len(all_columns),
                'common_columns': len(common_columns),
                'only_in_df1': len(only_in_df1),
                'only_in_df2': len(only_in_df2),
                'column_results': comparison_results
            }
        }
    
    def _compare_column(self, col1: pd.Series, col2: pd.Series, col_name: str, 
                       include_nulls: bool, include_stats: bool, tolerance: float) -> Dict[str, Any]:
        """Compare two columns and return detailed results."""
        differences = []
        
        # Get statistics for both columns
        stats1 = self._get_column_stats(col1, include_nulls, include_stats)
        stats2 = self._get_column_stats(col2, include_nulls, include_stats)
        
        # Compare data types
        if stats1['dtype'] != stats2['dtype']:
            differences.append(f"Data type differs: {stats1['dtype']} vs {stats2['dtype']}")
        
        # Compare row counts
        if stats1['count'] != stats2['count']:
            differences.append(f"Row count differs: {stats1['count']} vs {stats2['count']}")
        
        # Compare null counts if requested
        if include_nulls and stats1['null_count'] != stats2['null_count']:
            differences.append(f"Null count differs: {stats1['null_count']} vs {stats2['null_count']}")
        
        # Compare statistical measures if requested and applicable
        if include_stats and stats1['dtype'] in ['int64', 'float64'] and stats2['dtype'] in ['int64', 'float64']:
            for stat_name in ['mean', 'std', 'min', 'max']:
                val1 = stats1.get(stat_name)
                val2 = stats2.get(stat_name)
                
                if val1 is not None and val2 is not None:
                    if not np.isclose(val1, val2, atol=tolerance, rtol=tolerance, equal_nan=True):
                        differences.append(f"{stat_name.capitalize()} differs: {val1:.6f} vs {val2:.6f}")
        
        # Compare unique value counts for categorical data
        if stats1['dtype'] == 'object' or stats2['dtype'] == 'object':
            if stats1['unique_count'] != stats2['unique_count']:
                differences.append(f"Unique value count differs: {stats1['unique_count']} vs {stats2['unique_count']}")
        
        return {
            'column': col_name,
            'status': 'common',
            'is_equal': len(differences) == 0,
            'df1_stats': stats1,
            'df2_stats': stats2,
            'differences': differences
        }
    
    def _get_column_stats(self, col: pd.Series, include_nulls: bool, include_stats: bool) -> Dict[str, Any]:
        """Get statistical information for a column."""
        stats = {
            'dtype': str(col.dtype),
            'count': len(col),
            'unique_count': col.nunique()
        }
        
        if include_nulls:
            stats['null_count'] = col.isnull().sum()
            stats['null_percentage'] = (stats['null_count'] / len(col)) * 100 if len(col) > 0 else 0
        
        if include_stats:
            if col.dtype in ['int64', 'float64']:
                # Numerical statistics
                try:
                    stats.update({
                        'mean': float(col.mean()) if not col.empty else None,
                        'std': float(col.std()) if not col.empty else None,
                        'min': float(col.min()) if not col.empty else None,
                        'max': float(col.max()) if not col.empty else None,
                        'median': float(col.median()) if not col.empty else None
                    })
                except Exception:
                    # Handle cases where statistics can't be computed
                    pass
            elif col.dtype == 'object':
                # String/categorical statistics
                try:
                    stats.update({
                        'most_common': col.mode().iloc[0] if not col.mode().empty else None,
                        'avg_length': col.astype(str).str.len().mean() if not col.empty else None
                    })
                except Exception:
                    pass
        
        return stats
    
    def _create_highlights_dataframe(self, comparison_results: list) -> DataFrame:
        """Create a DataFrame highlighting the comparison results."""
        highlights_data = []
        
        for result in comparison_results:
            row = {
                'Column': result['column'],
                'Status': result['status'],
                'Equal': result['is_equal'],
                'Differences': '; '.join(result['differences']) if result['differences'] else 'None'
            }
            
            # Add statistics from both DataFrames
            if result['df1_stats']:
                row['DF1_Type'] = result['df1_stats']['dtype']
                row['DF1_Count'] = result['df1_stats']['count']
                row['DF1_Unique'] = result['df1_stats']['unique_count']
                if 'null_count' in result['df1_stats']:
                    row['DF1_Nulls'] = result['df1_stats']['null_count']
                if 'mean' in result['df1_stats']:
                    row['DF1_Mean'] = result['df1_stats']['mean']
            
            if result['df2_stats']:
                row['DF2_Type'] = result['df2_stats']['dtype']
                row['DF2_Count'] = result['df2_stats']['count']
                row['DF2_Unique'] = result['df2_stats']['unique_count']
                if 'null_count' in result['df2_stats']:
                    row['DF2_Nulls'] = result['df2_stats']['null_count']
                if 'mean' in result['df2_stats']:
                    row['DF2_Mean'] = result['df2_stats']['mean']
            
            # Add diff type for styling
            if result['status'] == 'only_in_df1':
                row['_diff_type'] = 'only_a'
            elif result['status'] == 'only_in_df2':
                row['_diff_type'] = 'only_b'
            elif not result['is_equal']:
                row['_diff_type'] = 'different'
            else:
                row['_diff_type'] = 'same'
            
            highlights_data.append(row)
        
        return pd.DataFrame(highlights_data)
    
    def _generate_summary(self, comparison_results: list, common_count: int, 
                         only_df1_count: int, only_df2_count: int) -> str:
        """Generate a human-readable summary of the comparison."""
        different_common = sum(1 for r in comparison_results 
                              if r['status'] == 'common' and not r['is_equal'])
        
        details = f"Column comparison results:\n"
        details += f"- Total columns compared: {len(comparison_results)}\n"
        details += f"- Common columns: {common_count}\n"
        details += f"- Columns only in first table: {only_df1_count}\n"
        details += f"- Columns only in second table: {only_df2_count}\n"
        details += f"- Common columns with differences: {different_common}\n"
        
        if different_common > 0:
            details += f"\nDifferences in common columns:\n"
            for result in comparison_results:
                if result['status'] == 'common' and not result['is_equal']:
                    details += f"- {result['column']}: {'; '.join(result['differences'])}\n"
        
        return details