import requests
import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import QProgressDialog, QMessageBox, QApplication

class PluginDownloadWorker(QThread):
    """Worker thread for downloading plugins."""
    
    progress_updated = pyqtSignal(int)  # Progress percentage
    status_updated = pyqtSignal(str)    # Status message
    download_finished = pyqtSignal(bool, str)  # Success, message
    
    def __init__(self, url: str, destination: str, filename: Optional[str] = None):
        super().__init__()
        self.url = url
        self.destination = Path(destination)
        self.filename = filename
        self.cancelled = False
    
    def run(self):
        """Download the plugin file."""
        try:
            self.status_updated.emit("Starting download...")
            
            # Make request with stream=True for progress tracking
            response = requests.get(self.url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Determine filename
            if not self.filename:
                # Try to get filename from Content-Disposition header
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    self.filename = content_disposition.split('filename=')[1].strip('"\'')
                else:
                    # Extract from URL
                    self.filename = self.url.split('/')[-1]
                    if not self.filename.endswith(('.py', '.zip')):
                        self.filename += '.py'
            
            # Ensure destination directory exists
            self.destination.mkdir(parents=True, exist_ok=True)
            
            # Full path for the downloaded file
            file_path = self.destination / self.filename
            
            # Get total file size for progress tracking
            total_size = int(response.headers.get('Content-Length', 0))
            
            self.status_updated.emit(f"Downloading {self.filename}...")
            
            # Download with progress tracking
            downloaded_size = 0
            chunk_size = 8192
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.cancelled:
                        f.close()
                        file_path.unlink(missing_ok=True)
                        self.download_finished.emit(False, "Download cancelled")
                        return
                    
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Update progress
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.progress_updated.emit(progress)
            
            self.status_updated.emit("Download completed")
            self.download_finished.emit(True, f"Successfully downloaded {self.filename}")
            
        except requests.exceptions.RequestException as e:
            self.download_finished.emit(False, f"Network error: {str(e)}")
        except Exception as e:
            self.download_finished.emit(False, f"Download error: {str(e)}")
    
    def cancel(self):
        """Cancel the download."""
        self.cancelled = True

class PluginDownloader(QObject):
    """Plugin downloader with GUI integration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.download_worker = None
        self.progress_dialog = None
    
    def download_plugin(self, url: str, destination: str, filename: Optional[str] = None) -> bool:
        """Download a plugin with progress dialog."""
        try:
            # Create progress dialog
            self.progress_dialog = QProgressDialog(
                "Downloading plugin...", "Cancel", 0, 100, self.parent
            )
            self.progress_dialog.setWindowTitle("Plugin Download")
            self.progress_dialog.setModal(True)
            self.progress_dialog.show()
            
            # Create and start download worker
            self.download_worker = PluginDownloadWorker(url, destination, filename)
            
            # Connect signals
            self.download_worker.progress_updated.connect(self.progress_dialog.setValue)
            self.download_worker.status_updated.connect(self.progress_dialog.setLabelText)
            self.download_worker.download_finished.connect(self._on_download_finished)
            self.progress_dialog.canceled.connect(self._on_download_cancelled)
            
            # Start download
            self.download_worker.start()
            
            # Process events until download is complete
            while self.download_worker.isRunning():
                QApplication.processEvents()
                self.download_worker.msleep(50)
            
            return True
            
        except Exception as e:
            self._show_error(f"Failed to start download: {str(e)}")
            return False
    
    def _on_download_finished(self, success: bool, message: str):
        """Handle download completion."""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        if success:
            QMessageBox.information(
                self.parent,
                "Download Complete",
                message
            )
        else:
            self._show_error(message)
    
    def _on_download_cancelled(self):
        """Handle download cancellation."""
        if self.download_worker:
            self.download_worker.cancel()
    
    def _show_error(self, message: str):
        """Show error message."""
        QMessageBox.critical(
            self.parent,
            "Download Error",
            message
        )
    
    @staticmethod
    def download_plugin_sync(url: str, destination: str, filename: Optional[str] = None, 
                           progress_callback: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
        """Download a plugin synchronously without GUI."""
        result = {
            'success': False,
            'message': '',
            'filename': filename,
            'file_path': None
        }
        
        try:
            # Make request
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Determine filename
            if not filename:
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"\'')
                else:
                    filename = url.split('/')[-1]
                    if not filename.endswith(('.py', '.zip')):
                        filename += '.py'
            
            result['filename'] = filename
            
            # Ensure destination directory exists
            dest_path = Path(destination)
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # Full path for the downloaded file
            file_path = dest_path / filename
            result['file_path'] = str(file_path)
            
            # Get total file size
            total_size = int(response.headers.get('Content-Length', 0))
            
            # Download with progress tracking
            downloaded_size = 0
            chunk_size = 8192
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Update progress
                        if progress_callback and total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            progress_callback(progress)
            
            result['success'] = True
            result['message'] = f"Successfully downloaded {filename}"
            
        except requests.exceptions.RequestException as e:
            result['message'] = f"Network error: {str(e)}"
        except Exception as e:
            result['message'] = f"Download error: {str(e)}"
        
        return result
    
    @staticmethod
    def validate_plugin_url(url: str) -> Dict[str, Any]:
        """Validate a plugin URL without downloading."""
        result = {
            'valid': False,
            'message': '',
            'filename': '',
            'size': 0,
            'content_type': ''
        }
        
        try:
            # Make HEAD request to check if URL is valid
            response = requests.head(url, timeout=10)
            response.raise_for_status()
            
            # Get file information
            content_type = response.headers.get('Content-Type', '')
            content_length = response.headers.get('Content-Length', '0')
            content_disposition = response.headers.get('Content-Disposition', '')
            
            # Determine filename
            filename = ''
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"\'')
            else:
                filename = url.split('/')[-1]
            
            # Validate file type
            if not filename.endswith(('.py', '.zip')):
                if 'python' in content_type.lower() or 'text' in content_type.lower():
                    filename += '.py'
                elif 'zip' in content_type.lower() or 'application/zip' in content_type.lower():
                    filename += '.zip'
                else:
                    result['message'] = f"Unsupported file type: {content_type}"
                    return result
            
            result['valid'] = True
            result['filename'] = filename
            result['size'] = int(content_length)
            result['content_type'] = content_type
            result['message'] = "URL is valid"
            
        except requests.exceptions.RequestException as e:
            result['message'] = f"Network error: {str(e)}"
        except Exception as e:
            result['message'] = f"Validation error: {str(e)}"
        
        return result
    
    @staticmethod
    def extract_plugin_info_from_url(url: str) -> Dict[str, str]:
        """Extract plugin information from URL (for GitHub, GitLab, etc.)."""
        info = {
            'name': '',
            'description': '',
            'author': '',
            'repository': ''
        }
        
        try:
            # Parse GitHub URLs
            if 'github.com' in url:
                parts = url.split('/')
                if len(parts) >= 5:
                    info['author'] = parts[3]
                    info['repository'] = parts[4]
                    info['name'] = parts[-1].replace('.py', '').replace('.zip', '')
                    info['description'] = f"Plugin from {info['author']}/{info['repository']}"
            
            # Parse GitLab URLs
            elif 'gitlab.com' in url:
                parts = url.split('/')
                if len(parts) >= 5:
                    info['author'] = parts[3]
                    info['repository'] = parts[4]
                    info['name'] = parts[-1].replace('.py', '').replace('.zip', '')
                    info['description'] = f"Plugin from {info['author']}/{info['repository']}"
            
            # Generic URL
            else:
                filename = url.split('/')[-1]
                info['name'] = filename.replace('.py', '').replace('.zip', '')
                info['description'] = f"Plugin from {url}"
        
        except Exception:
            pass
        
        return info

class PluginRepository:
    """Manages a repository of available plugins."""
    
    def __init__(self):
        self.repositories = [
            {
                'name': 'Official Plugins',
                'url': 'https://raw.githubusercontent.com/example/plugins/main/repository.json',
                'plugins': []
            }
        ]
    
    def add_repository(self, name: str, url: str):
        """Add a plugin repository."""
        self.repositories.append({
            'name': name,
            'url': url,
            'plugins': []
        })
    
    def refresh_repositories(self) -> bool:
        """Refresh plugin lists from all repositories."""
        success = True
        
        for repo in self.repositories:
            try:
                response = requests.get(repo['url'], timeout=10)
                response.raise_for_status()
                
                repo_data = response.json()
                repo['plugins'] = repo_data.get('plugins', [])
                
            except Exception as e:
                print(f"Failed to refresh repository {repo['name']}: {e}")
                success = False
        
        return success
    
    def get_available_plugins(self) -> List[Dict[str, Any]]:
        """Get list of all available plugins from all repositories."""
        all_plugins = []
        
        for repo in self.repositories:
            for plugin in repo['plugins']:
                plugin_info = plugin.copy()
                plugin_info['repository'] = repo['name']
                all_plugins.append(plugin_info)
        
        return all_plugins
    
    def find_plugin(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a plugin by name."""
        for repo in self.repositories:
            for plugin in repo['plugins']:
                if plugin.get('name', '').lower() == name.lower():
                    plugin_info = plugin.copy()
                    plugin_info['repository'] = repo['name']
                    return plugin_info
        
        return None