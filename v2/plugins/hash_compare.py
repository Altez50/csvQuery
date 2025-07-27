from plugins.base_compare import BaseComparePlugin
import pandas as pd
import hashlib
import json
from pandas import DataFrame
from typing import Dict, Any

class HashComparePlugin(BaseComparePlugin):
    """Plugin for hash-based comparison of DataFrames."""
    
    def get_name(self) -> str:
        return "Hash-based Comparison"
    
    def get_description(self) -> str:
        return "Fast comparison using MD5 hashes of DataFrame content and structure"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            'hash_algorithm': {
                'type': 'list',
                'default': 'md5',
                'description': 'Hash algorithm to use',
                'options': ['md5', 'sha1', 'sha256']
            },
            'include_index': {
                'type': 'bool',
                'default': False,
                'description': 'Include DataFrame index in hash calculation'
            },
            'chunk_size': {
                'type': 'int',
                'default': 1000,
                'description': 'Number of rows to process in each chunk for large DataFrames'
            },
            'detailed_analysis': {
                'type': 'bool',
                'default': True,
                'description': 'Perform detailed analysis when hashes differ'
            }
        }
    
    def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
        """Compare DataFrames using hash-based approach."""
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
        hash_algorithm = kwargs.get('hash_algorithm', 'md5')
        include_index = kwargs.get('include_index', False)
        chunk_size = kwargs.get('chunk_size', 1000)
        detailed_analysis = kwargs.get('detailed_analysis', True)
        
        # Calculate overall hashes
        hash1 = self._calculate_dataframe_hash(df1, hash_algorithm, include_index)
        hash2 = self._calculate_dataframe_hash(df2, hash_algorithm, include_index)
        
        is_equal = hash1 == hash2
        
        # If hashes are equal, DataFrames are identical
        if is_equal:
            return {
                'is_equal': True,
                'details': f"DataFrames are identical (hash: {hash1})",
                'highlights': pd.DataFrame(),
                'metadata': {
                    'hash1': hash1,
                    'hash2': hash2,
                    'algorithm': hash_algorithm,
                    'include_index': include_index
                }
            }
        
        # If hashes differ, perform detailed analysis if requested
        analysis_results = {}
        highlights = pd.DataFrame()
        
        if detailed_analysis:
            analysis_results = self._perform_detailed_analysis(
                df1, df2, hash_algorithm, include_index, chunk_size
            )
            highlights = self._create_highlights_from_analysis(analysis_results)
        
        # Generate summary
        details = self._generate_summary(hash1, hash2, hash_algorithm, analysis_results)
        
        return {
            'is_equal': False,
            'details': details,
            'highlights': highlights,
            'metadata': {
                'hash1': hash1,
                'hash2': hash2,
                'algorithm': hash_algorithm,
                'include_index': include_index,
                'analysis': analysis_results
            }
        }
    
    def _calculate_dataframe_hash(self, df: DataFrame, algorithm: str, include_index: bool) -> str:
        """Calculate hash for entire DataFrame."""
        hasher = hashlib.new(algorithm)
        
        # Add shape information
        hasher.update(str(df.shape).encode('utf-8'))
        
        # Add column names and types
        columns_info = [(col, str(df[col].dtype)) for col in df.columns]
        hasher.update(json.dumps(columns_info, sort_keys=True).encode('utf-8'))
        
        # Add index if requested
        if include_index:
            hasher.update(str(df.index.tolist()).encode('utf-8'))
        
        # Add data content
        for col in df.columns:
            col_hash = self._calculate_column_hash(df[col], algorithm)
            hasher.update(col_hash.encode('utf-8'))
        
        return hasher.hexdigest()
    
    def _calculate_column_hash(self, series: pd.Series, algorithm: str) -> str:
        """Calculate hash for a single column."""
        hasher = hashlib.new(algorithm)
        
        # Convert series to string representation, handling NaN values
        series_str = series.fillna('__NaN__').astype(str)
        
        # Add each value to hash
        for value in series_str:
            hasher.update(value.encode('utf-8'))
        
        return hasher.hexdigest()
    
    def _calculate_chunk_hash(self, df: DataFrame, start_idx: int, end_idx: int, 
                             algorithm: str, include_index: bool) -> str:
        """Calculate hash for a chunk of DataFrame."""
        chunk = df.iloc[start_idx:end_idx]
        return self._calculate_dataframe_hash(chunk, algorithm, include_index)
    
    def _perform_detailed_analysis(self, df1: DataFrame, df2: DataFrame, 
                                  algorithm: str, include_index: bool, chunk_size: int) -> Dict[str, Any]:
        """Perform detailed analysis to identify where differences occur."""
        analysis = {
            'structure_differences': [],
            'column_differences': {},
            'chunk_differences': []
        }
        
        # Check structure differences
        if df1.shape != df2.shape:
            analysis['structure_differences'].append(f"Shape differs: {df1.shape} vs {df2.shape}")
        
        if list(df1.columns) != list(df2.columns):
            analysis['structure_differences'].append(f"Columns differ: {list(df1.columns)} vs {list(df2.columns)}")
        
        if list(df1.dtypes) != list(df2.dtypes):
            analysis['structure_differences'].append("Data types differ")
        
        # Check column-level differences for common columns
        common_columns = set(df1.columns) & set(df2.columns)
        for col in common_columns:
            hash1 = self._calculate_column_hash(df1[col], algorithm)
            hash2 = self._calculate_column_hash(df2[col], algorithm)
            
            if hash1 != hash2:
                analysis['column_differences'][col] = {
                    'hash1': hash1,
                    'hash2': hash2,
                    'differs': True
                }
            else:
                analysis['column_differences'][col] = {
                    'hash1': hash1,
                    'hash2': hash2,
                    'differs': False
                }
        
        # Check chunk-level differences (only if DataFrames have same shape)
        if df1.shape == df2.shape and len(df1) > chunk_size:
            for start_idx in range(0, len(df1), chunk_size):
                end_idx = min(start_idx + chunk_size, len(df1))
                
                chunk_hash1 = self._calculate_chunk_hash(df1, start_idx, end_idx, algorithm, include_index)
                chunk_hash2 = self._calculate_chunk_hash(df2, start_idx, end_idx, algorithm, include_index)
                
                if chunk_hash1 != chunk_hash2:
                    analysis['chunk_differences'].append({
                        'start_row': start_idx,
                        'end_row': end_idx - 1,
                        'hash1': chunk_hash1,
                        'hash2': chunk_hash2
                    })
        
        return analysis
    
    def _create_highlights_from_analysis(self, analysis: Dict[str, Any]) -> DataFrame:
        """Create highlights DataFrame from detailed analysis."""
        highlights_data = []
        
        # Add structure differences
        for diff in analysis['structure_differences']:
            highlights_data.append({
                'Type': 'Structure',
                'Item': 'DataFrame',
                'Difference': diff,
                '_diff_type': 'different'
            })
        
        # Add column differences
        for col, col_info in analysis['column_differences'].items():
            if col_info['differs']:
                highlights_data.append({
                    'Type': 'Column',
                    'Item': col,
                    'Difference': f"Hash differs: {col_info['hash1'][:8]}... vs {col_info['hash2'][:8]}...",
                    '_diff_type': 'different'
                })
            else:
                highlights_data.append({
                    'Type': 'Column',
                    'Item': col,
                    'Difference': 'Identical',
                    '_diff_type': 'same'
                })
        
        # Add chunk differences
        for chunk_diff in analysis['chunk_differences']:
            highlights_data.append({
                'Type': 'Chunk',
                'Item': f"Rows {chunk_diff['start_row']}-{chunk_diff['end_row']}",
                'Difference': f"Hash differs: {chunk_diff['hash1'][:8]}... vs {chunk_diff['hash2'][:8]}...",
                '_diff_type': 'different'
            })
        
        return pd.DataFrame(highlights_data)
    
    def _generate_summary(self, hash1: str, hash2: str, algorithm: str, 
                         analysis: Dict[str, Any]) -> str:
        """Generate human-readable summary."""
        details = f"Hash comparison results ({algorithm.upper()}):\n"
        details += f"- First DataFrame hash: {hash1}\n"
        details += f"- Second DataFrame hash: {hash2}\n"
        details += f"- DataFrames are different\n\n"
        
        if analysis:
            if analysis['structure_differences']:
                details += f"Structure differences ({len(analysis['structure_differences'])}): \n"
                for diff in analysis['structure_differences']:
                    details += f"  - {diff}\n"
                details += "\n"
            
            column_diffs = sum(1 for col_info in analysis['column_differences'].values() if col_info['differs'])
            if column_diffs > 0:
                details += f"Columns with differences: {column_diffs}/{len(analysis['column_differences'])}\n"
                for col, col_info in analysis['column_differences'].items():
                    if col_info['differs']:
                        details += f"  - {col}: {col_info['hash1'][:8]}... vs {col_info['hash2'][:8]}...\n"
                details += "\n"
            
            if analysis['chunk_differences']:
                details += f"Chunks with differences: {len(analysis['chunk_differences'])}\n"
                for chunk_diff in analysis['chunk_differences']:
                    details += f"  - Rows {chunk_diff['start_row']}-{chunk_diff['end_row']}: {chunk_diff['hash1'][:8]}... vs {chunk_diff['hash2'][:8]}...\n"
        
        return details