from abc import ABC, abstractmethod
from pandas import DataFrame
from typing import Dict, Any, Optional

class BaseComparePlugin(ABC):
    """Base class for all comparison plugins."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return plugin display name (e.g., 'Row-by-Row Compare')."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return plugin description."""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Return plugin version."""
        pass
    
    @abstractmethod
    def compare(self, df1: DataFrame, df2: DataFrame, **kwargs) -> Dict[str, Any]:
        """Compare two DataFrames and return results.
        
        Args:
            df1: First DataFrame to compare
            df2: Second DataFrame to compare
            **kwargs: Additional parameters specific to the plugin
            
        Returns:
            Dict with keys:
            - 'is_equal': bool indicating if DataFrames are equal
            - 'details': str with human-readable summary
            - 'highlights': DataFrame or dict with difference highlights
            - 'metadata': dict with additional comparison metadata
        """
        pass
    
    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Return plugin-specific parameters for UI configuration.
        
        Returns:
            Dict where keys are parameter names and values are dicts with:
            - 'type': parameter type ('str', 'int', 'float', 'bool', 'list')
            - 'default': default value
            - 'description': parameter description
            - 'options': list of options (for 'list' type)
        """
        return {}
    
    def validate_dataframes(self, df1: DataFrame, df2: DataFrame) -> Optional[str]:
        """Validate input DataFrames before comparison.
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            
        Returns:
            None if valid, error message string if invalid
        """
        if df1 is None or df2 is None:
            return "One or both DataFrames are None"
        
        if df1.empty and df2.empty:
            return "Both DataFrames are empty"
            
        return None