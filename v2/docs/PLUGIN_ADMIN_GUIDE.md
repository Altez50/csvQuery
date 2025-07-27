# Plugin Administrator Reference Guide

## Overview

This guide provides comprehensive documentation for administrators responsible for managing, deploying, and maintaining the plugin system in the CSV Query Tool. It covers installation, configuration, security, monitoring, and troubleshooting aspects of plugin administration.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation and Setup](#installation-and-setup)
3. [Plugin Management](#plugin-management)
4. [Security Considerations](#security-considerations)
5. [Configuration Management](#configuration-management)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Performance Optimization](#performance-optimization)
8. [Backup and Recovery](#backup-and-recovery)
9. [Troubleshooting](#troubleshooting)
10. [User Management](#user-management)
11. [Plugin Repository Management](#plugin-repository-management)
12. [Deployment Strategies](#deployment-strategies)
13. [Maintenance Procedures](#maintenance-procedures)
14. [API Administration](#api-administration)

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python**: 3.7 or higher
- **Memory**: 4 GB RAM (8 GB recommended)
- **Storage**: 1 GB free space for plugins and cache
- **Network**: Internet access for plugin downloads (optional)

### Recommended Requirements

- **Python**: 3.9 or higher
- **Memory**: 16 GB RAM for large dataset processing
- **Storage**: 10 GB free space
- **CPU**: Multi-core processor for parallel processing

### Dependencies

```bash
# Core dependencies
pip install pandas>=1.3.0
pip install PyQt5>=5.15.0
pip install numpy>=1.19.0

# Optional dependencies for enhanced functionality
pip install requests>=2.25.0  # For plugin downloads
pip install cryptography>=3.4.0  # For plugin verification
pip install psutil>=5.8.0  # For performance monitoring
```

## Installation and Setup

### Initial Setup

1. **Install the CSV Query Tool**:
   ```bash
   git clone <repository-url>
   cd venvcsvQuery
   pip install -r requirements.txt
   ```

2. **Create plugin directory structure**:
   ```bash
   mkdir -p plugins
   mkdir -p plugins/cache
   mkdir -p plugins/repositories
   mkdir -p plugins/disabled
   ```

3. **Set up configuration**:
   ```bash
   cp config/plugin_config.example.json config/plugin_config.json
   ```

4. **Initialize plugin system**:
   ```python
   python -c "from utils.plugin_loader import PluginLoader; PluginLoader().load_plugins()"
   ```

### Directory Structure

```
venvcsvQuery/
├── plugins/
│   ├── __init__.py
│   ├── base_compare.py          # Base plugin class
│   ├── row_compare.py           # Built-in plugins
│   ├── column_compare.py
│   ├── hash_compare.py
│   ├── schema_compare.py
│   ├── cache/                   # Plugin cache
│   ├── repositories/            # Repository metadata
│   ├── disabled/                # Disabled plugins
│   └── custom/                  # Custom user plugins
├── utils/
│   ├── plugin_loader.py         # Plugin loading system
│   └── plugin_downloader.py     # Plugin download utilities
├── config/
│   ├── plugin_config.json       # Plugin configuration
│   └── security_policy.json     # Security policies
└── logs/
    ├── plugin_system.log        # Plugin system logs
    └── security.log             # Security-related logs
```

## Plugin Management

### Plugin Installation

#### Manual Installation

1. **Single Python file**:
   ```bash
   cp my_plugin.py plugins/
   ```

2. **ZIP package**:
   ```bash
   cp my_plugin.zip plugins/
   # Plugin system will auto-extract on next load
   ```

3. **Directory package**:
   ```bash
   cp -r my_plugin_package/ plugins/
   ```

#### Programmatic Installation

```python
from utils.plugin_loader import PluginLoader

loader = PluginLoader()

# Install from URL
loader.install_plugin_from_url("https://example.com/plugin.zip")

# Install from local file
loader.install_plugin_from_file("/path/to/plugin.zip")

# Verify installation
if "My Plugin" in loader.get_available_plugins():
    print("Plugin installed successfully")
```

### Plugin Removal

#### Safe Removal

```python
from utils.plugin_loader import PluginLoader

loader = PluginLoader()

# Disable plugin first
loader.disable_plugin("My Plugin")

# Remove plugin files
loader.uninstall_plugin("My Plugin")

# Verify removal
loader.reload_plugins()
```

#### Manual Removal

```bash
# Move to disabled directory
mv plugins/my_plugin.py plugins/disabled/

# Or delete permanently
rm plugins/my_plugin.py
```

### Plugin Updates

#### Automated Updates

```python
from utils.plugin_downloader import PluginDownloader

downloader = PluginDownloader()

# Check for updates
updates = downloader.check_for_updates()

# Update specific plugin
downloader.update_plugin("My Plugin", "2.0.0")

# Update all plugins
downloader.update_all_plugins()
```

#### Manual Updates

1. **Backup current version**:
   ```bash
   cp plugins/my_plugin.py plugins/backup/my_plugin_v1.0.py
   ```

2. **Install new version**:
   ```bash
   cp new_my_plugin.py plugins/my_plugin.py
   ```

3. **Test and verify**:
   ```python
   python test_plugins.py
   ```

### Plugin Validation

#### Automated Validation

```python
from utils.plugin_loader import PluginLoader

loader = PluginLoader()

# Validate all plugins
validation_results = loader.validate_all_plugins()

for plugin_name, result in validation_results.items():
    if result['valid']:
        print(f"✓ {plugin_name}: Valid")
    else:
        print(f"✗ {plugin_name}: {result['errors']}")
```

#### Manual Validation

```bash
# Run validation script
python scripts/validate_plugins.py

# Check specific plugin
python scripts/validate_plugins.py --plugin "My Plugin"
```

## Security Considerations

### Plugin Security Policy

#### Configuration (`config/security_policy.json`)

```json
{
  "plugin_security": {
    "allow_external_plugins": true,
    "require_signature_verification": false,
    "allowed_domains": [
      "github.com",
      "gitlab.com",
      "trusted-plugin-repo.com"
    ],
    "blocked_domains": [
      "malicious-site.com"
    ],
    "max_plugin_size_mb": 50,
    "scan_for_malicious_code": true,
    "quarantine_suspicious_plugins": true
  },
  "execution_limits": {
    "max_memory_mb": 1024,
    "max_execution_time_seconds": 300,
    "allow_network_access": false,
    "allow_file_system_access": "restricted"
  }
}
```

#### Security Scanning

```python
from utils.plugin_security import PluginSecurityScanner

scanner = PluginSecurityScanner()

# Scan plugin for security issues
result = scanner.scan_plugin("plugins/my_plugin.py")

if result['safe']:
    print("Plugin passed security scan")
else:
    print(f"Security issues found: {result['issues']}")
    # Quarantine plugin
    scanner.quarantine_plugin("my_plugin.py")
```

#### Code Signing and Verification

```python
from utils.plugin_security import PluginSigner, PluginVerifier

# Sign plugin (for plugin developers)
signer = PluginSigner(private_key_path="keys/private.pem")
signer.sign_plugin("my_plugin.py")

# Verify plugin signature (for administrators)
verifier = PluginVerifier(public_key_path="keys/public.pem")
if verifier.verify_plugin("my_plugin.py"):
    print("Plugin signature valid")
else:
    print("Plugin signature invalid - potential security risk")
```

### Access Control

#### User Permissions

```json
{
  "user_permissions": {
    "admin": {
      "can_install_plugins": true,
      "can_remove_plugins": true,
      "can_modify_security_policy": true,
      "can_access_all_plugins": true
    },
    "power_user": {
      "can_install_plugins": true,
      "can_remove_plugins": false,
      "can_modify_security_policy": false,
      "can_access_all_plugins": true
    },
    "regular_user": {
      "can_install_plugins": false,
      "can_remove_plugins": false,
      "can_modify_security_policy": false,
      "can_access_all_plugins": false,
      "allowed_plugins": ["row_compare", "column_compare"]
    }
  }
}
```

## Configuration Management

### Plugin Configuration

#### Main Configuration (`config/plugin_config.json`)

```json
{
  "plugin_system": {
    "enabled": true,
    "auto_load_on_startup": true,
    "plugin_directory": "plugins",
    "cache_directory": "plugins/cache",
    "max_concurrent_comparisons": 4,
    "default_timeout_seconds": 300
  },
  "repositories": [
    {
      "name": "official",
      "url": "https://plugins.csvquery.com/repository",
      "enabled": true,
      "auto_update": true
    },
    {
      "name": "community",
      "url": "https://github.com/csvquery/community-plugins",
      "enabled": true,
      "auto_update": false
    }
  ],
  "plugin_settings": {
    "row_compare": {
      "enabled": true,
      "max_rows": 1000000,
      "default_key_columns": ["id"]
    },
    "column_compare": {
      "enabled": true,
      "default_tolerance": 0.001
    },
    "hash_compare": {
      "enabled": true,
      "default_algorithm": "sha256",
      "chunk_size": 8192
    },
    "schema_compare": {
      "enabled": true,
      "strict_mode": false
    }
  }
}
```

#### Environment-Specific Configuration

```bash
# Development environment
export PLUGIN_ENV=development
export PLUGIN_DEBUG=true
export PLUGIN_CACHE_ENABLED=false

# Production environment
export PLUGIN_ENV=production
export PLUGIN_DEBUG=false
export PLUGIN_CACHE_ENABLED=true
export PLUGIN_SECURITY_STRICT=true
```

### Configuration Management Script

```python
#!/usr/bin/env python3
# scripts/manage_config.py

import json
import os
import argparse
from typing import Dict, Any

class PluginConfigManager:
    def __init__(self, config_path: str = "config/plugin_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def save_config(self) -> None:
        """Save configuration to file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def enable_plugin(self, plugin_name: str) -> None:
        """Enable a specific plugin."""
        if plugin_name not in self.config['plugin_settings']:
            self.config['plugin_settings'][plugin_name] = {}
        self.config['plugin_settings'][plugin_name]['enabled'] = True
        self.save_config()
    
    def disable_plugin(self, plugin_name: str) -> None:
        """Disable a specific plugin."""
        if plugin_name in self.config['plugin_settings']:
            self.config['plugin_settings'][plugin_name]['enabled'] = False
            self.save_config()
    
    def set_plugin_setting(self, plugin_name: str, setting: str, value: Any) -> None:
        """Set a plugin-specific setting."""
        if plugin_name not in self.config['plugin_settings']:
            self.config['plugin_settings'][plugin_name] = {}
        self.config['plugin_settings'][plugin_name][setting] = value
        self.save_config()
    
    def add_repository(self, name: str, url: str, enabled: bool = True) -> None:
        """Add a plugin repository."""
        repo = {
            'name': name,
            'url': url,
            'enabled': enabled,
            'auto_update': False
        }
        self.config['repositories'].append(repo)
        self.save_config()
    
    def remove_repository(self, name: str) -> None:
        """Remove a plugin repository."""
        self.config['repositories'] = [
            repo for repo in self.config['repositories']
            if repo['name'] != name
        ]
        self.save_config()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage plugin configuration")
    parser.add_argument("action", choices=["enable", "disable", "set", "add-repo", "remove-repo"])
    parser.add_argument("--plugin", help="Plugin name")
    parser.add_argument("--setting", help="Setting name")
    parser.add_argument("--value", help="Setting value")
    parser.add_argument("--repo-name", help="Repository name")
    parser.add_argument("--repo-url", help="Repository URL")
    
    args = parser.parse_args()
    manager = PluginConfigManager()
    
    if args.action == "enable":
        manager.enable_plugin(args.plugin)
    elif args.action == "disable":
        manager.disable_plugin(args.plugin)
    elif args.action == "set":
        manager.set_plugin_setting(args.plugin, args.setting, args.value)
    elif args.action == "add-repo":
        manager.add_repository(args.repo_name, args.repo_url)
    elif args.action == "remove-repo":
        manager.remove_repository(args.repo_name)
```

## Monitoring and Logging

### Logging Configuration

#### Setup (`config/logging.json`)

```json
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "standard": {
      "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    },
    "detailed": {
      "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
    }
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "level": "INFO",
      "formatter": "standard",
      "stream": "ext://sys.stdout"
    },
    "file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "DEBUG",
      "formatter": "detailed",
      "filename": "logs/plugin_system.log",
      "maxBytes": 10485760,
      "backupCount": 5
    },
    "security": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "WARNING",
      "formatter": "detailed",
      "filename": "logs/security.log",
      "maxBytes": 10485760,
      "backupCount": 10
    }
  },
  "loggers": {
    "plugin_system": {
      "level": "DEBUG",
      "handlers": ["console", "file"],
      "propagate": false
    },
    "plugin_security": {
      "level": "WARNING",
      "handlers": ["console", "security"],
      "propagate": false
    }
  }
}
```

### Performance Monitoring

```python
# utils/plugin_monitor.py
import time
import psutil
import logging
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PluginMetrics:
    plugin_name: str
    execution_time: float
    memory_usage: int
    cpu_usage: float
    timestamp: datetime
    success: bool
    error_message: str = None

class PluginMonitor:
    def __init__(self):
        self.logger = logging.getLogger("plugin_monitor")
        self.metrics = []
    
    def monitor_plugin_execution(self, plugin_name: str, func, *args, **kwargs):
        """Monitor plugin execution and collect metrics."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        start_cpu = psutil.Process().cpu_percent()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error_message = None
        except Exception as e:
            result = None
            success = False
            error_message = str(e)
            self.logger.error(f"Plugin {plugin_name} failed: {e}")
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        end_cpu = psutil.Process().cpu_percent()
        
        metrics = PluginMetrics(
            plugin_name=plugin_name,
            execution_time=end_time - start_time,
            memory_usage=end_memory - start_memory,
            cpu_usage=end_cpu - start_cpu,
            timestamp=datetime.now(),
            success=success,
            error_message=error_message
        )
        
        self.metrics.append(metrics)
        self._log_metrics(metrics)
        
        return result
    
    def _log_metrics(self, metrics: PluginMetrics):
        """Log plugin metrics."""
        self.logger.info(
            f"Plugin: {metrics.plugin_name}, "
            f"Time: {metrics.execution_time:.2f}s, "
            f"Memory: {metrics.memory_usage / 1024 / 1024:.2f}MB, "
            f"Success: {metrics.success}"
        )
    
    def get_plugin_statistics(self, plugin_name: str = None) -> Dict[str, Any]:
        """Get statistics for plugins."""
        filtered_metrics = self.metrics
        if plugin_name:
            filtered_metrics = [m for m in self.metrics if m.plugin_name == plugin_name]
        
        if not filtered_metrics:
            return {}
        
        execution_times = [m.execution_time for m in filtered_metrics]
        memory_usage = [m.memory_usage for m in filtered_metrics]
        success_rate = sum(1 for m in filtered_metrics if m.success) / len(filtered_metrics)
        
        return {
            'total_executions': len(filtered_metrics),
            'success_rate': success_rate,
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'max_execution_time': max(execution_times),
            'avg_memory_usage': sum(memory_usage) / len(memory_usage),
            'max_memory_usage': max(memory_usage)
        }
```

### Health Checks

```python
# scripts/health_check.py
import json
import sys
from utils.plugin_loader import PluginLoader
from utils.plugin_monitor import PluginMonitor

def check_plugin_system_health():
    """Perform comprehensive health check of plugin system."""
    health_report = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': 'healthy',
        'checks': {}
    }
    
    # Check plugin loading
    try:
        loader = PluginLoader()
        plugins = loader.load_plugins()
        health_report['checks']['plugin_loading'] = {
            'status': 'pass',
            'plugins_loaded': len(plugins),
            'errors': loader.get_plugin_errors()
        }
    except Exception as e:
        health_report['checks']['plugin_loading'] = {
            'status': 'fail',
            'error': str(e)
        }
        health_report['overall_status'] = 'unhealthy'
    
    # Check plugin functionality
    try:
        # Test each plugin with sample data
        import pandas as pd
        test_df1 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        test_df2 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 7]})
        
        plugin_tests = {}
        for plugin in plugins:
            try:
                result = plugin.compare(test_df1, test_df2)
                plugin_tests[plugin.get_name()] = 'pass'
            except Exception as e:
                plugin_tests[plugin.get_name()] = f'fail: {str(e)}'
        
        health_report['checks']['plugin_functionality'] = {
            'status': 'pass' if all(status == 'pass' for status in plugin_tests.values()) else 'partial',
            'plugin_tests': plugin_tests
        }
    except Exception as e:
        health_report['checks']['plugin_functionality'] = {
            'status': 'fail',
            'error': str(e)
        }
    
    # Check disk space
    import shutil
    try:
        total, used, free = shutil.disk_usage('plugins')
        free_gb = free / (1024**3)
        
        health_report['checks']['disk_space'] = {
            'status': 'pass' if free_gb > 1 else 'warning',
            'free_space_gb': free_gb
        }
    except Exception as e:
        health_report['checks']['disk_space'] = {
            'status': 'fail',
            'error': str(e)
        }
    
    return health_report

if __name__ == "__main__":
    report = check_plugin_system_health()
    print(json.dumps(report, indent=2))
    
    if report['overall_status'] != 'healthy':
        sys.exit(1)
```

## Performance Optimization

### Caching Strategy

```python
# utils/plugin_cache.py
import pickle
import hashlib
import os
from typing import Any, Optional
from datetime import datetime, timedelta

class PluginCache:
    def __init__(self, cache_dir: str = "plugins/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, plugin_name: str, df1_hash: str, df2_hash: str, params: dict) -> str:
        """Generate cache key for comparison result."""
        key_data = f"{plugin_name}:{df1_hash}:{df2_hash}:{str(sorted(params.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_dataframe_hash(self, df) -> str:
        """Generate hash for DataFrame."""
        return hashlib.md5(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()
    
    def get(self, plugin_name: str, df1, df2, params: dict, max_age_hours: int = 24) -> Optional[Any]:
        """Get cached comparison result."""
        df1_hash = self._get_dataframe_hash(df1)
        df2_hash = self._get_dataframe_hash(df2)
        cache_key = self._get_cache_key(plugin_name, df1_hash, df2_hash, params)
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        if not os.path.exists(cache_file):
            return None
        
        # Check age
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if file_age > timedelta(hours=max_age_hours):
            os.remove(cache_file)
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception:
            # Corrupted cache file
            os.remove(cache_file)
            return None
    
    def set(self, plugin_name: str, df1, df2, params: dict, result: Any) -> None:
        """Cache comparison result."""
        df1_hash = self._get_dataframe_hash(df1)
        df2_hash = self._get_dataframe_hash(df2)
        cache_key = self._get_cache_key(plugin_name, df1_hash, df2_hash, params)
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            # Log error but don't fail
            logging.getLogger("plugin_cache").warning(f"Failed to cache result: {e}")
    
    def clear(self, max_age_hours: int = 0) -> int:
        """Clear old cache files."""
        cleared = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.pkl'):
                file_path = os.path.join(self.cache_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_time < cutoff_time:
                    os.remove(file_path)
                    cleared += 1
        
        return cleared
```

### Parallel Processing

```python
# utils/plugin_executor.py
import concurrent.futures
import threading
from typing import List, Dict, Any, Callable
from queue import Queue

class PluginExecutor:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = {}
        self.task_lock = threading.Lock()
    
    def submit_comparison(self, plugin, df1, df2, params: dict, callback: Callable = None) -> str:
        """Submit comparison task for parallel execution."""
        task_id = f"{plugin.get_name()}_{threading.current_thread().ident}_{time.time()}"
        
        future = self.executor.submit(self._execute_comparison, plugin, df1, df2, params)
        
        with self.task_lock:
            self.active_tasks[task_id] = {
                'future': future,
                'plugin_name': plugin.get_name(),
                'callback': callback,
                'start_time': time.time()
            }
        
        # Add completion callback
        future.add_done_callback(lambda f: self._task_completed(task_id, f))
        
        return task_id
    
    def _execute_comparison(self, plugin, df1, df2, params: dict) -> Dict[str, Any]:
        """Execute plugin comparison with monitoring."""
        try:
            return plugin.compare(df1, df2, **params)
        except Exception as e:
            return {
                'is_equal': False,
                'details': {'summary': f'Execution failed: {str(e)}', 'errors': [str(e)]},
                'highlights': {},
                'metadata': {'plugin_name': plugin.get_name(), 'status': 'error'}
            }
    
    def _task_completed(self, task_id: str, future: concurrent.futures.Future):
        """Handle task completion."""
        with self.task_lock:
            if task_id in self.active_tasks:
                task_info = self.active_tasks.pop(task_id)
                
                if task_info['callback']:
                    try:
                        result = future.result()
                        task_info['callback'](task_id, result)
                    except Exception as e:
                        task_info['callback'](task_id, {'error': str(e)})
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a submitted task."""
        with self.task_lock:
            if task_id not in self.active_tasks:
                return {'status': 'not_found'}
            
            task_info = self.active_tasks[task_id]
            future = task_info['future']
            
            if future.done():
                try:
                    result = future.result()
                    return {'status': 'completed', 'result': result}
                except Exception as e:
                    return {'status': 'failed', 'error': str(e)}
            else:
                return {
                    'status': 'running',
                    'plugin_name': task_info['plugin_name'],
                    'elapsed_time': time.time() - task_info['start_time']
                }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        with self.task_lock:
            if task_id in self.active_tasks:
                future = self.active_tasks[task_id]['future']
                cancelled = future.cancel()
                if cancelled:
                    del self.active_tasks[task_id]
                return cancelled
        return False
    
    def shutdown(self, wait: bool = True):
        """Shutdown the executor."""
        self.executor.shutdown(wait=wait)
```

## Backup and Recovery

### Backup Strategy

```bash
#!/bin/bash
# scripts/backup_plugins.sh

BACKUP_DIR="backups/plugins"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="plugin_backup_${TIMESTAMP}.tar.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create backup archive
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
    plugins/ \
    config/plugin_config.json \
    config/security_policy.json \
    logs/plugin_system.log

echo "Backup created: ${BACKUP_DIR}/${BACKUP_FILE}"

# Keep only last 10 backups
ls -t "${BACKUP_DIR}"/plugin_backup_*.tar.gz | tail -n +11 | xargs -r rm

echo "Backup cleanup completed"
```

### Recovery Procedures

```python
# scripts/restore_plugins.py
import os
import shutil
import tarfile
import argparse
from datetime import datetime

def restore_plugins(backup_file: str, restore_point: str = None):
    """Restore plugins from backup."""
    
    # Create restore point if requested
    if restore_point:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        restore_dir = f"restore_points/{restore_point}_{timestamp}"
        os.makedirs(restore_dir, exist_ok=True)
        
        # Backup current state
        if os.path.exists("plugins"):
            shutil.copytree("plugins", f"{restore_dir}/plugins")
        if os.path.exists("config/plugin_config.json"):
            shutil.copy2("config/plugin_config.json", f"{restore_dir}/")
        
        print(f"Current state backed up to: {restore_dir}")
    
    # Extract backup
    with tarfile.open(backup_file, 'r:gz') as tar:
        tar.extractall()
    
    print(f"Plugins restored from: {backup_file}")
    
    # Reload plugins
    from utils.plugin_loader import PluginLoader
    loader = PluginLoader()
    plugins = loader.load_plugins()
    
    print(f"Loaded {len(plugins)} plugins after restore")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore plugins from backup")
    parser.add_argument("backup_file", help="Path to backup file")
    parser.add_argument("--restore-point", help="Create restore point before restoring")
    
    args = parser.parse_args()
    restore_plugins(args.backup_file, args.restore_point)
```

## Troubleshooting

### Common Issues and Solutions

#### Plugin Loading Failures

**Issue**: Plugin fails to load with import errors

**Diagnosis**:
```python
from utils.plugin_loader import PluginLoader

loader = PluginLoader()
loader.load_plugins()
errors = loader.get_plugin_errors()

for plugin_file, error in errors.items():
    print(f"Plugin: {plugin_file}")
    print(f"Error: {error}")
    print("-" * 50)
```

**Solutions**:
1. Check Python path and dependencies
2. Verify plugin syntax
3. Check file permissions
4. Review plugin requirements

#### Memory Issues

**Issue**: Out of memory errors during large dataset comparisons

**Diagnosis**:
```python
import psutil

def monitor_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")
    print(f"Available: {psutil.virtual_memory().available / 1024 / 1024:.2f} MB")
```

**Solutions**:
1. Implement chunked processing
2. Increase system memory
3. Use memory-efficient algorithms
4. Enable result caching

#### Performance Issues

**Issue**: Slow plugin execution

**Diagnosis**:
```python
import cProfile
import pstats

def profile_plugin(plugin, df1, df2, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = plugin.compare(df1, df2, **kwargs)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    return result
```

**Solutions**:
1. Optimize algorithm implementation
2. Use vectorized operations
3. Implement parallel processing
4. Add progress indicators

### Diagnostic Tools

```python
# scripts/diagnose_plugins.py
import sys
import traceback
from utils.plugin_loader import PluginLoader
from utils.plugin_monitor import PluginMonitor

def run_comprehensive_diagnosis():
    """Run comprehensive plugin system diagnosis."""
    
    print("=== Plugin System Diagnosis ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()
    
    # Test plugin loading
    print("1. Testing plugin loading...")
    try:
        loader = PluginLoader()
        plugins = loader.load_plugins()
        print(f"   ✓ Loaded {len(plugins)} plugins")
        
        errors = loader.get_plugin_errors()
        if errors:
            print(f"   ⚠ {len(errors)} plugins failed to load:")
            for plugin_file, error in errors.items():
                print(f"     - {plugin_file}: {error}")
    except Exception as e:
        print(f"   ✗ Plugin loading failed: {e}")
        traceback.print_exc()
    
    print()
    
    # Test plugin functionality
    print("2. Testing plugin functionality...")
    import pandas as pd
    
    test_df1 = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'value': [10, 20, 30, 40, 50]
    })
    
    test_df2 = pd.DataFrame({
        'id': [1, 2, 3, 4, 6],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Frank'],
        'value': [10, 25, 30, 40, 60]
    })
    
    for plugin in plugins:
        try:
            result = plugin.compare(test_df1, test_df2)
            if isinstance(result, dict) and 'is_equal' in result:
                print(f"   ✓ {plugin.get_name()}: Working")
            else:
                print(f"   ⚠ {plugin.get_name()}: Invalid result format")
        except Exception as e:
            print(f"   ✗ {plugin.get_name()}: {e}")
    
    print()
    
    # Test system resources
    print("3. Checking system resources...")
    try:
        import psutil
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        print(f"   Memory: {memory.available / 1024**3:.2f} GB available")
        print(f"   Disk: {disk.free / 1024**3:.2f} GB free")
        print(f"   CPU cores: {psutil.cpu_count()}")
    except ImportError:
        print("   ⚠ psutil not available for resource monitoring")
    
    print()
    print("=== Diagnosis Complete ===")

if __name__ == "__main__":
    run_comprehensive_diagnosis()
```

## User Management

### Role-Based Access Control

```python
# utils/plugin_rbac.py
from enum import Enum
from typing import List, Dict, Any
import json

class Permission(Enum):
    INSTALL_PLUGIN = "install_plugin"
    REMOVE_PLUGIN = "remove_plugin"
    CONFIGURE_PLUGIN = "configure_plugin"
    USE_PLUGIN = "use_plugin"
    MANAGE_SECURITY = "manage_security"
    VIEW_LOGS = "view_logs"
    MANAGE_USERS = "manage_users"

class Role(Enum):
    ADMIN = "admin"
    POWER_USER = "power_user"
    USER = "user"
    GUEST = "guest"

class PluginRBAC:
    def __init__(self, config_file: str = "config/rbac.json"):
        self.config_file = config_file
        self.permissions = self._load_permissions()
    
    def _load_permissions(self) -> Dict[Role, List[Permission]]:
        """Load role permissions from configuration."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            permissions = {}
            for role_name, perms in config.items():
                role = Role(role_name)
                permissions[role] = [Permission(p) for p in perms]
            
            return permissions
        except FileNotFoundError:
            return self._get_default_permissions()
    
    def _get_default_permissions(self) -> Dict[Role, List[Permission]]:
        """Get default role permissions."""
        return {
            Role.ADMIN: list(Permission),
            Role.POWER_USER: [
                Permission.INSTALL_PLUGIN,
                Permission.CONFIGURE_PLUGIN,
                Permission.USE_PLUGIN,
                Permission.VIEW_LOGS
            ],
            Role.USER: [
                Permission.USE_PLUGIN,
                Permission.CONFIGURE_PLUGIN
            ],
            Role.GUEST: [
                Permission.USE_PLUGIN
            ]
        }
    
    def has_permission(self, user_role: Role, permission: Permission) -> bool:
        """Check if role has specific permission."""
        return permission in self.permissions.get(user_role, [])
    
    def get_allowed_plugins(self, user_role: Role) -> List[str]:
        """Get list of plugins user can access."""
        if self.has_permission(user_role, Permission.USE_PLUGIN):
            # Load plugin restrictions from config
            try:
                with open("config/plugin_access.json", 'r') as f:
                    access_config = json.load(f)
                return access_config.get(user_role.value, [])
            except FileNotFoundError:
                # Default: all plugins for users with USE_PLUGIN permission
                return ["all"]
        return []
```

### User Session Management

```python
# utils/session_manager.py
import uuid
import time
from typing import Dict, Optional
from dataclasses import dataclass
from utils.plugin_rbac import Role, PluginRBAC

@dataclass
class UserSession:
    session_id: str
    user_id: str
    role: Role
    created_at: float
    last_activity: float
    active_plugins: List[str]

class SessionManager:
    def __init__(self, session_timeout: int = 3600):
        self.sessions: Dict[str, UserSession] = {}
        self.session_timeout = session_timeout
        self.rbac = PluginRBAC()
    
    def create_session(self, user_id: str, role: Role) -> str:
        """Create new user session."""
        session_id = str(uuid.uuid4())
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            role=role,
            created_at=time.time(),
            last_activity=time.time(),
            active_plugins=[]
        )
        
        self.sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID."""
        session = self.sessions.get(session_id)
        
        if session and self._is_session_valid(session):
            session.last_activity = time.time()
            return session
        elif session:
            # Session expired
            del self.sessions[session_id]
        
        return None
    
    def _is_session_valid(self, session: UserSession) -> bool:
        """Check if session is still valid."""
        return (time.time() - session.last_activity) < self.session_timeout
    
    def authorize_plugin_access(self, session_id: str, plugin_name: str) -> bool:
        """Check if user can access specific plugin."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        allowed_plugins = self.rbac.get_allowed_plugins(session.role)
        return "all" in allowed_plugins or plugin_name in allowed_plugins
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions."""
        current_time = time.time()
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if (current_time - session.last_activity) >= self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        return len(expired_sessions)
```

## Plugin Repository Management

### Repository Configuration

```json
{
  "repositories": [
    {
      "name": "official",
      "url": "https://plugins.csvquery.com/api/v1",
      "type": "rest_api",
      "enabled": true,
      "auto_update": true,
      "update_interval_hours": 24,
      "authentication": {
        "type": "api_key",
        "key": "${OFFICIAL_REPO_API_KEY}"
      },
      "trust_level": "high"
    },
    {
      "name": "community",
      "url": "https://github.com/csvquery/community-plugins",
      "type": "git",
      "enabled": true,
      "auto_update": false,
      "branch": "main",
      "trust_level": "medium"
    },
    {
      "name": "internal",
      "url": "file:///opt/csvquery/internal-plugins",
      "type": "local",
      "enabled": true,
      "trust_level": "high"
    }
  ],
  "security": {
    "require_signature_verification": true,
    "allowed_trust_levels": ["high", "medium"],
    "quarantine_unknown_plugins": true
  }
}
```

### Repository Management Tools

```python
# scripts/manage_repositories.py
import json
import requests
import git
from typing import List, Dict, Any
from utils.plugin_downloader import PluginDownloader

class RepositoryManager:
    def __init__(self, config_file: str = "config/repositories.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.downloader = PluginDownloader()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load repository configuration."""
        with open(self.config_file, 'r') as f:
            return json.load(f)
    
    def sync_repository(self, repo_name: str) -> Dict[str, Any]:
        """Sync plugins from repository."""
        repo_config = next(
            (repo for repo in self.config['repositories'] if repo['name'] == repo_name),
            None
        )
        
        if not repo_config or not repo_config['enabled']:
            return {'status': 'error', 'message': 'Repository not found or disabled'}
        
        if repo_config['type'] == 'rest_api':
            return self._sync_rest_api_repository(repo_config)
        elif repo_config['type'] == 'git':
            return self._sync_git_repository(repo_config)
        elif repo_config['type'] == 'local':
            return self._sync_local_repository(repo_config)
        else:
            return {'status': 'error', 'message': f"Unknown repository type: {repo_config['type']}"}
    
    def _sync_rest_api_repository(self, repo_config: Dict[str, Any]) -> Dict[str, Any]:
        """Sync from REST API repository."""
        try:
            headers = {}
            if 'authentication' in repo_config:
                auth = repo_config['authentication']
                if auth['type'] == 'api_key':
                    headers['Authorization'] = f"Bearer {auth['key']}"
            
            response = requests.get(f"{repo_config['url']}/plugins", headers=headers)
            response.raise_for_status()
            
            plugins = response.json()
            synced_plugins = []
            
            for plugin_info in plugins:
                download_url = plugin_info['download_url']
                plugin_name = plugin_info['name']
                
                # Download and install plugin
                result = self.downloader.download_plugin(download_url, plugin_name)
                if result['success']:
                    synced_plugins.append(plugin_name)
            
            return {
                'status': 'success',
                'synced_plugins': synced_plugins,
                'total_available': len(plugins)
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _sync_git_repository(self, repo_config: Dict[str, Any]) -> Dict[str, Any]:
        """Sync from Git repository."""
        try:
            repo_dir = f"plugins/repositories/{repo_config['name']}"
            
            if os.path.exists(repo_dir):
                # Update existing repository
                repo = git.Repo(repo_dir)
                repo.remotes.origin.pull()
            else:
                # Clone repository
                git.Repo.clone_from(repo_config['url'], repo_dir)
            
            # Copy plugins to main plugins directory
            synced_plugins = []
            plugins_dir = os.path.join(repo_dir, 'plugins')
            
            if os.path.exists(plugins_dir):
                for filename in os.listdir(plugins_dir):
                    if filename.endswith('.py') or filename.endswith('.zip'):
                        src = os.path.join(plugins_dir, filename)
                        dst = os.path.join('plugins', filename)
                        shutil.copy2(src, dst)
                        synced_plugins.append(filename)
            
            return {
                'status': 'success',
                'synced_plugins': synced_plugins
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def list_available_plugins(self, repo_name: str = None) -> List[Dict[str, Any]]:
        """List available plugins from repositories."""
        all_plugins = []
        
        repositories = self.config['repositories']
        if repo_name:
            repositories = [repo for repo in repositories if repo['name'] == repo_name]
        
        for repo_config in repositories:
            if not repo_config['enabled']:
                continue
            
            try:
                if repo_config['type'] == 'rest_api':
                    plugins = self._list_rest_api_plugins(repo_config)
                elif repo_config['type'] == 'git':
                    plugins = self._list_git_plugins(repo_config)
                elif repo_config['type'] == 'local':
                    plugins = self._list_local_plugins(repo_config)
                else:
                    continue
                
                for plugin in plugins:
                    plugin['repository'] = repo_config['name']
                    all_plugins.append(plugin)
                    
            except Exception as e:
                print(f"Error listing plugins from {repo_config['name']}: {e}")
        
        return all_plugins
```

## Deployment Strategies

### Production Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  csvquery:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./plugins:/app/plugins
      - ./config:/app/config
      - ./logs:/app/logs
      - ./data:/app/data
    environment:
      - PLUGIN_ENV=production
      - PLUGIN_SECURITY_STRICT=true
      - PLUGIN_CACHE_ENABLED=true
    restart: unless-stopped
    
  plugin-monitor:
    build: ./monitoring
    ports:
      - "9090:9090"
    volumes:
      - ./logs:/app/logs:ro
    depends_on:
      - csvquery
    restart: unless-stopped
```

### Kubernetes Deployment

```yaml
# k8s/plugin-system.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: csvquery-plugin-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: csvquery
  template:
    metadata:
      labels:
        app: csvquery
    spec:
      containers:
      - name: csvquery
        image: csvquery:latest
        ports:
        - containerPort: 8080
        env:
        - name: PLUGIN_ENV
          value: "production"
        - name: PLUGIN_SECURITY_STRICT
          value: "true"
        volumeMounts:
        - name: plugin-storage
          mountPath: /app/plugins
        - name: config-volume
          mountPath: /app/config
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: plugin-storage
        persistentVolumeClaim:
          claimName: plugin-storage-pvc
      - name: config-volume
        configMap:
          name: plugin-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: plugin-config
data:
  plugin_config.json: |
    {
      "plugin_system": {
        "enabled": true,
        "max_concurrent_comparisons": 4
      }
    }
```

### CI/CD Pipeline

```yaml
# .github/workflows/plugin-deployment.yml
name: Plugin System Deployment

on:
  push:
    branches: [main]
    paths: ['plugins/**', 'utils/plugin_*']

jobs:
  test-plugins:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run plugin tests
      run: |
        python test_plugins.py
        pytest tests/test_plugin_system.py -v --cov=utils/
    
    - name: Security scan
      run: |
        python scripts/security_scan.py plugins/
  
  deploy-staging:
    needs: test-plugins
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to staging
      run: |
        # Deploy to staging environment
        kubectl apply -f k8s/staging/
        kubectl rollout status deployment/csvquery-plugin-system
  
  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
    - name: Deploy to production
      run: |
        # Deploy to production environment
        kubectl apply -f k8s/production/
        kubectl rollout status deployment/csvquery-plugin-system
```

## Maintenance Procedures

### Regular Maintenance Tasks

```bash
#!/bin/bash
# scripts/maintenance.sh

echo "Starting plugin system maintenance..."

# 1. Clean old cache files
echo "Cleaning cache..."
python -c "from utils.plugin_cache import PluginCache; PluginCache().clear(max_age_hours=168)"  # 1 week

# 2. Rotate logs
echo "Rotating logs..."
find logs/ -name "*.log" -size +100M -exec gzip {} \;
find logs/ -name "*.log.gz" -mtime +30 -delete

# 3. Update plugin repositories
echo "Updating repositories..."
python scripts/update_repositories.py

# 4. Run health checks
echo "Running health checks..."
python scripts/health_check.py

# 5. Backup plugins
echo "Creating backup..."
./scripts/backup_plugins.sh

# 6. Check for plugin updates
echo "Checking for updates..."
python scripts/check_updates.py

# 7. Validate all plugins
echo "Validating plugins..."
python scripts/validate_plugins.py

echo "Maintenance completed successfully!"
```

### Automated Maintenance

```python
# scripts/automated_maintenance.py
import schedule
import time
import logging
from datetime import datetime
from utils.plugin_cache import PluginCache
from utils.plugin_loader import PluginLoader
from scripts.health_check import check_plugin_system_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def daily_maintenance():
    """Run daily maintenance tasks."""
    logger.info("Starting daily maintenance")
    
    # Clean cache
    cache = PluginCache()
    cleared = cache.clear(max_age_hours=24)
    logger.info(f"Cleared {cleared} old cache files")
    
    # Health check
    health = check_plugin_system_health()
    if health['overall_status'] != 'healthy':
        logger.warning(f"Health check failed: {health}")
    
    logger.info("Daily maintenance completed")

def weekly_maintenance():
    """Run weekly maintenance tasks."""
    logger.info("Starting weekly maintenance")
    
    # Full plugin validation
    loader = PluginLoader()
    loader.reload_plugins()
    
    # Deep cache clean
    cache = PluginCache()
    cleared = cache.clear(max_age_hours=0)  # Clear all
    logger.info(f"Cleared all cache files: {cleared}")
    
    logger.info("Weekly maintenance completed")

# Schedule maintenance tasks
schedule.every().day.at("02:00").do(daily_maintenance)
schedule.every().sunday.at("03:00").do(weekly_maintenance)

if __name__ == "__main__":
    logger.info("Starting maintenance scheduler")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
```

### Plugin Lifecycle Management

```python
# utils/plugin_lifecycle.py
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

class PluginStatus(Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"
    QUARANTINED = "quarantined"
    PENDING_REMOVAL = "pending_removal"

@dataclass
class PluginLifecycle:
    plugin_name: str
    version: str
    status: PluginStatus
    install_date: datetime
    last_used: datetime
    usage_count: int
    deprecation_date: Optional[datetime] = None
    removal_date: Optional[datetime] = None
    reason: Optional[str] = None

class PluginLifecycleManager:
    def __init__(self, config_file: str = "config/plugin_lifecycle.json"):
        self.config_file = config_file
        self.plugins: Dict[str, PluginLifecycle] = self._load_lifecycle_data()
    
    def register_plugin(self, plugin_name: str, version: str) -> None:
        """Register a new plugin in the lifecycle system."""
        lifecycle = PluginLifecycle(
            plugin_name=plugin_name,
            version=version,
            status=PluginStatus.ACTIVE,
            install_date=datetime.now(),
            last_used=datetime.now(),
            usage_count=0
        )
        self.plugins[plugin_name] = lifecycle
        self._save_lifecycle_data()
    
    def record_usage(self, plugin_name: str) -> None:
        """Record plugin usage."""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].last_used = datetime.now()
            self.plugins[plugin_name].usage_count += 1
            self._save_lifecycle_data()
    
    def deprecate_plugin(self, plugin_name: str, reason: str, removal_days: int = 90) -> None:
        """Mark plugin as deprecated."""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].status = PluginStatus.DEPRECATED
            self.plugins[plugin_name].deprecation_date = datetime.now()
            self.plugins[plugin_name].removal_date = datetime.now() + timedelta(days=removal_days)
            self.plugins[plugin_name].reason = reason
            self._save_lifecycle_data()
    
    def get_plugins_for_removal(self) -> List[str]:
        """Get list of plugins ready for removal."""
        now = datetime.now()
        return [
            name for name, lifecycle in self.plugins.items()
            if lifecycle.removal_date and lifecycle.removal_date <= now
        ]
    
    def get_unused_plugins(self, days: int = 30) -> List[str]:
        """Get list of plugins not used in specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            name for name, lifecycle in self.plugins.items()
            if lifecycle.last_used < cutoff and lifecycle.usage_count == 0
        ]
```

## API Administration

### REST API for Plugin Management

```python
# api/plugin_admin_api.py
from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from utils.plugin_loader import PluginLoader
from utils.plugin_rbac import PluginRBAC, Role, Permission
from utils.session_manager import SessionManager

app = Flask(__name__)
auth = HTTPBasicAuth()

loader = PluginLoader()
rbac = PluginRBAC()
session_manager = SessionManager()

@auth.verify_password
def verify_password(username, password):
    # Implement your authentication logic here
    return True  # Placeholder

@app.route('/api/plugins', methods=['GET'])
@auth.login_required
def list_plugins():
    """List all available plugins."""
    try:
        plugins = loader.get_available_plugins()
        plugin_info = []
        
        for name, plugin_class in plugins.items():
            info = loader.get_plugin_info(name)
            plugin_info.append({
                'name': name,
                'description': info.get('description', ''),
                'version': info.get('version', '1.0.0'),
                'author': info.get('author', 'Unknown'),
                'status': 'active'
            })
        
        return jsonify({
            'status': 'success',
            'plugins': plugin_info
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/plugins/<plugin_name>', methods=['GET'])
@auth.login_required
def get_plugin_details(plugin_name):
    """Get detailed information about a specific plugin."""
    try:
        info = loader.get_plugin_info(plugin_name)
        if not info:
            return jsonify({
                'status': 'error',
                'message': 'Plugin not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'plugin': info
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/plugins/<plugin_name>/install', methods=['POST'])
@auth.login_required
def install_plugin(plugin_name):
    """Install a plugin from repository."""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({
                'status': 'error',
                'message': 'Plugin URL required'
            }), 400
        
        result = loader.install_plugin_from_url(url)
        
        return jsonify({
            'status': 'success' if result else 'error',
            'message': 'Plugin installed successfully' if result else 'Installation failed'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/plugins/<plugin_name>/uninstall', methods=['DELETE'])
@auth.login_required
def uninstall_plugin(plugin_name):
    """Uninstall a plugin."""
    try:
        result = loader.uninstall_plugin(plugin_name)
        
        return jsonify({
            'status': 'success' if result else 'error',
            'message': 'Plugin uninstalled successfully' if result else 'Uninstallation failed'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/system/health', methods=['GET'])
@auth.login_required
def system_health():
    """Get system health status."""
    try:
        from scripts.health_check import check_plugin_system_health
        health = check_plugin_system_health()
        
        return jsonify({
            'status': 'success',
            'health': health
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### Command Line Interface

```python
# cli/plugin_admin_cli.py
import click
import json
from utils.plugin_loader import PluginLoader
from scripts.health_check import check_plugin_system_health
from scripts.manage_config import PluginConfigManager

@click.group()
def cli():
    """Plugin Administration CLI"""
    pass

@cli.command()
def list_plugins():
    """List all available plugins"""
    loader = PluginLoader()
    plugins = loader.get_available_plugins()
    
    click.echo("Available Plugins:")
    click.echo("-" * 50)
    
    for name, plugin_class in plugins.items():
        info = loader.get_plugin_info(name)
        click.echo(f"Name: {name}")
        click.echo(f"Description: {info.get('description', 'N/A')}")
        click.echo(f"Version: {info.get('version', '1.0.0')}")
        click.echo("-" * 30)

@cli.command()
@click.argument('plugin_name')
def plugin_info(plugin_name):
    """Get detailed information about a plugin"""
    loader = PluginLoader()
    info = loader.get_plugin_info(plugin_name)
    
    if info:
        click.echo(json.dumps(info, indent=2))
    else:
        click.echo(f"Plugin '{plugin_name}' not found")

@cli.command()
@click.argument('url')
def install(url):
    """Install plugin from URL"""
    loader = PluginLoader()
    
    with click.progressbar(length=100, label='Installing plugin') as bar:
        result = loader.install_plugin_from_url(url)
        bar.update(100)
    
    if result:
        click.echo("Plugin installed successfully")
    else:
        click.echo("Plugin installation failed")

@cli.command()
@click.argument('plugin_name')
def uninstall(plugin_name):
    """Uninstall a plugin"""
    if click.confirm(f"Are you sure you want to uninstall '{plugin_name}'?"):
        loader = PluginLoader()
        result = loader.uninstall_plugin(plugin_name)
        
        if result:
            click.echo("Plugin uninstalled successfully")
        else:
            click.echo("Plugin uninstallation failed")

@cli.command()
def health():
    """Check system health"""
    health = check_plugin_system_health()
    
    status_color = 'green' if health['overall_status'] == 'healthy' else 'red'
    click.echo(f"Overall Status: ", nl=False)
    click.secho(health['overall_status'].upper(), fg=status_color)
    
    for check_name, check_result in health['checks'].items():
        status = check_result.get('status', 'unknown')
        color = 'green' if status == 'pass' else 'red'
        click.echo(f"{check_name}: ", nl=False)
        click.secho(status.upper(), fg=color)

@cli.command()
@click.argument('plugin_name')
@click.option('--enable/--disable', default=True)
def toggle(plugin_name, enable):
    """Enable or disable a plugin"""
    config_manager = PluginConfigManager()
    
    if enable:
        config_manager.enable_plugin(plugin_name)
        click.echo(f"Plugin '{plugin_name}' enabled")
    else:
        config_manager.disable_plugin(plugin_name)
        click.echo(f"Plugin '{plugin_name}' disabled")

if __name__ == '__main__':
    cli()
```

## Conclusion

This administrator reference guide provides comprehensive documentation for managing the plugin system in the CSV Query Tool. It covers all aspects of plugin administration from installation and configuration to monitoring and troubleshooting.

### Key Takeaways

1. **Security First**: Always prioritize security when managing plugins
2. **Regular Maintenance**: Implement automated maintenance procedures
3. **Monitor Performance**: Keep track of plugin performance and resource usage
4. **Plan for Scale**: Design your deployment to handle growth
5. **Document Everything**: Maintain clear documentation for all procedures

### Support and Resources

- **Documentation**: `/docs/` directory
- **Issue Tracking**: GitHub Issues
- **Community**: Plugin developer forums
- **Professional Support**: Contact the development team

### Version History

- **v1.0.0**: Initial plugin system implementation
- **v1.1.0**: Added security features and RBAC
- **v1.2.0**: Enhanced monitoring and performance optimization

For the latest updates and additional resources, visit the project repository and documentation site.