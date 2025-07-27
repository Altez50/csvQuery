import importlib.util
import os
import sys
import traceback
import zipfile
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path

class PluginLoader:
    """Utility class for loading and managing comparison plugins."""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins = []
        self.plugin_errors = {}
        self.base_plugin_class = None
        
        # Ensure plugin directory exists
        self.plugin_dir.mkdir(exist_ok=True)
        
        # Create __init__.py if it doesn't exist
        init_file = self.plugin_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Plugin directory\n")
    
    def load_plugins(self) -> List[Any]:
        """Load all valid plugins from the plugin directory."""
        self.plugins = []
        self.plugin_errors = {}
        
        # First, load the base plugin class
        self._load_base_plugin_class()
        
        if not self.base_plugin_class:
            print("Warning: Could not load base plugin class")
            return []
        
        # Load plugins from .py files
        self._load_python_plugins()
        
        # Load plugins from .zip files
        self._load_zip_plugins()
        
        return self.plugins
    
    def _load_base_plugin_class(self):
        """Load the BaseComparePlugin class."""
        base_plugin_path = self.plugin_dir / "base_compare.py"
        
        if not base_plugin_path.exists():
            print(f"Warning: Base plugin file not found at {base_plugin_path}")
            return
        
        try:
            spec = importlib.util.spec_from_file_location(
                "plugins.base_compare", 
                str(base_plugin_path)
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules["plugins.base_compare"] = module
            spec.loader.exec_module(module)
            
            self.base_plugin_class = getattr(module, "BaseComparePlugin", None)
            
        except Exception as e:
            print(f"Error loading base plugin class: {e}")
            traceback.print_exc()
    
    def _load_python_plugins(self):
        """Load plugins from .py files in the plugin directory."""
        for file_path in self.plugin_dir.glob("*.py"):
            if file_path.name in ["__init__.py", "base_compare.py"]:
                continue
            
            self._load_plugin_from_file(file_path)
    
    def _load_zip_plugins(self):
        """Load plugins from .zip files in the plugin directory."""
        for zip_path in self.plugin_dir.glob("*.zip"):
            self._load_plugin_from_zip(zip_path)
    
    def _load_plugin_from_file(self, file_path: Path):
        """Load a plugin from a Python file."""
        try:
            module_name = f"plugins.{file_path.stem}"
            
            spec = importlib.util.spec_from_file_location(
                module_name, 
                str(file_path)
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find plugin classes in the module
            plugin_classes = self._find_plugin_classes(module)
            
            for plugin_class in plugin_classes:
                try:
                    plugin_instance = plugin_class()
                    self.plugins.append(plugin_instance)
                    print(f"Loaded plugin: {plugin_instance.get_name()}")
                except Exception as e:
                    error_msg = f"Error instantiating plugin {plugin_class.__name__}: {e}"
                    self.plugin_errors[str(file_path)] = error_msg
                    print(error_msg)
        
        except Exception as e:
            error_msg = f"Error loading plugin from {file_path}: {e}"
            self.plugin_errors[str(file_path)] = error_msg
            print(error_msg)
            traceback.print_exc()
    
    def _load_plugin_from_zip(self, zip_path: Path):
        """Load a plugin from a ZIP file."""
        temp_dir = None
        try:
            # Extract ZIP to temporary directory
            temp_dir = Path(tempfile.mkdtemp())
            
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                zip_file.extractall(temp_dir)
            
            # Look for Python files in the extracted content
            for py_file in temp_dir.rglob("*.py"):
                if py_file.name in ["__init__.py", "base_compare.py"]:
                    continue
                
                self._load_plugin_from_file(py_file)
        
        except Exception as e:
            error_msg = f"Error loading plugin from ZIP {zip_path}: {e}"
            self.plugin_errors[str(zip_path)] = error_msg
            print(error_msg)
        
        finally:
            # Clean up temporary directory
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _find_plugin_classes(self, module) -> List[type]:
        """Find all plugin classes in a module."""
        plugin_classes = []
        
        if not self.base_plugin_class:
            return plugin_classes
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # Check if it's a class that inherits from BaseComparePlugin
            if (isinstance(attr, type) and 
                issubclass(attr, self.base_plugin_class) and 
                attr != self.base_plugin_class):
                plugin_classes.append(attr)
        
        return plugin_classes
    
    def get_plugin_by_name(self, name: str) -> Optional[Any]:
        """Get a plugin by its name."""
        for plugin in self.plugins:
            if plugin.get_name() == name:
                return plugin
        return None
    
    def get_available_plugins(self) -> Dict[str, type]:
        """Get a dictionary of available plugin names to plugin classes."""
        # Load plugins if not already loaded
        if not self.plugins:
            self.load_plugins()
        
        plugin_dict = {}
        for plugin in self.plugins:
            try:
                plugin_dict[plugin.get_name()] = plugin.__class__
            except Exception as e:
                print(f"Error getting plugin name for {plugin.__class__.__name__}: {e}")
        
        return plugin_dict
    
    def get_plugin_info(self) -> List[Dict[str, str]]:
        """Get information about all loaded plugins."""
        plugin_info = []
        
        for plugin in self.plugins:
            try:
                info = {
                    'name': plugin.get_name(),
                    'description': plugin.get_description(),
                    'version': plugin.get_version(),
                    'status': 'loaded'
                }
                plugin_info.append(info)
            except Exception as e:
                info = {
                    'name': f"Unknown ({plugin.__class__.__name__})",
                    'description': f"Error getting info: {e}",
                    'version': 'unknown',
                    'status': 'error'
                }
                plugin_info.append(info)
        
        return plugin_info
    
    def get_plugin_errors(self) -> Dict[str, str]:
        """Get errors that occurred during plugin loading."""
        return self.plugin_errors.copy()
    
    def reload_plugins(self) -> List[Any]:
        """Reload all plugins from the plugin directory."""
        # Clear existing plugins and errors
        self.plugins = []
        self.plugin_errors = {}
        
        # Remove modules from sys.modules to force reload
        modules_to_remove = []
        for module_name in sys.modules:
            if module_name.startswith("plugins."):
                modules_to_remove.append(module_name)
        
        for module_name in modules_to_remove:
            del sys.modules[module_name]
        
        # Reload plugins
        return self.load_plugins()
    
    def validate_plugin(self, plugin) -> List[str]:
        """Validate a plugin instance and return any validation errors."""
        errors = []
        
        if not self.base_plugin_class:
            errors.append("Base plugin class not available")
            return errors
        
        if not isinstance(plugin, self.base_plugin_class):
            errors.append(f"Plugin does not inherit from BaseComparePlugin")
            return errors
        
        # Check required methods
        required_methods = ['get_name', 'get_description', 'get_version', 'compare']
        
        for method_name in required_methods:
            if not hasattr(plugin, method_name):
                errors.append(f"Missing required method: {method_name}")
            elif not callable(getattr(plugin, method_name)):
                errors.append(f"Method {method_name} is not callable")
        
        # Test method calls
        try:
            name = plugin.get_name()
            if not isinstance(name, str) or not name.strip():
                errors.append("get_name() must return a non-empty string")
        except Exception as e:
            errors.append(f"Error calling get_name(): {e}")
        
        try:
            description = plugin.get_description()
            if not isinstance(description, str):
                errors.append("get_description() must return a string")
        except Exception as e:
            errors.append(f"Error calling get_description(): {e}")
        
        try:
            version = plugin.get_version()
            if not isinstance(version, str) or not version.strip():
                errors.append("get_version() must return a non-empty string")
        except Exception as e:
            errors.append(f"Error calling get_version(): {e}")
        
        return errors
    
    def install_plugin_from_url(self, url: str, filename: Optional[str] = None) -> bool:
        """Download and install a plugin from a URL."""
        try:
            import requests
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            if not filename:
                # Try to extract filename from URL
                filename = url.split('/')[-1]
                if not filename.endswith(('.py', '.zip')):
                    filename += '.py'
            
            # Save to plugin directory
            plugin_path = self.plugin_dir / filename
            
            with open(plugin_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded plugin to {plugin_path}")
            
            # Try to load the new plugin
            if filename.endswith('.py'):
                self._load_plugin_from_file(plugin_path)
            elif filename.endswith('.zip'):
                self._load_plugin_from_zip(plugin_path)
            
            return True
        
        except Exception as e:
            error_msg = f"Error downloading plugin from {url}: {e}"
            print(error_msg)
            return False
    
    def uninstall_plugin(self, plugin_name: str) -> bool:
        """Uninstall a plugin by removing its file and instance."""
        try:
            # Find and remove plugin instance
            plugin_to_remove = None
            for plugin in self.plugins:
                if plugin.get_name() == plugin_name:
                    plugin_to_remove = plugin
                    break
            
            if plugin_to_remove:
                self.plugins.remove(plugin_to_remove)
            
            # Try to find and remove plugin file
            for file_path in self.plugin_dir.glob("*"):
                if file_path.suffix in ['.py', '.zip']:
                    # This is a simple approach - in a real implementation,
                    # you might want to track which file each plugin came from
                    pass
            
            return True
        
        except Exception as e:
            print(f"Error uninstalling plugin {plugin_name}: {e}")
            return False


# Global plugin loader instance
_plugin_loader = None

def get_plugin_loader(plugin_dir: str = "plugins") -> PluginLoader:
    """Get the global plugin loader instance."""
    global _plugin_loader
    if _plugin_loader is None:
        _plugin_loader = PluginLoader(plugin_dir)
    return _plugin_loader

def load_plugins(plugin_dir: str = "plugins") -> List[Any]:
    """Convenience function to load plugins."""
    loader = get_plugin_loader(plugin_dir)
    return loader.load_plugins()